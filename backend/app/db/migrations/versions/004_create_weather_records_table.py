"""create weather_records table

Revision ID: 7d4f2a9b1e63
Revises: 13aabbe35d51
Create Date: 2026-06-15 21:00:00.000000

Creates the weather_records table — a time-series of meteorological
observations attached to a Field.  WeatherRecord extends the AGRIFLOW-AI
domain hierarchy:

    Farm → Field → Crop
                ↘ SoilProfile    (one-to-one)
                ↘ WeatherRecord  (one-to-many, time-series)

Notable DDL decisions
---------------------
- ``field_id`` and ``recorded_at`` each carry independent B-tree indexes to
  support the two primary query patterns: "all readings for a given field"
  and "readings within a time window".  A composite index is intentionally
  omitted at this stage; it can be added in a follow-up migration once
  real query plans are observed.
- ``rainfall_mm`` and ``wind_speed_kmh`` default to 0 at the database level
  so partially populated rows (e.g. from sensors that do not measure every
  metric) remain valid without requiring application-side padding.
- ``data_source`` defaults to 'MANUAL' to distinguish operator-entered
  readings from automated ingestion pipelines (IoT sensors, weather APIs).
- ForeignKeyConstraint is declared explicitly as a table-level constraint
  (not inline) to allow Alembic autogenerate to diff it reliably.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7d4f2a9b1e63"
down_revision: Union[str, None] = "13aabbe35d51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weather_records",
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
            comment="Parent field that owns this weather observation",
        ),
        # ── Observation timestamp ─────────────────────────────────────────────
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Timestamp when the weather observation was recorded",
        ),
        # ── Atmospheric measurements ──────────────────────────────────────────
        sa.Column(
            "temperature_c",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            comment="Air temperature in degrees Celsius",
        ),
        sa.Column(
            "humidity_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            comment="Relative humidity percentage",
        ),
        sa.Column(
            "rainfall_mm",
            sa.Numeric(precision=8, scale=2),
            nullable=False,
            server_default="0",
            comment="Rainfall in millimeters",
        ),
        sa.Column(
            "wind_speed_kmh",
            sa.Numeric(precision=6, scale=2),
            nullable=False,
            server_default="0",
            comment="Wind speed in kilometers per hour",
        ),
        # ── Provenance ────────────────────────────────────────────────────────
        sa.Column(
            "data_source",
            sa.String(50),
            nullable=False,
            server_default="MANUAL",
            comment="Origin of weather data",
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
            name="fk_weather_records_field_id",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_weather_records"),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index(
        op.f("ix_weather_records_field_id"),
        "weather_records",
        ["field_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_weather_records_recorded_at"),
        "weather_records",
        ["recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    # Reverse order: indexes first, then table.
    # The ForeignKeyConstraint and PrimaryKeyConstraint are dropped
    # automatically when the table is removed.
    op.drop_index(
        op.f("ix_weather_records_recorded_at"),
        table_name="weather_records",
    )
    op.drop_index(
        op.f("ix_weather_records_field_id"),
        table_name="weather_records",
    )
    op.drop_table("weather_records")
