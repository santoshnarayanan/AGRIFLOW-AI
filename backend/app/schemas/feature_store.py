"""Pydantic schemas for the AI Feature Store API (Phase 15)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.features.types import FEATURE_REGISTRY_VERSION


class FeatureCatalogItemResponse(BaseModel):
    feature_id: str
    display_name: str
    description: str
    unit: str
    window_days: int
    primary_source: str
    secondary_source: str | None = None


class FeatureCatalogResponse(BaseModel):
    registry_version: str = FEATURE_REGISTRY_VERSION
    features: list[FeatureCatalogItemResponse]
    count: int


class FeatureValuePayload(BaseModel):
    value: float | str | None = None
    unit: str
    source: str
    window_days: int
    available: bool


class FeatureMaterializeRequest(BaseModel):
    crop_id: uuid.UUID | None = Field(
        default=None,
        description="Optional crop scope for yield/disease features",
    )
    as_of: datetime | None = Field(
        default=None,
        description="Reference time for rolling windows (defaults to UTC now)",
    )


class FieldFeatureSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field_id: uuid.UUID
    crop_id: uuid.UUID | None
    registry_version: str
    as_of: datetime
    features: dict[str, Any]
    materialization_notes: str | None
    created_at: datetime
    updated_at: datetime


class FieldFeatureSnapshotListResponse(BaseModel):
    snapshots: list[FieldFeatureSnapshotResponse]
    count: int
