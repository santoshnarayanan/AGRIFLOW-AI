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

from app.db.repositories.crop import CropRepository
from app.db.repositories.farm import FarmRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.irrigation_event import IrrigationEventRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.db.repositories.soil_profile import SoilProfileRepository
from app.db.repositories.weather_record import WeatherRecordRepository
from app.db.repositories.yield_record import YieldRecordRepository
from app.db.session import AsyncSessionFactory
from app.services.crop import CropService
from app.services.field import FieldService
from app.services.irrigation_event import IrrigationEventService
from app.services.sensor_reading import SensorReadingService
from app.services.soil_profile import SoilProfileService
from app.services.weather_record import WeatherRecordService
from app.services.yield_record import YieldRecordService


# ── Database session ──────────────────────────────────────────────────────────


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional AsyncSession for the duration of one request."""
    async with AsyncSessionFactory() as session:
        async with session.begin():
            yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ── Domain service factories ──────────────────────────────────────────────────


def get_field_service(session: SessionDep) -> FieldService:
    """Construct a ``FieldService`` wired to the request-scoped session."""
    return FieldService(
        field_repository=FieldRepository(session),
        farm_repository=FarmRepository(session),
    )


FieldServiceDep = Annotated[FieldService, Depends(get_field_service)]


def get_crop_service(session: SessionDep) -> CropService:
    """Construct a ``CropService`` wired to the request-scoped session."""
    return CropService(
        crop_repository=CropRepository(session),
        field_repository=FieldRepository(session),
    )


CropServiceDep = Annotated[CropService, Depends(get_crop_service)]


def get_soil_profile_service(session: SessionDep) -> SoilProfileService:
    """Construct a ``SoilProfileService`` wired to the request-scoped session."""
    return SoilProfileService(
        soil_profile_repository=SoilProfileRepository(session),
        field_repository=FieldRepository(session),
    )


SoilProfileServiceDep = Annotated[SoilProfileService, Depends(get_soil_profile_service)]


def get_weather_record_service(session: SessionDep) -> WeatherRecordService:
    """Construct a ``WeatherRecordService`` wired to the request-scoped session."""
    return WeatherRecordService(
        weather_record_repository=WeatherRecordRepository(session),
        field_repository=FieldRepository(session),
    )


WeatherRecordServiceDep = Annotated[WeatherRecordService, Depends(get_weather_record_service)]


def get_sensor_reading_service(session: SessionDep) -> SensorReadingService:
    """Construct a ``SensorReadingService`` wired to the request-scoped session."""
    return SensorReadingService(
        sensor_reading_repository=SensorReadingRepository(session),
        field_repository=FieldRepository(session),
    )


SensorReadingServiceDep = Annotated[SensorReadingService, Depends(get_sensor_reading_service)]


def get_irrigation_event_service(session: SessionDep) -> IrrigationEventService:
    """Construct an ``IrrigationEventService`` wired to the request-scoped session."""
    return IrrigationEventService(
        irrigation_event_repository=IrrigationEventRepository(session),
        field_repository=FieldRepository(session),
    )


IrrigationEventServiceDep = Annotated[IrrigationEventService, Depends(get_irrigation_event_service)]


def get_yield_record_service(session: SessionDep) -> YieldRecordService:
    """Construct a ``YieldRecordService`` wired to the request-scoped session."""
    return YieldRecordService(
        yield_record_repository=YieldRecordRepository(session),
        crop_repository=CropRepository(session),
    )


YieldRecordServiceDep = Annotated[YieldRecordService, Depends(get_yield_record_service)]
