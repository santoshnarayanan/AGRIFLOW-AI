"""Domain event publishers — outbox and no-op (Phase 14)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging.logger import get_logger
from app.db.models.crop import Crop, CropStatus
from app.db.models.disease_observation import DiseaseObservation
from app.db.models.irrigation_event import IrrigationEvent
from app.db.models.satellite_observation import SatelliteObservation
from app.db.models.sensor_reading import SensorReading
from app.db.models.weather_record import WeatherRecord
from app.db.models.yield_record import YieldRecord
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository
from app.events.catalog import get_catalog_entry
from app.events.schemas import (
    CropLifecycleChangedPayloadV1,
    DiseaseObservedPayloadV1,
    DomainEventEnvelopeV1,
    IrrigationCompletedPayloadV1,
    SatelliteObservedPayloadV1,
    SensorReadingCreatedPayloadV1,
    WeatherRecordCreatedPayloadV1,
    YieldRecordedPayloadV1,
)
from app.events.types import AggregateType, DomainEventType

logger = get_logger(__name__)


class DomainEventPublisher(ABC):
    @abstractmethod
    async def sensor_reading_created(self, reading: SensorReading) -> None: ...

    @abstractmethod
    async def weather_record_created(self, record: WeatherRecord) -> None: ...

    @abstractmethod
    async def irrigation_completed(self, event: IrrigationEvent) -> None: ...

    @abstractmethod
    async def yield_recorded(self, record: YieldRecord) -> None: ...

    @abstractmethod
    async def disease_observed(self, observation: DiseaseObservation) -> None: ...

    @abstractmethod
    async def satellite_observed(self, observation: SatelliteObservation) -> None: ...

    @abstractmethod
    async def crop_lifecycle_changed(
        self,
        crop: Crop,
        *,
        previous_status: CropStatus,
        new_status: CropStatus,
    ) -> None: ...


class NoOpDomainEventPublisher(DomainEventPublisher):
    async def sensor_reading_created(self, reading: SensorReading) -> None:
        return

    async def weather_record_created(self, record: WeatherRecord) -> None:
        return

    async def irrigation_completed(self, event: IrrigationEvent) -> None:
        return

    async def yield_recorded(self, record: YieldRecord) -> None:
        return

    async def disease_observed(self, observation: DiseaseObservation) -> None:
        return

    async def satellite_observed(self, observation: SatelliteObservation) -> None:
        return

    async def crop_lifecycle_changed(
        self,
        crop: Crop,
        *,
        previous_status: CropStatus,
        new_status: CropStatus,
    ) -> None:
        return


class OutboxDomainEventPublisher(DomainEventPublisher):
    """Writes event envelopes to the transactional outbox (same DB session)."""

    def __init__(self, outbox_repository: DomainEventOutboxRepository) -> None:
        self._outbox = outbox_repository
        self._settings = get_settings()

    async def _enqueue(
        self,
        *,
        event_type: DomainEventType,
        aggregate_type: AggregateType,
        aggregate_id: UUID,
        body: BaseModel,
    ) -> None:
        if not self._settings.EVENTS_ENABLED:
            return

        entry = get_catalog_entry(event_type)
        outbox_row = await self._outbox.enqueue(
            event_type=entry.event_type.value,
            aggregate_type=aggregate_type.value,
            aggregate_id=aggregate_id,
            topic=entry.topic,
            payload={"_pending": True},
        )

        envelope = DomainEventEnvelopeV1(
            event_id=outbox_row.id,
            event_type=entry.event_type.value,
            schema_version=entry.schema_version,
            occurred_at=datetime.now(timezone.utc),
            aggregate_type=aggregate_type.value,
            aggregate_id=aggregate_id,
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
            aggregate_id=str(aggregate_id),
        )

    async def sensor_reading_created(self, reading: SensorReading) -> None:
        body = SensorReadingCreatedPayloadV1(
            sensor_reading_id=reading.id,
            field_id=reading.field_id,
            sensor_type=reading.sensor_type,
            sensor_value=reading.sensor_value,
            unit=reading.unit,
            recorded_at=reading.recorded_at,
            notes=reading.notes,
        )
        await self._enqueue(
            event_type=DomainEventType.SENSOR_READING_CREATED,
            aggregate_type=AggregateType.SENSOR_READING,
            aggregate_id=reading.id,
            body=body,
        )

    async def weather_record_created(self, record: WeatherRecord) -> None:
        body = WeatherRecordCreatedPayloadV1(
            weather_record_id=record.id,
            field_id=record.field_id,
            recorded_at=record.recorded_at,
            data_source=record.data_source,
        )
        await self._enqueue(
            event_type=DomainEventType.WEATHER_RECORD_CREATED,
            aggregate_type=AggregateType.WEATHER_RECORD,
            aggregate_id=record.id,
            body=body,
        )

    async def irrigation_completed(self, event: IrrigationEvent) -> None:
        body = IrrigationCompletedPayloadV1(
            irrigation_event_id=event.id,
            field_id=event.field_id,
            irrigation_method=event.irrigation_method,
            water_source=event.water_source,
            started_at=event.started_at,
            ended_at=event.ended_at,
            duration_minutes=float(event.duration_minutes)
            if event.duration_minutes is not None
            else None,
            water_volume_liters=float(event.water_volume_liters)
            if event.water_volume_liters is not None
            else None,
        )
        await self._enqueue(
            event_type=DomainEventType.IRRIGATION_COMPLETED,
            aggregate_type=AggregateType.IRRIGATION_EVENT,
            aggregate_id=event.id,
            body=body,
        )

    async def yield_recorded(self, record: YieldRecord) -> None:
        body = YieldRecordedPayloadV1(
            yield_record_id=record.id,
            crop_id=record.crop_id,
            field_id=record.field_id,
            recorded_at=record.recorded_at,
            yield_value_tons_ha=float(record.yield_value_tons_ha),
            measurement_method=record.measurement_method,
        )
        await self._enqueue(
            event_type=DomainEventType.YIELD_RECORDED,
            aggregate_type=AggregateType.YIELD_RECORD,
            aggregate_id=record.id,
            body=body,
        )

    async def disease_observed(self, observation: DiseaseObservation) -> None:
        body = DiseaseObservedPayloadV1(
            disease_observation_id=observation.id,
            crop_id=observation.crop_id,
            field_id=observation.field_id,
            observed_at=observation.observed_at,
            disease_name=observation.disease_name,
            severity=observation.severity,
            diagnosis_method=observation.diagnosis_method,
        )
        await self._enqueue(
            event_type=DomainEventType.DISEASE_OBSERVED,
            aggregate_type=AggregateType.DISEASE_OBSERVATION,
            aggregate_id=observation.id,
            body=body,
        )

    async def satellite_observed(self, observation: SatelliteObservation) -> None:
        body = SatelliteObservedPayloadV1(
            satellite_observation_id=observation.id,
            field_id=observation.field_id,
            observed_at=observation.observed_at,
            spectral_index=observation.spectral_index,
            index_value=observation.index_value,
            satellite_provider=observation.satellite_provider,
        )
        await self._enqueue(
            event_type=DomainEventType.SATELLITE_OBSERVED,
            aggregate_type=AggregateType.SATELLITE_OBSERVATION,
            aggregate_id=observation.id,
            body=body,
        )

    async def crop_lifecycle_changed(
        self,
        crop: Crop,
        *,
        previous_status: CropStatus,
        new_status: CropStatus,
    ) -> None:
        body = CropLifecycleChangedPayloadV1(
            crop_id=crop.id,
            field_id=crop.field_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_at=datetime.now(timezone.utc),
        )
        await self._enqueue(
            event_type=DomainEventType.CROP_LIFECYCLE_CHANGED,
            aggregate_type=AggregateType.CROP,
            aggregate_id=crop.id,
            body=body,
        )
