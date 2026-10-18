"""
AGRIFLOW-AI — FastAPI application entry point.

Startup sequence:
  1. Configure structured logging
  2. Load and validate settings
  3. Mount API routers under /api/v1
  4. Register global exception handlers
  5. Attach lifespan context manager (DB pool warm-up / teardown)
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.security.headers import SecurityHeadersMiddleware
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import engine

settings = get_settings()

configure_logging(
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage resources that must be initialised once and cleaned up on shutdown."""
    logger.info(
        "startup",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
    )
    yield
    await engine.dispose()
    logger.info("shutdown", app=settings.APP_NAME)


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AGRIFLOW-AI — Agricultural Decision Intelligence Platform. "
            "AI-powered crop management, yield forecasting, and field analytics."
        ),
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.METRICS_ENABLED:
        from app.core.observability.metrics import HTTP_LATENCY, HTTP_REQUESTS

        @app.middleware("http")
        async def prometheus_http_middleware(request: Request, call_next):
            if request.url.path.endswith("/metrics"):
                return await call_next(request)
            start = time.perf_counter()
            response = await call_next(request)
            route = request.scope.get("route")
            path_template = getattr(route, "path", request.url.path)
            elapsed = time.perf_counter() - start
            HTTP_REQUESTS.labels(
                method=request.method,
                path_template=path_template,
                status=str(response.status_code),
            ).inc()
            HTTP_LATENCY.labels(method=request.method, path_template=path_template).observe(
                elapsed
            )
            return response

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # ── Exception Handlers ────────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            path=str(request.url),
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred.", "code": "INTERNAL_ERROR"},
        )

    return app


app = create_application()
