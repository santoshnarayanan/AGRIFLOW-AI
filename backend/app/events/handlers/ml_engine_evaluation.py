"""
ML engine stub triggers from domain events (Phase 14).

When ``ML_ENGINE_AUTO_RUN_ENABLED`` is true, selected event types invoke stub
engines that write into the Recommendation domain (and emit RecommendationCreated).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging.logger import get_logger
from app.db.repositories.crop import CropRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.recommendation import RecommendationRepository
from app.events.publisher import NoOpDomainEventPublisher, OutboxDomainEventPublisher
from app.events.schemas import (
    DiseaseObservedPayloadV1,
    DomainEventEnvelopeV1,
    SatelliteObservedPayloadV1,
    YieldRecordedPayloadV1,
)
from app.events.types import DomainEventType
from app.ml.engines.base import EngineRunContext
from app.ml.service import MLEngineService
from app.ml.types import MLEngineId
from app.services.recommendation import RecommendationService

logger = get_logger(__name__)

_EVENT_ENGINE_MAP: dict[str, MLEngineId] = {
    DomainEventType.YIELD_RECORDED.value: MLEngineId.YIELD_FORECAST,
    DomainEventType.SATELLITE_OBSERVED.value: MLEngineId.IRRIGATION_OPTIMIZATION,
    DomainEventType.DISEASE_OBSERVED.value: MLEngineId.DISEASE_RISK,
}


async def handle_domain_event(session: AsyncSession, envelope: DomainEventEnvelopeV1) -> None:
    settings = get_settings()
    if not settings.ML_ENGINE_AUTO_RUN_ENABLED:
        return

    engine_id = _EVENT_ENGINE_MAP.get(envelope.event_type)
    if engine_id is None:
        return

    event_publisher = NoOpDomainEventPublisher()
    if settings.EVENTS_ENABLED:
        from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository

        event_publisher = OutboxDomainEventPublisher(DomainEventOutboxRepository(session))

    ml_service = MLEngineService(
        RecommendationService(
            recommendation_repository=RecommendationRepository(session),
            field_repository=FieldRepository(session),
            crop_repository=CropRepository(session),
            event_publisher=event_publisher,
        )
    )

    context = _context_for_event(envelope)
    if context is None:
        return

    field_id = _field_id_for_event(envelope)
    if field_id is None:
        return

    try:
        await ml_service.run_engine(field_id, engine_id, context=context)
    except Exception as exc:
        logger.warning(
            "ml_engine_evaluation.run_failed",
            event_type=envelope.event_type,
            event_id=str(envelope.event_id),
            error=str(exc),
        )


def _field_id_for_event(envelope: DomainEventEnvelopeV1):
    if envelope.event_type == DomainEventType.YIELD_RECORDED.value:
        return YieldRecordedPayloadV1.model_validate(envelope.payload).field_id
    if envelope.event_type == DomainEventType.DISEASE_OBSERVED.value:
        return DiseaseObservedPayloadV1.model_validate(envelope.payload).field_id
    if envelope.event_type == DomainEventType.SATELLITE_OBSERVED.value:
        return SatelliteObservedPayloadV1.model_validate(envelope.payload).field_id
    return None


def _context_for_event(envelope: DomainEventEnvelopeV1) -> EngineRunContext | None:
    if envelope.event_type == DomainEventType.YIELD_RECORDED.value:
        payload = YieldRecordedPayloadV1.model_validate(envelope.payload)
        return EngineRunContext(
            crop_id=payload.crop_id,
            trigger_event_type=envelope.event_type,
            trigger_aggregate_id=payload.yield_record_id,
            notes=f"Triggered by yield {payload.yield_value_tons_ha} t/ha.",
        )
    if envelope.event_type == DomainEventType.DISEASE_OBSERVED.value:
        payload = DiseaseObservedPayloadV1.model_validate(envelope.payload)
        return EngineRunContext(
            crop_id=payload.crop_id,
            trigger_event_type=envelope.event_type,
            trigger_aggregate_id=payload.disease_observation_id,
            notes=f"Disease {payload.disease_name} severity {payload.severity.value}.",
        )
    if envelope.event_type == DomainEventType.SATELLITE_OBSERVED.value:
        payload = SatelliteObservedPayloadV1.model_validate(envelope.payload)
        return EngineRunContext(
            trigger_event_type=envelope.event_type,
            trigger_aggregate_id=payload.satellite_observation_id,
            notes=(
                f"{payload.spectral_index.value}={payload.index_value} "
                f"({payload.satellite_provider.value})."
            ),
        )
    return None
