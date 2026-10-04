"""
Farm API router.

Farm is the aggregate root of the AGRIFLOW-AI domain hierarchy (Phase 1 model,
Phase 13 API completion). All other entities — Field, Crop, and all time-series
domains — are children of a Farm.

Delivered endpoints:
    POST   /farms                — create a new farm
    GET    /farms                — list all farms (paginated)
    GET    /farms/{farm_id}      — get a single farm by ID
    PATCH  /farms/{farm_id}      — partial update of a farm
    DELETE /farms/{farm_id}      — delete a farm (cascades to all child fields)
"""

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import FarmServiceDep
from app.schemas.farm import FarmCreate, FarmResponse, FarmUpdate
from app.services.farm import DuplicateFarmCodeError, FarmNotFoundError

router = APIRouter(prefix="/farms", tags=["farms"])


@router.post("", response_model=FarmResponse, status_code=201)
async def create_farm(
    payload: FarmCreate,
    farm_service: FarmServiceDep,
) -> FarmResponse:
    """Create a new farm. farm_code must be unique across the platform."""
    try:
        farm = await farm_service.create_farm(payload)
    except DuplicateFarmCodeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return FarmResponse.model_validate(farm)


@router.get("", response_model=list[FarmResponse])
async def list_farms(
    farm_service: FarmServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[FarmResponse]:
    """Return all farms, ordered by creation date descending."""
    farms = await farm_service.list_farms(limit=limit, offset=offset)
    return [FarmResponse.model_validate(f) for f in farms]


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: uuid.UUID,
    farm_service: FarmServiceDep,
) -> FarmResponse:
    """Return a single farm by ID."""
    farm = await farm_service.get_farm(farm_id)
    if farm is None:
        raise HTTPException(status_code=404, detail=f"Farm '{farm_id}' not found.")
    return FarmResponse.model_validate(farm)


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: uuid.UUID,
    payload: FarmUpdate,
    farm_service: FarmServiceDep,
) -> FarmResponse:
    """Partially update a farm. Only supplied fields are changed."""
    try:
        farm = await farm_service.update_farm(farm_id, payload)
    except FarmNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FarmResponse.model_validate(farm)


@router.delete("/{farm_id}", status_code=204)
async def delete_farm(
    farm_id: uuid.UUID,
    farm_service: FarmServiceDep,
) -> None:
    """Delete a farm and all its child fields (cascade delete)."""
    try:
        await farm_service.delete_farm(farm_id)
    except FarmNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
