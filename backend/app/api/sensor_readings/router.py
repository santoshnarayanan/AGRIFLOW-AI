"""
Sensor Reading endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /fields/{field_id}/sensor-readings              — create a telemetry observation under a field
    GET    /fields/{field_id}/sensor-readings              — list telemetry observations for a field
    GET    /sensor-readings/{sensor_reading_id}            — fetch a single telemetry observation
    DELETE /sensor-readings/{sensor_reading_id}           — administrative removal of a telemetry observation

Absent by design (ADR-007-29, ADR-007-32)
------------------------------------------
    PATCH  /sensor-readings/{sensor_reading_id}  — NOT IMPLEMENTED; telemetry is immutable
    PUT    /sensor-readings/{sensor_reading_id}  — NOT IMPLEMENTED; telemetry is immutable

Domain exception → HTTP status mapping (ADR-007-33)
-----------------------------------------------------
    FieldNotFoundError              → 404 Not Found
    SensorReadingNotFoundError      → 404 Not Found
    InvalidSensorTimestampError     → 422 Unprocessable Entity
"""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SensorReadingServiceDep
from app.core.logging import get_logger
from app.schemas.sensor_reading import SensorReadingCreate, SensorReadingResponse
from app.services.field import FieldNotFoundError
from app.services.sensor_reading import InvalidSensorTimestampError, SensorReadingNotFoundError

router = APIRouter(tags=["Sensor Readings"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/fields/{field_id}/sensor-readings",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sensor reading",
    description=(
        "Create a new telemetry observation under an existing field. "
        "Sensor readings are immutable and append-only. "
        "``recorded_at`` must be timezone-aware and cannot be in the future."
    ),
)
async def create_sensor_reading(
    field_id: uuid.UUID,
    payload: SensorReadingCreate,
    service: SensorReadingServiceDep,
) -> SensorReadingResponse:
    log = logger.bind(field_id=str(field_id), sensor_type=payload.sensor_type.value)
    try:
        reading = await service.create_sensor_reading(field_id, payload)
    except FieldNotFoundError as exc:
        log.warning("api.sensor_readings.create.field_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidSensorTimestampError as exc:
        log.warning("api.sensor_readings.create.invalid_timestamp")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    log.info("api.sensor_readings.create.success", sensor_reading_id=str(reading.id))
    return SensorReadingResponse.model_validate(reading)


# ── List by field ──────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/sensor-readings",
    response_model=list[SensorReadingResponse],
    status_code=status.HTTP_200_OK,
    summary="List sensor readings for a field",
    description=(
        "Return all telemetry observations belonging to a field, ordered by "
        "recorded_at descending (most recent observation first)."
    ),
)
async def list_field_sensor_readings(
    field_id: uuid.UUID,
    service: SensorReadingServiceDep,
) -> list[SensorReadingResponse]:
    log = logger.bind(field_id=str(field_id))
    try:
        readings = await service.list_field_sensor_readings(field_id)
    except FieldNotFoundError as exc:
        log.warning("api.sensor_readings.list.field_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.sensor_readings.list.success", count=len(readings))
    return [SensorReadingResponse.model_validate(r) for r in readings]


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/sensor-readings/{sensor_reading_id}",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a sensor reading",
    description="Fetch a single telemetry observation by UUID.",
)
async def get_sensor_reading(
    sensor_reading_id: uuid.UUID,
    service: SensorReadingServiceDep,
) -> SensorReadingResponse:
    log = logger.bind(sensor_reading_id=str(sensor_reading_id))
    try:
        reading = await service.get_sensor_reading(sensor_reading_id)
    except SensorReadingNotFoundError as exc:
        log.warning("api.sensor_readings.get.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return SensorReadingResponse.model_validate(reading)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/sensor-readings/{sensor_reading_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sensor reading",
    description=(
        "Permanently remove a telemetry observation. "
        "Intended for administrative cleanup of invalid or corrupted telemetry."
    ),
)
async def delete_sensor_reading(
    sensor_reading_id: uuid.UUID,
    service: SensorReadingServiceDep,
) -> None:
    log = logger.bind(sensor_reading_id=str(sensor_reading_id))
    try:
        await service.delete_sensor_reading(sensor_reading_id)
    except SensorReadingNotFoundError as exc:
        log.warning("api.sensor_readings.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.sensor_readings.delete.success")
