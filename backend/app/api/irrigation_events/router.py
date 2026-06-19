"""
Irrigation Event endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /fields/{field_id}/irrigation-events           — log an irrigation event under a field
    GET    /fields/{field_id}/irrigation-events           — list irrigation events for a field
    GET    /irrigation-events/{event_id}                  — fetch a single irrigation event
    PATCH  /irrigation-events/{event_id}                  — partial update of an irrigation event
    DELETE /irrigation-events/{event_id}                  — remove an irrigation event

Domain exception → HTTP status mapping
---------------------------------------
    FieldNotFoundError                → 404 Not Found
    IrrigationEventNotFoundError      → 404 Not Found
    InvalidIrrigationTimestampError   → 400 Bad Request
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import IrrigationEventServiceDep
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse
from app.schemas.irrigation_event import (
    IrrigationEventCreate,
    IrrigationEventResponse,
    IrrigationEventUpdate,
)
from app.services.field import FieldNotFoundError
from app.services.irrigation_event import (
    InvalidIrrigationTimestampError,
    IrrigationEventNotFoundError,
)

router = APIRouter(tags=["Irrigation Events"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/fields/{field_id}/irrigation-events",
    response_model=IrrigationEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log an irrigation event",
    description=(
        "Log a new irrigation event under an existing field. "
        "``started_at`` must be timezone-aware and cannot be in the future. "
        "``ended_at``, when supplied, must be timezone-aware and not earlier than "
        "``started_at``. "
        "``duration_minutes`` and ``water_volume_liters`` are optional for "
        "non-metered systems."
    ),
)
async def create_irrigation_event(
    field_id: uuid.UUID,
    payload: IrrigationEventCreate,
    service: IrrigationEventServiceDep,
) -> IrrigationEventResponse:
    log = logger.bind(
        field_id=str(field_id),
        irrigation_method=payload.irrigation_method.value,
    )
    try:
        event = await service.create_irrigation_event(field_id, payload)
    except FieldNotFoundError as exc:
        log.warning("api.irrigation_events.create.field_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidIrrigationTimestampError as exc:
        log.warning("api.irrigation_events.create.invalid_timestamp")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.irrigation_events.create.success", event_id=str(event.id))
    return IrrigationEventResponse.model_validate(event)


# ── List by field ──────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/irrigation-events",
    response_model=PaginatedResponse[IrrigationEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List irrigation events for a field",
    description=(
        "Return all irrigation events belonging to a field, ordered by "
        "started_at descending (most recent event first). "
        "Supports pagination via ``limit`` and ``offset``."
    ),
)
async def list_field_irrigation_events(
    field_id: uuid.UUID,
    service: IrrigationEventServiceDep,
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
) -> PaginatedResponse[IrrigationEventResponse]:
    events = await service.list_field_irrigation_events(
        field_id,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse[IrrigationEventResponse](
        items=[IrrigationEventResponse.model_validate(e) for e in events],
        total=len(events),
        limit=limit,
        offset=offset,
    )


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/irrigation-events/{event_id}",
    response_model=IrrigationEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an irrigation event",
    description="Fetch a single irrigation event by its UUID primary key.",
)
async def get_irrigation_event(
    event_id: uuid.UUID,
    service: IrrigationEventServiceDep,
) -> IrrigationEventResponse:
    event = await service.get_irrigation_event(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Irrigation event '{event_id}' does not exist.",
        )
    return IrrigationEventResponse.model_validate(event)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/irrigation-events/{event_id}",
    response_model=IrrigationEventResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an irrigation event",
    description=(
        "Apply a partial update to an existing irrigation event. "
        "Only the fields present in the request body are modified. "
        "``started_at``, when supplied, must not be in the future. "
        "The effective ``ended_at`` must not precede the effective ``started_at`` "
        "after the update is applied."
    ),
)
async def update_irrigation_event(
    event_id: uuid.UUID,
    payload: IrrigationEventUpdate,
    service: IrrigationEventServiceDep,
) -> IrrigationEventResponse:
    log = logger.bind(event_id=str(event_id))
    try:
        event = await service.update_irrigation_event(event_id, payload)
    except IrrigationEventNotFoundError as exc:
        log.warning("api.irrigation_events.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidIrrigationTimestampError as exc:
        log.warning("api.irrigation_events.update.invalid_timestamp")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.irrigation_events.update.success")
    return IrrigationEventResponse.model_validate(event)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/irrigation-events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an irrigation event",
    description="Permanently remove an irrigation event by its UUID primary key.",
)
async def delete_irrigation_event(
    event_id: uuid.UUID,
    service: IrrigationEventServiceDep,
) -> None:
    log = logger.bind(event_id=str(event_id))
    try:
        await service.delete_irrigation_event(event_id)
    except IrrigationEventNotFoundError as exc:
        log.warning("api.irrigation_events.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.irrigation_events.delete.success")
