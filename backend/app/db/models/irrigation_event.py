"""
IrrigationEvent ORM model.

Represents a discrete irrigation intervention applied to a Field.
IrrigationEvent is the Phase 8 domain — the first agricultural intervention
record in AGRIFLOW-AI:

    Farm → Field → Crop
                ↘ SoilProfile       (one-to-one)
                ↘ WeatherRecord     (one-to-many)
                ↘ SensorReading     (one-to-many, append-only)
                ↘ IrrigationEvent   (one-to-many)

Unlike SensorReading (machine-generated, immutable telemetry), IrrigationEvent
is a human-logged management action.  PATCH is permitted so operators can
correct water volume, duration, or method after the fact.

The ``started_at`` column is the primary time key.  It is:
- Timezone-aware (TIMESTAMPTZ) — mandatory, validated by the service layer
- The primary ordering key for all list queries (started_at DESC)
- The partition key for future TimescaleDB hypertable promotion
- The clustering key for future Apache Cassandra migration

Both ``ended_at`` and ``duration_minutes`` are nullable and independent.
The service layer validates consistency when both are supplied.

The model is intentionally forward-compatible with future migration to:
- TimescaleDB hypertables (partition key: ``started_at``)
- Apache Cassandra (partition key: ``field_id``, cluster key: ``started_at``)
- Redpanda / Kafka event streaming (IrrigationEventCreated domain event)
- CQRS read/write separation
- Digital Twin field water-balance state updates
- GaaS IrrigationAdvisor tool layer
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import IrrigationMethod, WaterSource
from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class IrrigationEvent(AuditableModel, Base):
    """
    A discrete irrigation intervention applied to a Field.

    Domain rules (enforced at service layer):
    - ``started_at`` must be timezone-aware; naive datetimes are rejected.
    - ``started_at`` must not be in the future.
    - ``ended_at``, when supplied, must be timezone-aware and after
      ``started_at``.
    - ``duration_minutes``, when supplied, must be greater than zero.
    - ``water_volume_liters``, when supplied, must be non-negative.
    - Field must exist before an IrrigationEvent can be created.
    """

    __tablename__ = "irrigation_events"

    __table_args__ = (
        Index(
            "ix_irrigation_events_field_id_started_at",
            "field_id",
            "started_at",
        ),
    )

    # ── Foreign key ───────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False,
        index=True,
        comment="Parent field on which this irrigation event was applied",
    )

    # ── Event window ──────────────────────────────────────────────────────────
    # started_at declared primary_key=True to express the composite PRIMARY KEY
    # (id, started_at) required by TimescaleDB 2.28.x.  UUID `id` is inherited
    # from AuditableModel with primary_key=True; both columns form the composite PK.
    # ADR-002 §Primary Key Strategy — Composite PK Strategy A.
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        primary_key=True,
        comment=(
            "Timezone-aware timestamp when irrigation began; "
            "primary time key and TimescaleDB partition key (composite PK with id)"
        ),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment=(
            "Timezone-aware timestamp when irrigation ended; "
            "optional — may be omitted when only duration is known"
        ),
    )

    # ── Quantification ────────────────────────────────────────────────────────
    duration_minutes: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=2),
        nullable=True,
        comment=(
            "Duration of the irrigation event in minutes; "
            "independent of ended_at — either or both may be supplied"
        ),
    )
    water_volume_liters: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=10, scale=3),
        nullable=True,
        comment=(
            "Total water volume applied in litres; "
            "nullable for non-metered systems — "
            "recording an event without volume is preferable to no record"
        ),
    )

    # ── Classification ────────────────────────────────────────────────────────
    irrigation_method: Mapped[IrrigationMethod] = mapped_column(
        Enum(IrrigationMethod, name="irrigation_method", create_constraint=True),
        nullable=False,
        comment=(
            "Delivery method used to apply water; "
            "drives FAO-56 application efficiency coefficients in AI models"
        ),
    )
    water_source: Mapped[WaterSource | None] = mapped_column(
        Enum(WaterSource, name="water_source", create_constraint=True),
        nullable=True,
        comment="Origin of the water applied; used in water management analytics",
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Operator free-text annotations, e.g. equipment issues or field observations",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="irrigation_events")

    def __repr__(self) -> str:
        return (
            f"<IrrigationEvent id={self.id}"
            f" field_id={self.field_id}"
            f" method={self.irrigation_method.value}"
            f" started_at={self.started_at}>"
        )
