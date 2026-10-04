"""
Pydantic schemas for the Recommendation domain.

Separation of concerns
----------------------
- RecommendationCreate   — inbound payload for POST /fields/{field_id}/recommendations
- RecommendationUpdate   — inbound payload for PATCH /recommendations/{id}; all fields optional
- RecommendationResponse — outbound representation with identity and audit fields
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import RecommendationPriority, RecommendationStatus, RecommendationType


def _require_timezone_aware(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} must be timezone-aware. "
            "Supply an ISO 8601 timestamp with an explicit UTC offset."
        )
    return value


class RecommendationCreate(BaseModel):
    """Request body for POST /fields/{field_id}/recommendations."""

    crop_id: uuid.UUID | None = Field(
        default=None,
        description="Optional crop context; required for HARVEST_TIMING and DISEASE_TREATMENT types",
    )
    recommendation_type: RecommendationType = Field(
        ...,
        description="Category of the recommendation (IRRIGATION | DISEASE_TREATMENT | FERTILIZATION | HARVEST_TIMING | SOIL_AMENDMENT | GENERAL)",
    )
    priority: RecommendationPriority = Field(
        default=RecommendationPriority.MEDIUM,
        description="Urgency level (LOW | MEDIUM | HIGH | CRITICAL)",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Short human-readable title",
    )
    description: str | None = Field(
        default=None,
        description="Detailed context and rationale",
    )
    recommended_action: str = Field(
        ...,
        min_length=1,
        description="Specific action the operator should take",
    )
    recommended_value: Decimal | None = Field(
        default=None,
        gt=0,
        description="Numeric magnitude of the recommended action (e.g. water volume)",
    )
    recommended_unit: str | None = Field(
        default=None,
        max_length=50,
        description="Unit for recommended_value (e.g. 'liters', 'kg/ha')",
    )
    confidence_score: Decimal | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Engine confidence in [0.000, 1.000]",
    )
    evidence_summary: str | None = Field(
        default=None,
        description="Summary of data signals that drove this recommendation",
    )
    engine_version: str | None = Field(
        default=None,
        max_length=50,
        description="Version of the recommendation engine (e.g. 'deterministic-v1.0')",
    )
    valid_from: datetime = Field(
        ...,
        description="Start of the validity window (timezone-aware ISO 8601)",
    )
    valid_until: datetime | None = Field(
        default=None,
        description="End of the validity window; None means open-ended",
    )
    notes: str | None = Field(default=None, description="Operator notes")

    @field_validator("valid_from")
    @classmethod
    def validate_valid_from_tz(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="valid_from")

    @field_validator("valid_until")
    @classmethod
    def validate_valid_until_tz(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="valid_until")

    @model_validator(mode="after")
    def validate_validity_window(self) -> Self:
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from.")
        return self


class RecommendationUpdate(BaseModel):
    """Request body for PATCH /recommendations/{id}. All fields optional."""

    status: RecommendationStatus | None = Field(default=None, description="New lifecycle status")
    priority: RecommendationPriority | None = Field(default=None, description="Updated urgency level")
    title: str | None = Field(default=None, min_length=1, max_length=255, description="Updated title")
    description: str | None = Field(default=None, description="Updated rationale")
    recommended_action: str | None = Field(default=None, min_length=1, description="Updated action")
    recommended_value: Decimal | None = Field(default=None, gt=0, description="Updated numeric value")
    recommended_unit: str | None = Field(default=None, max_length=50, description="Updated unit")
    confidence_score: Decimal | None = Field(default=None, ge=0, le=1, description="Updated confidence")
    evidence_summary: str | None = Field(default=None, description="Updated evidence summary")
    valid_until: datetime | None = Field(default=None, description="Updated expiry (timezone-aware)")
    acknowledged_at: datetime | None = Field(default=None, description="Acknowledgement timestamp")
    notes: str | None = Field(default=None, description="Operator notes")

    @field_validator("valid_until", "acknowledged_at")
    @classmethod
    def validate_tz(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="datetime field")


class RecommendationResponse(BaseModel):
    """Outbound representation of a Recommendation returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key")
    field_id: uuid.UUID = Field(description="Parent field UUID")
    crop_id: uuid.UUID | None = Field(description="Optional crop UUID")
    recommendation_type: RecommendationType = Field(description="Category of the recommendation")
    status: RecommendationStatus = Field(description="Current lifecycle state")
    priority: RecommendationPriority = Field(description="Urgency level")
    title: str = Field(description="Short title")
    description: str | None = Field(description="Detailed rationale")
    recommended_action: str = Field(description="Specific action to take")
    recommended_value: Decimal | None = Field(description="Numeric magnitude")
    recommended_unit: str | None = Field(description="Unit of recommended_value")
    confidence_score: Decimal | None = Field(description="Engine confidence [0, 1]")
    evidence_summary: str | None = Field(description="Data signals summary")
    engine_version: str | None = Field(description="Engine version identifier")
    valid_from: datetime = Field(description="Start of validity window")
    valid_until: datetime | None = Field(description="End of validity window")
    acknowledged_at: datetime | None = Field(description="Acknowledgement timestamp")
    notes: str | None = Field(description="Operator notes")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
