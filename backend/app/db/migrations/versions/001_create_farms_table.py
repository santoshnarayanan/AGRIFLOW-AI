"""create farms table

Revision ID: 8f3a1c2d9e04
Revises:
Create Date: 2026-06-06 16:42:00.000000

Creates the farms table as the foundational entity in the AGRIFLOW-AI
domain hierarchy (Farm → Field → Crop).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8f3a1c2d9e04"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "farms",
        # ── Primary key ───────────────────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID v4 primary key",
        ),
        # ── Identity ──────────────────────────────────────────────────────────
        sa.Column(
            "farm_code",
            sa.String(50),
            nullable=False,
            comment="Short human-readable identifier, e.g. FARM-001",
        ),
        sa.Column(
            "farm_name",
            sa.String(255),
            nullable=False,
            comment="Display name of the farm",
        ),
        sa.Column(
            "owner_name",
            sa.String(255),
            nullable=False,
            comment="Full name of the farm owner or managing entity",
        ),
        # ── Location ──────────────────────────────────────────────────────────
        sa.Column(
            "country",
            sa.String(100),
            nullable=False,
            comment="Country where the farm is located",
        ),
        sa.Column(
            "state",
            sa.String(100),
            nullable=False,
            comment="State or province",
        ),
        sa.Column(
            "city",
            sa.String(100),
            nullable=False,
            comment="Nearest city or municipality",
        ),
        sa.Column(
            "latitude",
            sa.Numeric(precision=9, scale=6),
            nullable=False,
            comment="WGS-84 latitude — range [-90, 90]",
        ),
        sa.Column(
            "longitude",
            sa.Numeric(precision=10, scale=6),
            nullable=False,
            comment="WGS-84 longitude — range [-180, 180]",
        ),
        # ── Agronomic metadata ────────────────────────────────────────────────
        sa.Column(
            "total_area_hectares",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            comment="Total farm area in hectares (4 d.p. ≈ 1 m² resolution)",
        ),
        # ── Status ────────────────────────────────────────────────────────────
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Soft-delete flag; inactive farms are retained for historical data",
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
    op.create_unique_constraint("uq_farms_farm_code", "farms", ["farm_code"])
    op.create_index("ix_farms_farm_code", "farms", ["farm_code"])


def downgrade() -> None:
    op.drop_index("ix_farms_farm_code", table_name="farms")
    op.drop_constraint("uq_farms_farm_code", "farms", type_="unique")
    op.drop_table("farms")
