"""
Field feature snapshot ORM model.

Persists versioned ML feature vectors materialised from TimescaleDB continuous
aggregates (ADR-004) and approved raw hypertables. Snapshots are immutable
once written; new materialisation runs create new rows.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.crop import Crop
    from app.db.models.field import Field


class FieldFeatureSnapshot(AuditableModel, Base):
    __tablename__ = "field_feature_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "field_id",
            "registry_version",
            "as_of",
            name="uq_field_feature_snapshots_field_version_as_of",
        ),
        Index("ix_field_feature_snapshots_field_id_as_of", "field_id", "as_of"),
    )

    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional crop scope for yield/disease features",
    )
    registry_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Feature registry version (e.g. cdd-v1.0.0)",
    )
    as_of: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Reference instant for rolling window calculations",
    )
    features: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Map of feature_id -> {value, unit, source, window_days, available}",
    )
    materialization_notes: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="Operator-facing notes (e.g. missing field area for irrigation depth)",
    )

    field: Mapped[Field] = relationship("Field", back_populates="feature_snapshots")
    crop: Mapped[Crop | None] = relationship("Crop")
