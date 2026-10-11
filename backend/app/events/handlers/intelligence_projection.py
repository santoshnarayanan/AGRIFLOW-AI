"""
Event-driven intelligence projection (Phase 15 slice 4).

On field-scoped domain events, refresh Feature Store snapshots, CQRS dashboard
read models, and Digital Twin state for the affected field.
"""

from __future__ import annotations

import uuid

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging.logger import get_logger
from app.db.repositories.crop import CropRepository
from app.db.repositories.feature_extraction import FeatureExtractionRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.field_dashboard_read_model import FieldDashboardReadModelRepository
from app.db.repositories.field_digital_twin_state import FieldDigitalTwinStateRepository
from app.db.repositories.field_feature_snapshot import FieldFeatureSnapshotRepository
from app.db.repositories.read_model_metrics import ReadModelMetricsRepository
from app.db.repositories.farm import FarmRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.events.schemas import (
    AlertTriggeredPayloadV1,
    CropLifecycleChangedPayloadV1,
    DiseaseObservedPayloadV1,
    DomainEventEnvelopeV1,
    IrrigationCompletedPayloadV1,
    RecommendationCreatedPayloadV1,
    SatelliteObservedPayloadV1,
    SensorReadingCreatedPayloadV1,
    WeatherRecordCreatedPayloadV1,
    YieldRecordedPayloadV1,
)
from app.events.types import DomainEventType
from app.services.digital_twin import DigitalTwinService
from app.services.feature_store import FeatureStoreService
from app.services.read_model_projection import ReadModelProjectionService

logger = get_logger(__name__)

_FIELD_EVENT_PAYLOADS: dict[DomainEventType, type] = {
    DomainEventType.SENSOR_READING_CREATED: SensorReadingCreatedPayloadV1,
    DomainEventType.WEATHER_RECORD_CREATED: WeatherRecordCreatedPayloadV1,
    DomainEventType.IRRIGATION_COMPLETED: IrrigationCompletedPayloadV1,
    DomainEventType.YIELD_RECORDED: YieldRecordedPayloadV1,
    DomainEventType.DISEASE_OBSERVED: DiseaseObservedPayloadV1,
    DomainEventType.SATELLITE_OBSERVED: SatelliteObservedPayloadV1,
    DomainEventType.CROP_LIFECYCLE_CHANGED: CropLifecycleChangedPayloadV1,
    DomainEventType.RECOMMENDATION_CREATED: RecommendationCreatedPayloadV1,
    DomainEventType.ALERT_TRIGGERED: AlertTriggeredPayloadV1,
}


def extract_field_id(envelope: DomainEventEnvelopeV1) -> uuid.UUID | None:
    try:
        event_type = DomainEventType(envelope.event_type)
    except ValueError:
        return None
    schema = _FIELD_EVENT_PAYLOADS.get(event_type)
    if schema is None:
        return None
    try:
        payload = schema.model_validate(envelope.payload)
    except ValidationError:
        return None
    field_id = getattr(payload, "field_id", None)
    return field_id if isinstance(field_id, uuid.UUID) else None


async def handle_domain_event(session: AsyncSession, envelope: DomainEventEnvelopeV1) -> None:
    settings = get_settings()
    if not settings.INTELLIGENCE_EVENT_PROJECTION_ENABLED:
        return

    field_id = extract_field_id(envelope)
    if field_id is None:
        return

    field_repo = FieldRepository(session)
    feature_store = FeatureStoreService(
        field_repository=field_repo,
        snapshot_repository=FieldFeatureSnapshotRepository(session),
        extraction_repository=FeatureExtractionRepository(session),
    )
    read_models = ReadModelProjectionService(
        farm_repository=FarmRepository(session),
        field_repository=field_repo,
        read_model_repository=FieldDashboardReadModelRepository(session),
        metrics_repository=ReadModelMetricsRepository(session),
        feature_snapshot_repository=FieldFeatureSnapshotRepository(session),
    )
    digital_twin = DigitalTwinService(
        field_repository=field_repo,
        crop_repository=CropRepository(session),
        sensor_reading_repository=SensorReadingRepository(session),
        twin_state_repository=FieldDigitalTwinStateRepository(session),
        read_model_projection_service=read_models,
    )

    try:
        await feature_store.materialize_field_snapshot(field_id)
        await read_models.refresh_field(field_id)
        await digital_twin.synchronize_field(field_id)
    except Exception as exc:
        logger.warning(
            "intelligence_projection.failed",
            field_id=str(field_id),
            event_type=envelope.event_type,
            error=str(exc),
        )
        raise

    logger.info(
        "intelligence_projection.refreshed",
        field_id=str(field_id),
        event_type=envelope.event_type,
        event_id=str(envelope.event_id),
    )
