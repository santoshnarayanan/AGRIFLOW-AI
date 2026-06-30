"""create continuous aggregates

Revision ID: e5f6a7b8c9d0
Revises: d4f5e6a7b8c9
Create Date: 2026-06-29

Phase 12 — Step 3B: TimescaleDB Continuous Aggregate Implementation

Purpose
-------
Create all eight approved continuous aggregates and register tiered refresh
policies (T1–T4), implementing ADR-004 exactly.

Governing Document
------------------
docs/adr/ADR-004-timescaledb-continuous-aggregate-strategy.md (Approved v1.0)

Decision Register References
-----------------------------
- P12-D012 — Continuous Aggregate Strategy

Rollout Sequence (ADR-004 §4)
------------------------------
Phase 1: ca_sensor_hourly, ca_sensor_daily, ca_weather_daily, ca_satellite_daily
Phase 2: ca_weather_weekly, ca_irrigation_monthly
Phase 3: ca_disease_weekly, ca_yield_seasonal

Scope Constraints
-----------------
This migration ONLY implements what is authorised by ADR-004:
  - NO hypertable changes
  - NO compression policy changes
  - NO retention policies
  - NO repository changes
  - NO service changes
  - NO API changes
  - NO SQLAlchemy model changes

TimescaleDB Continuous Aggregate Object Type (critical implementation note)
---------------------------------------------------------------------------
Although continuous aggregates are created with CREATE MATERIALIZED VIEW ...
WITH (timescaledb.continuous), TimescaleDB does NOT store them as PostgreSQL
materialized views internally. In pg_class, their relkind is 'v' (VIEW), not
'm' (MATERIALIZED VIEW). Confirmed on TimescaleDB 2.28.1 / PostgreSQL 17.10:

    SELECT relkind FROM pg_class WHERE relname = '<ca_name>';
    -- returns 'v', not 'm'

    SELECT COUNT(*) FROM pg_matviews WHERE matviewname = '<ca_name>';
    -- returns 0

    SELECT COUNT(*) FROM pg_views WHERE viewname = '<ca_name>';
    -- returns 1

Consequence: COMMENT ON MATERIALIZED VIEW raises WrongObjectTypeError (42809)
because PostgreSQL's native catalog lookup strictly checks relkind = 'm'.
The correct DDL for commenting is: COMMENT ON VIEW <ca_name> IS '...';

DROP MATERIALIZED VIEW remains correct for downgrade — TimescaleDB intercepts
this DDL specifically for continuous aggregates and enforces it via a HINT:
"Use DROP MATERIALIZED VIEW to drop a continuous aggregate."

This is intentional TimescaleDB design confirmed in timescale/timescaledb#5194.

Implementation Assumptions (documented in Step 3B report)
---------------------------------------------------------
- ca_sensor_daily sources raw sensor_readings (not hierarchical from ca_sensor_hourly).
- ca_yield_seasonal uses INTERVAL '90 days' time_bucket as a fixed crop-season proxy.
- ca_yield_seasonal T4 event-driven refresh is approximated with a daily policy and
  a 365-day start_offset representing the full-season lookback window.
- ca_weather_weekly frost_day_count counts frost-flagged observations per week;
  at one-observation-per-day granularity this equals frost-day count.

Downgrade Governance
--------------------
remove_continuous_aggregate_policy() on each aggregate, then DROP MATERIALIZED VIEW.
Hypertables, compression settings, and raw data are preserved.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4f5e6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (view_name, start_offset, end_offset, schedule_interval)
# Values are authoritative per ADR-004 §6 — do not modify without ADR amendment.
_REFRESH_POLICIES: list[tuple[str, str, str, str]] = [
    # T1 — Near-real-time
    ("ca_sensor_hourly", "3 days", "1 hour", "15 minutes"),
    # T2 — Hourly
    ("ca_sensor_daily", "7 days", "1 day", "1 hour"),
    ("ca_weather_daily", "7 days", "1 day", "1 hour"),
    # T3 — Daily (per-domain start_offset per ADR-004 §6 late-arrival table)
    # ca_weather_weekly: ADR-004 specified 7 days (aligned with weather late-arrival risk),
    # but TimescaleDB requires start_offset - end_offset >= 2 * bucket_width.
    # For a 1-week bucket: min window = 14 days; 7 days - 1 day = 6 days < 14 days → FAILS.
    # Corrected to 21 days (3 × bucket_width): window = 20 days ≥ 14 days. ✅
    # Three weekly buckets cover the ADR-004 7-day late-arrival allowance with margin.
    ("ca_weather_weekly", "21 days", "1 day", "1 day"),
    ("ca_satellite_daily", "30 days", "1 day", "1 day"),
    ("ca_irrigation_monthly", "90 days", "1 day", "1 day"),
    ("ca_disease_weekly", "60 days", "1 day", "1 day"),
    # T4 — Event-driven (daily schedule; full-season start_offset — see module docstring)
    ("ca_yield_seasonal", "365 days", "1 day", "1 day"),
]

# Creation order matches ADR-004 rollout phases 1 → 3.
_AGGREGATE_VIEWS: list[str] = [
    "ca_sensor_hourly",
    "ca_sensor_daily",
    "ca_weather_daily",
    "ca_satellite_daily",
    "ca_weather_weekly",
    "ca_irrigation_monthly",
    "ca_disease_weekly",
    "ca_yield_seasonal",
]

_CONTINUOUS_AGGREGATE_DDLS: dict[str, str] = {
    # Phase 1 — sensor_readings (T1/T2)
    "ca_sensor_hourly": """
        CREATE MATERIALIZED VIEW ca_sensor_hourly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 hour', recorded_at) AS bucket,
            field_id,
            sensor_type,
            AVG(sensor_value) AS avg_sensor_value,
            MIN(sensor_value) AS min_sensor_value,
            MAX(sensor_value) AS max_sensor_value,
            COUNT(*) AS reading_count
        FROM sensor_readings
        GROUP BY bucket, field_id, sensor_type
        WITH NO DATA
    """,
    "ca_sensor_daily": """
        CREATE MATERIALIZED VIEW ca_sensor_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 day', recorded_at) AS bucket,
            field_id,
            sensor_type,
            AVG(sensor_value) AS avg_sensor_value,
            MIN(sensor_value) AS min_sensor_value,
            MAX(sensor_value) AS max_sensor_value,
            STDDEV(sensor_value) AS stddev_sensor_value,
            COUNT(*) AS reading_count
        FROM sensor_readings
        GROUP BY bucket, field_id, sensor_type
        WITH NO DATA
    """,
    # Phase 1 — weather_records (T2)
    "ca_weather_daily": """
        CREATE MATERIALIZED VIEW ca_weather_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 day', recorded_at) AS bucket,
            field_id,
            AVG(temperature_c) AS avg_temperature_c,
            MIN(COALESCE(temperature_min_c, temperature_c)) AS min_temperature_c,
            MAX(COALESCE(temperature_max_c, temperature_c)) AS max_temperature_c,
            SUM(rainfall_mm) AS total_rainfall_mm,
            AVG(humidity_percent) AS avg_humidity_percent,
            SUM(COALESCE(solar_radiation_wm2, 0)) AS total_solar_radiation_wm2
        FROM weather_records
        GROUP BY bucket, field_id
        WITH NO DATA
    """,
    # Phase 1 — satellite_observations (T3)
    "ca_satellite_daily": """
        CREATE MATERIALIZED VIEW ca_satellite_daily
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 day', observed_at) AS bucket,
            field_id,
            spectral_index,
            AVG(index_value) AS avg_index_value,
            MIN(index_value) AS min_index_value,
            MAX(index_value) AS max_index_value,
            AVG(cloud_cover_percent) AS avg_cloud_cover_percent
        FROM satellite_observations
        GROUP BY bucket, field_id, spectral_index
        WITH NO DATA
    """,
    # Phase 2 — weather_records weekly (T3)
    "ca_weather_weekly": """
        CREATE MATERIALIZED VIEW ca_weather_weekly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 week', recorded_at) AS bucket,
            field_id,
            SUM(rainfall_mm) AS total_rainfall_mm,
            AVG(temperature_c) AS avg_temperature_c,
            SUM(
                CASE
                    WHEN COALESCE(temperature_min_c, temperature_c) <= 0 THEN 1
                    ELSE 0
                END
            ) AS frost_day_count
        FROM weather_records
        GROUP BY bucket, field_id
        WITH NO DATA
    """,
    # Phase 2 — irrigation_events monthly (T3)
    "ca_irrigation_monthly": """
        CREATE MATERIALIZED VIEW ca_irrigation_monthly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 month', started_at) AS bucket,
            field_id,
            irrigation_method,
            SUM(water_volume_liters) AS total_water_volume_liters,
            COUNT(*) AS event_count,
            SUM(duration_minutes) AS total_duration_minutes
        FROM irrigation_events
        GROUP BY bucket, field_id, irrigation_method
        WITH NO DATA
    """,
    # Phase 3 — disease_observations weekly (T3)
    "ca_disease_weekly": """
        CREATE MATERIALIZED VIEW ca_disease_weekly
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 week', observed_at) AS bucket,
            field_id,
            crop_id,
            MAX(severity) AS max_severity,
            COUNT(*) AS observation_count,
            AVG(affected_area_percent) AS avg_affected_area_percent
        FROM disease_observations
        GROUP BY bucket, field_id, crop_id
        WITH NO DATA
    """,
    # Phase 3 — yield_records seasonal (T4)
    "ca_yield_seasonal": """
        CREATE MATERIALIZED VIEW ca_yield_seasonal
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '90 days', recorded_at) AS bucket,
            field_id,
            crop_id,
            AVG(yield_value_tons_ha) AS avg_yield_value_tons_ha,
            MAX(yield_value_tons_ha) AS max_yield_value_tons_ha,
            COUNT(*) AS harvest_event_count
        FROM yield_records
        GROUP BY bucket, field_id, crop_id
        WITH NO DATA
    """,
}

_AGGREGATE_COMMENTS: dict[str, str] = {
    "ca_sensor_hourly": (
        "ADR-004 Phase 1 / T1. Hourly sensor rollups by (field_id, sensor_type). "
        "Metrics: AVG/MIN/MAX/COUNT of sensor_value. Source: sensor_readings."
    ),
    "ca_sensor_daily": (
        "ADR-004 Phase 1 / T2. Daily sensor rollups by (field_id, sensor_type). "
        "Metrics: AVG/MIN/MAX/STDDEV/COUNT of sensor_value. Source: sensor_readings."
    ),
    "ca_weather_daily": (
        "ADR-004 Phase 1 / T2. Daily weather summary by field_id. "
        "Metrics: temperature AVG/MIN/MAX, rainfall SUM, humidity AVG, solar SUM. "
        "Source: weather_records."
    ),
    "ca_satellite_daily": (
        "ADR-004 Phase 1 / T3. Daily spectral index rollups by (field_id, spectral_index). "
        "Metrics: AVG/MIN/MAX index_value, AVG cloud_cover_percent. "
        "Source: satellite_observations."
    ),
    "ca_weather_weekly": (
        "ADR-004 Phase 2 / T3. Weekly weather rollups by field_id. "
        "Metrics: rainfall SUM, temperature AVG, frost_day_count. "
        "Source: weather_records."
    ),
    "ca_irrigation_monthly": (
        "ADR-004 Phase 2 / T3. Monthly irrigation rollups by (field_id, irrigation_method). "
        "Metrics: water volume SUM, event COUNT, duration SUM. "
        "Source: irrigation_events."
    ),
    "ca_disease_weekly": (
        "ADR-004 Phase 3 / T3. Weekly disease rollups by (field_id, crop_id). "
        "Metrics: MAX severity, observation COUNT, AVG affected_area_percent. "
        "Source: disease_observations."
    ),
    "ca_yield_seasonal": (
        "ADR-004 Phase 3 / T4. Seasonal yield rollups by (field_id, crop_id). "
        "90-day time_bucket as crop-season proxy. "
        "Metrics: AVG/MAX yield_value_tons_ha, harvest event COUNT. "
        "Source: yield_records."
    ),
}


def _create_continuous_aggregate(view_name: str) -> None:
    """Create one continuous aggregate and attach a comment.

    CREATE MATERIALIZED VIEW ... WITH (timescaledb.continuous) is the correct
    creation DDL; TimescaleDB intercepts it and registers the CA.

    Despite the MATERIALIZED VIEW creation syntax, TimescaleDB stores CAs as
    regular VIEWs (pg_class.relkind = 'v').  COMMENT ON MATERIALIZED VIEW
    therefore raises WrongObjectTypeError (42809) because PostgreSQL's catalog
    lookup strictly requires relkind = 'm'.  COMMENT ON VIEW is the correct
    form and works because the CA object is relkind = 'v'.
    """
    op.execute(_CONTINUOUS_AGGREGATE_DDLS[view_name].strip())
    comment = _AGGREGATE_COMMENTS[view_name].replace("'", "''")
    op.execute(f"COMMENT ON VIEW {view_name} IS '{comment}';")


def _add_refresh_policy(
    view_name: str, start_offset: str, end_offset: str, schedule_interval: str
) -> None:
    """Register (or replace) a continuous aggregate refresh policy."""
    op.execute(
        f"SELECT remove_continuous_aggregate_policy('{view_name}', if_exists => true);"
    )
    op.execute(
        f"""
        SELECT add_continuous_aggregate_policy(
            '{view_name}',
            start_offset => INTERVAL '{start_offset}',
            end_offset => INTERVAL '{end_offset}',
            schedule_interval => INTERVAL '{schedule_interval}'
        );
        """
    )


def _remove_refresh_policy(view_name: str) -> None:
    """Remove refresh policy before dropping the continuous aggregate."""
    op.execute(
        f"SELECT remove_continuous_aggregate_policy('{view_name}', if_exists => true);"
    )


def _drop_continuous_aggregate(view_name: str) -> None:
    """Drop one continuous aggregate materialized view."""
    op.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view_name} CASCADE;")


def upgrade() -> None:
    """Phase 12 Step 3B: Create eight continuous aggregates per ADR-004."""
    for view_name in _AGGREGATE_VIEWS:
        _create_continuous_aggregate(view_name)

    for view_name, start_offset, end_offset, schedule_interval in _REFRESH_POLICIES:
        _add_refresh_policy(view_name, start_offset, end_offset, schedule_interval)


def downgrade() -> None:
    """Remove refresh policies then drop all continuous aggregates."""
    for view_name in reversed(_AGGREGATE_VIEWS):
        _remove_refresh_policy(view_name)
        _drop_continuous_aggregate(view_name)
