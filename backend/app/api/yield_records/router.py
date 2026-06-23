"""
Yield Record endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /crops/{crop_id}/yield-records              — log a yield record for a crop cycle
    GET    /crops/{crop_id}/yield-records              — list yield records for a crop cycle
    GET    /yield-records/{yield_record_id}            — fetch a single yield record
    PATCH  /yield-records/{yield_record_id}            — partial update of a yield record
    DELETE /yield-records/{yield_record_id}            — remove a yield record

Domain exception → HTTP status mapping
---------------------------------------
    CropNotFoundError        → 404 Not Found
    YieldRecordNotFoundError → 404 Not Found
    InvalidYieldRecordError  → 400 Bad Request
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import YieldRecordServiceDep
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse
from app.schemas.yield_record import (
    YieldRecordCreate,
    YieldRecordResponse,
    YieldRecordUpdate,
)
from app.services.crop import CropNotFoundError
from app.services.yield_record import (
    InvalidYieldRecordError,
    YieldRecordNotFoundError,
)

router = APIRouter(tags=["Yield Records"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/crops/{crop_id}/yield-records",
    response_model=YieldRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a yield record",
    description=(
        "Log a new yield observation for an existing crop cycle. "
        "``recorded_at`` must be timezone-aware and cannot be in the future. "
        "``field_id`` is resolved server-side from the crop record and must not "
        "be supplied in the request body. "
        "``area_harvested_ha``, when supplied, must be greater than zero. "
        "``test_weight_kg_hl``, when supplied, must be greater than zero."
    ),
)
async def create_yield_record(
    crop_id: uuid.UUID,
    payload: YieldRecordCreate,
    service: YieldRecordServiceDep,
) -> YieldRecordResponse:
    log = logger.bind(
        crop_id=str(crop_id),
        measurement_method=payload.measurement_method.value,
    )
    try:
        record = await service.create_yield_record(crop_id, payload)
    except CropNotFoundError as exc:
        log.warning("api.yield_records.create.crop_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidYieldRecordError as exc:
        log.warning("api.yield_records.create.invalid_record")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.yield_records.create.success", record_id=str(record.id))
    return YieldRecordResponse.model_validate(record)


# ── List by crop ───────────────────────────────────────────────────────────────


@router.get(
    "/crops/{crop_id}/yield-records",
    response_model=PaginatedResponse[YieldRecordResponse],
    status_code=status.HTTP_200_OK,
    summary="List yield records for a crop cycle",
    description=(
        "Return all yield records belonging to a crop cycle, ordered by "
        "recorded_at descending (most recent measurement first). "
        "Supports pagination via ``limit`` and ``offset``."
    ),
)
async def list_crop_yield_records(
    crop_id: uuid.UUID,
    service: YieldRecordServiceDep,
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
) -> PaginatedResponse[YieldRecordResponse]:
    records = await service.list_crop_yield_records(
        crop_id,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse[YieldRecordResponse](
        items=[YieldRecordResponse.model_validate(r) for r in records],
        total=len(records),
        limit=limit,
        offset=offset,
    )


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/yield-records/{yield_record_id}",
    response_model=YieldRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a yield record",
    description="Fetch a single yield record by its UUID primary key.",
)
async def get_yield_record(
    yield_record_id: uuid.UUID,
    service: YieldRecordServiceDep,
) -> YieldRecordResponse:
    record = await service.get_yield_record(yield_record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Yield record '{yield_record_id}' does not exist.",
        )
    return YieldRecordResponse.model_validate(record)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/yield-records/{yield_record_id}",
    response_model=YieldRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a yield record",
    description=(
        "Apply a partial update to an existing yield record. "
        "Only the fields present in the request body are modified. "
        "``crop_id`` and ``field_id`` are immutable and cannot be changed. "
        "``recorded_at``, when supplied, must not be in the future. "
        "``area_harvested_ha`` and ``test_weight_kg_hl``, when supplied, "
        "must be greater than zero."
    ),
)
async def update_yield_record(
    yield_record_id: uuid.UUID,
    payload: YieldRecordUpdate,
    service: YieldRecordServiceDep,
) -> YieldRecordResponse:
    log = logger.bind(yield_record_id=str(yield_record_id))
    try:
        record = await service.update_yield_record(yield_record_id, payload)
    except YieldRecordNotFoundError as exc:
        log.warning("api.yield_records.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidYieldRecordError as exc:
        log.warning("api.yield_records.update.invalid_record")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.yield_records.update.success")
    return YieldRecordResponse.model_validate(record)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/yield-records/{yield_record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a yield record",
    description="Permanently remove a yield record by its UUID primary key.",
)
async def delete_yield_record(
    yield_record_id: uuid.UUID,
    service: YieldRecordServiceDep,
) -> None:
    log = logger.bind(yield_record_id=str(yield_record_id))
    try:
        await service.delete_yield_record(yield_record_id)
    except YieldRecordNotFoundError as exc:
        log.warning("api.yield_records.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.yield_records.delete.success")
