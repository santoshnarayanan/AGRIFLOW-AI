"""CQRS read model — denormalised field dashboard KPIs (Phase 15 slice 2)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class FieldDashboardReadModel(AuditableModel, Base):
    __tablename__ = "field_dashboard_read_models"

    __table_args__ = (
        UniqueConstraint("field_id", name="uq_field_dashboard_read_models_field_id"),
        Index("ix_field_dashboard_read_models_farm_id", "farm_id"),
    )

    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    open_alerts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_alerts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_recommendations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    feature_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Latest Feature Store snapshot at refresh time",
    )
    feature_snapshot_as_of: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    kpi_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Highlighted agronomic KPIs for dashboards",
    )
    projection_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    field: Mapped[Field] = relationship("Field", back_populates="dashboard_read_model")
