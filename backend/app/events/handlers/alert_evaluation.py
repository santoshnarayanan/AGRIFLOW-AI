"""
Alert evaluation handler — first business consumer (Phase 14 stub).

Reacts to ``SensorReadingCreated`` when soil moisture drops below a configured
threshold and creates a ``SOIL_MOISTURE_LOW`` alert if none is already open.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import AlertSeverity, AlertType, SensorType
from app.core.logging.logger import get_logger
from app.db.repositories.alert import AlertRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.recommendation import RecommendationRepository
from app.events.schemas import DomainEventEnvelopeV1, SensorReadingCreatedPayloadV1
from app.events.types import DomainEventType
from app.schemas.alert import AlertCreate
from app.services.alert import AlertService

logger = get_logger(__name__)


async def handle_domain_event(session: AsyncSession, envelope: DomainEventEnvelopeV1) -> None:
    if envelope.event_type != DomainEventType.SENSOR_READING_CREATED.value:
        return

    settings = get_settings()
    if not settings.ALERT_EVALUATION_ENABLED:
        return

    payload = SensorReadingCreatedPayloadV1.model_validate(envelope.payload)
    if payload.sensor_type != SensorType.SOIL_MOISTURE:
        return

    threshold = settings.SOIL_MOISTURE_LOW_THRESHOLD_PERCENT
    if payload.sensor_value >= threshold:
        return

    alert_repo = AlertRepository(session)
    existing = await alert_repo.list_by_type(
        payload.field_id,
        AlertType.SOIL_MOISTURE_LOW,
        limit=5,
    )
    if any(not row.is_acknowledged for row in existing):
        logger.debug(
            "alert_evaluation.skip_duplicate",
            field_id=str(payload.field_id),
        )
        return

    alert_service = AlertService(
        alert_repository=alert_repo,
        field_repository=FieldRepository(session),
        recommendation_repository=RecommendationRepository(session),
    )

    triggered_at = payload.recorded_at
    if triggered_at.tzinfo is None:
        triggered_at = triggered_at.replace(tzinfo=timezone.utc)

    await alert_service.create_alert(
        payload.field_id,
        AlertCreate(
            alert_type=AlertType.SOIL_MOISTURE_LOW,
            severity=AlertSeverity.WARNING,
            title="Soil moisture below threshold",
            message=(
                f"Soil moisture reading {payload.sensor_value}{payload.unit} "
                f"is below threshold {threshold}% (event {envelope.event_id})."
            ),
            triggered_at=triggered_at,
            source_metric="soil_moisture_pct",
            source_value=Decimal(str(payload.sensor_value)),
            threshold_value=Decimal(str(threshold)),
        ),
    )
    logger.info(
        "alert_evaluation.created",
        field_id=str(payload.field_id),
        event_id=str(envelope.event_id),
    )
