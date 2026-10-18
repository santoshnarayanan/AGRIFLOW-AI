"""
MCP stdio server — exposes Farm Copilot tools to Claude Desktop / Cursor agents.

Requires a running API (`AGRIFLOW_API_URL`, default http://localhost:8000/api/v1).
When ``AUTH_REQUIRED`` is enabled, set ``AGRIFLOW_BEARER_TOKEN`` for tool invoke.

Usage:
    python -m app.mcp_stdio.server
"""

from __future__ import annotations

import json
import os

import httpx

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit(
        "MCP SDK not installed. Use: pip install -r requirements-mcp.txt "
        "(prefer a dedicated venv for the stdio server)."
    ) from exc

API_BASE = os.environ.get("AGRIFLOW_API_URL", "http://localhost:8000/api/v1").rstrip("/")
BEARER = os.environ.get("AGRIFLOW_BEARER_TOKEN", "").strip()

mcp = FastMCP("agriflow-ai")


def _headers() -> dict[str, str]:
    if BEARER:
        return {"Authorization": f"Bearer {BEARER}"}
    return {}


async def _invoke(tool_name: str, field_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE}/mcp/tools/invoke",
            headers=_headers(),
            json={"tool_name": tool_name, "arguments": {"field_id": field_id}},
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("result", payload)


@mcp.tool()
async def get_field_context(field_id: str) -> str:
    """Farm and field metadata for a UUID field_id."""
    return json.dumps(await _invoke("get_field_context", field_id))


@mcp.tool()
async def get_latest_soil_moisture(field_id: str) -> str:
    """Latest soil moisture reading for irrigation decisions."""
    return json.dumps(await _invoke("get_latest_soil_moisture", field_id))


@mcp.tool()
async def get_open_alerts(field_id: str) -> str:
    """Unacknowledged alerts for the field."""
    return json.dumps(await _invoke("get_open_alerts", field_id))


@mcp.tool()
async def get_digital_twin_state(field_id: str) -> str:
    """Digital Twin JSON document for the field."""
    return json.dumps(await _invoke("get_digital_twin_state", field_id))


@mcp.tool()
async def get_dashboard_kpis(field_id: str) -> str:
    """CQRS dashboard KPI payload for the field."""
    return json.dumps(await _invoke("get_dashboard_kpis", field_id))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
