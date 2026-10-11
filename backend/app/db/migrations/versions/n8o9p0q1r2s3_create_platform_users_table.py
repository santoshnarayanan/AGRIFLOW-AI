"""create platform_users table

Phase 15 slice 5 — JWT/RBAC operator accounts.

Revision ID: n8o9p0q1r2s3
Revises: m7n8o9p0q1r2
Create Date: 2026-10-11
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "n8o9p0q1r2s3"
down_revision: str = "m7n8o9p0q1r2"
branch_labels = None
depends_on = None

_BOOTSTRAP_ADMIN_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
_BOOTSTRAP_ADMIN_HASH = (
    "$2b$12$6WEY3AaxMAhp7RVXDfuLYeaSG8NLQtshETz1SlvB50iIfDy8pKGha"
)


def upgrade() -> None:
    platform_role_enum = postgresql.ENUM(
        "VIEWER",
        "OPERATOR",
        "ADMIN",
        name="platform_role",
    )
    platform_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "platform_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "VIEWER",
                "OPERATOR",
                "ADMIN",
                name="platform_role",
                create_type=False,
            ),
            nullable=False,
            server_default="OPERATOR",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("email", name="uq_platform_users_email"),
    )
    op.create_index("ix_platform_users_email", "platform_users", ["email"], unique=True)

    op.execute(
        sa.text(
            """
            INSERT INTO platform_users (id, email, password_hash, role, is_active)
            VALUES (
                :id,
                'admin@agriflow.local',
                :password_hash,
                'ADMIN',
                true
            )
            ON CONFLICT (email) DO NOTHING
            """
        ).bindparams(id=_BOOTSTRAP_ADMIN_ID, password_hash=_BOOTSTRAP_ADMIN_HASH)
    )


def downgrade() -> None:
    op.drop_index("ix_platform_users_email", table_name="platform_users")
    op.drop_table("platform_users")
    postgresql.ENUM(name="platform_role").drop(op.get_bind(), checkfirst=True)
