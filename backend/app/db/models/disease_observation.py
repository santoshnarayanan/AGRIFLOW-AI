"""
DiseaseObservation ORM model.

Represents a disease event observed during a specific crop lifecycle.
DiseaseObservation is the Phase 10 domain — a grandchild entity in AGRIFLOW-AI:

    Farm → Field → Crop → DiseaseObservation

Like YieldRecord, DiseaseObservation is anchored on Crop because disease
pressure is a per-crop-cycle measurement.  ``field_id`` is denormalized
directly onto the table (ADR-009-02) to enable field-scoped queries without
a JOIN through ``crops``.

The ``observed_at`` column is the primary time key.  It is:
- Timezone-aware (TIMESTAMPTZ) — mandatory, validated by the service layer
- The primary ordering key for all list queries (observed_at DESC)
- The partition key for future TimescaleDB hypertable promotion
- The clustering key for future Apache Cassandra migration

The model is intentionally forward-compatible with future migration to:
- TimescaleDB hypertables (partition key: ``observed_at``)
- Apache Cassandra (partition key: ``crop_id``, cluster key: ``observed_at``)
- Redpanda / Kafka event streaming (DiseaseObservationCreated domain event)
- Phase 13 Disease Risk Scoring Engine (training label source)
- GaaS PlantHealthAdvisor tool layer
- Digital Twin crop health state
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DiagnosisMethod, DiseaseSeverity
from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.crop import Crop
    from app.db.models.field import Field


class DiseaseObservation(AuditableModel, Base):
    """
    A disease event observed during a crop cycle.

    Domain rules (enforced at service layer):
    - Crop must exist before a DiseaseObservation can be created.
    - ``observed_at`` must be timezone-aware; naive datetimes are rejected.
    - ``observed_at`` must not be in the future.
    - ``affected_area_percent``, when supplied, must be in [0, 100].
    - ``crop_id`` is immutable after creation.
    """

    __tablename__ = "disease_observations"

    __table_args__ = (
        Index(
            "ix_disease_observations_crop_id_observed_at",
            "crop_id",
            "observed_at",
        ),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment=(
            "Crop cycle this disease observation belongs to; "
            "primary domain anchor — disease pressure is per crop cycle"
        ),
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment=(
            "Denormalized field FK (ADR-009-02); "
            "enables direct field-scoped queries without a JOIN through crops"
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
            "Timezone-aware timestamp when this disease was observed; "
            "primary time key and TimescaleDB partition key (composite PK with id)"
        ),
    )

    # ── Disease identification ──────────────────────────────────────────────────
    disease_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Free-text disease name, e.g. 'Rust', 'Powdery Mildew', 'Late Blight'",
    )
    severity: Mapped[DiseaseSeverity] = mapped_column(
        Enum(DiseaseSeverity, name="disease_severity", create_constraint=True),
        nullable=False,
        index=True,
        comment="Severity classification of the observed disease pressure",
    )
    affected_area_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
        comment="Percentage of crop area affected by the disease; valid range [0, 100]",
    )

    # ── Diagnosis classification ────────────────────────────────────────────────
    diagnosis_method: Mapped[DiagnosisMethod] = mapped_column(
        Enum(DiagnosisMethod, name="diagnosis_method", create_constraint=True),
        nullable=False,
        comment="Method by which the disease was identified or confirmed",
    )

    # ── Treatment and metadata ──────────────────────────────────────────────────
    treatment_applied: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Treatment applied in response to the observation, e.g. fungicide application",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Operator free-text annotations, e.g. follow-up inspection plans",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    crop: Mapped[Crop] = relationship(back_populates="disease_observations")
    field: Mapped[Field] = relationship(back_populates="disease_observations")

    def __repr__(self) -> str:
        return (
            f"<DiseaseObservation id={self.id}"
            f" crop_id={self.crop_id}"
            f" field_id={self.field_id}"
            f" disease={self.disease_name!r}"
            f" severity={self.severity.value}"
            f" observed_at={self.observed_at}>"
        )
