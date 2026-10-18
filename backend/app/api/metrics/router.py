"""Prometheus metrics scrape endpoint."""

from fastapi import APIRouter, Response

from app.core.config import get_settings
from app.core.observability.metrics import metrics_payload

router = APIRouter(tags=["Observability"])


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    if not get_settings().METRICS_ENABLED:
        return Response(status_code=404, content="metrics disabled")
    body, content_type = metrics_payload()
    return Response(content=body, media_type=content_type)
