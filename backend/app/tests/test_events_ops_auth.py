"""Events ops API key guard tests (Phase 14)."""

import pytest
from fastapi import HTTPException

from app.api.security.events_ops import require_events_ops_key
from app.core.config import Settings, get_settings


@pytest.mark.asyncio
async def test_ops_key_allows_development_without_configured_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = get_settings()

    def _settings() -> Settings:
        return base.model_copy(update={"APP_ENV": "development", "EVENTS_OPS_API_KEY": None})

    monkeypatch.setattr("app.api.security.events_ops.get_settings", _settings)
    await require_events_ops_key(x_events_ops_key=None)


@pytest.mark.asyncio
async def test_ops_key_rejects_missing_header_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = get_settings()

    def _settings() -> Settings:
        return base.model_copy(
            update={"APP_ENV": "staging", "EVENTS_OPS_API_KEY": "test-ops-secret"}
        )

    monkeypatch.setattr("app.api.security.events_ops.get_settings", _settings)

    with pytest.raises(HTTPException) as exc_info:
        await require_events_ops_key(x_events_ops_key=None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_ops_key_accepts_valid_header(monkeypatch: pytest.MonkeyPatch) -> None:
    base = get_settings()

    def _settings() -> Settings:
        return base.model_copy(
            update={"APP_ENV": "staging", "EVENTS_OPS_API_KEY": "test-ops-secret"}
        )

    monkeypatch.setattr("app.api.security.events_ops.get_settings", _settings)
    await require_events_ops_key(x_events_ops_key="test-ops-secret")
