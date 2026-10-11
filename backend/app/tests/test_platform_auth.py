"""Platform operator authentication tests (Phase 15 slice 5)."""

import pytest
from fastapi import HTTPException

from app.core.config import Settings, get_settings
from app.core.security.platform_auth import require_platform_operator


@pytest.mark.asyncio
async def test_development_bypass_when_auth_not_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = get_settings()

    def _settings() -> Settings:
        return base.model_copy(
            update={
                "APP_ENV": "development",
                "AUTH_REQUIRED": False,
                "EVENTS_OPS_API_KEY": None,
            }
        )

    monkeypatch.setattr("app.core.security.platform_auth.get_settings", _settings)
    principal = await require_platform_operator(authorization=None, x_events_ops_key=None)
    assert principal.auth_method == "development_bypass"
    assert principal.role.value == "ADMIN"


@pytest.mark.asyncio
async def test_ops_key_accepts_valid_header(monkeypatch: pytest.MonkeyPatch) -> None:
    base = get_settings()

    def _settings() -> Settings:
        return base.model_copy(
            update={
                "APP_ENV": "staging",
                "AUTH_REQUIRED": True,
                "EVENTS_OPS_API_KEY": "test-ops-secret",
            }
        )

    monkeypatch.setattr("app.core.security.platform_auth.get_settings", _settings)
    principal = await require_platform_operator(
        authorization=None,
        x_events_ops_key="test-ops-secret",
    )
    assert principal.auth_method == "ops_key"


@pytest.mark.asyncio
async def test_rejects_when_auth_required_and_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = get_settings()

    def _settings() -> Settings:
        return base.model_copy(
            update={
                "APP_ENV": "staging",
                "AUTH_REQUIRED": True,
                "EVENTS_OPS_API_KEY": "test-ops-secret",
            }
        )

    monkeypatch.setattr("app.core.security.platform_auth.get_settings", _settings)

    with pytest.raises(HTTPException) as exc_info:
        await require_platform_operator(authorization=None, x_events_ops_key=None)

    assert exc_info.value.status_code == 401
