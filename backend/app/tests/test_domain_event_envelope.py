"""Contract tests for domain event envelopes (Phase 14)."""

from datetime import datetime, timezone
from uuid import uuid4

from app.core.enums import SensorType
from app.events.schemas import DomainEventEnvelopeV1, SensorReadingCreatedPayloadV1
from app.events.types import AggregateType, DomainEventType


def test_sensor_reading_envelope_roundtrip_json() -> None:
    event_id = uuid4()
    field_id = uuid4()
    reading_id = uuid4()
    recorded_at = datetime(2026, 10, 11, 12, 0, 0, tzinfo=timezone.utc)

    body = SensorReadingCreatedPayloadV1(
        sensor_reading_id=reading_id,
        field_id=field_id,
        sensor_type=SensorType.SOIL_MOISTURE,
        sensor_value=15.5,
        unit="%",
        recorded_at=recorded_at,
    )

    envelope = DomainEventEnvelopeV1(
        event_id=event_id,
        event_type=DomainEventType.SENSOR_READING_CREATED.value,
        schema_version="1.0",
        occurred_at=datetime.now(timezone.utc),
        aggregate_type=AggregateType.SENSOR_READING.value,
        aggregate_id=reading_id,
        payload=body.model_dump(mode="json"),
    )

    raw = envelope.model_dump(mode="json")
    restored = DomainEventEnvelopeV1.model_validate(raw)

    assert restored.event_id == event_id
    assert restored.event_type == DomainEventType.SENSOR_READING_CREATED.value
    assert restored.payload["sensor_type"] == SensorType.SOIL_MOISTURE.value
    assert restored.payload["sensor_value"] == 15.5
