"""
SensorReading ORM model.

Represents a discrete telemetry reading captured by an IoT sensor attached to
a Field.  SensorReading is AGRIFLOW-AI's first telemetry domain:

    Farm → Field → Crop
                ↘ SoilProfile      (one-to-one)
                ↘ WeatherRecord    (one-to-many)
                ↘ SensorReading    (one-to-many, append-only)

Telemetry data is strictly append-only; readings must never be mutated after
creation.  The ``recorded_at`` column carries timezone information so readings
from sensors in different UTC offsets compare correctly without ambiguity.

The model is intentionally forward-compatible with future migration to:
- TimescaleDB hypertables (partition key: ``recorded_at``)
- Apache Cassandra (partition key: ``field_id``, cluster key: ``recorded_at``)
- Redpanda / Kafka event streaming (append-only semantics are preserved)
- CQRS read/write separation (read models can be projected from this table)
- Digital Twin and GaaS (Graph-as-a-Service) topologies
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Double, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import SensorType
from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class SensorReading(AuditableModel, Base):
    """
    A discrete telemetry reading captured by an IoT sensor for a Field.

    Domain rules (enforced at service layer):
    - Records are append-only; once persisted they must not be updated.
    - ``sensor_value`` carries no domain-level range constraint — valid ranges
      are sensor_type-specific and enforced upstream by the ingestion service.
    - ``unit`` must match the SI or industry-standard unit for the given
      ``sensor_type`` (e.g. "%" for SOIL_MOISTURE, "°C" for SOIL_TEMPERATURE,
      "lux" for LIGHT_INTENSITY, "dS/m" for ELECTRICAL_CONDUCTIVITY).
    - ``recorded_at`` must be timezone-aware and supplied by the originating
      device or ingestion gateway; it is not generated server-side.
    """

    __tablename__ = "sensor_readings"

    __table_args__ = (
        Index(
            "ix_sensor_readings_field_id_recorded_at",
            "field_id",
            "recorded_at",
        ),
        Index(
            "ix_sensor_readings_sensor_type_recorded_at",
            "sensor_type",
            "recorded_at",
        ),
    )

    # ── Foreign key ───────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False,
        index=True,
        comment="Parent field that owns this sensor reading",
    )

    # ── Sensor classification ─────────────────────────────────────────────────
    sensor_type: Mapped[SensorType] = mapped_column(
        Enum(SensorType, name="sensor_type", create_constraint=True),
        nullable=False,
        index=True,
        comment="Physical quantity measured by the sensor",
    )

    # ── Measurement ───────────────────────────────────────────────────────────
    sensor_value: Mapped[float] = mapped_column(
        Double(),
        nullable=False,
        comment=(
            "Raw numeric value recorded by the sensor; stored as PostgreSQL "
            "DOUBLE PRECISION to preserve full IoT telemetry resolution"
        ),
    )
    unit: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment=(
            "SI or industry-standard unit for the recorded value "
            "(e.g. '%', '°C', 'lux', 'dS/m', 'mm', 'V')"
        ),
    )

    # ── Observation timestamp (TimescaleDB partition key) ────────────────────
    # Declared primary_key=True to express the composite PRIMARY KEY (id, recorded_at)
    # required by TimescaleDB 2.28.x.  UUID `id` is inherited from AuditableModel
    # with primary_key=True; both columns together form the composite PK.
    # All repository queries use WHERE id = :id predicate — zero code impact.
    # ADR-002 §Primary Key Strategy — Composite PK Strategy A.
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        primary_key=True,
        comment="Timezone-aware timestamp when the sensor captured this reading; TimescaleDB partition key",
    )

    # ── Metadata ──────────────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text annotations or anomaly flags from the ingestion pipeline",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="sensor_readings")

    def __repr__(self) -> str:
        return (
            f"<SensorReading id={self.id}"
            f" field_id={self.field_id}"
            f" sensor_type={self.sensor_type.value}"
            f" recorded_at={self.recorded_at}>"
        )
