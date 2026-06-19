"""create irrigation_events table

Revision ID: 235a51cdf901
Revises: a8f3d1b6e924
Create Date: 2026-06-19 19:56:58.908566

Creates the irrigation_events table — Phase 8 of AGRIFLOW-AI.
IrrigationEvent is the first agricultural intervention domain:

    Farm → Field → Crop
                ↘ SoilProfile       (one-to-one)
                ↘ WeatherRecord     (one-to-many)
                ↘ SensorReading     (one-to-many, append-only)
                ↘ IrrigationEvent   (one-to-many)

Notable DDL decisions
---------------------
- Two named PostgreSQL ENUM types are created before the table:
    ``irrigation_method`` — delivery method (DRIP, SPRINKLER, FLOOD, …)
    ``water_source``      — origin of water (GROUNDWATER, MUNICIPAL, …)
  Both are dropped explicitly in downgrade() because PostgreSQL does NOT
  automatically drop named enum types when the owning table is removed.
- postgresql.ENUM with create_type=False is used for both enums so that
  op.create_table() does not emit a second CREATE TYPE.  The type lifecycle
  is owned entirely by the .create() / .drop() calls (see migration 006 for
  the rationale — sa.Enum._copy() does not forward create_type=False in
  SQLAlchemy 2.0.x).
- Unlike SensorReading (append-only), IrrigationEvent is mutable: it
  represents a human-logged management action that may need correction.
  A full CRUD surface (including PATCH) is therefore provided by the API.
- ``started_at`` is the primary time key: TIMESTAMPTZ NOT NULL, individually
  indexed, and included in the compound index with field_id.  It is the
  partition key for a future TimescaleDB hypertable promotion.
- Three indexes cover the dominant access patterns:
    1. ix_irrigation_events_field_id             — "all events for a field"
    2. ix_irrigation_events_started_at           — "events in a time window"
    3. ix_irrigation_events_field_id_started_at  — "field events in a range"
  Index 3 is the primary compound access pattern for irrigation history
  queries and AI feature pipelines.
- field_id carries ON DELETE CASCADE consistent with all other Field children.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "235a51cdf901"
down_revision: Union[str, None] = "a8f3d1b6e924"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# postgresql.ENUM (not sa.Enum) is used here intentionally.
# sa.Enum._copy() — called internally by op.create_table() when the type is
# cloned into the temporary Table object — does not forward create_type=False
# in SQLAlchemy 2.0.x, causing a DuplicateObjectError on fresh databases.
# postgresql.ENUM preserves create_type=False through _set_table() and _copy()
# so op.create_table() emits no DDL for these types.
irrigation_method_enum = postgresql.ENUM(
    "DRIP",
    "SPRINKLER",
    "FLOOD",
    "FURROW",
    "CENTER_PIVOT",
    "SUBSURFACE",
    "MANUAL",
    "AUTOMATED",
    name="irrigation_method",
    create_type=False,
)

water_source_enum = postgresql.ENUM(
    "GROUNDWATER",
    "SURFACE_WATER",
    "RAINWATER",
    "MUNICIPAL",
    "RECYCLED_WATER",
    name="water_source",
    create_type=False,
)


def upgrade() -> None:
    # ── 1. Create PostgreSQL ENUM types ───────────────────────────────────────
    # Must exist before the table that references them.  create_type=False on
    # the enum objects above ensures op.create_table() does not emit a second
    # CREATE TYPE for either enum.
    irrigation_method_enum.create(op.get_bind(), checkfirst=True)
    water_source_enum.create(op.get_bind(), checkfirst=True)

    # ── 2. Create the irrigation_events table ─────────────────────────────────
    op.create_table(
        "irrigation_events",
        # ── Primary key ───────────────────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="UUID v4 primary key",
        ),
        # ── Foreign key ───────────────────────────────────────────────────────
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Parent field on which this irrigation event was applied",
        ),
        # ── Event window ──────────────────────────────────────────────────────
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment=(
                "Timezone-aware timestamp when irrigation began; "
                "serves as the primary time key and TimescaleDB partition key"
            ),
        ),
        sa.Column(
            "ended_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment=(
                "Timezone-aware timestamp when irrigation ended; "
                "optional — may be omitted when only duration is known"
            ),
        ),
        # ── Quantification ────────────────────────────────────────────────────
        sa.Column(
            "duration_minutes",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
            comment=(
                "Duration of the irrigation event in minutes; "
                "independent of ended_at — either or both may be supplied"
            ),
        ),
        sa.Column(
            "water_volume_liters",
            sa.Numeric(precision=10, scale=3),
            nullable=True,
            comment=(
                "Total water volume applied in litres; "
                "nullable for non-metered systems — "
                "recording an event without volume is preferable to no record"
            ),
        ),
        # ── Classification ────────────────────────────────────────────────────
        sa.Column(
            "irrigation_method",
            irrigation_method_enum,
            nullable=False,
            comment=(
                "Delivery method used to apply water; "
                "drives FAO-56 application efficiency coefficients in AI models"
            ),
        ),
        sa.Column(
            "water_source",
            water_source_enum,
            nullable=True,
            comment="Origin of the water applied; used in water management analytics",
        ),
        # ── Metadata ──────────────────────────────────────────────────────────
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Operator free-text annotations, e.g. equipment issues or field observations",
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
            ["field_id"],
            ["fields.id"],
            name="fk_irrigation_events_field_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_irrigation_events"),
    )

    # ── 3. Indexes ────────────────────────────────────────────────────────────
    # Individual indexes support single-predicate queries; the compound index
    # is the primary access pattern for irrigation history and AI features.
    op.create_index(
        op.f("ix_irrigation_events_field_id"),
        "irrigation_events",
        ["field_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_irrigation_events_started_at"),
        "irrigation_events",
        ["started_at"],
        unique=False,
    )
    op.create_index(
        "ix_irrigation_events_field_id_started_at",
        "irrigation_events",
        ["field_id", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    # Reverse order: compound index → individual indexes → table → enum types.
    # ForeignKeyConstraint and PrimaryKeyConstraint are dropped automatically
    # when the table is removed.

    # ── Compound index ────────────────────────────────────────────────────────
    op.drop_index(
        "ix_irrigation_events_field_id_started_at",
        table_name="irrigation_events",
    )

    # ── Individual indexes ────────────────────────────────────────────────────
    op.drop_index(
        op.f("ix_irrigation_events_started_at"),
        table_name="irrigation_events",
    )
    op.drop_index(
        op.f("ix_irrigation_events_field_id"),
        table_name="irrigation_events",
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.drop_table("irrigation_events")

    # ── Enum types ────────────────────────────────────────────────────────────
    # PostgreSQL retains named enum types after the owning table is dropped;
    # explicit removal is required to leave no orphan types in the schema.
    # .drop() is symmetric with .create() in upgrade().
    water_source_enum.drop(op.get_bind(), checkfirst=False)
    irrigation_method_enum.drop(op.get_bind(), checkfirst=False)
