"""create sensor_readings table

Revision ID: a8f3d1b6e924
Revises: f3a8c1d9e047
Create Date: 2026-06-18 20:00:00.000000

Creates the sensor_readings table — AGRIFLOW-AI's first telemetry domain.
SensorReading extends the Field domain as an append-only time-series:

    Farm → Field → Crop
                ↘ SoilProfile      (one-to-one)
                ↘ WeatherRecord    (one-to-many)
                ↘ SensorReading    (one-to-many, append-only)

Notable DDL decisions
---------------------
- ``sensor_type`` is created as a named PostgreSQL ENUM type before the table
  so that the column definition can reference it by name.  The type is dropped
  explicitly in ``downgrade`` because PostgreSQL does NOT automatically drop
  named enum types when the owning table is removed.
- ``sensor_value`` is stored as DOUBLE PRECISION (64-bit IEEE 754) to preserve
  full IoT telemetry resolution.  NUMERIC(precision, scale) is intentionally
  avoided: sensor ADC outputs and floating-point units (mV, µS/cm, lux) require
  the 15–17 significant decimal digits DOUBLE PRECISION provides, without the
  overhead of arbitrary-precision arithmetic.
- ``field_id`` carries ON DELETE CASCADE so that deleting a Field in a single
  statement removes all its sensor readings atomically, consistent with the
  SQLAlchemy ``cascade="all, delete-orphan"`` declared on the ORM relationship.
- Five indexes cover the dominant telemetry query patterns:
    1. ix_sensor_readings_field_id                — "all readings for a field"
    2. ix_sensor_readings_sensor_type             — "all readings of a type"
    3. ix_sensor_readings_recorded_at             — "readings in a time window"
    4. ix_sensor_readings_field_id_recorded_at    — "field readings in a range"
    5. ix_sensor_readings_sensor_type_recorded_at — "typed readings in a range"
  Indexes 4 and 5 are the primary compound access patterns for telemetry
  dashboards and AI feature pipelines.
- This migration is structurally forward-compatible with TimescaleDB hypertable
  promotion (partition by ``recorded_at``) and Cassandra migration (partition
  by ``field_id``, cluster by ``recorded_at``).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a8f3d1b6e924"
down_revision: Union[str, None] = "f3a8c1d9e047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# postgresql.ENUM (not sa.Enum) is used here intentionally.
#
# sa.Enum._copy() — called internally by op.create_table() when the type is
# cloned into the temporary Table object — does not forward create_type=False
# in SQLAlchemy 2.0.x.  The copy is constructed with the default
# create_type=True, which registers a before_create DDL listener and causes a
# second "CREATE TYPE sensor_type" to be emitted, colliding with the explicit
# creation below.
#
# postgresql.ENUM handles _set_table() and _copy() correctly: create_type=False
# is preserved through the copy and no DDL listener is registered.  The type
# lifecycle is managed entirely by the explicit .create() / .drop() calls.
sensor_type_enum = postgresql.ENUM(
    "SOIL_MOISTURE",
    "SOIL_TEMPERATURE",
    "AIR_TEMPERATURE",
    "AIR_HUMIDITY",
    "LIGHT_INTENSITY",
    "LEAF_WETNESS",
    "ELECTRICAL_CONDUCTIVITY",
    "SOIL_SALINITY",
    "WATER_LEVEL",
    "BATTERY_STATUS",
    "DEVICE_HEALTH",
    name="sensor_type",
    create_type=False,
)


def upgrade() -> None:
    # ── 1. Create the PostgreSQL ENUM type ────────────────────────────────────
    # Must exist before the table that references it.  PostgreSQL will NOT drop
    # this type automatically when the table is removed, so downgrade() handles
    # it explicitly via .drop() to leave no orphan types in the schema.
    #
    # .create() is used instead of op.execute(sa.text("CREATE TYPE ...")) so
    # that the lifecycle is owned entirely by the sensor_type_enum object.
    # create_type=False on the object ensures op.create_table() below does NOT
    # emit a second CREATE TYPE when the type is attached to the table column.
    sensor_type_enum.create(op.get_bind(), checkfirst=False)

    # ── 2. Create the sensor_readings table ───────────────────────────────────
    op.create_table(
        "sensor_readings",
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
            comment="Parent field that owns this sensor reading",
        ),
        # ── Sensor classification ─────────────────────────────────────────────
        sa.Column(
            "sensor_type",
            sensor_type_enum,
            nullable=False,
            comment="Physical quantity measured by the sensor",
        ),
        # ── Measurement ───────────────────────────────────────────────────────
        sa.Column(
            "sensor_value",
            sa.Double(),
            nullable=False,
            comment=(
                "Raw numeric value recorded by the sensor; stored as PostgreSQL "
                "DOUBLE PRECISION to preserve full IoT telemetry resolution"
            ),
        ),
        sa.Column(
            "unit",
            sa.String(50),
            nullable=False,
            comment=(
                "SI or industry-standard unit for the recorded value "
                "(e.g. '%', '°C', 'lux', 'dS/m', 'mm', 'V')"
            ),
        ),
        # ── Observation timestamp ─────────────────────────────────────────────
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Timezone-aware timestamp when the sensor captured this reading",
        ),
        # ── Metadata ──────────────────────────────────────────────────────────
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Free-text annotations or anomaly flags from the ingestion pipeline",
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
            name="fk_sensor_readings_field_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sensor_readings"),
    )

    # ── 3. Individual B-tree indexes ──────────────────────────────────────────
    # Each covers a single-column predicate: "all readings for a field",
    # "all readings of a sensor type", "readings within a time window".
    op.create_index(
        op.f("ix_sensor_readings_field_id"),
        "sensor_readings",
        ["field_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sensor_readings_sensor_type"),
        "sensor_readings",
        ["sensor_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sensor_readings_recorded_at"),
        "sensor_readings",
        ["recorded_at"],
        unique=False,
    )

    # ── 4. Compound B-tree indexes ────────────────────────────────────────────
    # Primary access patterns for telemetry dashboards and AI feature pipelines.
    op.create_index(
        "ix_sensor_readings_field_id_recorded_at",
        "sensor_readings",
        ["field_id", "recorded_at"],
        unique=False,
    )
    op.create_index(
        "ix_sensor_readings_sensor_type_recorded_at",
        "sensor_readings",
        ["sensor_type", "recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    # Reverse order: compound indexes → individual indexes → table → enum type.
    # ForeignKeyConstraint and PrimaryKeyConstraint are dropped automatically
    # when the table is removed.

    # ── Compound indexes ──────────────────────────────────────────────────────
    op.drop_index(
        "ix_sensor_readings_sensor_type_recorded_at",
        table_name="sensor_readings",
    )
    op.drop_index(
        "ix_sensor_readings_field_id_recorded_at",
        table_name="sensor_readings",
    )

    # ── Individual indexes ────────────────────────────────────────────────────
    op.drop_index(
        op.f("ix_sensor_readings_recorded_at"),
        table_name="sensor_readings",
    )
    op.drop_index(
        op.f("ix_sensor_readings_sensor_type"),
        table_name="sensor_readings",
    )
    op.drop_index(
        op.f("ix_sensor_readings_field_id"),
        table_name="sensor_readings",
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.drop_table("sensor_readings")

    # ── Enum type ─────────────────────────────────────────────────────────────
    # PostgreSQL retains named enum types after the owning table is dropped;
    # explicit removal is required to leave no orphan types in the schema.
    # .drop() is symmetric with .create() above — the object manages its own
    # full lifecycle, matching how upgrade() created it.
    sensor_type_enum.drop(op.get_bind(), checkfirst=False)
