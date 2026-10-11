"""Domain event publishers — outbox and no-op (Phase 14)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.core.logging.logger import get_logger
from app.db.models.sensor_reading import SensorReading
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository
from app.events.catalog import get_catalog_entry
from app.events.schemas import DomainEventEnvelopeV1, SensorReadingCreatedPayloadV1
from app.events.types import AggregateType, DomainEventType

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


class DomainEventPublisher(ABC):
    @abstractmethod
    async def sensor_reading_created(self, reading: SensorReading) -> None:
        """Emit after a sensor reading is persisted."""


class NoOpDomainEventPublisher(DomainEventPublisher):
    async def sensor_reading_created(self, reading: SensorReading) -> None:
        return


class OutboxDomainEventPublisher(DomainEventPublisher):
    """Writes event envelopes to the transactional outbox (same DB session)."""

    def __init__(self, outbox_repository: DomainEventOutboxRepository) -> None:
        self._outbox = outbox_repository
        self._settings = get_settings()

    async def sensor_reading_created(self, reading: SensorReading) -> None:
        if not self._settings.EVENTS_ENABLED:
            return

        entry = get_catalog_entry(DomainEventType.SENSOR_READING_CREATED)
        body = SensorReadingCreatedPayloadV1(
            sensor_reading_id=reading.id,
            field_id=reading.field_id,
            sensor_type=reading.sensor_type,
            sensor_value=reading.sensor_value,
            unit=reading.unit,
            recorded_at=reading.recorded_at,
            notes=reading.notes,
        )

        outbox_row = await self._outbox.enqueue(
            event_type=entry.event_type.value,
            aggregate_type=AggregateType.SENSOR_READING.value,
            aggregate_id=reading.id,
            topic=entry.topic,
            payload={"_pending": True},
        )

        envelope = DomainEventEnvelopeV1(
            event_id=outbox_row.id,
            event_type=entry.event_type.value,
            schema_version=entry.schema_version,
            occurred_at=datetime.now(timezone.utc),
            aggregate_type=AggregateType.SENSOR_READING.value,
            aggregate_id=reading.id,
            payload=body.model_dump(mode="json"),
        )

        await self._outbox.update(
            outbox_row.id,
            {"payload": envelope.model_dump(mode="json")},
        )

        logger.info(
            "domain_event.outbox.enqueued",
            event_type=entry.event_type.value,
            event_id=str(outbox_row.id),
            aggregate_id=str(reading.id),
        )
