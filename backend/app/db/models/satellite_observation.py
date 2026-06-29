"""
SatelliteObservation ORM model.

Represents a derived spectral index observation computed from satellite
imagery for a Field.  SatelliteObservation is the Phase 11 domain — a
direct child of Field in the AGRIFLOW-AI domain hierarchy:

    Farm → Field → SatelliteObservation

Satellite observations are anchored on Field (not Crop) because satellite
imagery is captured at the field level independently of any specific crop
cycle.  A SatelliteObservation persists as permanent historical field-level
environmental data across multiple crop cycles.

This contrasts with YieldRecord (Phase 9) and DiseaseObservation (Phase 10),
which anchor on Crop because those measurements are per-crop-cycle.  The
closest analogues to SatelliteObservation are SensorReading (Phase 7) and
IrrigationEvent (Phase 8), both of which anchor directly on Field.

The ``observed_at`` column is the primary time key.  It is:
- Timezone-aware (TIMESTAMPTZ) — mandatory, validated by the service layer
- The primary ordering key for all list queries (observed_at DESC)
- The partition key for future TimescaleDB hypertable promotion
- The clustering key for future Apache Cassandra migration

SatelliteObservation is mutable: PATCH is permitted so data engineers and
operators can correct index values, processing levels, or provenance metadata
after ingestion — for example, when imagery is reprocessed at a higher
processing level (L1C → L2A) or when a cloud mask revision changes the
reported cloud cover.

The model is intentionally forward-compatible with future migration to:
- TimescaleDB hypertables (partition key: ``observed_at``)
- Apache Cassandra (partition key: ``field_id``, cluster key: ``observed_at``)
- Redpanda / Kafka event streaming (SatelliteObservationCreated domain event)
- Phase 12 Yield Prediction Engine (NDVI/EVI/LAI growing-season features)
- Phase 13 Disease Risk Engine (NDRE/NDWI early-stress signal features)
- Phase 14 Irrigation Recommendation Engine (NDWI water-deficit features)
- Digital Twin field canopy health and water-stress state
- GaaS SatelliteAdvisor tool layer
- Feature Store satellite feature ingestion pipeline
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ProcessingLevel, SatelliteProvider, SpectralIndex
from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class SatelliteObservation(AuditableModel, Base):
    """
    A derived spectral index observation computed from satellite imagery
    for a specific Field.

    Domain rules (enforced at service layer):
    - Field must exist before a SatelliteObservation can be created.
    - ``observed_at`` must be timezone-aware; naive datetimes are rejected.
    - ``observed_at`` must not be in the future.
    - ``cloud_cover_percent``, when supplied, must be in [0, 100].
    - ``resolution_m``, when supplied, must be > 0.
    - SatelliteObservation is mutable — PATCH is permitted to allow
      operators and data engineers to correct index values or metadata
      after reprocessing.
    """

    __tablename__ = "satellite_observations"

    __table_args__ = (
        Index(
            "ix_satellite_observations_field_id_observed_at",
            "field_id",
            "observed_at",
        ),
        Index(
            "ix_satellite_observations_spectral_index_observed_at",
            "spectral_index",
            "observed_at",
        ),
    )

    # ── Foreign key ───────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False,
        index=True,
        comment=(
            "Field this satellite observation belongs to; "
            "primary domain anchor — satellite imagery is field-level, "
            "not crop-cycle-level"
        ),
    )

    # ── Observation timestamp (TimescaleDB partition key) ────────────────────
    # Declared primary_key=True to express the composite PRIMARY KEY (id, observed_at)
    # required by TimescaleDB 2.28.x.  UUID `id` is inherited from AuditableModel
    # with primary_key=True; both columns together form the composite PK.
    # ADR-002 §Primary Key Strategy — Composite PK Strategy A.
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        primary_key=True,
        comment=(
            "Timezone-aware timestamp of the satellite overpass; "
            "primary time key and TimescaleDB partition key (composite PK with id)"
        ),
    )

    # ── Source classification ─────────────────────────────────────────────────
    satellite_provider: Mapped[SatelliteProvider] = mapped_column(
        Enum(SatelliteProvider, name="satellite_provider", create_constraint=True),
        nullable=False,
        index=True,
        comment=(
            "Satellite platform or data provider that sourced the imagery; "
            "used as a spatial-resolution quality weight in AI training pipelines"
        ),
    )
    processing_level: Mapped[ProcessingLevel] = mapped_column(
        Enum(ProcessingLevel, name="processing_level", create_constraint=True),
        nullable=False,
        comment=(
            "Processing tier of the source data before index computation; "
            "ARD and L2A are required for multi-temporal AI training features; "
            "L1C observations are stored but down-weighted or excluded from "
            "model training by the feature engineering pipeline"
        ),
    )

    # ── Spectral measurement ──────────────────────────────────────────────────
    spectral_index: Mapped[SpectralIndex] = mapped_column(
        Enum(SpectralIndex, name="spectral_index", create_constraint=True),
        nullable=False,
        index=True,
        comment=(
            "Derived spectral or vegetation index type; "
            "primary measurement discriminator — the satellite equivalent of SensorType"
        ),
    )
    index_value: Mapped[Decimal] = mapped_column(
        Numeric(precision=9, scale=6),
        nullable=False,
        comment=(
            "Computed index value; typical ranges: "
            "NDVI/EVI/NDWI/SAVI/NDRE/MSAVI/GNDVI [-1.0, 1.0], "
            "LAI [0, ~10]; "
            "stored as NUMERIC to avoid IEEE-754 accumulation errors in "
            "aggregate and time-series queries"
        ),
    )

    # ── Image quality metadata ────────────────────────────────────────────────
    cloud_cover_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
        comment=(
            "Percentage of the scene covered by cloud or cloud shadow; "
            "valid range [0, 100]; "
            "feature pipelines should filter observations above the "
            "project-standard threshold (typically 20 %) before AI training"
        ),
    )
    resolution_m: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=2),
        nullable=True,
        comment=(
            "Effective pixel resolution of the source imagery in metres; "
            "e.g. 10.0 (Sentinel-2), 30.0 (Landsat), 3.0 (Planet), 250.0 (MODIS); "
            "used as a quality weight in spatial feature engineering"
        ),
    )

    # ── Provenance ────────────────────────────────────────────────────────────
    scene_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment=(
            "Provider-assigned scene or tile identifier; "
            "enables traceability back to the original imagery source, "
            "e.g. 'S2A_MSIL2A_20240615T102021_N0510_R065_T32UMD_20240615T130512'"
        ),
    )
    source_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment=(
            "URL or cloud storage path to the source Cloud Optimised GeoTIFF (COG) "
            "or derived product; supports ingestion pipeline traceability "
            "and reprocessing workflows"
        ),
    )

    # ── Operator metadata ─────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment=(
            "Operator or pipeline free-text annotations, "
            "e.g. reprocessing notes, known image artefacts, or calibration flags"
        ),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="satellite_observations")

    def __repr__(self) -> str:
        return (
            f"<SatelliteObservation id={self.id}"
            f" field_id={self.field_id}"
            f" provider={self.satellite_provider.value}"
            f" index={self.spectral_index.value}"
            f" value={self.index_value}"
            f" observed_at={self.observed_at}>"
        )
