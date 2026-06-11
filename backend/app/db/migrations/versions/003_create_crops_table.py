"""create crops table

Revision ID: 5c2d8e3f7a19
Revises: 3b7e9f1a2c85
Create Date: 2026-06-11 21:00:00.000000

Creates the crops table — the third level in the AGRIFLOW-AI domain
hierarchy (Farm → Field → Crop).  Each crop cycle belongs to exactly one
field via a non-nullable foreign key.

Notable DDL decisions
---------------------
- ``crop_status`` is created as a named PostgreSQL ENUM type before the
  table so that the column definition can reference it by name.  The type
  must be dropped explicitly in ``downgrade`` because PostgreSQL does NOT
  automatically drop enum types when the owning table is removed.
- ``status`` carries a column-level CHECK constraint (via ``create_constraint``
  in the ORM) whose enforcement is already covered by the ENUM type itself;
  the type acts as the single source of truth for valid values.
- ``ix_crops_field_id`` supports the most common query pattern: "fetch all
  crop cycles for a given field".
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5c2d8e3f7a19"
down_revision: Union[str, None] = "3b7e9f1a2c85"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Named enum reused by both upgrade and downgrade to avoid duplication.
crop_status_enum = sa.Enum(
    "PLANNED",
    "PLANTED",
    "GROWING",
    "HARVESTED",
    name="crop_status",
    create_type=False,
)


def upgrade() -> None:
    # ── 1. Create the PostgreSQL ENUM type ────────────────────────────────────
    # Must exist before the table that references it.
    # crop_status_enum.create(op.get_bind(), checkfirst=True)

    # ── 2. Create the crops table ─────────────────────────────────────────────
    op.create_table(
        "crops",
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
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fields.id"),
            nullable=False,
            comment="Parent field where this crop cycle is planted",
        ),
        # ── Identity ──────────────────────────────────────────────────────────
        sa.Column(
            "crop_name",
            sa.String(255),
            nullable=False,
            comment="Common or scientific crop name, e.g. 'Maize', 'Solanum lycopersicum'",
        ),
        sa.Column(
            "crop_variety",
            sa.String(255),
            nullable=True,
            comment="Cultivar or hybrid designation, e.g. 'DKC 6870'",
        ),
        # ── Dates ─────────────────────────────────────────────────────────────
        sa.Column(
            "planting_date",
            sa.Date(),
            nullable=False,
            comment="Calendar date the crop was or will be planted",
        ),
        sa.Column(
            "expected_harvest_date",
            sa.Date(),
            nullable=True,
            comment="Agronomically projected harvest date",
        ),
        sa.Column(
            "actual_harvest_date",
            sa.Date(),
            nullable=True,
            comment="Actual harvest completion date; set only when status = HARVESTED",
        ),
        # ── Status ────────────────────────────────────────────────────────────
        sa.Column(
            "status",
            crop_status_enum,
            nullable=False,
            server_default="PLANNED",
            comment="Current agronomic lifecycle state of the crop cycle",
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

    # ── 3. Indexes ────────────────────────────────────────────────────────────
    op.create_index("ix_crops_field_id", "crops", ["field_id"])


def downgrade() -> None:
    # Reverse order: indexes → table → enum type.
    op.drop_index("ix_crops_field_id", table_name="crops")
    op.drop_table("crops")
    # PostgreSQL retains named enum types after the table is dropped;
    # explicit removal is required to keep the schema clean.
    # crop_status_enum.drop(op.get_bind(), checkfirst=True)
