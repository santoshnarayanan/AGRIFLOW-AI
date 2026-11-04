"""convert farms.farm_code to a system-generated UUID

farm_code was a client-supplied VARCHAR(50) (e.g. "FARM-001"). It becomes a
UUID that the platform generates, so users no longer enter it.

Existing values that are already valid UUID text are cast in place; any other
value (e.g. "AGRIFLOW-DEMO", "FARM-001") is replaced with a fresh
gen_random_uuid(). The unique constraint and index on farm_code are preserved
by ALTER COLUMN ... TYPE.

Downgrade casts the UUIDs back to text; the original human-readable codes are
not recoverable.

Revision ID: o9p0q1r2s3t4
Revises: n8o9p0q1r2s3
Create Date: 2026-11-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "o9p0q1r2s3t4"
down_revision: str = "n8o9p0q1r2s3"
branch_labels = None
depends_on = None

_UUID_REGEX = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"


def upgrade() -> None:
    # gen_random_uuid() is built into PostgreSQL 13+; no extension required.
    op.execute(
        f"""
        ALTER TABLE farms
        ALTER COLUMN farm_code TYPE UUID
        USING (
            CASE
                WHEN farm_code ~ '{_UUID_REGEX}' THEN farm_code::uuid
                ELSE gen_random_uuid()
            END
        )
        """
    )
    op.alter_column(
        "farms",
        "farm_code",
        server_default=sa.text("gen_random_uuid()"),
        comment="System-generated UUID business key (auto-assigned on insert)",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column("farms", "farm_code", server_default=None, existing_nullable=False)
    op.execute(
        "ALTER TABLE farms ALTER COLUMN farm_code TYPE VARCHAR(50) USING farm_code::text"
    )
    op.alter_column(
        "farms",
        "farm_code",
        comment="Short human-readable identifier, e.g. FARM-001",
        existing_type=sa.String(50),
        existing_nullable=False,
    )
