"""AI Feature Store API (Phase 15)."""

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import FeatureStoreServiceDep
from app.core.security.platform_auth import PlatformOperatorDep
from app.features.catalog import FEATURE_CATALOG, registry_version
from app.schemas.feature_store import (
    FeatureCatalogItemResponse,
    FeatureCatalogResponse,
    FeatureMaterializeRequest,
    FieldFeatureSnapshotListResponse,
    FieldFeatureSnapshotResponse,
)
from app.services.feature_store import FeatureSnapshotNotFoundError
from app.services.field import FieldNotFoundError

router = APIRouter(prefix="/features", tags=["Feature Store"])


@router.get("/catalog", response_model=FeatureCatalogResponse)
async def list_feature_catalog() -> FeatureCatalogResponse:
    """Registered CDD features and their continuous aggregate sources."""
    items = [
        FeatureCatalogItemResponse(
            feature_id=entry.feature_id.value,
            display_name=entry.display_name,
            description=entry.description,
            unit=entry.unit,
            window_days=entry.window_days,
            primary_source=entry.primary_source,
            secondary_source=entry.secondary_source,
        )
        for entry in FEATURE_CATALOG.values()
    ]
    items.sort(key=lambda item: item.feature_id)
    return FeatureCatalogResponse(
        registry_version=registry_version(),
        features=items,
        count=len(items),
    )


@router.post(
    "/fields/{field_id}/materialize",
    response_model=FieldFeatureSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def materialize_field_features(
    field_id: uuid.UUID,
    body: FeatureMaterializeRequest,
    feature_store: FeatureStoreServiceDep,
    _: PlatformOperatorDep,
) -> FieldFeatureSnapshotResponse:
    """Compute features from continuous aggregates and persist a snapshot."""
    try:
        snapshot = await feature_store.materialize_field_snapshot(
            field_id,
            crop_id=body.crop_id,
            as_of=body.as_of,
        )
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FieldFeatureSnapshotResponse.model_validate(snapshot)


@router.get(
    "/fields/{field_id}/snapshots/latest",
    response_model=FieldFeatureSnapshotResponse,
)
async def get_latest_field_snapshot(
    field_id: uuid.UUID,
    feature_store: FeatureStoreServiceDep,
) -> FieldFeatureSnapshotResponse:
    try:
        snapshot = await feature_store.get_latest_snapshot(field_id)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No feature snapshot materialised for this field yet.",
        )
    return FieldFeatureSnapshotResponse.model_validate(snapshot)


@router.get(
    "/fields/{field_id}/snapshots",
    response_model=FieldFeatureSnapshotListResponse,
)
async def list_field_snapshots(
    field_id: uuid.UUID,
    feature_store: FeatureStoreServiceDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> FieldFeatureSnapshotListResponse:
    try:
        snapshots = await feature_store.list_snapshots(field_id, limit=limit, offset=offset)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    items = [FieldFeatureSnapshotResponse.model_validate(s) for s in snapshots]
    return FieldFeatureSnapshotListResponse(snapshots=items, count=len(items))


@router.get(
    "/fields/{field_id}/snapshots/{snapshot_id}",
    response_model=FieldFeatureSnapshotResponse,
)
async def get_field_snapshot(
    field_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    feature_store: FeatureStoreServiceDep,
) -> FieldFeatureSnapshotResponse:
    try:
        snapshot = await feature_store.get_snapshot(field_id, snapshot_id)
    except FieldNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FeatureSnapshotNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FieldFeatureSnapshotResponse.model_validate(snapshot)
