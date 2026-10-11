"""Digital Twin — materialized field state document (Phase 15 slice 3)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.field import Field


class FieldDigitalTwinState(AuditableModel, Base):
    __tablename__ = "field_digital_twin_states"

    __table_args__ = (UniqueConstraint("field_id", name="uq_field_digital_twin_states_field_id"),)

    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state_version: Mapped[str] = mapped_column(String(16), nullable=False, default="twin-v1")
    state_document: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    synchronized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    field: Mapped[Field] = relationship("Field", back_populates="digital_twin_state")
