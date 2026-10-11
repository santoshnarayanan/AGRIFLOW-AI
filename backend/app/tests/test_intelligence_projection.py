"""Tests for event-driven intelligence projection field extraction (Phase 15 slice 4)."""

from datetime import datetime, timezone
from uuid import uuid4

from app.core.enums import SensorType
from app.events.handlers.intelligence_projection import extract_field_id
from app.events.schemas import DomainEventEnvelopeV1, SensorReadingCreatedPayloadV1
from app.events.types import AggregateType, DomainEventType


def test_extract_field_id_from_sensor_reading_event() -> None:
    field_id = uuid4()
    reading_id = uuid4()
    body = SensorReadingCreatedPayloadV1(
        sensor_reading_id=reading_id,
        field_id=field_id,
        sensor_type=SensorType.SOIL_MOISTURE,
        sensor_value=12.0,
        unit="%",
        recorded_at=datetime.now(timezone.utc),
    )
    envelope = DomainEventEnvelopeV1(
        event_id=uuid4(),
        event_type=DomainEventType.SENSOR_READING_CREATED.value,
        schema_version="1.0",
        occurred_at=datetime.now(timezone.utc),
        aggregate_type=AggregateType.SENSOR_READING.value,
        aggregate_id=reading_id,
        payload=body.model_dump(mode="json"),
    )
    assert extract_field_id(envelope) == field_id


def test_extract_field_id_returns_none_for_unknown_event_type() -> None:
    envelope = DomainEventEnvelopeV1(
        event_id=uuid4(),
        event_type="not.a.real.event",
        schema_version="1.0",
        occurred_at=datetime.now(timezone.utc),
        aggregate_type=AggregateType.SENSOR_READING.value,
        aggregate_id=uuid4(),
        payload={},
    )
    assert extract_field_id(envelope) is None
