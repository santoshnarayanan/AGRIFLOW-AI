"""Optional API-key guard for domain event operations endpoints (Phase 14)."""

from fastapi import Header, HTTPException, status

from app.core.config import Settings, get_settings


async def require_events_ops_key(
    x_events_ops_key: str | None = Header(default=None, alias="X-Events-Ops-Key"),
) -> None:
    """
    Protect outbox inspection and replay routes.

    When ``EVENTS_OPS_API_KEY`` is unset in development, ops routes remain open.
    In staging/production, the key must be configured and sent on every request.
    """
    settings = get_settings()
    expected = settings.EVENTS_OPS_API_KEY

    if not expected:
        if settings.APP_ENV == "development":
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Events ops API key is not configured.",
        )

    if not x_events_ops_key or x_events_ops_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Events-Ops-Key header.",
        )
