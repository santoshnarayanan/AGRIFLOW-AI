"""
SoilProfile endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /fields/{field_id}/soil-profile      — create the soil profile for a field
    GET    /fields/{field_id}/soil-profile      — fetch the soil profile for a field
    PATCH  /soil-profiles/{soil_profile_id}     — partial update of a soil profile
    DELETE /soil-profiles/{soil_profile_id}     — remove a soil profile

Domain exception → HTTP status mapping
---------------------------------------
    FieldNotFoundError        → 404 Not Found
    SoilProfileNotFoundError  → 404 Not Found
    DuplicateSoilProfileError → 409 Conflict
"""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SoilProfileServiceDep
from app.core.logging import get_logger
from app.schemas.soil_profile import (
    SoilProfileCreate,
    SoilProfileResponse,
    SoilProfileUpdate,
)
from app.services.field import FieldNotFoundError
from app.services.soil_profile import DuplicateSoilProfileError, SoilProfileNotFoundError

router = APIRouter(tags=["Soil Profiles"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/fields/{field_id}/soil-profile",
    response_model=SoilProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a soil profile",
    description=(
        "Create a soil profile for an existing field. "
        "Each field may have at most one soil profile. "
        "Nutrient measurements (pH, organic matter, NPK) are optional at creation "
        "and can be added later via PATCH."
    ),
)
async def create_soil_profile(
    field_id: uuid.UUID,
    payload: SoilProfileCreate,
    service: SoilProfileServiceDep,
) -> SoilProfileResponse:
    log = logger.bind(field_id=str(field_id))
    try:
        profile = await service.create_soil_profile(field_id, payload)
    except FieldNotFoundError as exc:
        log.warning("api.soil_profiles.create.field_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except DuplicateSoilProfileError as exc:
        log.warning("api.soil_profiles.create.duplicate_profile")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    log.info("api.soil_profiles.create.success", profile_id=str(profile.id))
    return SoilProfileResponse.model_validate(profile)


# ── Get by field ───────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/soil-profile",
    response_model=SoilProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the soil profile for a field",
    description="Fetch the soil profile associated with a specific field by its UUID.",
)
async def get_soil_profile_by_field(
    field_id: uuid.UUID,
    service: SoilProfileServiceDep,
) -> SoilProfileResponse:
    log = logger.bind(field_id=str(field_id))
    try:
        profile = await service.get_soil_profile_by_field(field_id)
    except SoilProfileNotFoundError as exc:
        log.warning("api.soil_profiles.get_by_field.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return SoilProfileResponse.model_validate(profile)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/soil-profiles/{soil_profile_id}",
    response_model=SoilProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a soil profile",
    description=(
        "Apply a partial update to an existing soil profile. "
        "Only the fields present in the request body are modified."
    ),
)
async def update_soil_profile(
    soil_profile_id: uuid.UUID,
    payload: SoilProfileUpdate,
    service: SoilProfileServiceDep,
) -> SoilProfileResponse:
    log = logger.bind(soil_profile_id=str(soil_profile_id))
    try:
        profile = await service.update_soil_profile(soil_profile_id, payload)
    except SoilProfileNotFoundError as exc:
        log.warning("api.soil_profiles.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.soil_profiles.update.success")
    return SoilProfileResponse.model_validate(profile)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/soil-profiles/{soil_profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a soil profile",
    description="Permanently remove a soil profile by its UUID primary key.",
)
async def delete_soil_profile(
    soil_profile_id: uuid.UUID,
    service: SoilProfileServiceDep,
) -> None:
    log = logger.bind(soil_profile_id=str(soil_profile_id))
    try:
        await service.delete_soil_profile(soil_profile_id)
    except SoilProfileNotFoundError as exc:
        log.warning("api.soil_profiles.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.soil_profiles.delete.success")
