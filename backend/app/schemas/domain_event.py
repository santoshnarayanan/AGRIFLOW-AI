"""Schemas for domain event catalog and outbox API (Phase 14)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EventCatalogItemResponse(BaseModel):
    event_type: str
    topic: str
    schema_version: str
    description: str


class EventCatalogResponse(BaseModel):
    events: list[EventCatalogItemResponse]
    count: int = Field(ge=0)


class OutboxStatsResponse(BaseModel):
    pending: int = Field(ge=0)
    published: int = Field(ge=0)
    failed: int = Field(ge=0)
    total: int = Field(ge=0)
    events_processed: int = Field(
        ge=0,
        description="Business consumer idempotency ledger row count",
    )


class OutboxEntryResponse(BaseModel):
    id: UUID
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    topic: str
    created_at: datetime
    published_at: datetime | None
    publish_attempts: int
    last_error: str | None


class OutboxEntryListResponse(BaseModel):
    entries: list[OutboxEntryResponse]
    count: int = Field(ge=0)
