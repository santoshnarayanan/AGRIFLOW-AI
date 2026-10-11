"""Pydantic schemas for CQRS dashboard read models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FieldDashboardReadModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field_id: uuid.UUID
    farm_id: uuid.UUID
    field_name: str
    open_alerts_count: int
    critical_alerts_count: int
    active_recommendations_count: int
    feature_snapshot_id: uuid.UUID | None
    feature_snapshot_as_of: datetime | None
    kpi_payload: dict[str, Any]
    projection_version: str
    refreshed_at: datetime


class FieldDashboardReadModelListResponse(BaseModel):
    items: list[FieldDashboardReadModelResponse]
    count: int


class FieldPressureSummary(BaseModel):
    field_id: str
    farm_id: str
    field_name: str
    open_alerts_count: int
    critical_alerts_count: int
    active_recommendations_count: int


class PlatformDashboardReadModelResponse(BaseModel):
    is_materialized: bool
    projection_version: str
    refreshed_at: datetime | None
    total_farms: int
    total_fields: int
    materialized_fields: int
    open_alerts: int
    critical_alerts: int
    active_recommendations: int
    fields_with_feature_snapshots: int
    alert_severity_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="Open (unacknowledged) alerts by severity",
    )
    top_fields_by_pressure: list[FieldPressureSummary] = Field(default_factory=list)


class ReadModelRefreshResponse(BaseModel):
    refreshed_fields: int
    projection_version: str
