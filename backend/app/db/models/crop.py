"""
Crop ORM model.

Represents a crop cycle planted within a Field.  Crops are the third level in
the AGRIFLOW-AI domain hierarchy:

    Farm → Field → Crop

A single Field can host multiple non-overlapping crop cycles over time.  The
``status`` column drives the agronomic state machine:

    PLANNED → PLANTED → GROWING → HARVESTED
"""

from __future__ import annotations

import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field
    from app.db.models.yield_record import YieldRecord


class CropStatus(str, enum.Enum):
    """
    Agronomic lifecycle state for a crop cycle.

    Inheriting ``str`` lets SQLAlchemy store the enum label as a plain
    VARCHAR, which is forward-compatible with schema changes and readable
    in raw SQL queries without requiring a type cast.
    """

    PLANNED = "PLANNED"
    PLANTED = "PLANTED"
    GROWING = "GROWING"
    HARVESTED = "HARVESTED"


class Crop(AuditableModel, Base):
    """
    A crop cycle planted within a specific Field.

    Lifecycle rules (enforced at service layer):
    - ``planting_date`` must be set before status transitions past PLANNED.
    - ``actual_harvest_date`` should only be populated when status = HARVESTED.
    """

    __tablename__ = "crops"

    # ── Foreign key ───────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False,
        index=True,
        comment="Parent field where this crop cycle is planted",
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    crop_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Common or scientific crop name, e.g. 'Maize', 'Solanum lycopersicum'",
    )
    crop_variety: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Cultivar or hybrid designation, e.g. 'DKC 6870'",
    )

    # ── Dates ─────────────────────────────────────────────────────────────────
    planting_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Calendar date the crop was or will be planted",
    )
    expected_harvest_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Agronomically projected harvest date",
    )
    actual_harvest_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Actual harvest completion date; set only when status = HARVESTED",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    status: Mapped[CropStatus] = mapped_column(
        Enum(CropStatus, name="crop_status", create_constraint=True),
        nullable=False,
        default=CropStatus.PLANNED,
        server_default=CropStatus.PLANNED.value,
        comment="Current agronomic lifecycle state of the crop cycle",
    )

    # ── AI data (P1 — Yield Prediction) ──────────────────────────────────────
    actual_yield_tons_ha: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=True,
        comment="Actual yield recorded at harvest in tonnes per hectare; populated only when status = HARVESTED",
    )
    expected_yield_tons_ha: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=4),
        nullable=True,
        comment="Agronomist or AI-projected yield target in tonnes per hectare",
    )
    seeding_rate_kg_ha: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=3),
        nullable=True,
        comment="Seeding density at planting in kg per hectare",
    )
    growth_stage: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Current BBCH phenological growth stage code, e.g. 'BBCH-59'",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="crops")
    yield_records: Mapped[list[YieldRecord]] = relationship(
        back_populates="crop",
        cascade="all, delete-orphan",
        order_by="desc(YieldRecord.recorded_at)",
    )

    def __repr__(self) -> str:
        return (
            f"<Crop id={self.id} name={self.crop_name!r}"
            f" field_id={self.field_id} status={self.status.value}>"
        )
