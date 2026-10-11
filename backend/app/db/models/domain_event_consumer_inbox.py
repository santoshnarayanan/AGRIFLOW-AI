"""Consumer idempotency inbox — one row per (event_id, consumer_group) (Phase 14)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin


class DomainEventConsumerInbox(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "domain_event_consumer_inbox"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "consumer_group_id",
            name="uq_domain_event_consumer_inbox_event_group",
        ),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    consumer_group_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
