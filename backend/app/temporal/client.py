"""Temporal client factory (Phase 16)."""

from __future__ import annotations

from functools import lru_cache

from temporalio.client import Client

from app.core.config import get_settings
from app.core.logging.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def temporal_target() -> str:
    return get_settings().TEMPORAL_HOST


async def get_temporal_client() -> Client:
    settings = get_settings()
    client = await Client.connect(
        settings.TEMPORAL_HOST,
        namespace=settings.TEMPORAL_NAMESPACE,
    )
    logger.debug("temporal.client.connected", host=settings.TEMPORAL_HOST)
    return client
