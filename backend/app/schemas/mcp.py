"""MCP tool evaluation schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class McpToolDescriptor(BaseModel):
    name: str
    description: str
    inputSchema: dict[str, Any]


class McpToolCatalogResponse(BaseModel):
    tools: list[McpToolDescriptor]


class McpToolInvokeRequest(BaseModel):
    tool_name: str = Field(..., min_length=1, max_length=100)
    arguments: dict[str, Any] = Field(default_factory=dict)


class McpToolInvokeResponse(BaseModel):
    tool_name: str
    result: dict[str, Any]
