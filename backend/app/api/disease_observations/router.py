"""
Disease Observation endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /crops/{crop_id}/disease-observations              — log a disease observation for a crop cycle
    GET    /crops/{crop_id}/disease-observations              — list disease observations for a crop cycle
    GET    /fields/{field_id}/disease-observations            — list disease observations for a field
    GET    /disease-observations/{observation_id}             — fetch a single disease observation
    PATCH  /disease-observations/{observation_id}             — partial update of a disease observation
    DELETE /disease-observations/{observation_id}             — remove a disease observation

Domain exception → HTTP status mapping
---------------------------------------
    CropNotFoundError                 → 404 Not Found
    DiseaseObservationNotFoundError   → 404 Not Found
    InvalidDiseaseObservationError    → 400 Bad Request
"""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DiseaseObservationServiceDep
from app.core.logging import get_logger
from app.schemas.disease_observation import (
    CreateDiseaseObservationRequest,
    DiseaseObservationListResponse,
    DiseaseObservationResponse,
    UpdateDiseaseObservationRequest,
)
from app.services.crop import CropNotFoundError
from app.services.disease_observation import (
    DiseaseObservationNotFoundError,
    InvalidDiseaseObservationError,
)

router = APIRouter(tags=["Disease Observations"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/crops/{crop_id}/disease-observations",
    response_model=DiseaseObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a disease observation",
    description=(
        "Log a new disease observation for an existing crop cycle. "
        "``observed_at`` must be timezone-aware and cannot be in the future. "
        "``field_id`` is resolved server-side from the crop record and must not "
        "be supplied in the request body. "
        "``severity`` accepts LOW, MEDIUM, HIGH, or CRITICAL. "
        "``diagnosis_method`` accepts VISUAL_INSPECTION, LAB_ANALYSIS, IMAGE_AI, "
        "AGRONOMIST, or SENSOR_DETECTED."
    ),
)
async def create_observation(
    crop_id: uuid.UUID,
    payload: CreateDiseaseObservationRequest,
    service: DiseaseObservationServiceDep,
) -> DiseaseObservationResponse:
    log = logger.bind(
        crop_id=str(crop_id),
        diagnosis_method=payload.diagnosis_method.value,
        severity=payload.severity.value,
    )
    try:
        observation = await service.create_observation(crop_id, payload)
    except CropNotFoundError as exc:
        log.warning("api.disease_observations.create.crop_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidDiseaseObservationError as exc:
        log.warning("api.disease_observations.create.invalid_observation")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info(
        "api.disease_observations.create.success",
        observation_id=str(observation.id),
    )
    return DiseaseObservationResponse.model_validate(observation)


# ── List by crop ───────────────────────────────────────────────────────────────


@router.get(
    "/crops/{crop_id}/disease-observations",
    response_model=DiseaseObservationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List disease observations for a crop cycle",
    description=(
        "Return all disease observations belonging to a crop cycle, ordered by "
        "observed_at descending (most recent observation first). "
        "Supports pagination via ``limit`` and ``offset``."
    ),
)
async def list_crop_observations(
    crop_id: uuid.UUID,
    service: DiseaseObservationServiceDep,
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
) -> DiseaseObservationListResponse:
    observations = await service.list_by_crop(
        crop_id,
        limit=limit,
        offset=offset,
    )
    return DiseaseObservationListResponse(
        items=[DiseaseObservationResponse.model_validate(o) for o in observations],
        total=len(observations),
        limit=limit,
        offset=offset,
    )


# ── List by field ──────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/disease-observations",
    response_model=DiseaseObservationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List disease observations for a field",
    description=(
        "Return all disease observations for a field across all crop cycles, "
        "ordered by observed_at descending (most recent observation first). "
        "Supports pagination via ``limit`` and ``offset``."
    ),
)
async def list_field_observations(
    field_id: uuid.UUID,
    service: DiseaseObservationServiceDep,
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
) -> DiseaseObservationListResponse:
    observations = await service.list_by_field(
        field_id,
        limit=limit,
        offset=offset,
    )
    return DiseaseObservationListResponse(
        items=[DiseaseObservationResponse.model_validate(o) for o in observations],
        total=len(observations),
        limit=limit,
        offset=offset,
    )


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/disease-observations/{observation_id}",
    response_model=DiseaseObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a disease observation",
    description="Fetch a single disease observation by its UUID primary key.",
)
async def get_observation(
    observation_id: uuid.UUID,
    service: DiseaseObservationServiceDep,
) -> DiseaseObservationResponse:
    try:
        observation = await service.get_observation(observation_id)
    except DiseaseObservationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return DiseaseObservationResponse.model_validate(observation)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/disease-observations/{observation_id}",
    response_model=DiseaseObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a disease observation",
    description=(
        "Apply a partial update to an existing disease observation. "
        "Only the fields present in the request body are modified. "
        "``crop_id`` and ``field_id`` are immutable and cannot be changed. "
        "``observed_at``, when supplied, must not be in the future."
    ),
)
async def update_observation(
    observation_id: uuid.UUID,
    payload: UpdateDiseaseObservationRequest,
    service: DiseaseObservationServiceDep,
) -> DiseaseObservationResponse:
    log = logger.bind(observation_id=str(observation_id))
    try:
        observation = await service.update_observation(observation_id, payload)
    except DiseaseObservationNotFoundError as exc:
        log.warning("api.disease_observations.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidDiseaseObservationError as exc:
        log.warning("api.disease_observations.update.invalid_observation")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.disease_observations.update.success")
    return DiseaseObservationResponse.model_validate(observation)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/disease-observations/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a disease observation",
    description="Permanently remove a disease observation by its UUID primary key.",
)
async def delete_observation(
    observation_id: uuid.UUID,
    service: DiseaseObservationServiceDep,
) -> None:
    log = logger.bind(observation_id=str(observation_id))
    try:
        await service.delete_observation(observation_id)
    except DiseaseObservationNotFoundError as exc:
        log.warning("api.disease_observations.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    log.info("api.disease_observations.delete.success")
