"""ML prediction engine stub API (Phase 14)."""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import MLEngineServiceDep
from app.ml.registry import ML_ENGINE_REGISTRY
from app.ml.types import MLEngineId
from app.schemas.ml_engine import (
    MLEngineCatalogItemResponse,
    MLEngineCatalogResponse,
    MLEngineRunResponse,
)
from app.services.field import FieldNotFoundError
from app.services.recommendation import CropFieldMismatchError, InvalidRecommendationError

router = APIRouter(prefix="/ml", tags=["ML Engines"])


@router.get("/engines", response_model=MLEngineCatalogResponse)
async def list_ml_engines() -> MLEngineCatalogResponse:
    """Catalog of registered stub engines and their trigger event types."""
    items = [
        MLEngineCatalogItemResponse(
            engine_id=spec.engine_id.value,
            display_name=spec.display_name,
            description=spec.description,
            engine_version=spec.engine_version,
            recommendation_type=spec.recommendation_type.value,
            trigger_events=[event.value for event in spec.trigger_events],
        )
        for spec in ML_ENGINE_REGISTRY.values()
    ]
    items.sort(key=lambda item: item.engine_id)
    return MLEngineCatalogResponse(engines=items, count=len(items))


@router.post(
    "/fields/{field_id}/engines/{engine_id}/run",
    response_model=MLEngineRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_ml_engine(
    field_id: uuid.UUID,
    engine_id: MLEngineId,
    ml_engine_service: MLEngineServiceDep,
) -> MLEngineRunResponse:
    """Run a stub engine for a field and persist a recommendation."""
    try:
        rec = await ml_engine_service.run_engine(field_id, engine_id)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CropFieldMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except InvalidRecommendationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return MLEngineRunResponse(
        engine_id=engine_id.value,
        engine_version=rec.engine_version or "",
        field_id=rec.field_id,
        recommendation_id=rec.id,
        recommendation_type=rec.recommendation_type.value,
        title=rec.title,
        created_at=rec.created_at,
    )
