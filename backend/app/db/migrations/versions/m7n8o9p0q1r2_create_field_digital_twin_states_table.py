"""create field_digital_twin_states table

Phase 15 slice 3 — Digital Twin field state foundation (ADR-009).

Revision ID: m7n8o9p0q1r2
Revises: l6m7n8o9p0q1
Create Date: 2026-10-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "m7n8o9p0q1r2"
down_revision: str = "l6m7n8o9p0q1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_digital_twin_states",
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
        sa.Column("field_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state_version", sa.String(length=16), nullable=False, server_default="twin-v1"),
        sa.Column("state_document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("synchronized_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("field_id", name="uq_field_digital_twin_states_field_id"),
    )
    op.create_index(
        "ix_field_digital_twin_states_field_id",
        "field_digital_twin_states",
        ["field_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_field_digital_twin_states_field_id", table_name="field_digital_twin_states")
    op.drop_table("field_digital_twin_states")
