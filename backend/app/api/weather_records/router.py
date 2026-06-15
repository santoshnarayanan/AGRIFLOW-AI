"""
Weather Record endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /fields/{field_id}/weather-records              — create a weather observation under a field
    GET    /fields/{field_id}/weather-records              — list weather observations for a field
    GET    /weather-records/{weather_record_id}            — fetch a single weather observation
    PATCH  /weather-records/{weather_record_id}           — partial update of a weather observation
    DELETE /weather-records/{weather_record_id}           — remove a weather observation

Domain exception → HTTP status mapping
---------------------------------------
    FieldNotFoundError              → 404 Not Found
    WeatherRecordNotFoundError      → 404 Not Found
    InvalidWeatherTimestampError    → 400 Bad Request
    InvalidWeatherMeasurementError  → 400 Bad Request
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import WeatherRecordServiceDep
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse
from app.schemas.weather_record import (
    WeatherRecordCreate,
    WeatherRecordResponse,
    WeatherRecordUpdate,
)
from app.services.field import FieldNotFoundError
from app.services.weather_record import (
    InvalidWeatherMeasurementError,
    InvalidWeatherTimestampError,
    WeatherRecordNotFoundError,
)

router = APIRouter(tags=["Weather Records"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/fields/{field_id}/weather-records",
    response_model=WeatherRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a weather record",
    description=(
        "Create a new weather observation under an existing field. "
        "``recorded_at`` must not be in the future. "
        "``humidity_percent`` must be in [0, 100]; ``rainfall_mm`` and "
        "``wind_speed_kmh`` must be non-negative. "
        "``data_source`` defaults to MANUAL when omitted."
    ),
)
async def create_weather_record(
    field_id: uuid.UUID,
    payload: WeatherRecordCreate,
    service: WeatherRecordServiceDep,
) -> WeatherRecordResponse:
    log = logger.bind(field_id=str(field_id))
    try:
        record = await service.create_weather_record(field_id, payload)
    except FieldNotFoundError as exc:
        log.warning("api.weather_records.create.field_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidWeatherTimestampError as exc:
        log.warning("api.weather_records.create.invalid_timestamp")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidWeatherMeasurementError as exc:
        log.warning("api.weather_records.create.invalid_measurement")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.weather_records.create.success", record_id=str(record.id))
    return WeatherRecordResponse.model_validate(record)


# ── List by field ──────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/weather-records",
    response_model=PaginatedResponse[WeatherRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="List weather records for a field",
    description=(
        "Return all weather observations belonging to a field, ordered by "
        "recorded_at descending (most recent observation first). "
        "Supports pagination via ``limit`` and ``offset``."
    ),
)
async def list_field_weather_records(
    field_id: uuid.UUID,
    service: WeatherRecordServiceDep,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of records to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip",
    ),
) -> PaginatedResponse[WeatherRecordResponse]:
    records = await service.list_field_weather_records(
        field_id,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse[WeatherRecordResponse](
        items=[WeatherRecordResponse.model_validate(r) for r in records],
        total=len(records),
        limit=limit,
        offset=offset,
    )


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/weather-records/{weather_record_id}",
    response_model=WeatherRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a weather record",
    description="Fetch a single weather observation by its UUID primary key.",
)
async def get_weather_record(
    weather_record_id: uuid.UUID,
    service: WeatherRecordServiceDep,
) -> WeatherRecordResponse:
    record = await service.get_weather_record(weather_record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather record '{weather_record_id}' does not exist.",
        )
    return WeatherRecordResponse.model_validate(record)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/weather-records/{weather_record_id}",
    response_model=WeatherRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a weather record",
    description=(
        "Apply a partial update to an existing weather observation. "
        "Only the fields present in the request body are modified. "
        "Validation rules for timestamp and measurement bounds apply to "
        "any field that is supplied."
    ),
)
async def update_weather_record(
    weather_record_id: uuid.UUID,
    payload: WeatherRecordUpdate,
    service: WeatherRecordServiceDep,
) -> WeatherRecordResponse:
    log = logger.bind(weather_record_id=str(weather_record_id))
    try:
        record = await service.update_weather_record(weather_record_id, payload)
    except WeatherRecordNotFoundError as exc:
        log.warning("api.weather_records.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidWeatherTimestampError as exc:
        log.warning("api.weather_records.update.invalid_timestamp")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidWeatherMeasurementError as exc:
        log.warning("api.weather_records.update.invalid_measurement")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.weather_records.update.success")
    return WeatherRecordResponse.model_validate(record)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/weather-records/{weather_record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a weather record",
    description="Permanently remove a weather observation by its UUID primary key.",
)
async def delete_weather_record(
    weather_record_id: uuid.UUID,
    service: WeatherRecordServiceDep,
) -> None:
    log = logger.bind(weather_record_id=str(weather_record_id))
    try:
        await service.delete_weather_record(weather_record_id)
    except WeatherRecordNotFoundError as exc:
        log.warning("api.weather_records.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.weather_records.delete.success")
