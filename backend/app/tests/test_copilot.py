"""Farm Copilot and MCP tool tests (Phase 16)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_copilot_service, get_session
from app.core.config import get_settings
from app.main import app
from app.services.field import FieldNotFoundError

settings = get_settings()
BASE_URL = f"http://testserver{settings.API_V1_PREFIX}"


@pytest.mark.asyncio
async def test_mcp_tools_catalog() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get("/mcp/tools")
    assert response.status_code == 200
    payload = response.json()
    names = {tool["name"] for tool in payload["tools"]}
    assert "get_latest_soil_moisture" in names
    assert "get_field_context" in names


@pytest.mark.asyncio
async def test_mcp_invoke_unknown_tool() -> None:
    async def _fake_session() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    app.dependency_overrides[get_session] = _fake_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                "/mcp/tools/invoke",
                json={"tool_name": "not_a_real_tool", "arguments": {}},
            )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_copilot_chat_field_not_found() -> None:
    class _FakeCopilot:
        async def chat(self, field_id: uuid.UUID, message: str) -> dict:
            raise FieldNotFoundError("missing")

    async def _fake_session() -> AsyncGenerator[AsyncMock, None]:
        yield AsyncMock()

    app.dependency_overrides[get_session] = _fake_session
    app.dependency_overrides[get_copilot_service] = lambda: _FakeCopilot()
    try:
        missing = str(uuid.uuid4())
        async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
            response = await client.post(
                f"/copilot/fields/{missing}/chat",
                json={"message": "Should I irrigate today?"},
            )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
