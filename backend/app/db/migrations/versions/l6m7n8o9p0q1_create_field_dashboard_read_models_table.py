"""create field_dashboard_read_models table

Phase 15 slice 2 — CQRS dashboard read models (ADR-008).

Revision ID: l6m7n8o9p0q1
Revises: k5l6m7n8o9p0
Create Date: 2026-10-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "l6m7n8o9p0q1"
down_revision: str = "k5l6m7n8o9p0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_dashboard_read_models",
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
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=255), nullable=False),
        sa.Column("open_alerts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_alerts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_recommendations_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("feature_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feature_snapshot_as_of", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "kpi_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("projection_version", sa.String(length=16), nullable=False, server_default="v1"),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("field_id", name="uq_field_dashboard_read_models_field_id"),
    )
    op.create_index(
        "ix_field_dashboard_read_models_field_id",
        "field_dashboard_read_models",
        ["field_id"],
    )
    op.create_index(
        "ix_field_dashboard_read_models_farm_id",
        "field_dashboard_read_models",
        ["farm_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_field_dashboard_read_models_farm_id", table_name="field_dashboard_read_models")
    op.drop_index("ix_field_dashboard_read_models_field_id", table_name="field_dashboard_read_models")
    op.drop_table("field_dashboard_read_models")
