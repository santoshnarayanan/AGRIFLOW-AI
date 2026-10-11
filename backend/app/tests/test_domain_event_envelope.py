"""Contract tests for domain event envelopes (Phase 14)."""

from datetime import datetime, timezone
from uuid import uuid4

from app.core.enums import (
    AlertSeverity,
    AlertType,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
    SensorType,
)
from app.events.schemas import (
    AlertTriggeredPayloadV1,
    DomainEventEnvelopeV1,
    RecommendationCreatedPayloadV1,
    SensorReadingCreatedPayloadV1,
)
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


def test_recommendation_created_envelope_roundtrip_json() -> None:
    event_id = uuid4()
    field_id = uuid4()
    recommendation_id = uuid4()
    valid_from = datetime(2026, 10, 11, 8, 0, 0, tzinfo=timezone.utc)

    body = RecommendationCreatedPayloadV1(
        recommendation_id=recommendation_id,
        field_id=field_id,
        recommendation_type=RecommendationType.IRRIGATION,
        status=RecommendationStatus.PENDING,
        priority=RecommendationPriority.HIGH,
        title="Increase irrigation",
        confidence_score=0.87,
        engine_version="deterministic-v1.0",
        valid_from=valid_from,
    )

    envelope = DomainEventEnvelopeV1(
        event_id=event_id,
        event_type=DomainEventType.RECOMMENDATION_CREATED.value,
        schema_version="1.0",
        occurred_at=datetime.now(timezone.utc),
        aggregate_type=AggregateType.RECOMMENDATION.value,
        aggregate_id=recommendation_id,
        payload=body.model_dump(mode="json"),
    )

    restored = DomainEventEnvelopeV1.model_validate(envelope.model_dump(mode="json"))
    assert restored.event_type == DomainEventType.RECOMMENDATION_CREATED.value
    assert restored.payload["recommendation_type"] == RecommendationType.IRRIGATION.value


def test_alert_triggered_envelope_roundtrip_json() -> None:
    event_id = uuid4()
    field_id = uuid4()
    alert_id = uuid4()
    triggered_at = datetime(2026, 10, 11, 9, 30, 0, tzinfo=timezone.utc)

    body = AlertTriggeredPayloadV1(
        alert_id=alert_id,
        field_id=field_id,
        alert_type=AlertType.SOIL_MOISTURE_LOW,
        severity=AlertSeverity.WARNING,
        title="Soil moisture below threshold",
        triggered_at=triggered_at,
    )

    envelope = DomainEventEnvelopeV1(
        event_id=event_id,
        event_type=DomainEventType.ALERT_TRIGGERED.value,
        schema_version="1.0",
        occurred_at=datetime.now(timezone.utc),
        aggregate_type=AggregateType.ALERT.value,
        aggregate_id=alert_id,
        payload=body.model_dump(mode="json"),
    )

    restored = DomainEventEnvelopeV1.model_validate(envelope.model_dump(mode="json"))
    assert restored.event_type == DomainEventType.ALERT_TRIGGERED.value
    assert restored.payload["alert_type"] == AlertType.SOIL_MOISTURE_LOW.value
