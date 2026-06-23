"""
Pydantic schemas for the DiseaseObservation domain object.

Separation of concerns
----------------------
- DiseaseObservationBase            — shared field inventory; parent of
                                      DiseaseObservationResponse.  Defines all
                                      disease observation and classification
                                      fields with their validation rules so
                                      constraints are expressed exactly once.
- CreateDiseaseObservationRequest   — inbound payload for POST
                                      /crops/{crop_id}/disease-observations.
                                      ``field_id`` is intentionally excluded;
                                      it is resolved server-side from the crop
                                      record, matching the pattern used by
                                      YieldRecordCreate and WeatherRecordCreate.
                                      ``observed_at``, ``disease_name``,
                                      ``severity``, and ``diagnosis_method`` are
                                      required; treatment and extent fields are
                                      optional because observation detail varies
                                      by diagnosis method and field conditions.
- UpdateDiseaseObservationRequest   — inbound payload for PATCH
                                      /disease-observations/{observation_id}.
                                      Every field is optional to support sparse
                                      partial updates.  ``crop_id`` and
                                      ``field_id`` are intentionally excluded —
                                      they are immutable after creation.
                                      All validation constraints from
                                      CreateDiseaseObservationRequest are
                                      retained so a partial payload is never
                                      weaker than a full one.
- DiseaseObservationResponse        — outbound representation returned to API
                                      consumers.  Extends DiseaseObservationBase
                                      with server-assigned identity and audit
                                      fields.  ``from_attributes=True`` enables
                                      direct construction from a SQLAlchemy ORM
                                      instance.
- DiseaseObservationListResponse    — collection response for list endpoints.
                                      Follows the YieldRecord list pattern:
                                      ``PaginatedResponse[DiseaseObservationResponse]``.

Mutability contract
-------------------
DiseaseObservation is a mutable domain.  PATCH is permitted so operators can
correct severity, diagnosis method, treatment notes, or extent after the fact.

Validation strategy
-------------------
Schema layer (this file):
  - ``observed_at`` timezone awareness — rejects naive datetimes with a clear
    error message before any service logic runs.
  - ``affected_area_percent`` ge=0, le=100 — schema-expressible range.
  - ``disease_name`` max_length=255 — matches VARCHAR(255) column.

Service layer (not this file):
  - ``observed_at`` must not be in the future (requires UTC clock).
  - Crop must exist before a DiseaseObservation can be created.
  - ``field_id`` is derived from the parent crop record.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import DiagnosisMethod, DiseaseSeverity
from app.schemas.common import PaginatedResponse


def _require_timezone_aware(value: datetime, *, field_name: str) -> datetime:
    """
    Reject naive datetimes — observation timestamps must carry an explicit offset.

    Mirrors the YieldRecord schema boundary: timezone-awareness is validated at
    the schema layer so the service layer can safely compare timestamps against
    UTC without ambiguity.
    """
    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} ({value.isoformat()}) must be timezone-aware. "
            "Supply an ISO 8601 timestamp with an explicit UTC offset, "
            "e.g. 2026-06-15T08:00:00Z or 2026-06-15T10:00:00+02:00."
        )
    return value


class DiseaseObservationBase(BaseModel):
    """
    Shared field inventory for the DiseaseObservation domain.

    Inherited by DiseaseObservationResponse.  CreateDiseaseObservationRequest
    and UpdateDiseaseObservationRequest mirror these fields but are defined
    separately to follow the project convention — this also prevents accidental
    schema coupling when Create/Update diverge from Base in future iterations.
    """

    observed_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when this disease was observed "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T08:00:00+02:00)"
        ),
    )
    disease_name: str = Field(
        ...,
        max_length=255,
        description=(
            "Free-text disease name, e.g. 'Rust', 'Powdery Mildew', 'Late Blight'"
        ),
    )
    severity: DiseaseSeverity = Field(
        ...,
        description=(
            "Severity classification of the observed disease pressure "
            "(LOW | MEDIUM | HIGH | CRITICAL)"
        ),
    )
    affected_area_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Percentage of crop area affected by the disease; valid range [0, 100]",
    )
    diagnosis_method: DiagnosisMethod = Field(
        ...,
        description=(
            "Method by which the disease was identified or confirmed "
            "(VISUAL_INSPECTION | LAB_ANALYSIS | IMAGE_AI | AGRONOMIST | "
            "SENSOR_DETECTED)"
        ),
    )
    treatment_applied: str | None = Field(
        default=None,
        description=(
            "Treatment applied in response to the observation, "
            "e.g. fungicide application"
        ),
    )
    notes: str | None = Field(
        default=None,
        description=(
            "Operator free-text annotations, e.g. follow-up inspection plans"
        ),
    )

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="observed_at")


class CreateDiseaseObservationRequest(BaseModel):
    """
    Request body for POST /crops/{crop_id}/disease-observations.

    ``crop_id`` is required in the payload for explicit crop-cycle anchoring.
    ``field_id`` is excluded — it is resolved server-side from the crop record
    (the service fetches the crop to extract its field_id).

    ``observed_at``, ``disease_name``, ``severity``, and ``diagnosis_method`` are
    required because they are the minimum identifiers for a disease observation.
    Treatment and extent fields are optional because observation detail varies
    by diagnosis method and field conditions.
    """

    crop_id: uuid.UUID = Field(
        ...,
        description="UUID of the crop cycle this disease observation belongs to",
    )
    observed_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when this disease was observed "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T08:00:00+02:00)"
        ),
    )
    disease_name: str = Field(
        ...,
        max_length=255,
        description=(
            "Free-text disease name, e.g. 'Rust', 'Powdery Mildew', 'Late Blight'"
        ),
    )
    severity: DiseaseSeverity = Field(
        ...,
        description=(
            "Severity classification of the observed disease pressure "
            "(LOW | MEDIUM | HIGH | CRITICAL)"
        ),
    )
    diagnosis_method: DiagnosisMethod = Field(
        ...,
        description=(
            "Method by which the disease was identified or confirmed "
            "(VISUAL_INSPECTION | LAB_ANALYSIS | IMAGE_AI | AGRONOMIST | "
            "SENSOR_DETECTED)"
        ),
    )
    affected_area_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Percentage of crop area affected by the disease; valid range [0, 100]",
    )
    treatment_applied: str | None = Field(
        default=None,
        description="Treatment applied in response to the observation",
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations",
    )

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="observed_at")


class UpdateDiseaseObservationRequest(BaseModel):
    """
    Request body for PATCH /disease-observations/{observation_id}.

    All fields are optional to support sparse partial updates.  The service
    layer applies only the fields explicitly provided by the caller.

    ``crop_id`` and ``field_id`` are intentionally excluded — they are immutable
    after creation.  Changing the crop association of a disease observation
    is not a valid correction; the record should be deleted and re-created if
    the crop link was wrong.
    """

    observed_at: datetime | None = Field(
        default=None,
        description=(
            "Timezone-aware timestamp when this disease was observed "
            "(ISO 8601 with timezone offset)"
        ),
    )
    disease_name: str | None = Field(
        default=None,
        max_length=255,
        description="Free-text disease name, e.g. 'Rust', 'Powdery Mildew'",
    )
    severity: DiseaseSeverity | None = Field(
        default=None,
        description="Severity classification of the observed disease pressure",
    )
    affected_area_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Percentage of crop area affected by the disease; valid range [0, 100]",
    )
    diagnosis_method: DiagnosisMethod | None = Field(
        default=None,
        description="Method by which the disease was identified or confirmed",
    )
    treatment_applied: str | None = Field(
        default=None,
        description="Treatment applied in response to the observation",
    )
    notes: str | None = Field(
        default=None,
        description="Operator free-text annotations",
    )

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="observed_at")


class DiseaseObservationResponse(DiseaseObservationBase):
    """
    Outbound representation of a DiseaseObservation returned to API consumers.

    Extends DiseaseObservationBase with server-assigned identity and audit fields.
    ``from_attributes=True`` enables direct construction from a SQLAlchemy
    ORM instance without a manual mapping step.

    Both ``crop_id`` and ``field_id`` are included — reflecting
    DiseaseObservation's dual-anchor design (crop ownership + denormalized field).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the disease observation")
    crop_id: uuid.UUID = Field(description="UUID of the parent crop cycle")
    field_id: uuid.UUID = Field(description="UUID of the parent field (denormalized)")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")


# YieldRecord list endpoints use PaginatedResponse[YieldRecordResponse] rather
# than a dedicated YieldRecordListResponse class.  DiseaseObservation follows
# the same collection response pattern.
DiseaseObservationListResponse = PaginatedResponse[DiseaseObservationResponse]
