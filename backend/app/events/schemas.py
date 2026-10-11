"""Versioned domain event payload schemas (Phase 14)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import SensorType


class SensorReadingCreatedPayloadV1(BaseModel):
    """Payload for ``SensorReadingCreated`` (schema 1.0)."""

    model_config = ConfigDict(from_attributes=True)

    sensor_reading_id: UUID
    field_id: UUID
    sensor_type: SensorType
    sensor_value: float
    unit: str
    recorded_at: datetime
    notes: str | None = None


class DomainEventEnvelopeV1(BaseModel):
    """Wire format published to Redpanda and stored in the outbox ``payload`` column."""

    event_id: UUID = Field(description="Outbox row id — unique message idempotency key")
    event_type: str
    schema_version: str
    occurred_at: datetime
    aggregate_type: str
    aggregate_id: UUID
    payload: dict
