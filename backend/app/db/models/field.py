"""
Field ORM model.

Represents a subdivided parcel within a Farm.  Fields are the second level in
the AGRIFLOW-AI domain hierarchy:

    Farm → Field → Crop
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.crop import Crop
    from app.db.models.disease_observation import DiseaseObservation
    from app.db.models.farm import Farm
    from app.db.models.irrigation_event import IrrigationEvent
    from app.db.models.satellite_observation import SatelliteObservation
    from app.db.models.sensor_reading import SensorReading
    from app.db.models.soil_profile import SoilProfile
    from app.db.models.weather_record import WeatherRecord
    from app.db.models.yield_record import YieldRecord


class Field(AuditableModel, Base):
    __tablename__ = "fields"

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id"),
        nullable=False,
        index=True,
        comment="Parent farm that owns this field",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name of the field",
    )
    area_hectares: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True,
        comment="Field area in hectares",
    )
    soil_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Dominant soil classification for the field",
    )
    latitude: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=True,
        comment="WGS-84 latitude — range [-90, 90]",
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=True,
        comment="WGS-84 longitude — range [-180, 180]",
    )

    # ── Topography (P1 — Yield Prediction) ───────────────────────────────────
    elevation_m: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=2),
        nullable=True,
        comment="Field elevation in metres above sea level; negative values valid (e.g. below sea level)",
    )

    farm: Mapped[Farm] = relationship(back_populates="fields")
    crops: Mapped[list[Crop]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )
    soil_profile: Mapped[SoilProfile | None] = relationship(
        back_populates="field",
        uselist=False,
        cascade="all, delete-orphan",
    )
    weather_records: Mapped[list[WeatherRecord]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )
    sensor_readings: Mapped[list[SensorReading]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
        order_by="SensorReading.recorded_at",
    )
    irrigation_events: Mapped[list[IrrigationEvent]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
        order_by="desc(IrrigationEvent.started_at)",
    )
    yield_records: Mapped[list[YieldRecord]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
        order_by="desc(YieldRecord.recorded_at)",
    )
    disease_observations: Mapped[list[DiseaseObservation]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
        order_by="desc(DiseaseObservation.observed_at)",
    )
    satellite_observations: Mapped[list[SatelliteObservation]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
        order_by="desc(SatelliteObservation.observed_at)",
    )

    def __repr__(self) -> str:
        return f"<Field id={self.id} name={self.name!r} farm_id={self.farm_id}>"
