"""CQRS dashboard read model API (Phase 15 slice 2)."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import ReadModelProjectionServiceDep
from app.schemas.read_model import (
    FieldDashboardReadModelListResponse,
    FieldDashboardReadModelResponse,
    PlatformDashboardReadModelResponse,
    ReadModelRefreshResponse,
)
from app.services.farm import FarmNotFoundError
from app.services.field import FieldNotFoundError
from app.services.read_model_projection import ReadModelNotMaterializedError

router = APIRouter(prefix="/read-models", tags=["Read Models"])


@router.get("/dashboard", response_model=PlatformDashboardReadModelResponse)
async def get_platform_dashboard(
    projection_service: ReadModelProjectionServiceDep,
) -> PlatformDashboardReadModelResponse:
    """Platform-wide KPIs aggregated from field dashboard read models."""
    payload = await projection_service.get_platform_dashboard()
    return PlatformDashboardReadModelResponse(**payload)


@router.post(
    "/dashboard/refresh",
    response_model=ReadModelRefreshResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_platform_dashboard(
    projection_service: ReadModelProjectionServiceDep,
) -> ReadModelRefreshResponse:
    """Rebuild read models for all fields."""
    count = await projection_service.refresh_platform()
    from app.core.config import get_settings

    return ReadModelRefreshResponse(
        refreshed_fields=count,
        projection_version=get_settings().READ_MODEL_PROJECTION_VERSION,
    )


@router.get(
    "/farms/{farm_id}/dashboard",
    response_model=FieldDashboardReadModelListResponse,
)
async def get_farm_dashboard(
    farm_id: uuid.UUID,
    projection_service: ReadModelProjectionServiceDep,
) -> FieldDashboardReadModelListResponse:
    try:
        items = await projection_service.get_farm_dashboard(farm_id)
    except FarmNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    responses = [FieldDashboardReadModelResponse.model_validate(m) for m in items]
    return FieldDashboardReadModelListResponse(items=responses, count=len(responses))


@router.post(
    "/farms/{farm_id}/dashboard/refresh",
    response_model=FieldDashboardReadModelListResponse,
)
async def refresh_farm_dashboard(
    farm_id: uuid.UUID,
    projection_service: ReadModelProjectionServiceDep,
) -> FieldDashboardReadModelListResponse:
    try:
        items = await projection_service.refresh_farm(farm_id)
    except FarmNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    responses = [FieldDashboardReadModelResponse.model_validate(m) for m in items]
    return FieldDashboardReadModelListResponse(items=responses, count=len(responses))


@router.get(
    "/fields/{field_id}/dashboard",
    response_model=FieldDashboardReadModelResponse,
)
async def get_field_dashboard(
    field_id: uuid.UUID,
    projection_service: ReadModelProjectionServiceDep,
) -> FieldDashboardReadModelResponse:
    try:
        model = await projection_service.get_field_dashboard(field_id)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ReadModelNotMaterializedError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FieldDashboardReadModelResponse.model_validate(model)


@router.post(
    "/fields/{field_id}/dashboard/refresh",
    response_model=FieldDashboardReadModelResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_field_dashboard(
    field_id: uuid.UUID,
    projection_service: ReadModelProjectionServiceDep,
) -> FieldDashboardReadModelResponse:
    try:
        model = await projection_service.refresh_field(field_id)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FieldDashboardReadModelResponse.model_validate(model)
