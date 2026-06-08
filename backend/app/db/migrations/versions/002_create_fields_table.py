"""create fields table

Revision ID: 3b7e9f1a2c85
Revises: 8f3a1c2d9e04
Create Date: 2026-06-08 14:45:00.000000

Creates the fields table — the second level in the AGRIFLOW-AI domain
hierarchy (Farm → Field → Crop).  Each field belongs to exactly one farm
via a non-nullable foreign key.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "3b7e9f1a2c85"
down_revision: Union[str, None] = "8f3a1c2d9e04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fields",
        # ── Primary key ───────────────────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID v4 primary key",
        ),
        # ── Foreign key ───────────────────────────────────────────────────────
        sa.Column(
            "farm_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("farms.id"),
            nullable=False,
            comment="Parent farm that owns this field",
        ),
        # ── Identity ──────────────────────────────────────────────────────────
        sa.Column(
            "name",
            sa.String(255),
            nullable=False,
            comment="Display name of the field",
        ),
        # ── Agronomic metadata ────────────────────────────────────────────────
        sa.Column(
            "area_hectares",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment="Field area in hectares",
        ),
        sa.Column(
            "soil_type",
            sa.String(50),
            nullable=True,
            comment="Dominant soil classification for the field",
        ),
        # ── Location ──────────────────────────────────────────────────────────
        sa.Column(
            "latitude",
            sa.Numeric(precision=10, scale=6),
            nullable=True,
            comment="WGS-84 latitude — range [-90, 90]",
        ),
        sa.Column(
            "longitude",
            sa.Numeric(precision=10, scale=6),
            nullable=True,
            comment="WGS-84 longitude — range [-180, 180]",
        ),
        # ── Audit timestamps (server-side) ────────────────────────────────────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Row creation timestamp (set by PostgreSQL)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Row last-updated timestamp (set by PostgreSQL)",
        ),
    )

    # ── Constraints & indexes ─────────────────────────────────────────────────
    op.create_index("ix_fields_farm_id", "fields", ["farm_id"])


def downgrade() -> None:
    op.drop_index("ix_fields_farm_id", table_name="fields")
    op.drop_table("fields")
