"""
Pydantic schemas for the SatelliteObservation domain object.

Separation of concerns
----------------------
- SatelliteObservationBase     — shared field inventory; parent of
                                  SatelliteObservationResponse.  Defines all
                                  satellite measurement and provenance fields with
                                  their validation rules so constraints are
                                  expressed exactly once.
- SatelliteObservationCreate   — inbound payload for POST
                                  /fields/{field_id}/satellite-observations.
                                  ``field_id`` is intentionally excluded; it is
                                  resolved from the URL path by the router,
                                  matching the pattern used by SensorReadingCreate
                                  and IrrigationEventCreate.  ``observed_at``,
                                  ``satellite_provider``, ``processing_level``,
                                  ``spectral_index``, and ``index_value`` are
                                  required — they are the minimum identifiers for
                                  a satellite observation.  Quality and provenance
                                  fields are optional because not all providers or
                                  ingestion pipelines supply them.
- SatelliteObservationUpdate   — inbound payload for PATCH
                                  /satellite-observations/{observation_id}.
                                  Every field is optional to support sparse partial
                                  updates.  ``field_id`` is intentionally excluded
                                  — it is immutable after creation.  All validation
                                  constraints from SatelliteObservationCreate are
                                  retained so a partial payload is never weaker
                                  than a full one.
- SatelliteObservationResponse — outbound representation returned to API
                                  consumers.  Extends SatelliteObservationBase
                                  with server-assigned identity and audit fields.
                                  ``from_attributes=True`` enables direct
                                  construction from a SQLAlchemy ORM instance
                                  without a manual mapping step.
- SatelliteObservationListResponse — collection response for list endpoints.
                                  Follows the DiseaseObservation list pattern:
                                  ``PaginatedResponse[SatelliteObservationResponse]``.

Mutability contract
-------------------
SatelliteObservation is a mutable domain.  PATCH is permitted so data engineers
and operators can correct index values, processing levels, cloud cover estimates,
or provenance metadata after ingestion — for example, when imagery is reprocessed
at a higher processing level (L1C → L2A) or when a cloud mask revision changes
the reported cloud cover percentage.

Validation strategy
-------------------
Schema layer (this file):
  - ``observed_at`` timezone awareness — rejects naive datetimes with a clear
    error message before any service logic runs.  Mirrors the pattern established
    by IrrigationEventCreate, YieldRecordCreate, and DiseaseObservationCreate.
  - ``index_value`` ge=-1 — structural lower bound; no vegetation or water index
    can produce a value below -1 by physical construction (ratio formula).
    The upper bound is left open at the schema layer because LAI can exceed 1.0
    in dense canopies (typical range 0–10); the service layer validates per-index
    contextual bounds if required.
  - ``cloud_cover_percent`` ge=0, le=100 — schema-expressible range;
    matches the same pattern as ``affected_area_percent`` in DiseaseObservation.
  - ``resolution_m`` ge=0 — Pydantic structural guard; service layer enforces > 0
    (zero-resolution is physically invalid, matching the ``area_harvested_ha``
    pattern in YieldRecord).
  - ``scene_id`` max_length=255 — matches VARCHAR(255) column.
  - ``source_url`` max_length=500 — matches VARCHAR(500) column.

Service layer (not this file):
  - ``observed_at`` must not be in the future (requires UTC clock).
  - Field must exist before a SatelliteObservation can be created.
  - ``resolution_m > 0`` when supplied (zero resolution is physically invalid).
  - Per-index contextual ``index_value`` bounds if required by future AI pipeline
    data quality gates.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ProcessingLevel, SatelliteProvider, SpectralIndex
from app.schemas.common import PaginatedResponse


def _require_timezone_aware(value: datetime, *, field_name: str) -> datetime:
    """
    Reject naive datetimes — satellite observation timestamps must carry an
    explicit timezone offset.

    Mirrors the pattern established across IrrigationEvent, YieldRecord, and
    DiseaseObservation schemas: timezone-awareness is validated at the schema
    boundary so the service layer can safely compare timestamps against UTC
    without ambiguity.
    """
    if value.tzinfo is None:
        raise ValueError(
            f"{field_name} ({value.isoformat()}) must be timezone-aware. "
            "Supply an ISO 8601 timestamp with an explicit UTC offset, "
            "e.g. 2026-06-15T10:20:00Z or 2026-06-15T12:20:00+02:00."
        )
    return value


class SatelliteObservationBase(BaseModel):
    """
    Shared field inventory for the SatelliteObservation domain.

    Inherited by SatelliteObservationResponse.  SatelliteObservationCreate and
    SatelliteObservationUpdate mirror these fields but are defined separately to
    follow the project convention — this also prevents accidental schema coupling
    when Create/Update diverge from Base in future iterations.
    """

    # ── Primary time key ─────────────────────────────────────────────────────
    observed_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp of the satellite overpass "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T10:20:00Z). "
            "Must not be in the future; validated by the service layer."
        ),
    )

    # ── Source classification ─────────────────────────────────────────────────
    satellite_provider: SatelliteProvider = Field(
        ...,
        description=(
            "Satellite platform or data provider that sourced the imagery "
            "(SENTINEL_2 | LANDSAT_8 | LANDSAT_9 | PLANET | MODIS | "
            "SPOT | WORLDVIEW | UNKNOWN)"
        ),
    )
    processing_level: ProcessingLevel = Field(
        ...,
        description=(
            "Processing tier of the source data before index computation. "
            "ARD and L2A are preferred for AI training — they are atmospherically "
            "corrected and directly comparable across dates and regions. "
            "L1C (top-of-atmosphere) is stored but down-weighted by feature "
            "pipelines. DERIVED covers composites and mosaics "
            "(L1C | L2A | ARD | DERIVED)"
        ),
    )

    # ── Spectral measurement ──────────────────────────────────────────────────
    spectral_index: SpectralIndex = Field(
        ...,
        description=(
            "Derived spectral or vegetation index type — the primary measurement "
            "discriminator for a satellite observation "
            "(NDVI | EVI | NDWI | SAVI | NDRE | LAI | MSAVI | GNDVI)"
        ),
    )
    index_value: Decimal = Field(
        ...,
        ge=-1,
        decimal_places=6,
        description=(
            "Computed index value. Typical ranges: "
            "NDVI / EVI / NDWI / SAVI / NDRE / MSAVI / GNDVI are bounded to [-1.0, 1.0]; "
            "LAI ranges from 0 to ~10 in dense canopies. "
            "Schema enforces ge=-1; per-index upper bounds are validated by the "
            "service layer. Stored as NUMERIC(9, 6)."
        ),
    )

    # ── Image quality metadata ────────────────────────────────────────────────
    cloud_cover_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description=(
            "Percentage of the scene covered by cloud or cloud shadow; "
            "valid range [0, 100]. "
            "AI feature pipelines typically filter observations above 20 %."
        ),
    )
    resolution_m: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description=(
            "Effective pixel resolution of the source imagery in metres; "
            "e.g. 10.0 (Sentinel-2), 30.0 (Landsat), 3.0 (Planet), 250.0 (MODIS). "
            "Must be > 0 if supplied (service layer enforces > 0). "
            "Schema allows >= 0."
        ),
    )

    # ── Provenance ────────────────────────────────────────────────────────────
    scene_id: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Provider-assigned scene or tile identifier for traceability back to "
            "the original imagery source, "
            "e.g. 'S2A_MSIL2A_20240615T102021_N0510_R065_T32UMD_20240615T130512'"
        ),
    )
    source_url: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "URL or cloud storage path to the source Cloud Optimised GeoTIFF (COG) "
            "or derived product; supports ingestion pipeline traceability and "
            "reprocessing workflows"
        ),
    )

    # ── Operator metadata ─────────────────────────────────────────────────────
    notes: str | None = Field(
        default=None,
        description=(
            "Operator or pipeline free-text annotations, "
            "e.g. reprocessing notes, known image artefacts, or calibration flags"
        ),
    )

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="observed_at")


class SatelliteObservationCreate(BaseModel):
    """
    Request body for POST /fields/{field_id}/satellite-observations.

    ``field_id`` is excluded — it is injected from the URL path by the router,
    matching the pattern used by SensorReadingCreate and IrrigationEventCreate.

    ``observed_at``, ``satellite_provider``, ``processing_level``,
    ``spectral_index``, and ``index_value`` are required because they constitute
    the minimum identifiers for a satellite observation: when, from where, at
    what quality, what was measured, and what value was recorded.

    All image quality, provenance, and metadata fields are optional because not
    all providers or ingestion pipelines supply them at ingest time.
    """

    # ── Primary time key ─────────────────────────────────────────────────────
    observed_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp of the satellite overpass "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T10:20:00Z)"
        ),
    )

    # ── Source classification ─────────────────────────────────────────────────
    satellite_provider: SatelliteProvider = Field(
        ...,
        description=(
            "Satellite platform or data provider that sourced the imagery "
            "(SENTINEL_2 | LANDSAT_8 | LANDSAT_9 | PLANET | MODIS | "
            "SPOT | WORLDVIEW | UNKNOWN)"
        ),
    )
    processing_level: ProcessingLevel = Field(
        ...,
        description=(
            "Processing tier of the source data before index computation "
            "(L1C | L2A | ARD | DERIVED)"
        ),
    )

    # ── Spectral measurement ──────────────────────────────────────────────────
    spectral_index: SpectralIndex = Field(
        ...,
        description=(
            "Derived spectral or vegetation index type "
            "(NDVI | EVI | NDWI | SAVI | NDRE | LAI | MSAVI | GNDVI)"
        ),
    )
    index_value: Decimal = Field(
        ...,
        ge=-1,
        decimal_places=6,
        description=(
            "Computed index value; ge=-1. "
            "Typical ranges: NDVI/EVI/NDWI/SAVI/NDRE/MSAVI/GNDVI [-1.0, 1.0], "
            "LAI [0, ~10]"
        ),
    )

    # ── Image quality metadata ────────────────────────────────────────────────
    cloud_cover_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Percentage of scene covered by cloud or cloud shadow; valid range [0, 100]",
    )
    resolution_m: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description=(
            "Effective pixel resolution in metres; e.g. 10.0, 30.0, 250.0. "
            "Must be > 0 if supplied."
        ),
    )

    # ── Provenance ────────────────────────────────────────────────────────────
    scene_id: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Provider-assigned scene or tile identifier, "
            "e.g. 'S2A_MSIL2A_20240615T102021_N0510_R065_T32UMD_20240615T130512'"
        ),
    )
    source_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL or cloud storage path to the source COG or derived product",
    )

    # ── Operator metadata ─────────────────────────────────────────────────────
    notes: str | None = Field(
        default=None,
        description="Operator or pipeline free-text annotations",
    )

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at_timezone(cls, value: datetime) -> datetime:
        return _require_timezone_aware(value, field_name="observed_at")


class SatelliteObservationUpdate(BaseModel):
    """
    Request body for PATCH /satellite-observations/{observation_id}.

    All fields are optional to support sparse partial updates.  The service
    layer applies only the fields explicitly provided by the caller.

    ``field_id`` is intentionally excluded — it is immutable after creation.
    Changing the field association of a satellite observation is not a valid
    correction; the record should be deleted and re-created if the field link
    was wrong.

    All validation constraints from SatelliteObservationCreate are retained so
    a partial PATCH payload is never weaker than a full POST payload.

    Common PATCH use cases:
    - Upgrade ``processing_level`` from L1C → L2A after reprocessing
    - Correct ``cloud_cover_percent`` after a revised cloud mask is applied
    - Add ``scene_id`` or ``source_url`` for provenance traceability
    - Correct ``index_value`` if a computation error is identified
    """

    # ── Primary time key ─────────────────────────────────────────────────────
    observed_at: datetime | None = Field(
        default=None,
        description=(
            "Timezone-aware timestamp of the satellite overpass "
            "(ISO 8601 with timezone offset)"
        ),
    )

    # ── Source classification ─────────────────────────────────────────────────
    satellite_provider: SatelliteProvider | None = Field(
        default=None,
        description=(
            "Satellite platform or data provider "
            "(SENTINEL_2 | LANDSAT_8 | LANDSAT_9 | PLANET | MODIS | "
            "SPOT | WORLDVIEW | UNKNOWN)"
        ),
    )
    processing_level: ProcessingLevel | None = Field(
        default=None,
        description="Processing tier of the source data (L1C | L2A | ARD | DERIVED)",
    )

    # ── Spectral measurement ──────────────────────────────────────────────────
    spectral_index: SpectralIndex | None = Field(
        default=None,
        description=(
            "Derived spectral or vegetation index type "
            "(NDVI | EVI | NDWI | SAVI | NDRE | LAI | MSAVI | GNDVI)"
        ),
    )
    index_value: Decimal | None = Field(
        default=None,
        ge=-1,
        decimal_places=6,
        description=(
            "Computed index value; ge=-1. "
            "Typical ranges: NDVI/EVI/NDWI/SAVI/NDRE/MSAVI/GNDVI [-1.0, 1.0], "
            "LAI [0, ~10]"
        ),
    )

    # ── Image quality metadata ────────────────────────────────────────────────
    cloud_cover_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Percentage of scene covered by cloud or cloud shadow; valid range [0, 100]",
    )
    resolution_m: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Effective pixel resolution in metres; must be > 0 if supplied",
    )

    # ── Provenance ────────────────────────────────────────────────────────────
    scene_id: str | None = Field(
        default=None,
        max_length=255,
        description="Provider-assigned scene or tile identifier",
    )
    source_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL or cloud storage path to the source COG or derived product",
    )

    # ── Operator metadata ─────────────────────────────────────────────────────
    notes: str | None = Field(
        default=None,
        description="Operator or pipeline free-text annotations",
    )

    @field_validator("observed_at")
    @classmethod
    def validate_observed_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return _require_timezone_aware(value, field_name="observed_at")


class SatelliteObservationResponse(SatelliteObservationBase):
    """
    Outbound representation of a SatelliteObservation returned to API consumers.

    Extends SatelliteObservationBase with server-assigned identity and audit
    fields.  ``from_attributes=True`` enables direct construction from a
    SQLAlchemy ORM instance without a manual mapping step.

    ``field_id`` is included — reflecting SatelliteObservation's direct Field
    anchor (Farm → Field → SatelliteObservation).  Unlike YieldRecord and
    DiseaseObservation, there is no ``crop_id`` because satellite observations
    are not crop-cycle-scoped.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the satellite observation")
    field_id: uuid.UUID = Field(description="UUID of the parent field")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")


# List endpoints use PaginatedResponse[SatelliteObservationResponse] following
# the same collection response pattern as DiseaseObservationListResponse.
SatelliteObservationListResponse = PaginatedResponse[SatelliteObservationResponse]
