"""
Farm ORM model.

Represents a physical agricultural farm entity.  A Farm is the top-level
aggregate root in the AGRIFLOW-AI domain hierarchy:

    Farm → Field → Crop

Latitude / longitude are stored as NUMERIC rather than FLOAT to avoid
IEEE-754 floating-point drift when persisting and comparing coordinates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class Farm(AuditableModel, Base):
    __tablename__ = "farms"

    # ── Identity ──────────────────────────────────────────────────────────────
    farm_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Short human-readable identifier, e.g. FARM-001",
    )
    farm_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name of the farm",
    )
    owner_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full name of the farm owner or managing entity",
    )

    # ── Location ──────────────────────────────────────────────────────────────
    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Country where the farm is located",
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="State or province",
    )
    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Nearest city or municipality",
    )
    latitude: Mapped[float] = mapped_column(
        Numeric(precision=9, scale=6),
        nullable=False,
        comment="WGS-84 latitude — range [-90, 90]",
    )
    longitude: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=6),
        nullable=False,
        comment="WGS-84 longitude — range [-180, 180]",
    )

    # ── Agronomic metadata ────────────────────────────────────────────────────
    total_area_hectares: Mapped[float] = mapped_column(
        Numeric(precision=12, scale=4),
        nullable=False,
        comment="Total farm area in hectares (4 d.p. ≈ 1 m² resolution)",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Soft-delete flag; inactive farms are retained for historical data",
    )

    fields: Mapped[list[Field]] = relationship(
    back_populates="farm",
    cascade="all, delete-orphan",
)

    def __repr__(self) -> str:
        return f"<Farm id={self.id} code={self.farm_code!r} name={self.farm_name!r}>"
