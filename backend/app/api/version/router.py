"""
Version endpoint.

GET /api/v1/version — returns application name, version, and environment.

Intentionally unauthenticated and allocation-free; safe to call from
dashboards, CI pipelines, and deployment scripts.
"""

from fastapi import APIRouter, status

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.common import VersionResponse

router = APIRouter(prefix="/version", tags=["Version"])
logger = get_logger(__name__)
_settings = get_settings()


@router.get(
    "",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Application version",
    description="Returns the application name, semantic version, and active environment.",
)
async def get_version() -> VersionResponse:
    logger.debug("version.request")
    return VersionResponse(
        application=_settings.APP_NAME,
        version=_settings.APP_VERSION,
        environment=_settings.APP_ENV,
    )
