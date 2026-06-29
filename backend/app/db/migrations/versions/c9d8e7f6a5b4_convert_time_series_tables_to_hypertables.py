"""convert time-series tables to TimescaleDB hypertables

Revision ID: c9d8e7f6a5b4
Revises: f1e2d3c4b5a6
Create Date: 2026-06-29

Phase 12 — Step 1E-B: Hypertable Conversion Implementation

Purpose
-------
Convert the six approved time-series domain tables to TimescaleDB hypertables,
implementing the Composite Primary Key strategy mandated by ADR-002.

Governing Document
------------------
ADR-002-hypertable-primary-key-conversion-strategy.md (Approved 2026-06-29)

Decision Register References
-----------------------------
- P12-D007 — Hypertable Primary Key Strategy (Composite PK Strategy A)
- P12-D008 — Hypertable Candidate Tables & Conversion Sequence
- P12-D009 — Hypertable Chunk Interval Strategy

Tables Converted (ADR-002 §Approved Decisions)
----------------------------------------------
P1 — Critical:
  - sensor_readings        : partition key = recorded_at,  chunk = 7 days
  - weather_records        : partition key = recorded_at,  chunk = 7 days
  - satellite_observations : partition key = observed_at,  chunk = 7 days

P2 — High:
  - irrigation_events      : partition key = started_at,   chunk = 1 month
  - yield_records          : partition key = recorded_at,  chunk = 3 months

P3 — Standard:
  - disease_observations   : partition key = observed_at,  chunk = 1 month

Additional Change (ADR-002 §Approved Decisions — weather_records compound index gap)
-------------------------------------------------------------------------------------
Adds the compound index ``ix_weather_records_field_id_recorded_at`` which was
identified as missing from the original weather_records migration (004).  All other
Field-anchored time-series tables carry this compound index; weather_records did not.

Tables NOT Modified (ADR-002 §Relational Tables)
-------------------------------------------------
farms, fields, crops, soil_profiles — remain standard PostgreSQL relations permanently.

Per-Table PK Migration Pattern
-------------------------------
For each of the six tables:

    Step 1: DROP CONSTRAINT pk_<table>   (UUID-only PRIMARY KEY)
    Step 2: ADD CONSTRAINT pk_<table> PRIMARY KEY (id, <time_col>)   (composite)
    Step 3: SELECT create_hypertable('<table>', '<time_col>',
                migrate_data     => TRUE,
                if_not_exists    => TRUE,
                chunk_time_interval => INTERVAL '<approved_interval>');

Scope Constraints
-----------------
This migration ONLY implements what is authorised by ADR-002:
  - NO compression policies
  - NO continuous aggregates
  - NO retention policies
  - NO repository changes
  - NO service changes
  - NO API changes
  - NO space partitioning

Downgrade Governance
--------------------
The downgrade() function is GOVERNANCE RESTRICTED.

Permitted use:  development environments ONLY, BEFORE any data has been inserted
                into the six hypertable tables (i.e., before production data
                ingestion begins).

After data ingestion, executing this downgrade would require table recreation and
data re-loading.  The approved rollback path for non-empty environments is Tier 2
pg_dump restore per P12-D005.

The downgrade implementation removes each hypertable's TimescaleDB catalog
registration from _timescaledb_catalog for empty tables, then reverts the
composite PK to UUID-only.  It does NOT drop or recreate the physical tables.
This technique is safe for empty hypertables (no chunks exist).

References
----------
- docs/adr/ADR-002-hypertable-primary-key-conversion-strategy.md
- PHASE12_DECISION_REGISTER.md  v1.3 — P12-D007, P12-D008, P12-D009
- PHASE12_STEP1EA_HYPERTABLE_ARCHITECTURE_ASSESSMENT.md — §6, §11
- PHASE12_STEP1D_EXTENSION_ENABLEMENT_REPORT.md
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c9d8e7f6a5b4"
down_revision: Union[str, None] = "f1e2d3c4b5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Approved conversion table (ADR-002 §Approved Decisions) ─────────────────
# (table_name, time_column, chunk_interval)
_HYPERTABLE_CONVERSIONS: list[tuple[str, str, str]] = [
    # P1 — Critical
    ("sensor_readings",        "recorded_at", "7 days"),
    ("weather_records",        "recorded_at", "7 days"),
    ("satellite_observations", "observed_at", "7 days"),
    # P2 — High
    ("irrigation_events",      "started_at",  "1 month"),
    ("yield_records",          "recorded_at", "3 months"),
    # P3 — Standard
    ("disease_observations",   "observed_at", "1 month"),
]


def upgrade() -> None:
    """Phase 12 Step 1E-B: Convert six time-series tables to TimescaleDB hypertables.

    Per ADR-002, for each table:
      1. Drop the UUID-only PRIMARY KEY constraint.
      2. Add the composite PRIMARY KEY (id, <time_col>).
      3. Call create_hypertable() with the approved chunk interval.

    Additionally adds the missing compound index on weather_records
    (field_id, recorded_at) identified in Step 1E-A §9.3.
    """
    # ── P1 Critical: sensor_readings ─────────────────────────────────────────
    op.drop_constraint("pk_sensor_readings", "sensor_readings", type_="primary")
    op.create_primary_key(
        "pk_sensor_readings", "sensor_readings", ["id", "recorded_at"]
    )
    op.execute(
        "SELECT create_hypertable('sensor_readings', 'recorded_at', "
        "migrate_data => TRUE, "
        "if_not_exists => TRUE, "
        "chunk_time_interval => INTERVAL '7 days');"
    )

    # ── P1 Critical: weather_records ─────────────────────────────────────────
    op.drop_constraint("pk_weather_records", "weather_records", type_="primary")
    op.create_primary_key(
        "pk_weather_records", "weather_records", ["id", "recorded_at"]
    )
    op.execute(
        "SELECT create_hypertable('weather_records', 'recorded_at', "
        "migrate_data => TRUE, "
        "if_not_exists => TRUE, "
        "chunk_time_interval => INTERVAL '7 days');"
    )
    # Add the missing compound index identified in Step 1E-A §9.3
    op.create_index(
        "ix_weather_records_field_id_recorded_at",
        "weather_records",
        ["field_id", "recorded_at"],
        unique=False,
    )

    # ── P1 Critical: satellite_observations ───────────────────────────────────
    op.drop_constraint(
        "pk_satellite_observations", "satellite_observations", type_="primary"
    )
    op.create_primary_key(
        "pk_satellite_observations",
        "satellite_observations",
        ["id", "observed_at"],
    )
    op.execute(
        "SELECT create_hypertable('satellite_observations', 'observed_at', "
        "migrate_data => TRUE, "
        "if_not_exists => TRUE, "
        "chunk_time_interval => INTERVAL '7 days');"
    )

    # ── P2 High: irrigation_events ────────────────────────────────────────────
    op.drop_constraint("pk_irrigation_events", "irrigation_events", type_="primary")
    op.create_primary_key(
        "pk_irrigation_events", "irrigation_events", ["id", "started_at"]
    )
    op.execute(
        "SELECT create_hypertable('irrigation_events', 'started_at', "
        "migrate_data => TRUE, "
        "if_not_exists => TRUE, "
        "chunk_time_interval => INTERVAL '1 month');"
    )

    # ── P2 High: yield_records ────────────────────────────────────────────────
    op.drop_constraint("pk_yield_records", "yield_records", type_="primary")
    op.create_primary_key(
        "pk_yield_records", "yield_records", ["id", "recorded_at"]
    )
    op.execute(
        "SELECT create_hypertable('yield_records', 'recorded_at', "
        "migrate_data => TRUE, "
        "if_not_exists => TRUE, "
        "chunk_time_interval => INTERVAL '3 months');"
    )

    # ── P3 Standard: disease_observations ────────────────────────────────────
    op.drop_constraint(
        "pk_disease_observations", "disease_observations", type_="primary"
    )
    op.create_primary_key(
        "pk_disease_observations",
        "disease_observations",
        ["id", "observed_at"],
    )
    op.execute(
        "SELECT create_hypertable('disease_observations', 'observed_at', "
        "migrate_data => TRUE, "
        "if_not_exists => TRUE, "
        "chunk_time_interval => INTERVAL '1 month');"
    )


def downgrade() -> None:
    """Revert the six hypertable conversions and restore UUID-only primary keys.

    GOVERNANCE RESTRICTED
    ─────────────────────
    This downgrade is valid ONLY in development environments BEFORE any data
    has been inserted into the six time-series tables.

    After data ingestion has begun, TimescaleDB stores data in immutable chunk
    tables.  Removing the hypertable catalog registration at that point would
    leave orphaned chunk tables and corrupt the database.  The approved rollback
    path for non-empty environments is Tier 2 pg_dump restore (P12-D005).

    Technical Approach
    ──────────────────
    TimescaleDB 2.x does not provide a public function to "un-hypertable" a
    table without dropping it.  For empty hypertables (no chunks have been
    created because no data has been inserted), the TimescaleDB catalog
    registration consists of exactly two rows:
      - _timescaledb_catalog.dimension  (the time partition dimension)
      - _timescaledb_catalog.hypertable (the main hypertable registration)

    Deleting these rows removes the hypertable designation while leaving the
    physical PostgreSQL table intact with all its data (empty).  After
    catalog cleanup, the composite PK constraint is dropped and the original
    UUID-only PK is restored.

    The implementation verifies that each table is empty before proceeding.
    If any table contains rows, the downgrade aborts with an error directing
    the operator to use Tier 2 pg_dump restore.
    """
    # ── Safety gate: verify all six tables are empty ──────────────────────────
    # Non-empty tables require Tier 2 pg_dump restore per P12-D005.
    op.execute(
        """
        DO $$
        DECLARE
            t   text;
            cnt bigint;
        BEGIN
            FOREACH t IN ARRAY ARRAY[
                'sensor_readings',
                'weather_records',
                'satellite_observations',
                'irrigation_events',
                'yield_records',
                'disease_observations'
            ]
            LOOP
                EXECUTE format('SELECT COUNT(*) FROM %I', t) INTO cnt;
                IF cnt > 0 THEN
                    RAISE EXCEPTION
                        'Step 1E-B downgrade blocked: table % contains % rows. '
                        'Use Tier 2 pg_dump restore per P12-D005 (ADR-002).',
                        t, cnt;
                END IF;
            END LOOP;
        END;
        $$;
        """
    )

    # ── Remove weather_records compound index added in this migration ─────────
    op.drop_index(
        "ix_weather_records_field_id_recorded_at",
        table_name="weather_records",
    )

    # ── Revert each hypertable (reverse priority order) ───────────────────────
    # For each table:
    #   1. Remove TimescaleDB catalog entries (empty table — no chunks exist)
    #   2. Drop composite primary key
    #   3. Restore UUID-only primary key
    for table, time_col, _ in reversed(_HYPERTABLE_CONVERSIONS):
        # Step 1: Remove TimescaleDB catalog registration for empty hypertable.
        # Deletes dimension rows first (FK child), then the hypertable row (FK parent).
        # ONLY safe for tables with 0 rows (verified by safety gate above).
        op.execute(
            f"""
            DO $$
            DECLARE
                ht_id integer;
            BEGIN
                SELECT id INTO ht_id
                FROM _timescaledb_catalog.hypertable
                WHERE schema_name = 'public' AND table_name = '{table}';

                IF ht_id IS NOT NULL THEN
                    -- Remove dimension registration (partition key metadata)
                    DELETE FROM _timescaledb_catalog.dimension
                    WHERE hypertable_id = ht_id;

                    -- Remove main hypertable registration
                    DELETE FROM _timescaledb_catalog.hypertable
                    WHERE id = ht_id;
                END IF;
            END;
            $$;
            """
        )

        # Step 2: Drop composite primary key (id, time_col)
        op.drop_constraint(f"pk_{table}", table, type_="primary")

        # Step 3: Restore UUID-only primary key (original Step 1D state)
        op.create_primary_key(f"pk_{table}", table, ["id"])
