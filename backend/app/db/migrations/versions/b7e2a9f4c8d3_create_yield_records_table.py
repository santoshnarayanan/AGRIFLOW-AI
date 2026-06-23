"""create yield_records table

Revision ID: b7e2a9f4c8d3
Revises: 235a51cdf901
Create Date: 2026-06-23 12:00:00.000000

Creates the yield_records table — Phase 9 of AGRIFLOW-AI.
YieldRecord is the first grandchild domain:

    Farm → Field → Crop → YieldRecord

Unlike IrrigationEvent (anchored directly on Field), YieldRecord anchors on
Crop because yield is a per-crop-cycle measurement, not a per-field point-in-
time event.  ``field_id`` is denormalized onto the table (ADR-009-02) to
enable field-scoped queries without a JOIN through ``crops``.

Notable DDL decisions
---------------------
- One named PostgreSQL ENUM type is created before the table:
    ``yield_measurement_method`` — measurement provenance
      (MANUAL_SCALE, COMBINE_MONITOR, YIELD_MAP, REMOTE_SENSING,
       CROP_CUT, LABORATORY_ANALYSIS, ESTIMATED)
  This type is dropped explicitly in downgrade() because PostgreSQL does NOT
  automatically drop named enum types when the owning table is removed.
- postgresql.ENUM with create_type=False is used so that op.create_table()
  does not emit a second CREATE TYPE.  The type lifecycle is owned entirely
  by the .create() / .drop() calls — see migration 235a51cdf901 for the
  full rationale (sa.Enum._copy() does not forward create_type=False in
  SQLAlchemy 2.0.x).
- ``recorded_at`` is the primary time key: TIMESTAMPTZ NOT NULL, individually
  indexed, and included in the compound index with crop_id.  It is the
  partition key for a future TimescaleDB hypertable promotion.
- Two FK constraints with ON DELETE CASCADE are declared:
    fk_yield_records_crop_id  — primary domain anchor
    fk_yield_records_field_id — denormalized path for field-scoped queries
  Both cascade on delete so yield records are removed when either the crop
  cycle or the field is deleted.
- Four indexes cover the dominant access patterns:
    1. ix_yield_records_crop_id             — "all records for a crop cycle"
    2. ix_yield_records_field_id            — "all records for a field (direct)"
    3. ix_yield_records_recorded_at         — "records in a time window"
    4. ix_yield_records_crop_id_recorded_at — "crop records in time order"
  Index 4 is the primary compound access pattern for yield history queries
  and the Phase 12 Yield Prediction Engine feature pipeline.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b7e2a9f4c8d3"
down_revision: Union[str, None] = "235a51cdf901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# postgresql.ENUM (not sa.Enum) is used here intentionally.
# sa.Enum._copy() — called internally by op.create_table() when the type is
# cloned into the temporary Table object — does not forward create_type=False
# in SQLAlchemy 2.0.x, causing a DuplicateObjectError on fresh databases.
# postgresql.ENUM preserves create_type=False through _set_table() and _copy()
# so op.create_table() emits no DDL for this type.
yield_measurement_method_enum = postgresql.ENUM(
    "MANUAL_SCALE",
    "COMBINE_MONITOR",
    "YIELD_MAP",
    "REMOTE_SENSING",
    "CROP_CUT",
    "LABORATORY_ANALYSIS",
    "ESTIMATED",
    name="yield_measurement_method",
    create_type=False,
)


def upgrade() -> None:
    # ── 1. Create PostgreSQL ENUM type ────────────────────────────────────────
    # Must exist before the table that references it.  create_type=False on
    # the enum object above ensures op.create_table() does not emit a second
    # CREATE TYPE.
    yield_measurement_method_enum.create(op.get_bind(), checkfirst=True)

    # ── 2. Create the yield_records table ─────────────────────────────────────
    op.create_table(
        "yield_records",
        # ── Primary key ───────────────────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="UUID v4 primary key",
        ),
        # ── Foreign keys ──────────────────────────────────────────────────────
        sa.Column(
            "crop_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment=(
                "Crop cycle this yield observation belongs to; "
                "primary domain anchor — yield is per crop cycle, not per field point-in-time"
            ),
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment=(
                "Denormalized field FK (ADR-009-02); "
                "enables direct field-scoped queries without a JOIN through crops"
            ),
        ),
        # ── Observation timestamp ─────────────────────────────────────────────
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment=(
                "Timezone-aware timestamp when this yield measurement was taken; "
                "serves as the primary time key and TimescaleDB partition key"
            ),
        ),
        # ── Primary measurement ───────────────────────────────────────────────
        sa.Column(
            "yield_value_tons_ha",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
            comment="Measured yield in tonnes per hectare; must be >= 0",
        ),
        # ── Measurement classification ────────────────────────────────────────
        sa.Column(
            "measurement_method",
            yield_measurement_method_enum,
            nullable=False,
            comment=(
                "Method used to obtain this measurement; "
                "acts as a data quality weight in the Phase 12 Yield Prediction Engine"
            ),
        ),
        # ── Optional quality attributes ───────────────────────────────────────
        sa.Column(
            "area_harvested_ha",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment=(
                "Sub-field harvested area in hectares; "
                "must be > 0 if supplied — zero area is agronomically invalid"
            ),
        ),
        sa.Column(
            "moisture_content_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
            comment="Grain moisture at harvest as a percentage; valid range [0, 100]",
        ),
        sa.Column(
            "test_weight_kg_hl",
            sa.Numeric(precision=6, scale=3),
            nullable=True,
            comment="Grain bulk density (test weight) in kg per hectolitre; must be > 0 if supplied",
        ),
        sa.Column(
            "quality_grade",
            sa.String(50),
            nullable=True,
            comment="Free-form quality classification, e.g. 'Grade 1', 'Feed Grade'",
        ),
        # ── Metadata ──────────────────────────────────────────────────────────
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Operator free-text annotations, e.g. equipment calibration notes or field conditions",
        ),
        # ── Audit timestamps (server-side) ────────────────────────────────────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row creation timestamp (set by PostgreSQL)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row last-updated timestamp (set by PostgreSQL)",
        ),
        # ── Table-level constraints ───────────────────────────────────────────
        sa.ForeignKeyConstraint(
            ["crop_id"],
            ["crops.id"],
            name="fk_yield_records_crop_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
            name="fk_yield_records_field_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_yield_records"),
    )

    # ── 3. Indexes ────────────────────────────────────────────────────────────
    # Three individual indexes support single-predicate queries.
    # The compound index is the primary access pattern for crop yield history
    # and the Phase 12 AI feature pipeline.
    op.create_index(
        op.f("ix_yield_records_crop_id"),
        "yield_records",
        ["crop_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_yield_records_field_id"),
        "yield_records",
        ["field_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_yield_records_recorded_at"),
        "yield_records",
        ["recorded_at"],
        unique=False,
    )
    op.create_index(
        "ix_yield_records_crop_id_recorded_at",
        "yield_records",
        ["crop_id", "recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    # Reverse order: compound index → individual indexes → table → enum type.
    # ForeignKeyConstraint and PrimaryKeyConstraint are dropped automatically
    # when the table is removed.

    # ── Compound index ────────────────────────────────────────────────────────
    op.drop_index(
        "ix_yield_records_crop_id_recorded_at",
        table_name="yield_records",
    )

    # ── Individual indexes ────────────────────────────────────────────────────
    op.drop_index(
        op.f("ix_yield_records_recorded_at"),
        table_name="yield_records",
    )
    op.drop_index(
        op.f("ix_yield_records_field_id"),
        table_name="yield_records",
    )
    op.drop_index(
        op.f("ix_yield_records_crop_id"),
        table_name="yield_records",
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.drop_table("yield_records")

    # ── Enum type ─────────────────────────────────────────────────────────────
    # PostgreSQL retains named enum types after the owning table is dropped;
    # explicit removal is required to leave no orphan types in the schema.
    # .drop() is symmetric with .create() in upgrade().
    yield_measurement_method_enum.drop(op.get_bind(), checkfirst=False)
