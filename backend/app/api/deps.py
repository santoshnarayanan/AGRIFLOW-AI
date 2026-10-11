"""
Shared FastAPI dependency providers.

Every route that needs a database session or a domain service receives it
through one of the ``Annotated`` aliases defined here.  This keeps route
signatures lean and ensures a single transaction per request.

Session lifecycle
-----------------
``get_session`` opens an ``AsyncSession``, begins an explicit transaction, and
yields to the route handler.  On success the transaction is committed; on any
unhandled exception it is rolled back.  The session is closed in all cases
because ``AsyncSessionFactory`` is used as an async context manager.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.repositories.alert import AlertRepository
from app.db.repositories.crop import CropRepository
from app.db.repositories.domain_event_consumer_inbox import (
    DomainEventConsumerInboxRepository,
)
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository
from app.db.repositories.disease_observation import DiseaseObservationRepository
from app.db.repositories.farm import FarmRepository
from app.db.repositories.feature_extraction import FeatureExtractionRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.field_dashboard_read_model import FieldDashboardReadModelRepository
from app.db.repositories.field_digital_twin_state import FieldDigitalTwinStateRepository
from app.db.repositories.field_feature_snapshot import FieldFeatureSnapshotRepository
from app.db.repositories.read_model_metrics import ReadModelMetricsRepository
from app.db.repositories.irrigation_event import IrrigationEventRepository
from app.db.repositories.platform_user import PlatformUserRepository
from app.db.repositories.recommendation import RecommendationRepository
from app.db.repositories.satellite_observation import SatelliteObservationRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.db.repositories.soil_profile import SoilProfileRepository
from app.db.repositories.weather_record import WeatherRecordRepository
from app.db.repositories.yield_record import YieldRecordRepository
from app.db.session import AsyncSessionFactory
from app.events.publisher import NoOpDomainEventPublisher, OutboxDomainEventPublisher
from app.ml.service import MLEngineService
from app.services.alert import AlertService
from app.services.crop import CropService
from app.services.domain_event_outbox import DomainEventOutboxService
from app.services.disease_observation import DiseaseObservationService
from app.services.farm import FarmService
from app.services.digital_twin import DigitalTwinService
from app.services.feature_store import FeatureStoreService
from app.services.read_model_projection import ReadModelProjectionService
from app.services.field import FieldService
from app.services.irrigation_event import IrrigationEventService
from app.services.recommendation import RecommendationService
from app.services.satellite_observation import SatelliteObservationService
from app.services.sensor_reading import SensorReadingService
from app.services.soil_profile import SoilProfileService
from app.services.weather_record import WeatherRecordService
from app.services.auth import AuthService
from app.services.yield_record import YieldRecordService


# ── Database session ──────────────────────────────────────────────────────────


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional AsyncSession for the duration of one request."""
    async with AsyncSessionFactory() as session:
        async with session.begin():
            yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ── Domain events (Phase 14) ──────────────────────────────────────────────────


def get_domain_event_publisher(
    session: SessionDep,
) -> OutboxDomainEventPublisher | NoOpDomainEventPublisher:
    if not get_settings().EVENTS_ENABLED:
        return NoOpDomainEventPublisher()
    return OutboxDomainEventPublisher(DomainEventOutboxRepository(session))


DomainEventPublisherDep = Annotated[
    OutboxDomainEventPublisher | NoOpDomainEventPublisher,
    Depends(get_domain_event_publisher),
]


def get_domain_event_outbox_service(session: SessionDep) -> DomainEventOutboxService:
    return DomainEventOutboxService(
        DomainEventOutboxRepository(session),
        DomainEventConsumerInboxRepository(session),
    )


DomainEventOutboxServiceDep = Annotated[
    DomainEventOutboxService,
    Depends(get_domain_event_outbox_service),
]


# ── Domain service factories ──────────────────────────────────────────────────


def get_field_service(session: SessionDep) -> FieldService:
    """Construct a ``FieldService`` wired to the request-scoped session."""
    return FieldService(
        field_repository=FieldRepository(session),
        farm_repository=FarmRepository(session),
    )


FieldServiceDep = Annotated[FieldService, Depends(get_field_service)]


def get_crop_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> CropService:
    """Construct a ``CropService`` wired to the request-scoped session."""
    return CropService(
        crop_repository=CropRepository(session),
        field_repository=FieldRepository(session),
        event_publisher=event_publisher,
    )


CropServiceDep = Annotated[CropService, Depends(get_crop_service)]


def get_disease_observation_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> DiseaseObservationService:
    """Construct a ``DiseaseObservationService`` wired to the request-scoped session."""
    return DiseaseObservationService(
        disease_observation_repository=DiseaseObservationRepository(session),
        crop_repository=CropRepository(session),
        event_publisher=event_publisher,
    )


DiseaseObservationServiceDep = Annotated[
    DiseaseObservationService, Depends(get_disease_observation_service)
]


def get_soil_profile_service(session: SessionDep) -> SoilProfileService:
    """Construct a ``SoilProfileService`` wired to the request-scoped session."""
    return SoilProfileService(
        soil_profile_repository=SoilProfileRepository(session),
        field_repository=FieldRepository(session),
    )


SoilProfileServiceDep = Annotated[SoilProfileService, Depends(get_soil_profile_service)]


def get_weather_record_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> WeatherRecordService:
    """Construct a ``WeatherRecordService`` wired to the request-scoped session."""
    return WeatherRecordService(
        weather_record_repository=WeatherRecordRepository(session),
        field_repository=FieldRepository(session),
        event_publisher=event_publisher,
    )


WeatherRecordServiceDep = Annotated[WeatherRecordService, Depends(get_weather_record_service)]


def get_sensor_reading_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> SensorReadingService:
    """Construct a ``SensorReadingService`` wired to the request-scoped session."""
    return SensorReadingService(
        sensor_reading_repository=SensorReadingRepository(session),
        field_repository=FieldRepository(session),
        event_publisher=event_publisher,
    )


SensorReadingServiceDep = Annotated[SensorReadingService, Depends(get_sensor_reading_service)]


def get_satellite_observation_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> SatelliteObservationService:
    """Construct a ``SatelliteObservationService`` wired to the request-scoped session."""
    return SatelliteObservationService(
        satellite_observation_repository=SatelliteObservationRepository(session),
        field_repository=FieldRepository(session),
        event_publisher=event_publisher,
    )


SatelliteObservationServiceDep = Annotated[
    SatelliteObservationService, Depends(get_satellite_observation_service)
]


def get_irrigation_event_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> IrrigationEventService:
    """Construct an ``IrrigationEventService`` wired to the request-scoped session."""
    return IrrigationEventService(
        irrigation_event_repository=IrrigationEventRepository(session),
        field_repository=FieldRepository(session),
        event_publisher=event_publisher,
    )


IrrigationEventServiceDep = Annotated[IrrigationEventService, Depends(get_irrigation_event_service)]


def get_yield_record_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> YieldRecordService:
    """Construct a ``YieldRecordService`` wired to the request-scoped session."""
    return YieldRecordService(
        yield_record_repository=YieldRecordRepository(session),
        crop_repository=CropRepository(session),
        event_publisher=event_publisher,
    )


YieldRecordServiceDep = Annotated[YieldRecordService, Depends(get_yield_record_service)]


def get_farm_service(session: SessionDep) -> FarmService:
    """Construct a ``FarmService`` wired to the request-scoped session."""
    return FarmService(farm_repository=FarmRepository(session))


FarmServiceDep = Annotated[FarmService, Depends(get_farm_service)]


def get_recommendation_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> RecommendationService:
    """Construct a ``RecommendationService`` wired to the request-scoped session."""
    return RecommendationService(
        recommendation_repository=RecommendationRepository(session),
        field_repository=FieldRepository(session),
        crop_repository=CropRepository(session),
        event_publisher=event_publisher,
    )


RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]


def get_alert_service(
    session: SessionDep,
    event_publisher: DomainEventPublisherDep,
) -> AlertService:
    """Construct an ``AlertService`` wired to the request-scoped session."""
    return AlertService(
        alert_repository=AlertRepository(session),
        field_repository=FieldRepository(session),
        recommendation_repository=RecommendationRepository(session),
        event_publisher=event_publisher,
    )


AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]


def get_feature_store_service(session: SessionDep) -> FeatureStoreService:
    return FeatureStoreService(
        field_repository=FieldRepository(session),
        snapshot_repository=FieldFeatureSnapshotRepository(session),
        extraction_repository=FeatureExtractionRepository(session),
    )


FeatureStoreServiceDep = Annotated[FeatureStoreService, Depends(get_feature_store_service)]


def get_read_model_projection_service(session: SessionDep) -> ReadModelProjectionService:
    return ReadModelProjectionService(
        farm_repository=FarmRepository(session),
        field_repository=FieldRepository(session),
        read_model_repository=FieldDashboardReadModelRepository(session),
        metrics_repository=ReadModelMetricsRepository(session),
        feature_snapshot_repository=FieldFeatureSnapshotRepository(session),
    )


ReadModelProjectionServiceDep = Annotated[
    ReadModelProjectionService, Depends(get_read_model_projection_service)
]


def get_digital_twin_service(
    session: SessionDep,
    read_model_projection_service: ReadModelProjectionServiceDep,
) -> DigitalTwinService:
    return DigitalTwinService(
        field_repository=FieldRepository(session),
        crop_repository=CropRepository(session),
        sensor_reading_repository=SensorReadingRepository(session),
        twin_state_repository=FieldDigitalTwinStateRepository(session),
        read_model_projection_service=read_model_projection_service,
    )


DigitalTwinServiceDep = Annotated[DigitalTwinService, Depends(get_digital_twin_service)]


def get_ml_engine_service(
    recommendation_service: RecommendationServiceDep,
    feature_store_service: FeatureStoreServiceDep,
) -> MLEngineService:
    return MLEngineService(recommendation_service, feature_store_service)


MLEngineServiceDep = Annotated[MLEngineService, Depends(get_ml_engine_service)]


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(PlatformUserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
