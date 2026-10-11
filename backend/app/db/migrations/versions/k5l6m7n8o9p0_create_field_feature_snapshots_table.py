"""create field_feature_snapshots table

Phase 15 — AI Feature Store snapshot persistence (ADR-007).

Revision ID: k5l6m7n8o9p0
Revises: j4k5l6m7n8o9
Create Date: 2026-10-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "k5l6m7n8o9p0"
down_revision: str = "j4k5l6m7n8o9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_feature_snapshots",
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
        sa.Column("crop_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("registry_version", sa.String(length=32), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("features", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("materialization_notes", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crop_id"], ["crops.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "field_id",
            "registry_version",
            "as_of",
            name="uq_field_feature_snapshots_field_version_as_of",
        ),
    )
    op.create_index(
        "ix_field_feature_snapshots_field_id",
        "field_feature_snapshots",
        ["field_id"],
    )
    op.create_index(
        "ix_field_feature_snapshots_crop_id",
        "field_feature_snapshots",
        ["crop_id"],
    )
    op.create_index(
        "ix_field_feature_snapshots_field_id_as_of",
        "field_feature_snapshots",
        ["field_id", "as_of"],
    )


def downgrade() -> None:
    op.drop_index("ix_field_feature_snapshots_field_id_as_of", table_name="field_feature_snapshots")
    op.drop_index("ix_field_feature_snapshots_crop_id", table_name="field_feature_snapshots")
    op.drop_index("ix_field_feature_snapshots_field_id", table_name="field_feature_snapshots")
    op.drop_table("field_feature_snapshots")
