"""MCP tool catalog and evaluation API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.copilot.tools import invoke_tool, mcp_tool_catalog
from app.schemas.mcp import (
    McpToolCatalogResponse,
    McpToolDescriptor,
    McpToolInvokeRequest,
    McpToolInvokeResponse,
)

router = APIRouter(prefix="/mcp", tags=["MCP Evaluation"])


@router.get("/tools", response_model=McpToolCatalogResponse)
async def list_mcp_tools() -> McpToolCatalogResponse:
    if not get_settings().MCP_TOOLS_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MCP tools disabled.")
    tools = [McpToolDescriptor(**item) for item in mcp_tool_catalog()]
    return McpToolCatalogResponse(tools=tools)


@router.post("/tools/invoke", response_model=McpToolInvokeResponse)
async def invoke_mcp_tool(
    body: McpToolInvokeRequest,
    session: SessionDep,
) -> McpToolInvokeResponse:
    if not get_settings().MCP_TOOLS_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MCP tools disabled.")
    try:
        result = await invoke_tool(session, body.tool_name, body.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return McpToolInvokeResponse(tool_name=body.tool_name, result=result)
