"""
Health endpoint integration tests.

Uses httpx AsyncClient with ASGI transport — no running server required.
Database calls are mocked so tests remain fast and self-contained.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.config import get_settings

settings = get_settings()
BASE_URL = f"http://testserver{settings.API_V1_PREFIX}"


@pytest.mark.asyncio
async def test_liveness_returns_200() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=BASE_URL
    ) as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "alive"
    assert body["version"] == settings.APP_VERSION


@pytest.mark.asyncio
async def test_readiness_with_healthy_db() -> None:
    mock_execute = AsyncMock()

    with patch("app.api.health.router.AsyncSession.execute", mock_execute):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url=BASE_URL
        ) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 200
