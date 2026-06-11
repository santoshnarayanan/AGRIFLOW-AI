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
    from app.db.models.farm import Farm


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

    farm: Mapped[Farm] = relationship(back_populates="fields")
    crops: Mapped[list[Crop]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Field id={self.id} name={self.name!r} farm_id={self.farm_id}>"
