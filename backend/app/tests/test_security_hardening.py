"""Phase 16 security and settings tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import app
from app.core.config import get_settings

BASE_URL = f"http://testserver{get_settings().API_V1_PREFIX}"


def test_openai_key_selects_provider() -> None:
    settings = Settings(
        POSTGRES_PASSWORD="x",
        SECRET_KEY="y" * 32,
        COPILOT_ENABLED=True,
        COPILOT_LLM_PROVIDER="none",
        OPENAI_API_KEY="sk-test",
    )
    assert settings.COPILOT_LLM_PROVIDER == "openai"


@pytest.mark.asyncio
async def test_security_headers_on_health() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
