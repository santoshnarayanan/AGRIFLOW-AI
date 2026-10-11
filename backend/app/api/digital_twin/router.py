"""Digital Twin field state API (Phase 15 slice 3)."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DigitalTwinServiceDep
from app.core.security.platform_auth import PlatformOperatorDep
from app.digital_twin.catalog import TWIN_STATE_SECTIONS, state_schema_version
from app.schemas.digital_twin import (
    DigitalTwinCatalogResponse,
    DigitalTwinPlatformSynchronizeResponse,
    DigitalTwinSynchronizeResponse,
    FieldDigitalTwinStateResponse,
    TwinStateSectionResponse,
)
from app.services.digital_twin import DigitalTwinStateNotFoundError
from app.services.field import FieldNotFoundError

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


@router.get("/catalog", response_model=DigitalTwinCatalogResponse)
async def get_digital_twin_catalog() -> DigitalTwinCatalogResponse:
    sections = [
        TwinStateSectionResponse(
            section=entry.section,
            description=entry.description,
            source=entry.source,
        )
        for entry in TWIN_STATE_SECTIONS
    ]
    return DigitalTwinCatalogResponse(
        state_version=state_schema_version(),
        sections=sections,
        count=len(sections),
    )


@router.get("/fields/{field_id}/state", response_model=FieldDigitalTwinStateResponse)
async def get_field_digital_twin_state(
    field_id: uuid.UUID,
    digital_twin_service: DigitalTwinServiceDep,
) -> FieldDigitalTwinStateResponse:
    try:
        state = await digital_twin_service.get_field_state(field_id)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DigitalTwinStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FieldDigitalTwinStateResponse.model_validate(state)


@router.post(
    "/fields/{field_id}/synchronize",
    response_model=DigitalTwinSynchronizeResponse,
    status_code=status.HTTP_200_OK,
)
async def synchronize_field_digital_twin(
    field_id: uuid.UUID,
    digital_twin_service: DigitalTwinServiceDep,
    _: PlatformOperatorDep,
) -> DigitalTwinSynchronizeResponse:
    try:
        state = await digital_twin_service.synchronize_field(field_id)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DigitalTwinSynchronizeResponse(
        field_id=state.field_id,
        state_version=state.state_version,
        synchronized_at=state.synchronized_at,
        state_id=state.id,
    )


@router.post(
    "/synchronize",
    response_model=DigitalTwinPlatformSynchronizeResponse,
    status_code=status.HTTP_200_OK,
)
async def synchronize_platform_digital_twin(
    digital_twin_service: DigitalTwinServiceDep,
    _: PlatformOperatorDep,
) -> DigitalTwinPlatformSynchronizeResponse:
    count = await digital_twin_service.synchronize_platform()
    from app.core.config import get_settings

    return DigitalTwinPlatformSynchronizeResponse(
        synchronized_fields=count,
        state_version=get_settings().DIGITAL_TWIN_STATE_VERSION,
    )
