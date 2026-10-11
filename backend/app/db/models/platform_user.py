"""Platform operator accounts for JWT authentication (Phase 15)."""

from __future__ import annotations

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import PlatformRole
from app.db.base import AuditableModel, Base


class PlatformUser(AuditableModel, Base):
    __tablename__ = "platform_users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[PlatformRole] = mapped_column(
        Enum(PlatformRole, name="platform_role", create_constraint=True, create_type=False),
        nullable=False,
        default=PlatformRole.OPERATOR,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
