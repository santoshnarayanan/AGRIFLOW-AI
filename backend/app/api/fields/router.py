"""
Field endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /farms/{farm_id}/fields       — create a field under a farm
    GET    /farms/{farm_id}/fields       — list all fields for a farm
    GET    /fields/{field_id}            — fetch a single field
    PATCH  /fields/{field_id}            — partial update of a field
    DELETE /fields/{field_id}            — remove a field

Domain exception → HTTP status mapping
---------------------------------------
    FarmNotFoundError      → 404 Not Found
    FieldNotFoundError     → 404 Not Found
    DuplicateFieldNameError → 409 Conflict
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import FieldServiceDep
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse
from app.schemas.field import FieldCreate, FieldResponse, FieldUpdate
from app.services.field import (
    DuplicateFieldNameError,
    FarmNotFoundError,
    FieldNotFoundError,
)

router = APIRouter(tags=["Fields"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/farms/{farm_id}/fields",
    response_model=FieldResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a field",
    description=(
        "Create a new field under an existing farm. "
        "Field names must be unique (case-insensitive) within the same farm."
    ),
)
async def create_field(
    farm_id: uuid.UUID,
    payload: FieldCreate,
    service: FieldServiceDep,
) -> FieldResponse:
    log = logger.bind(farm_id=str(farm_id))
    try:
        field = await service.create_field(farm_id, payload)
    except FarmNotFoundError as exc:
        log.warning("api.fields.create.farm_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DuplicateFieldNameError as exc:
        log.warning("api.fields.create.duplicate_name", field_name=payload.name)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    log.info("api.fields.create.success", field_id=str(field.id))
    return FieldResponse.model_validate(field)


# ── List by farm ───────────────────────────────────────────────────────────────


@router.get(
    "/farms/{farm_id}/fields",
    response_model=PaginatedResponse[FieldResponse],
    status_code=status.HTTP_200_OK,
    summary="List fields for a farm",
    description="Return all fields belonging to a farm, ordered by name. Supports pagination.",
)
async def list_fields_by_farm(
    farm_id: uuid.UUID,
    service: FieldServiceDep,
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
) -> PaginatedResponse[FieldResponse]:
    fields = await service.get_fields_by_farm(farm_id, limit=limit, offset=offset)
    return PaginatedResponse[FieldResponse](
        items=[FieldResponse.model_validate(f) for f in fields],
        total=len(fields),
        limit=limit,
        offset=offset,
    )


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}",
    response_model=FieldResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a field",
    description="Fetch a single field by its UUID primary key.",
)
async def get_field(
    field_id: uuid.UUID,
    service: FieldServiceDep,
) -> FieldResponse:
    field = await service.get_field(field_id)
    if field is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Field '{field_id}' does not exist.",
        )
    return FieldResponse.model_validate(field)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/fields/{field_id}",
    response_model=FieldResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a field",
    description=(
        "Apply a partial update to an existing field. "
        "Only the fields present in the request body are modified."
    ),
)
async def update_field(
    field_id: uuid.UUID,
    payload: FieldUpdate,
    service: FieldServiceDep,
) -> FieldResponse:
    log = logger.bind(field_id=str(field_id))
    try:
        field = await service.update_field(field_id, payload)
    except FieldNotFoundError as exc:
        log.warning("api.fields.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DuplicateFieldNameError as exc:
        log.warning("api.fields.update.duplicate_name")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    log.info("api.fields.update.success")
    return FieldResponse.model_validate(field)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/fields/{field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a field",
    description="Permanently remove a field by its UUID primary key.",
)
async def delete_field(
    field_id: uuid.UUID,
    service: FieldServiceDep,
) -> None:
    log = logger.bind(field_id=str(field_id))
    try:
        await service.delete_field(field_id)
    except FieldNotFoundError as exc:
        log.warning("api.fields.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.fields.delete.success")
