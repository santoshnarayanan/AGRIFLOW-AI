"""
Satellite Observation endpoints.

Route map (all paths are relative to the /api/v1 prefix in main.py):

    POST   /fields/{field_id}/satellite-observations
           — create a satellite observation under a field
    GET    /fields/{field_id}/satellite-observations
           — list satellite observations for a field
    GET    /fields/{field_id}/satellite-observations/range
           — list field observations within an observed_at date range
    GET    /fields/{field_id}/satellite-observations/latest
           — fetch the latest observation for a field and spectral index
    GET    /satellite-observations/by-provider/{satellite_provider}
           — list observations filtered by satellite provider
    GET    /satellite-observations/by-processing-level/{processing_level}
           — list observations filtered by processing level
    GET    /satellite-observations/{observation_id}
           — fetch a single satellite observation
    PATCH  /satellite-observations/{observation_id}
           — partial update of a satellite observation
    DELETE /satellite-observations/{observation_id}
           — remove a satellite observation

Domain exception → HTTP status mapping
---------------------------------------
    FieldNotFoundError                  → 404 Not Found
    SatelliteObservationNotFoundError   → 404 Not Found
    InvalidSatelliteObservationError      → 400 Bad Request
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import SatelliteObservationServiceDep
from app.core.enums import ProcessingLevel, SatelliteProvider, SpectralIndex
from app.core.logging import get_logger
from app.schemas.satellite_observation import (
    SatelliteObservationCreate,
    SatelliteObservationListResponse,
    SatelliteObservationResponse,
    SatelliteObservationUpdate,
)
from app.services.field import FieldNotFoundError
from app.services.satellite_observation import (
    InvalidSatelliteObservationError,
    SatelliteObservationNotFoundError,
)

router = APIRouter(tags=["Satellite Observations"])
logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/fields/{field_id}/satellite-observations",
    response_model=SatelliteObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a satellite observation",
    description=(
        "Create a new satellite observation under an existing field. "
        "``observed_at`` must be timezone-aware and cannot be in the future. "
        "``index_value`` is validated against the contextual range for the "
        "selected ``spectral_index`` (ratio indices in [-1.0, 1.0]; LAI > 0). "
        "``resolution_m``, when supplied, must be greater than zero. "
        "``cloud_cover_percent``, when supplied, must be in [0, 100]."
    ),
)
async def create_satellite_observation(
    field_id: uuid.UUID,
    payload: SatelliteObservationCreate,
    service: SatelliteObservationServiceDep,
) -> SatelliteObservationResponse:
    log = logger.bind(
        field_id=str(field_id),
        spectral_index=payload.spectral_index.value,
        satellite_provider=payload.satellite_provider.value,
    )
    try:
        observation = await service.create_satellite_observation(field_id, payload)
    except FieldNotFoundError as exc:
        log.warning("api.satellite_observations.create.field_not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidSatelliteObservationError as exc:
        log.warning("api.satellite_observations.create.invalid_observation")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info(
        "api.satellite_observations.create.success",
        observation_id=str(observation.id),
    )
    return SatelliteObservationResponse.model_validate(observation)


# ── List by field ──────────────────────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/satellite-observations",
    response_model=SatelliteObservationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List satellite observations for a field",
    description=(
        "Return all satellite observations belonging to a field, ordered by "
        "observed_at descending (most recent observation first). "
        "Supports pagination via ``limit`` and ``offset``."
    ),
)
async def list_field_satellite_observations(
    field_id: uuid.UUID,
    service: SatelliteObservationServiceDep,
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
) -> SatelliteObservationListResponse:
    observations = await service.list_field_satellite_observations(
        field_id,
        limit=limit,
        offset=offset,
    )
    return SatelliteObservationListResponse(
        items=[SatelliteObservationResponse.model_validate(o) for o in observations],
        total=len(observations),
        limit=limit,
        offset=offset,
    )


# ── List by field and date range ───────────────────────────────────────────────


@router.get(
    "/fields/{field_id}/satellite-observations/range",
    response_model=SatelliteObservationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List field satellite observations by date range",
    description=(
        "Return satellite observations for a field within an inclusive "
        "``observed_at`` window. "
        "Both ``start`` and ``end`` must be timezone-aware ISO 8601 timestamps. "
        "Supports pagination via ``limit`` and ``offset``. "
        "Primary access pattern for AI feature extraction and historical analytics."
    ),
)
async def list_field_satellite_observations_by_date_range(
    field_id: uuid.UUID,
    service: SatelliteObservationServiceDep,
    start: datetime = Query(
        ...,
        description=(
            "Inclusive range start (ISO 8601 with timezone offset, "
            "e.g. 2024-04-01T00:00:00Z)"
        ),
    ),
    end: datetime = Query(
        ...,
        description=(
            "Inclusive range end (ISO 8601 with timezone offset, "
            "e.g. 2024-09-30T23:59:59Z)"
        ),
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
) -> SatelliteObservationListResponse:
    log = logger.bind(field_id=str(field_id))
    try:
        observations = await service.list_field_satellite_observations_by_date_range(
            field_id,
            start,
            end,
            limit=limit,
            offset=offset,
        )
    except InvalidSatelliteObservationError as exc:
        log.warning("api.satellite_observations.range.invalid_range")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return SatelliteObservationListResponse(
        items=[SatelliteObservationResponse.model_validate(o) for o in observations],
        total=len(observations),
        limit=limit,
        offset=offset,
    )


# ── Latest by field and spectral index ────────────────────────────────────────


@router.get(
    "/fields/{field_id}/satellite-observations/latest",
    response_model=SatelliteObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest satellite observation for a spectral index",
    description=(
        "Return the most recent satellite observation for a field and spectral "
        "index pair. "
        "Supports Digital Twin current-state updates and real-time analytics "
        "dashboards (e.g. latest NDVI canopy health or NDWI water-stress signal)."
    ),
)
async def get_latest_field_spectral_index_observation(
    field_id: uuid.UUID,
    service: SatelliteObservationServiceDep,
    spectral_index: SpectralIndex = Query(
        ...,
        description=(
            "Spectral index type to retrieve "
            "(NDVI | EVI | NDWI | SAVI | NDRE | LAI | MSAVI | GNDVI)"
        ),
    ),
) -> SatelliteObservationResponse:
    observation = await service.get_latest_field_spectral_index_observation(
        field_id,
        spectral_index,
    )
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No satellite observation found for field '{field_id}' "
                f"with spectral index '{spectral_index.value}'."
            ),
        )
    return SatelliteObservationResponse.model_validate(observation)


# ── List by provider ─────────────────────────────────────────────────────────


@router.get(
    "/satellite-observations/by-provider/{satellite_provider}",
    response_model=SatelliteObservationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List satellite observations by provider",
    description=(
        "Return all satellite observations sourced from a given satellite "
        "provider, ordered by observed_at descending. "
        "Supports provider-scoped analytics and resolution-aware training data "
        "curation."
    ),
)
async def list_satellite_observations_by_provider(
    satellite_provider: SatelliteProvider,
    service: SatelliteObservationServiceDep,
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
) -> SatelliteObservationListResponse:
    observations = await service.list_satellite_observations_by_provider(
        satellite_provider,
        limit=limit,
        offset=offset,
    )
    return SatelliteObservationListResponse(
        items=[SatelliteObservationResponse.model_validate(o) for o in observations],
        total=len(observations),
        limit=limit,
        offset=offset,
    )


# ── List by processing level ─────────────────────────────────────────────────


@router.get(
    "/satellite-observations/by-processing-level/{processing_level}",
    response_model=SatelliteObservationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List satellite observations by processing level",
    description=(
        "Return all satellite observations at a given processing level, ordered "
        "by observed_at descending. "
        "Supports AI quality-gate queries — for example, retrieving ARD or L2A "
        "observations suitable for multi-temporal model training."
    ),
)
async def list_satellite_observations_by_processing_level(
    processing_level: ProcessingLevel,
    service: SatelliteObservationServiceDep,
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
) -> SatelliteObservationListResponse:
    observations = await service.list_satellite_observations_by_processing_level(
        processing_level,
        limit=limit,
        offset=offset,
    )
    return SatelliteObservationListResponse(
        items=[SatelliteObservationResponse.model_validate(o) for o in observations],
        total=len(observations),
        limit=limit,
        offset=offset,
    )


# ── Get single ─────────────────────────────────────────────────────────────────


@router.get(
    "/satellite-observations/{observation_id}",
    response_model=SatelliteObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a satellite observation",
    description="Fetch a single satellite observation by its UUID primary key.",
)
async def get_satellite_observation(
    observation_id: uuid.UUID,
    service: SatelliteObservationServiceDep,
) -> SatelliteObservationResponse:
    observation = await service.get_satellite_observation(observation_id)
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Satellite observation '{observation_id}' does not exist.",
        )
    return SatelliteObservationResponse.model_validate(observation)


# ── Update ─────────────────────────────────────────────────────────────────────


@router.patch(
    "/satellite-observations/{observation_id}",
    response_model=SatelliteObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a satellite observation",
    description=(
        "Apply a partial update to an existing satellite observation. "
        "Only the fields present in the request body are modified. "
        "``field_id`` is immutable and cannot be changed. "
        "``observed_at``, when supplied, must not be in the future. "
        "``index_value`` is validated against the effective ``spectral_index`` "
        "after the update is applied."
    ),
)
async def update_satellite_observation(
    observation_id: uuid.UUID,
    payload: SatelliteObservationUpdate,
    service: SatelliteObservationServiceDep,
) -> SatelliteObservationResponse:
    log = logger.bind(observation_id=str(observation_id))
    try:
        observation = await service.update_satellite_observation(
            observation_id,
            payload,
        )
    except SatelliteObservationNotFoundError as exc:
        log.warning("api.satellite_observations.update.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidSatelliteObservationError as exc:
        log.warning("api.satellite_observations.update.invalid_observation")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    log.info("api.satellite_observations.update.success")
    return SatelliteObservationResponse.model_validate(observation)


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/satellite-observations/{observation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a satellite observation",
    description="Permanently remove a satellite observation by its UUID primary key.",
)
async def delete_satellite_observation(
    observation_id: uuid.UUID,
    service: SatelliteObservationServiceDep,
) -> None:
    log = logger.bind(observation_id=str(observation_id))
    deleted = await service.delete_satellite_observation(observation_id)
    if not deleted:
        log.warning("api.satellite_observations.delete.not_found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Satellite observation '{observation_id}' does not exist.",
        )
    log.info("api.satellite_observations.delete.success")
