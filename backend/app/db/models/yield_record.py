"""
YieldRecord ORM model.

Represents a discrete, time-keyed yield observation for a crop cycle.
YieldRecord is the Phase 9 domain — the first grandchild entity in AGRIFLOW-AI:

    Farm → Field → Crop → YieldRecord

Unlike IrrigationEvent (anchored directly on Field), YieldRecord is anchored
on Crop because yield is a per-crop-cycle measurement, not a per-field
point-in-time event.  ``field_id`` is denormalized directly onto the table
(ADR-009-02) to enable field-scoped queries without a JOIN through ``crops``.

The ``recorded_at`` column is the primary time key.  It is:
- Timezone-aware (TIMESTAMPTZ) — mandatory, validated by the service layer
- The primary ordering key for all list queries (recorded_at DESC)
- The partition key for future TimescaleDB hypertable promotion
- The clustering key for future Apache Cassandra migration

YieldRecord is mutable (ADR-009-04): PATCH is permitted so operators can
correct measurement values after the fact.  ``crop_id`` is immutable after
creation (ADR-009-05) — changing the crop association of a measurement is
not a valid correction and is excluded from the Update schema.

The model is intentionally forward-compatible with future migration to:
- TimescaleDB hypertables (partition key: ``recorded_at``)
- Apache Cassandra (partition key: ``crop_id``, cluster key: ``recorded_at``)
- Redpanda / Kafka event streaming (YieldRecordCreated domain event)
- CQRS read/write separation
- Phase 12 Yield Prediction Engine (training label source)
- GaaS YieldAdvisor tool layer
- Digital Twin field productivity state
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import YieldMeasurementMethod
from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.crop import Crop
    from app.db.models.field import Field


class YieldRecord(AuditableModel, Base):
    """
    A discrete yield observation for a crop cycle.

    Domain rules (enforced at service layer):
    - Crop must exist before a YieldRecord can be created.
    - ``recorded_at`` must be timezone-aware; naive datetimes are rejected.
    - ``recorded_at`` must not be in the future.
    - ``yield_value_tons_ha`` must be non-negative (>= 0).
    - ``area_harvested_ha``, when supplied, must be > 0 (zero area is
      agronomically invalid — see ADR-009-06).
    - ``moisture_content_percent``, when supplied, must be in [0, 100].
    - ``test_weight_kg_hl``, when supplied, must be > 0.
    - ``crop_id`` is immutable after creation.
    """

    __tablename__ = "yield_records"

    __table_args__ = (
        Index(
            "ix_yield_records_crop_id_recorded_at",
            "crop_id",
            "recorded_at",
        ),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment=(
            "Crop cycle this yield observation belongs to; "
            "primary domain anchor — yield is per crop cycle, not per field point-in-time"
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

    # ── Observation timestamp ─────────────────────────────────────────────────
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment=(
            "Timezone-aware timestamp when this yield measurement was taken; "
            "serves as the primary time key and TimescaleDB partition key"
        ),
    )

    # ── Primary measurement ───────────────────────────────────────────────────
    yield_value_tons_ha: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=False,
        comment="Measured yield in tonnes per hectare; must be >= 0",
    )

    # ── Measurement classification ────────────────────────────────────────────
    measurement_method: Mapped[YieldMeasurementMethod] = mapped_column(
        Enum(YieldMeasurementMethod, name="yield_measurement_method", create_constraint=True),
        nullable=False,
        comment=(
            "Method used to obtain this measurement; "
            "acts as a data quality weight in the Phase 12 Yield Prediction Engine"
        ),
    )

    # ── Optional quality attributes ───────────────────────────────────────────
    area_harvested_ha: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=True,
        comment=(
            "Sub-field harvested area in hectares; "
            "must be > 0 if supplied — zero area is agronomically invalid"
        ),
    )
    moisture_content_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
        comment="Grain moisture at harvest as a percentage; valid range [0, 100]",
    )
    test_weight_kg_hl: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=6, scale=3),
        nullable=True,
        comment="Grain bulk density (test weight) in kg per hectolitre; must be > 0 if supplied",
    )
    quality_grade: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Free-form quality classification, e.g. 'Grade 1', 'Feed Grade'",
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Operator free-text annotations, e.g. equipment calibration notes or field conditions",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    crop: Mapped[Crop] = relationship(back_populates="yield_records")
    field: Mapped[Field] = relationship(back_populates="yield_records")

    def __repr__(self) -> str:
        return (
            f"<YieldRecord id={self.id}"
            f" crop_id={self.crop_id}"
            f" field_id={self.field_id}"
            f" method={self.measurement_method.value}"
            f" recorded_at={self.recorded_at}>"
        )
