"""
Crop endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /fields/{field_id}/crops      — create a crop cycle under a field
    GET    /fields/{field_id}/crops      — list all crop cycles for a field
    GET    /crops/{crop_id}              — fetch a single crop cycle
    PATCH  /crops/{crop_id}             — partial update of a crop cycle
    DELETE /crops/{crop_id}             — remove a crop cycle

Domain exception → HTTP status mapping
---------------------------------------
    FieldNotFoundError      → 404 Not Found
    CropNotFoundError       → 404 Not Found
    InvalidHarvestDateError → 400 Bad Request
    InvalidYieldDataError   → 400 Bad Request
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CropServiceDep
from app.core.logging import get_logger
from app.db.models.crop import CropStatus
from app.schemas.common import PaginatedResponse
from app.schemas.crop import CropCreate, CropResponse, CropUpdate
from app.services.crop import CropNotFoundError, InvalidHarvestDateError, InvalidYieldDataError
from app.services.field import FieldNotFoundError

router = APIRouter(tags=["Crops"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/fields/{field_id}/crops",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a crop cycle",
    description=(
        "Create a new crop cycle under an existing field. "
        "Status is initialised to PLANNED; actual_harvest_date is set during "
        "a subsequent PATCH when the crop reaches HARVESTED."
    ),
)
async def create_crop(
    field_id: uuid.UUID,
    payload: CropCreate,
    service: CropServiceDep,
) -> CropResponse:
    log = logger.bind(field_id=str(field_id))
    try:
        crop = await service.create_crop(field_id, payload)
    except FieldNotFoundError as exc:
        log.warning("api.crops.create.field_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.crops.create.success", crop_id=str(crop.id))
    return CropResponse.model_validate(crop)


# ── List by field ──────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/crops",
    response_model=PaginatedResponse[CropResponse],
    status_code=status.HTTP_200_OK,
    summary="List crop cycles for a field",
    description=(
        "Return all crop cycles belonging to a field, ordered by planting_date "
        "descending (most recent first). Supports pagination and optional "
        "filtering by lifecycle status."
    ),
)
async def list_field_crops(
    field_id: uuid.UUID,
    service: CropServiceDep,
    status_filter: CropStatus | None = Query(
        default=None,
        alias="status",
        description="Filter results to a specific lifecycle status",
    ),
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
) -> PaginatedResponse[CropResponse]:
    crops = await service.list_field_crops(
        field_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse[CropResponse](
        items=[CropResponse.model_validate(c) for c in crops],
        total=len(crops),
        limit=limit,
        offset=offset,
    )


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/crops/{crop_id}",
    response_model=CropResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a crop cycle",
    description="Fetch a single crop cycle by its UUID primary key.",
)
async def get_crop(
    crop_id: uuid.UUID,
    service: CropServiceDep,
) -> CropResponse:
    crop = await service.get_crop(crop_id)
    if crop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop '{crop_id}' does not exist.",
        )
    return CropResponse.model_validate(crop)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/crops/{crop_id}",
    response_model=CropResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a crop cycle",
    description=(
        "Apply a partial update to an existing crop cycle. "
        "Only the fields present in the request body are modified. "
        "actual_harvest_date must not be earlier than planting_date."
    ),
)
async def update_crop(
    crop_id: uuid.UUID,
    payload: CropUpdate,
    service: CropServiceDep,
) -> CropResponse:
    log = logger.bind(crop_id=str(crop_id))
    try:
        crop = await service.update_crop(crop_id, payload)
    except CropNotFoundError as exc:
        log.warning("api.crops.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidHarvestDateError as exc:
        log.warning("api.crops.update.invalid_harvest_date")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidYieldDataError as exc:
        log.warning("api.crops.update.invalid_yield_data")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.crops.update.success")
    return CropResponse.model_validate(crop)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/crops/{crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a crop cycle",
    description="Permanently remove a crop cycle by its UUID primary key.",
)
async def delete_crop(
    crop_id: uuid.UUID,
    service: CropServiceDep,
) -> None:
    log = logger.bind(crop_id=str(crop_id))
    try:
        await service.delete_crop(crop_id)
    except CropNotFoundError as exc:
        log.warning("api.crops.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.crops.delete.success")
