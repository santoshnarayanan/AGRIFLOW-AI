"""
Health check endpoints.

GET /api/v1/health/live   — Kubernetes liveness probe (app is running)
GET /api/v1/health/ready  — Kubernetes readiness probe (app + DB are reachable)

These endpoints are intentionally unauthenticated and fast — they are called
frequently by load balancers and orchestrators.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.dependencies import get_db
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])
logger = get_logger(__name__)
_settings = get_settings()


@router.get(
    "/live",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Returns 200 if the application process is running.",
)
async def liveness() -> HealthResponse:
    return HealthResponse(
        status="alive",
        version=_settings.APP_VERSION,
        environment=_settings.APP_ENV,
        database="unchecked",
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Returns 200 only when the application and PostgreSQL are reachable.",
)
async def readiness(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    db_status = "unreachable"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
        logger.info("health.ready", db=db_status)
    except Exception as exc:
        logger.error("health.ready.db_error", error=str(exc))
        db_status = "unreachable"

    return HealthResponse(
        status="ready" if db_status == "connected" else "degraded",
        version=_settings.APP_VERSION,
        environment=_settings.APP_ENV,
        database=db_status,
    )
