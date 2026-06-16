"""
WeatherRecord ORM model.

Represents a point-in-time meteorological observation attached to a Field.
WeatherRecord sits alongside the core domain hierarchy:

    Farm → Field → Crop
                ↘ SoilProfile    (one-to-one)
                ↘ WeatherRecord  (one-to-many)

Each Field accumulates an ordered time-series of weather observations. The
``recorded_at`` column carries timezone information so observations from
fields in different UTC offsets compare correctly without ambiguity.

``data_source`` distinguishes manually entered readings from those ingested
via automated integrations (e.g. IoT sensors, third-party weather APIs).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class WeatherRecord(AuditableModel, Base):
    """
    A single meteorological observation for a Field at a specific point in time.

    Domain rules (enforced at service layer):
    - ``temperature_c`` is unconstrained by range — sub-zero values are valid.
    - ``humidity_percent`` must be in the range [0, 100].
    - ``rainfall_mm`` and ``wind_speed_kmh`` must be non-negative.
    - ``data_source`` defaults to "MANUAL" for operator-entered readings.
    """

    __tablename__ = "weather_records"

    # ── Foreign key ───────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False,
        index=True,
        comment="Parent field that owns this weather observation",
    )

    # ── Observation timestamp ─────────────────────────────────────────────────
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Timestamp when the weather observation was recorded",
    )

    # ── Atmospheric measurements ──────────────────────────────────────────────
    temperature_c: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
        comment="Air temperature in degrees Celsius",
    )
    humidity_percent: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
        comment="Relative humidity percentage",
    )
    rainfall_mm: Mapped[Decimal] = mapped_column(
        Numeric(precision=8, scale=2),
        nullable=False,
        server_default="0",
        comment="Rainfall in millimeters",
    )
    wind_speed_kmh: Mapped[Decimal] = mapped_column(
        Numeric(precision=6, scale=2),
        nullable=False,
        server_default="0",
        comment="Wind speed in kilometers per hour",
    )

    # ── Solar / temperature range (P1 — Yield Prediction) ────────────────────
    solar_radiation_wm2: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=8, scale=3),
        nullable=True,
        comment="Solar irradiance in W/m²; required for Penman-Monteith ET₀ calculation",
    )
    temperature_min_c: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
        comment="Daily minimum air temperature in °C; used for Growing Degree Day calculation",
    )
    temperature_max_c: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
        comment="Daily maximum air temperature in °C; used for Growing Degree Day calculation",
    )

    # ── Provenance ────────────────────────────────────────────────────────────
    data_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="MANUAL",
        comment="Origin of weather data",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="weather_records")

    def __repr__(self) -> str:
        return (
            f"<WeatherRecord id={self.id}"
            f" field_id={self.field_id}"
            f" recorded_at={self.recorded_at}>"
        )
