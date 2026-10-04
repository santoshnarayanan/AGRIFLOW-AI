"""
Pydantic schemas for the Alert domain.

Separation of concerns
----------------------
- AlertCreate   — inbound payload for POST /fields/{field_id}/alerts
- AlertUpdate   — inbound payload for PATCH /alerts/{id}; all fields optional
- AlertResponse — outbound representation with identity and audit fields
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import AlertSeverity, AlertType


def _require_timezone_aware(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} must be timezone-aware. "
            "Supply an ISO 8601 timestamp with an explicit UTC offset."
        )
    return value


class AlertCreate(BaseModel):
    """Request body for POST /fields/{field_id}/alerts."""

    crop_id: uuid.UUID | None = Field(
        default=None,
        description="Optional crop context for crop-specific alerts",
    )
    recommendation_id: uuid.UUID | None = Field(
        default=None,
        description="Optional: the recommendation that triggered this alert",
    )
    alert_type: AlertType = Field(
        ...,
        description=(
            "Type of condition (SOIL_MOISTURE_LOW | SOIL_MOISTURE_HIGH | DISEASE_RISK_HIGH | "
            "DISEASE_OUTBREAK | FROST_RISK | HEAT_STRESS | DROUGHT_STRESS | "
            "SENSOR_ANOMALY | IRRIGATION_OVERDUE | HARVEST_WINDOW_OPEN)"
        ),
    )
    severity: AlertSeverity = Field(
        ...,
        description="Urgency level (INFO | WARNING | HIGH | CRITICAL)",
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Short human-readable alert title",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Detailed alert message describing the condition",
    )
    triggered_at: datetime = Field(
        ...,
        description="Timezone-aware timestamp when the alert condition was detected",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional expiry timestamp; None means active until acknowledged",
    )
    source_metric: str | None = Field(
        default=None,
        max_length=100,
        description="Name of the metric that triggered the alert (e.g. 'soil_moisture_pct')",
    )
    source_value: Decimal | None = Field(
        default=None,
        description="Actual metric value at triggering",
    )
    threshold_value: Decimal | None = Field(
        default=None,
        description="Threshold value that was crossed",
    )

    @field_validator("triggered_at")
    @classmethod
    def validate_triggered_at_tz(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="triggered_at")

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at_tz(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="expires_at")

    @model_validator(mode="after")
    def validate_expiry_after_trigger(self) -> Self:
        if self.expires_at is not None and self.expires_at <= self.triggered_at:
            raise ValueError("expires_at must be after triggered_at.")
        return self


class AlertUpdate(BaseModel):
    """Request body for PATCH /alerts/{id}. All fields optional."""

    severity: AlertSeverity | None = Field(default=None, description="Updated severity level")
    title: str | None = Field(default=None, min_length=1, max_length=255, description="Updated title")
    message: str | None = Field(default=None, min_length=1, description="Updated message")
    is_acknowledged: bool | None = Field(default=None, description="Set to true to acknowledge")
    acknowledged_at: datetime | None = Field(
        default=None,
        description="Acknowledgement timestamp (timezone-aware); auto-set by service when is_acknowledged=true",
    )
    expires_at: datetime | None = Field(default=None, description="Updated expiry (timezone-aware)")

    @field_validator("acknowledged_at", "expires_at")
    @classmethod
    def validate_tz(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="datetime field")


class AlertResponse(BaseModel):
    """Outbound representation of an Alert returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key")
    field_id: uuid.UUID = Field(description="Parent field UUID")
    crop_id: uuid.UUID | None = Field(description="Optional crop UUID")
    recommendation_id: uuid.UUID | None = Field(description="Optional source recommendation UUID")
    alert_type: AlertType = Field(description="Type of condition that triggered this alert")
    severity: AlertSeverity = Field(description="Urgency level")
    title: str = Field(description="Short alert title")
    message: str = Field(description="Detailed alert message")
    triggered_at: datetime = Field(description="When the alert condition was detected")
    expires_at: datetime | None = Field(description="Optional expiry timestamp")
    is_acknowledged: bool = Field(description="Whether the alert has been acknowledged")
    acknowledged_at: datetime | None = Field(description="Acknowledgement timestamp")
    source_metric: str | None = Field(description="Metric that triggered the alert")
    source_value: Decimal | None = Field(description="Actual metric value at triggering")
    threshold_value: Decimal | None = Field(description="Threshold that was crossed")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
