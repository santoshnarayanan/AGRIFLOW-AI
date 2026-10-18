"""Farm Copilot API schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class CopilotChatResponse(BaseModel):
    field_id: uuid.UUID
    mode: str
    answer: str
    tools: list[dict[str, Any]]
    mcp_catalog_size: int
