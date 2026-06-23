"""
Pydantic schemas for the YieldRecord domain object.

Separation of concerns
----------------------
- YieldRecordBase     — shared field inventory; parent of YieldRecordResponse.
                        Defines all yield measurement and classification fields
                        with their validation rules so constraints are expressed
                        exactly once.
- YieldRecordCreate   — inbound payload for POST
                        /crops/{crop_id}/yield-records.
                        ``crop_id`` and ``field_id`` are intentionally excluded;
                        ``crop_id`` is resolved from the URL path by the router
                        and ``field_id`` is resolved server-side from the crop
                        record, matching the pattern used by WeatherRecordCreate
                        and IrrigationEventCreate.  ``recorded_at``,
                        ``yield_value_tons_ha``, and ``measurement_method`` are
                        required; all quality attributes are optional because
                        measurement detail varies by method and instrument.
- YieldRecordUpdate   — inbound payload for PATCH
                        /yield-records/{yield_record_id}.
                        Every field is optional to support sparse partial
                        updates.  ``crop_id`` is intentionally excluded —
                        it is immutable after creation (ADR-009-05).  All
                        validation constraints from YieldRecordCreate are
                        retained so a partial payload is never weaker than a
                        full one.
- YieldRecordResponse — outbound representation returned to API consumers.
                        Extends YieldRecordBase with server-assigned identity
                        and audit fields.  ``from_attributes=True`` enables
                        direct construction from a SQLAlchemy ORM instance.

Mutability contract
-------------------
YieldRecord is a mutable domain (ADR-009-04).  PATCH is permitted so operators
can correct measurement values after the fact (e.g. recalibrated moisture
content, corrected area).  This differs from SensorReading (append-only
immutable telemetry).

Validation strategy
-------------------
Schema layer (this file):
  - ``recorded_at`` timezone awareness — rejects naive datetimes with a clear
    error message before any service logic runs.
  - ``yield_value_tons_ha`` ge=0 — structural invariant; a negative yield
    measurement is not physically meaningful.
  - ``moisture_content_percent`` ge=0, le=100 — schema-expressible range.
  - ``area_harvested_ha`` ge=0 — Pydantic structural guard.
  - ``test_weight_kg_hl`` ge=0 — Pydantic structural guard.
  - ``quality_grade`` max_length=50 — matches VARCHAR(50) column.

Service layer (not this file):
  - ``recorded_at`` must not be in the future (requires UTC clock — ADR-009-03).
  - ``area_harvested_ha > 0`` when supplied (zero area is agronomically invalid;
    Pydantic allows exactly 0 but service tightens to > 0 — ADR-009-06).
  - ``test_weight_kg_hl > 0`` when supplied (same reasoning).
  - Crop must exist before a YieldRecord can be created.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import YieldMeasurementMethod


def _require_timezone_aware(value: datetime, *, field_name: str) -> datetime:
    """
    Reject naive datetimes — yield timestamps must carry an explicit offset.

    Mirrors ADR-009-03: timezone-awareness is validated at the schema boundary
    so the service layer can safely compare timestamps against UTC without
    ambiguity.
    """
    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} ({value.isoformat()}) must be timezone-aware. "
            "Supply an ISO 8601 timestamp with an explicit UTC offset, "
            "e.g. 2026-06-15T08:00:00Z or 2026-06-15T10:00:00+02:00."
        )
    return value


class YieldRecordBase(BaseModel):
    """
    Shared field inventory for the YieldRecord domain.

    Inherited by YieldRecordResponse.  YieldRecordCreate and YieldRecordUpdate
    mirror these fields but are defined separately to follow the project
    convention — this also prevents accidental schema coupling when
    Create/Update diverge from Base in future iterations.
    """

    recorded_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when this yield measurement was taken "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T08:00:00+02:00)"
        ),
    )
    yield_value_tons_ha: Decimal = Field(
        ...,
        ge=0,
        decimal_places=4,
        description=(
            "Measured yield in tonnes per hectare; must be >= 0.  "
            "Use NUMERIC(10,4) precision."
        ),
    )
    measurement_method: YieldMeasurementMethod = Field(
        ...,
        description=(
            "Method used to obtain this measurement "
            "(MANUAL_SCALE | COMBINE_MONITOR | YIELD_MAP | REMOTE_SENSING | "
            "CROP_CUT | LABORATORY_ANALYSIS | ESTIMATED)"
        ),
    )
    area_harvested_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description=(
            "Sub-field harvested area in hectares; must be > 0 if supplied "
            "(zero area is agronomically invalid — ADR-009-06).  "
            "Schema allows >= 0; service layer enforces > 0."
        ),
    )
    moisture_content_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Grain moisture at harvest as a percentage; valid range [0, 100]",
    )
    test_weight_kg_hl: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description=(
            "Grain bulk density (test weight) in kg per hectolitre; "
            "must be > 0 if supplied.  Schema allows >= 0; service layer enforces > 0."
        ),
    )
    quality_grade: str | None = Field(
        default=None,
        max_length=50,
        description="Free-form quality classification, e.g. 'Grade 1', 'Feed Grade'",
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations, e.g. equipment calibration notes or field conditions",
    )

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="recorded_at")


class YieldRecordCreate(BaseModel):
    """
    Request body for POST /crops/{crop_id}/yield-records.

    ``crop_id`` is excluded — it is injected from the URL path by the router.
    ``field_id`` is excluded — it is resolved server-side from the crop record
    (the service fetches the crop to extract its field_id).

    ``recorded_at``, ``yield_value_tons_ha``, and ``measurement_method`` are
    required because they are the minimum identifiers for a yield observation.
    All quality attribute fields are optional because measurement detail varies
    by method and available instrumentation.
    """

    recorded_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when this yield measurement was taken "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T08:00:00+02:00)"
        ),
    )
    yield_value_tons_ha: Decimal = Field(
        ...,
        ge=0,
        decimal_places=4,
        description="Measured yield in tonnes per hectare; must be >= 0",
    )
    measurement_method: YieldMeasurementMethod = Field(
        ...,
        description=(
            "Method used to obtain this measurement "
            "(MANUAL_SCALE | COMBINE_MONITOR | YIELD_MAP | REMOTE_SENSING | "
            "CROP_CUT | LABORATORY_ANALYSIS | ESTIMATED)"
        ),
    )
    area_harvested_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description=(
            "Sub-field harvested area in hectares; must be > 0 if supplied "
            "(service layer enforces > 0)"
        ),
    )
    moisture_content_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Grain moisture at harvest as a percentage; valid range [0, 100]",
    )
    test_weight_kg_hl: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Grain bulk density in kg per hectolitre; must be > 0 if supplied",
    )
    quality_grade: str | None = Field(
        default=None,
        max_length=50,
        description="Free-form quality classification, e.g. 'Grade 1', 'Feed Grade'",
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations",
    )

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="recorded_at")


class YieldRecordUpdate(BaseModel):
    """
    Request body for PATCH /yield-records/{yield_record_id}.

    All fields are optional to support sparse partial updates.  The service
    layer applies only the fields explicitly provided by the caller.

    ``crop_id`` is intentionally excluded — it is immutable after creation
    (ADR-009-05).  Changing the crop association of a yield measurement is not
    a valid correction; the record should be deleted and re-created if the
    crop link was wrong.

    ``field_id`` is excluded — it is always derived from the crop record and
    cannot be changed independently.
    """

    recorded_at: datetime | None = Field(
        default=None,
        description=(
            "Timezone-aware timestamp when this yield measurement was taken "
            "(ISO 8601 with timezone offset)"
        ),
    )
    yield_value_tons_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Measured yield in tonnes per hectare; must be >= 0",
    )
    measurement_method: YieldMeasurementMethod | None = Field(
        default=None,
        description="Method used to obtain this measurement",
    )
    area_harvested_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Sub-field harvested area in hectares; must be > 0 if supplied",
    )
    moisture_content_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Grain moisture at harvest as a percentage; valid range [0, 100]",
    )
    test_weight_kg_hl: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Grain bulk density in kg per hectolitre; must be > 0 if supplied",
    )
    quality_grade: str | None = Field(
        default=None,
        max_length=50,
        description="Free-form quality classification, e.g. 'Grade 1', 'Feed Grade'",
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations",
    )

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="recorded_at")


class YieldRecordResponse(YieldRecordBase):
    """
    Outbound representation of a YieldRecord returned to API consumers.

    Extends YieldRecordBase with server-assigned identity and audit fields.
    ``from_attributes=True`` enables direct construction from a SQLAlchemy
    ORM instance without a manual mapping step.

    Both ``crop_id`` and ``field_id`` are included — this is the first
    response schema in the project that exposes two parent FKs, reflecting
    YieldRecord's dual-anchor design (ADR-009-01, ADR-009-02).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the yield record")
    crop_id: uuid.UUID = Field(description="UUID of the parent crop cycle")
    field_id: uuid.UUID = Field(description="UUID of the parent field (denormalized)")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
