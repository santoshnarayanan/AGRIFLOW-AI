"""Temporal activities — soil moisture alert pipeline (Phase 16)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from temporalio import activity

from app.core.config import get_settings
from app.core.enums import (
    AlertSeverity,
    AlertType,
    RecommendationPriority,
    RecommendationType,
    SensorType,
)
from app.core.logging.logger import get_logger
from app.db.repositories.alert import AlertRepository
from app.db.repositories.crop import CropRepository
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.recommendation import RecommendationRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.db.session import AsyncSessionFactory
from app.events.publisher import NoOpDomainEventPublisher, OutboxDomainEventPublisher
from app.schemas.alert import AlertCreate
from app.schemas.recommendation import RecommendationCreate
from app.services.alert import AlertService
from app.services.recommendation import RecommendationService
from app.temporal.types import IrrigationRecommendationResult, LatestSoilMoistureResult

logger = get_logger(__name__)


@activity.defn(name="get_latest_soil_moisture")
async def get_latest_soil_moisture(field_id: str, threshold_percent: float) -> dict:
    """Return latest soil moisture for a field and whether it is below threshold."""
    fid = uuid.UUID(field_id)
    async with AsyncSessionFactory() as session:
        async with session.begin():
            repo = SensorReadingRepository(session)
            readings = await repo.latest_per_sensor_type(fid)
            moisture = next(
                (r for r in readings if r.sensor_type == SensorType.SOIL_MOISTURE),
                None,
            )
            if moisture is None:
                result = LatestSoilMoistureResult(
                    field_id=fid,
                    sensor_value=None,
                    unit=None,
                    recorded_at=None,
                    below_threshold=False,
                )
            else:
                below = float(moisture.sensor_value) < threshold_percent
                result = LatestSoilMoistureResult(
                    field_id=fid,
                    sensor_value=float(moisture.sensor_value),
                    unit=moisture.unit,
                    recorded_at=moisture.recorded_at,
                    below_threshold=below,
                )
    return {
        "field_id": str(result.field_id),
        "sensor_value": result.sensor_value,
        "unit": result.unit,
        "recorded_at": result.recorded_at.isoformat() if result.recorded_at else None,
        "below_threshold": result.below_threshold,
    }


@activity.defn(name="create_irrigation_recommendation_for_low_moisture")
async def create_irrigation_recommendation_for_low_moisture(
    field_id: str,
    threshold_percent: float,
    trigger_reading_id: str,
) -> dict:
    """Create irrigation recommendation and companion alert when deficit persists."""
    settings = get_settings()
    fid = uuid.UUID(field_id)
    reading_id = uuid.UUID(trigger_reading_id)
    now = datetime.now(timezone.utc)

    async with AsyncSessionFactory() as session:
        async with session.begin():
            event_publisher = NoOpDomainEventPublisher()
            if settings.EVENTS_ENABLED:
                event_publisher = OutboxDomainEventPublisher(
                    DomainEventOutboxRepository(session),
                )

            rec_service = RecommendationService(
                recommendation_repository=RecommendationRepository(session),
                field_repository=FieldRepository(session),
                crop_repository=CropRepository(session),
                event_publisher=event_publisher,
            )
            recommendation = await rec_service.create_recommendation(
                fid,
                RecommendationCreate(
                    recommendation_type=RecommendationType.IRRIGATION,
                    priority=RecommendationPriority.HIGH,
                    title="Irrigate field — sustained low soil moisture",
                    description=(
                        "Temporal SoilMoistureAlertWorkflow detected soil moisture "
                        f"below {threshold_percent}% after the persistence window."
                    ),
                    recommended_action=(
                        "Schedule irrigation for this field and verify soil moisture "
                        "recovery within 24 hours."
                    ),
                    confidence_score=Decimal("0.85"),
                    engine_version="temporal:SoilMoistureAlertWorkflow-v1",
                    valid_from=now,
                ),
            )

            alert_service = AlertService(
                alert_repository=AlertRepository(session),
                field_repository=FieldRepository(session),
                recommendation_repository=RecommendationRepository(session),
                event_publisher=event_publisher,
            )
            alert = await alert_service.create_alert(
                fid,
                AlertCreate(
                    alert_type=AlertType.SOIL_MOISTURE_LOW,
                    severity=AlertSeverity.WARNING,
                    title="Sustained low soil moisture",
                    message=(
                        f"Workflow escalation: moisture still below {threshold_percent}% "
                        f"(trigger reading {reading_id})."
                    ),
                    triggered_at=now,
                    source_metric="soil_moisture_pct",
                    threshold_value=Decimal(str(threshold_percent)),
                ),
            )

    outcome = IrrigationRecommendationResult(
        recommendation_id=recommendation.id,
        alert_id=alert.id,
    )
    logger.info(
        "temporal.activity.irrigation_created",
        field_id=field_id,
        recommendation_id=str(outcome.recommendation_id),
        alert_id=str(outcome.alert_id) if outcome.alert_id else None,
    )
    return {
        "recommendation_id": str(outcome.recommendation_id),
        "alert_id": str(outcome.alert_id) if outcome.alert_id else None,
    }
