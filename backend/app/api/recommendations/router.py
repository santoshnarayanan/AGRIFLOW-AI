"""
Recommendation API router.

Delivers the Phase 13 actionable intelligence layer. Recommendations are the
primary output of the AGRIFLOW-AI decision engine — the first step from a
data platform toward a decision-support platform.

Delivered endpoints:
    POST   /fields/{field_id}/recommendations           — create a recommendation
    GET    /fields/{field_id}/recommendations           — list all for a field
    GET    /recommendations/{recommendation_id}         — get single
    PATCH  /recommendations/{recommendation_id}         — partial update / status change
    DELETE /recommendations/{recommendation_id}         — delete
"""

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import RecommendationServiceDep
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationResponse,
    RecommendationUpdate,
)
from app.services.field import FieldNotFoundError
from app.services.recommendation import (
    CropFieldMismatchError,
    InvalidRecommendationError,
    RecommendationNotFoundError,
)

router = APIRouter(tags=["recommendations"])


@router.post(
    "/fields/{field_id}/recommendations",
    response_model=RecommendationResponse,
    status_code=201,
)
async def create_recommendation(
    field_id: uuid.UUID,
    payload: RecommendationCreate,
    recommendation_service: RecommendationServiceDep,
) -> RecommendationResponse:
    """Create a new recommendation for a field."""
    try:
        rec = await recommendation_service.create_recommendation(field_id, payload)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CropFieldMismatchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InvalidRecommendationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RecommendationResponse.model_validate(rec)


@router.get(
    "/fields/{field_id}/recommendations",
    response_model=list[RecommendationResponse],
)
async def list_field_recommendations(
    field_id: uuid.UUID,
    recommendation_service: RecommendationServiceDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[RecommendationResponse]:
    """List all recommendations for a field, newest first."""
    recs = await recommendation_service.list_field_recommendations(
        field_id, limit=limit, offset=offset
    )
    return [RecommendationResponse.model_validate(r) for r in recs]


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationResponse,
)
async def get_recommendation(
    recommendation_id: uuid.UUID,
    recommendation_service: RecommendationServiceDep,
) -> RecommendationResponse:
    """Return a single recommendation by ID."""
    rec = await recommendation_service.get_recommendation(recommendation_id)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation '{recommendation_id}' not found.",
        )
    return RecommendationResponse.model_validate(rec)


@router.patch(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationResponse,
)
async def update_recommendation(
    recommendation_id: uuid.UUID,
    payload: RecommendationUpdate,
    recommendation_service: RecommendationServiceDep,
) -> RecommendationResponse:
    """Partially update a recommendation — use to change status, priority, or notes."""
    try:
        rec = await recommendation_service.update_recommendation(recommendation_id, payload)
    except RecommendationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidRecommendationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RecommendationResponse.model_validate(rec)


@router.delete("/recommendations/{recommendation_id}", status_code=204)
async def delete_recommendation(
    recommendation_id: uuid.UUID,
    recommendation_service: RecommendationServiceDep,
) -> None:
    """Delete a recommendation permanently."""
    try:
        await recommendation_service.delete_recommendation(recommendation_id)
    except RecommendationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
