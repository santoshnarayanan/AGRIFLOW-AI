"""
SoilProfile ORM model.

Represents the agronomic soil composition data for a Field.  SoilProfile sits
alongside the core domain hierarchy:

    Farm → Field → Crop
                ↘ SoilProfile  (one-to-one)

Each Field may have at most one SoilProfile.  The uniqueness constraint on
``field_id`` enforces this invariant at the database level, complementing the
``uselist=False`` convention on the SQLAlchemy relationship side.

Nutrient columns (nitrogen, phosphorus, potassium) are expressed in mg/kg
(parts per million) to a precision of four decimal places, accommodating
laboratory-grade measurement granularity.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class SoilType(str, enum.Enum):
    """
    Dominant soil texture classification for a field.

    Inheriting ``str`` lets SQLAlchemy store the enum label as a plain
    VARCHAR, which is forward-compatible with schema changes and readable
    in raw SQL queries without requiring a type cast.
    """

    SANDY = "SANDY"
    CLAY = "CLAY"
    LOAM = "LOAM"
    SILT = "SILT"
    PEAT = "PEAT"
    CHALK = "CHALK"


class SoilProfile(AuditableModel, Base):
    """
    Soil composition and nutrient profile for a Field.

    Domain rules (enforced at service layer):
    - A Field may have at most one SoilProfile (enforced by UNIQUE on field_id).
    - ``ph`` must be in the range [0, 14].
    - ``organic_matter``, ``nitrogen``, ``phosphorus``, ``potassium`` must be
      non-negative; values are rejected at the service layer before persistence.
    """

    __tablename__ = "soil_profiles"

    # ── Foreign key ───────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id"),
        nullable=False,
        unique=True,  # enforces the one-to-one cardinality at DB level
        index=True,
        comment="Parent field this soil profile belongs to (one-to-one)",
    )

    # ── Soil classification ───────────────────────────────────────────────────
    soil_type: Mapped[SoilType] = mapped_column(
        Enum(SoilType, name="soil_type", create_constraint=True),
        nullable=False,
        comment="Dominant soil texture classification",
    )

    # ── Chemistry ─────────────────────────────────────────────────────────────
    ph: Mapped[float | None] = mapped_column(
        Numeric(precision=4, scale=2),
        nullable=True,
        comment="Soil pH on the 0–14 scale; 7.0 is neutral",
    )
    organic_matter: Mapped[float | None] = mapped_column(
        Numeric(precision=6, scale=3),
        nullable=True,
        comment="Organic matter content as a percentage by weight (e.g. 3.500 = 3.5%)",
    )

    # ── Macronutrients (mg/kg ≡ ppm) ─────────────────────────────────────────
    nitrogen: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=4),
        nullable=True,
        comment="Total nitrogen concentration in mg/kg (ppm)",
    )
    phosphorus: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=4),
        nullable=True,
        comment="Available phosphorus concentration in mg/kg (ppm)",
    )
    potassium: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=4),
        nullable=True,
        comment="Available potassium concentration in mg/kg (ppm)",
    )

    # ── Physical properties (P1 — Yield Prediction) ──────────────────────────
    soil_depth_cm: Mapped[float | None] = mapped_column(
        Numeric(precision=6, scale=2),
        nullable=True,
        comment="Effective rooting zone depth in centimetres",
    )
    cation_exchange_capacity_meq: Mapped[float | None] = mapped_column(
        Numeric(precision=8, scale=4),
        nullable=True,
        comment="Cation exchange capacity in meq/100g; indicates soil nutrient retention",
    )

    # ── Agronomic notes ───────────────────────────────────────────────────────
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text agronomist observations or lab report references",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="soil_profile")

    def __repr__(self) -> str:
        return (
            f"<SoilProfile id={self.id}"
            f" field_id={self.field_id}"
            f" soil_type={self.soil_type.value}"
            f" ph={self.ph}>"
        )
