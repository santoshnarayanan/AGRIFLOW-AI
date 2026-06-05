"""
SQLAlchemy declarative base with shared timestamp + UUID primary key mixin.

All domain models must inherit from Base.  Alembic's env.py imports Base.metadata
so autogenerate picks up every model registered against it.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""


class TimestampMixin:
    """
    Adds server-side created_at / updated_at columns to any model.

    Uses PostgreSQL NOW() so timestamps are set by the DB, not the app layer,
    avoiding clock-skew issues in distributed deployments.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """UUID v4 primary key — avoids sequential ID enumeration in public APIs."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class AuditableModel(UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Convenience base combining UUID PK + timestamps.

    Use as:
        class MyModel(AuditableModel, Base):
            __tablename__ = "my_table"
    """
