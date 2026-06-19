"""
Pydantic schemas for the IrrigationEvent domain object.

Separation of concerns
----------------------
- IrrigationEventBase     — shared field inventory; parent of IrrigationEventResponse.
                            Defines all irrigation measurement and classification fields
                            with their validation rules so constraints are expressed
                            exactly once.
- IrrigationEventCreate     — inbound payload for POST
                              /fields/{field_id}/irrigation-events.
                              ``field_id`` is intentionally excluded; it is resolved
                              from the URL path by the router, matching the pattern
                              used by CropCreate, SoilProfileCreate, and
                              WeatherRecordCreate.  ``started_at`` and
                              ``irrigation_method`` are required; quantification
                              fields are optional because non-metered systems may
                              record an event without volume or duration.
- IrrigationEventUpdate     — inbound payload for PATCH
                              /fields/{field_id}/irrigation-events/{event_id}.
                              Every field is optional to support sparse partial
                              updates.  All validation constraints from
                              IrrigationEventCreate are retained so a partial
                              payload is never weaker than a full one.
- IrrigationEventResponse   — outbound representation returned to API consumers.
                              Extends IrrigationEventBase with server-assigned identity
                              and audit fields.  ``from_attributes=True`` enables direct
                              construction from a SQLAlchemy ORM instance.

Mutability contract
-------------------
IrrigationEvent is a human-logged management action.  PATCH is permitted so
operators can correct water volume, duration, method, or notes after the fact.
This differs from SensorReading (append-only immutable telemetry).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import IrrigationMethod, WaterSource


def _require_timezone_aware(value: datetime, *, field_name: str) -> datetime:
    """
    Reject naive datetimes — irrigation timestamps must carry an explicit offset.

    Mirrors ADR-007-25 / ADR-008-04: timezone-awareness is validated before any
    cross-field timestamp comparison.
    """
    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} ({value.isoformat()}) must be timezone-aware. "
            "Supply an ISO 8601 timestamp with an explicit UTC offset, "
            "e.g. 2026-06-18T20:00:00Z or 2026-06-18T22:00:00+02:00."
        )
    return value


class IrrigationEventBase(BaseModel):
    """
    Shared field inventory for the IrrigationEvent domain.

    Inherited by IrrigationEventResponse.  IrrigationEventCreate and
    IrrigationEventUpdate mirror these fields but are defined separately to
    follow the project convention — this also prevents accidental schema
    coupling when Create/Update diverge from the Base in future iterations.
    """

    started_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when irrigation began "
            "(ISO 8601 with timezone offset, e.g. 2026-06-18T06:00:00+02:00)"
        ),
    )
    ended_at: datetime | None = Field(
        default=None,
        description=(
            "Timezone-aware timestamp when irrigation ended; "
            "optional — may be omitted when only duration is known"
        ),
    )
    duration_minutes: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Duration of the irrigation event in minutes; must be non-negative",
    )
    water_volume_liters: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Total water volume applied in litres; must be non-negative",
    )
    irrigation_method: IrrigationMethod = Field(
        ...,
        description=(
            "Delivery method used to apply water "
            "(DRIP | SPRINKLER | FLOOD | FURROW | CENTER_PIVOT | "
            "SUBSURFACE | MANUAL | AUTOMATED)"
        ),
    )
    water_source: WaterSource | None = Field(
        default=None,
        description=(
            "Origin of the water applied "
            "(GROUNDWATER | SURFACE_WATER | RAINWATER | MUNICIPAL | RECYCLED_WATER)"
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations, e.g. equipment issues or field observations",
    )

    @field_validator("started_at")
    @classmethod
    def validate_started_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="started_at")

    @field_validator("ended_at")
    @classmethod
    def validate_ended_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="ended_at")

    @model_validator(mode="after")
    def validate_ended_at_after_started_at(self) -> Self:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError(
                f"ended_at ({self.ended_at.isoformat()}) must be greater than or "
                f"equal to started_at ({self.started_at.isoformat()})."
            )
        return self


class IrrigationEventCreate(BaseModel):
    """
    Request body for POST /fields/{field_id}/irrigation-events.

    ``field_id`` is excluded — it is injected from the URL path by the router.
    ``started_at`` and ``irrigation_method`` are required because they identify
    when and how the intervention occurred.  Quantification fields are optional
    because non-metered systems may record an event without volume or duration.
    """

    started_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when irrigation began "
            "(ISO 8601 with timezone offset, e.g. 2026-06-18T06:00:00+02:00)"
        ),
    )
    ended_at: datetime | None = Field(
        default=None,
        description=(
            "Timezone-aware timestamp when irrigation ended; "
            "optional — may be omitted when only duration is known"
        ),
    )
    duration_minutes: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Duration of the irrigation event in minutes; must be non-negative",
    )
    water_volume_liters: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Total water volume applied in litres; must be non-negative",
    )
    irrigation_method: IrrigationMethod = Field(
        ...,
        description=(
            "Delivery method used to apply water "
            "(DRIP | SPRINKLER | FLOOD | FURROW | CENTER_PIVOT | "
            "SUBSURFACE | MANUAL | AUTOMATED)"
        ),
    )
    water_source: WaterSource | None = Field(
        default=None,
        description=(
            "Origin of the water applied "
            "(GROUNDWATER | SURFACE_WATER | RAINWATER | MUNICIPAL | RECYCLED_WATER)"
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations, e.g. equipment issues or field observations",
    )

    @field_validator("started_at")
    @classmethod
    def validate_started_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="started_at")

    @field_validator("ended_at")
    @classmethod
    def validate_ended_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="ended_at")

    @model_validator(mode="after")
    def validate_ended_at_after_started_at(self) -> Self:
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError(
                f"ended_at ({self.ended_at.isoformat()}) must be greater than or "
                f"equal to started_at ({self.started_at.isoformat()})."
            )
        return self


class IrrigationEventUpdate(BaseModel):
    """
    Request body for PATCH /fields/{field_id}/irrigation-events/{event_id}.

    All fields are optional to support sparse partial updates.  The service
    layer applies only the fields explicitly provided by the caller and
    re-validates cross-field timestamp ordering against the persisted record
    when only one of ``started_at`` or ``ended_at`` is supplied.
    """

    started_at: datetime | None = Field(
        default=None,
        description=(
            "Timezone-aware timestamp when irrigation began "
            "(ISO 8601 with timezone offset)"
        ),
    )
    ended_at: datetime | None = Field(
        default=None,
        description=(
            "Timezone-aware timestamp when irrigation ended "
            "(ISO 8601 with timezone offset)"
        ),
    )
    duration_minutes: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Duration of the irrigation event in minutes; must be non-negative",
    )
    water_volume_liters: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Total water volume applied in litres; must be non-negative",
    )
    irrigation_method: IrrigationMethod | None = Field(
        default=None,
        description="Delivery method used to apply water",
    )
    water_source: WaterSource | None = Field(
        default=None,
        description="Origin of the water applied",
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations",
    )

    @field_validator("started_at")
    @classmethod
    def validate_started_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="started_at")

    @field_validator("ended_at")
    @classmethod
    def validate_ended_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="ended_at")

    @model_validator(mode="after")
    def validate_ended_at_after_started_at(self) -> Self:
        if (
            self.started_at is not None
            and self.ended_at is not None
            and self.ended_at < self.started_at
        ):
            raise ValueError(
                f"ended_at ({self.ended_at.isoformat()}) must be greater than or "
                f"equal to started_at ({self.started_at.isoformat()})."
            )
        return self


class IrrigationEventResponse(IrrigationEventBase):
    """
    Outbound representation of an IrrigationEvent returned to API consumers.

    Extends IrrigationEventBase with server-assigned identity and audit fields.
    ``from_attributes=True`` enables direct construction from a SQLAlchemy
    ORM instance without a manual mapping step.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the irrigation event")
    field_id: uuid.UUID = Field(description="UUID of the parent field")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
