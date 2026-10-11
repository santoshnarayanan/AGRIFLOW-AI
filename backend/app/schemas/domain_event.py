"""Schemas for domain event catalog API (Phase 14)."""

from pydantic import BaseModel, Field


class EventCatalogItemResponse(BaseModel):
    event_type: str
    topic: str
    schema_version: str
    description: str


class EventCatalogResponse(BaseModel):
    events: list[EventCatalogItemResponse]
    count: int = Field(ge=0)
