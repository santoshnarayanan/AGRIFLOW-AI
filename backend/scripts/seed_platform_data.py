"""
Populate the local database with the Canonical Development Dataset (CDD) and
derived Phase 13–15 intelligence tables.

Usage (from backend/, venv active, PostgreSQL on POSTGRES_HOST:POSTGRES_PORT):

    python scripts/seed_platform_data.py

Skips CDD when farms already exist unless --force is passed (not implemented:
truncate manually or wipe the DB volume first).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select, text

from app.cdd import execute_cdd_workflow
from app.core.config import get_settings
from app.core.enums import AlertSeverity, AlertType
from app.core.logging import configure_logging
from app.db.models.alert import Alert
from app.db.models.domain_event_outbox import DomainEventOutbox
from app.db.models.farm import Farm
from app.db.models.field import Field
from app.db.models.field_dashboard_read_model import FieldDashboardReadModel
from app.db.models.field_digital_twin_state import FieldDigitalTwinState
from app.db.models.field_feature_snapshot import FieldFeatureSnapshot
from app.db.models.platform_user import PlatformUser
from app.db.models.recommendation import Recommendation
from app.db.repositories.alert import AlertRepository
from app.db.repositories.crop import CropRepository
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository
from app.db.repositories.farm import FarmRepository
from app.db.repositories.feature_extraction import FeatureExtractionRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.field_dashboard_read_model import FieldDashboardReadModelRepository
from app.db.repositories.field_digital_twin_state import FieldDigitalTwinStateRepository
from app.db.repositories.field_feature_snapshot import FieldFeatureSnapshotRepository
from app.db.repositories.read_model_metrics import ReadModelMetricsRepository
from app.db.repositories.recommendation import RecommendationRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.db.session import AsyncSessionFactory, engine
from app.events.publisher import OutboxDomainEventPublisher
from app.ml.service import MLEngineService
from app.ml.types import MLEngineId
from app.schemas.alert import AlertCreate
from app.services.alert import AlertService
from app.services.digital_twin import DigitalTwinService
from app.services.feature_store import FeatureStoreService
from app.services.read_model_projection import ReadModelProjectionService
from app.services.recommendation import RecommendationService

logger = logging.getLogger(__name__)

_CONTINUOUS_AGGREGATES: tuple[str, ...] = (
    "ca_sensor_hourly",
    "ca_sensor_daily",
    "ca_weather_daily",
    "ca_satellite_daily",
    "ca_weather_weekly",
    "ca_irrigation_monthly",
    "ca_disease_weekly",
    "ca_yield_seasonal",
)


async def _count(session, model) -> int:
    result = await session.scalar(select(func.count()).select_from(model))
    return int(result or 0)


async def refresh_continuous_aggregates() -> None:
    """Timescale refresh must run outside a SQLAlchemy transaction."""
    async with engine.connect() as conn:
        autocommit = await conn.execution_options(isolation_level="AUTOCOMMIT")
        for name in _CONTINUOUS_AGGREGATES:
            logger.info("Refreshing continuous aggregate %s", name)
            await autocommit.execute(
                text("CALL refresh_continuous_aggregate(:view, NULL, NULL)"),
                {"view": name},
            )


async def seed_intelligence_layer(session) -> None:
    field_repo = FieldRepository(session)
    event_publisher = OutboxDomainEventPublisher(DomainEventOutboxRepository(session))

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
    twin = DigitalTwinService(
        field_repository=field_repo,
        crop_repository=CropRepository(session),
        sensor_reading_repository=SensorReadingRepository(session),
        twin_state_repository=FieldDigitalTwinStateRepository(session),
        read_model_projection_service=read_models,
    )
    recommendations = RecommendationService(
        recommendation_repository=RecommendationRepository(session),
        field_repository=field_repo,
        crop_repository=CropRepository(session),
        event_publisher=event_publisher,
    )
    alerts = AlertService(
        alert_repository=AlertRepository(session),
        field_repository=field_repo,
        recommendation_repository=RecommendationRepository(session),
        event_publisher=event_publisher,
    )
    ml = MLEngineService(recommendations, feature_store)

    fields = await field_repo.list_all(limit=5000)
    for field in fields:
        await feature_store.materialize_field_snapshot(field.id)

    for field in fields:
        for engine_id in (
            MLEngineId.IRRIGATION_OPTIMIZATION,
            MLEngineId.DISEASE_RISK,
            MLEngineId.YIELD_FORECAST,
        ):
            await ml.run_engine(field.id, engine_id)

    now = datetime.now(timezone.utc)
    for field in fields[:3]:
        await alerts.create_alert(
            field.id,
            AlertCreate(
                alert_type=AlertType.SOIL_MOISTURE_LOW,
                severity=AlertSeverity.WARNING,
                title="Demo soil moisture alert",
                message="Seeded alert for UI and read-model validation.",
                triggered_at=now,
            ),
        )

    await read_models.refresh_platform()
    await twin.synchronize_platform()
    await session.commit()


async def run_seed(skip_cdd: bool) -> int:
    settings = get_settings()
    configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)

    async with AsyncSessionFactory() as probe:
        farm_count = await _count(probe, Farm)

    if farm_count == 0 and not skip_cdd:
        logger.info("Running CDD workflow (this may take ~1–2 minutes)...")
        report = await execute_cdd_workflow(notes="seed_platform_data.py")
        if not report.success:
            for err in report.errors:
                logger.error("CDD error: %s", err)
            return 1
        logger.info(
            "CDD persisted rows=%s",
            report.persistence_result.total_rows if report.persistence_result else 0,
        )
    elif farm_count > 0:
        logger.info("Farms already present (%s); skipping CDD load", farm_count)
    else:
        logger.warning("skip_cdd set and no farms — intelligence layer only")

    async with AsyncSessionFactory() as session:
        await refresh_continuous_aggregates()
        await seed_intelligence_layer(session)

        counts = {
            "farms": await _count(session, Farm),
            "fields": await _count(session, Field),
            "recommendations": await _count(session, Recommendation),
            "alerts": await _count(session, Alert),
            "field_feature_snapshots": await _count(session, FieldFeatureSnapshot),
            "field_dashboard_read_models": await _count(session, FieldDashboardReadModel),
            "field_digital_twin_states": await _count(session, FieldDigitalTwinState),
            "domain_event_outbox": await _count(session, DomainEventOutbox),
            "platform_users": await _count(session, PlatformUser),
        }
        logger.info("Seed complete: %s", counts)
        print("Seed complete:")
        for table, n in counts.items():
            print(f"  {table}: {n}")
        print(
            "  domain_event_consumer_inbox: (populated when Redpanda consumers run; optional in dev)"
        )
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed AGRIFLOW local database")
    parser.add_argument(
        "--skip-cdd",
        action="store_true",
        help="Only refresh aggregates and intelligence projections (DB must already have CDD)",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_seed(skip_cdd=args.skip_cdd)))


if __name__ == "__main__":
    main()
