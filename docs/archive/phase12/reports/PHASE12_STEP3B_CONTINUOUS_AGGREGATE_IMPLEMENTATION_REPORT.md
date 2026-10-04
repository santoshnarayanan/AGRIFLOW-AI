# AGRIFLOW-AI — Phase 12 Step 3B

## TimescaleDB Continuous Aggregate Implementation Report

**Document Type:** Implementation Report  
**Version:** 1.3  
**Date:** 2026-06-30  
**Scope:** Phase 12 Step 3B — Continuous Aggregate DDL and Refresh Policy Activation; ADR-004 Implementation  
**Status:** Migration Corrected — Runtime Execution Pending  
**Author:** Senior Platform Architecture  
**Governing Document:** `docs/adr/ADR-004-timescaledb-continuous-aggregate-strategy.md` v1.0 (Approved)

---

## 1. Executive Summary

Phase 12 Step 3B completes the **implementation** of eight TimescaleDB continuous aggregates and tiered refresh policies (T1–T4) across six hypertables, as mandated by ADR-004. The Alembic migration `e5f6a7b8c9d0` has been authored and documented. **Runtime execution** (`alembic upgrade head`) is intentionally deferred — consistent with the governance-first Phase 12 workflow established in Steps 2B and 2C.

| Metric | Result |
|---|---|
| **Migration revision (authored)** | `e5f6a7b8c9d0` |
| **Prior Alembic head** | `d4f5e6a7b8c9` |
| **Target Alembic head (after runtime execution)** | `e5f6a7b8c9d0` |
| **Continuous aggregates defined** | 8 of 8 (in migration DDL) |
| **Refresh policies defined** | 8 of 8 (in migration DDL) |
| **Application layer changes** | 0 |
| **Hypertable / compression changes** | 0 |
| **Backend status** | Operational (pre-Step-3B runtime baseline) |
| **API contracts** | Unchanged |

The migration targets PostgreSQL 17.10 / TimescaleDB 2.28.1. All continuous aggregates are created `WITH NO DATA`; initial materialisation occurs via registered refresh policies after migration execution.

**Step 3C Validation** (refresh job verification, aggregation correctness against CDD v1.0.0, performance benchmarks) follows runtime migration execution.

### Pre-Migration Backup Reminder

> **⚠️ Before applying migration `e5f6a7b8c9d0`, take a full PostgreSQL backup of the `agriflow` database.**
>
> Recommended command (execute manually on the target host — **not automated by this step**):
>
> ```bash
> pg_dump -h <host> -p <port> -U <user> -Fc -f agriflow_pre_step3b_$(date +%Y%m%d).dump agriflow
> ```
>
> A backup ensures rollback to the pre-CA state without data loss if migration execution encounters unexpected TimescaleDB catalogue conflicts or refresh policy registration failures. This reminder does not authorise automatic backup execution as part of Step 3B.

---

## Implementation Execution Status

| Item | Status |
|---|---|
| Architecture Assessment (Step 3A) | ✅ Approved |
| ADR-004 | ✅ Approved |
| Alembic Migration Authored | ✅ Complete |
| Migration Corrected (direct DDL — v1.1) | ✅ Complete |
| Migration Corrected (COMMENT ON VIEW — v1.2) | ✅ Complete |
| Migration Corrected (refresh window minimum — v1.3) | ✅ Complete |
| Implementation Documentation | ✅ Complete (v1.3) |
| Runtime Migration Execution (`alembic upgrade head`) | ⏳ Pending — retry after v1.3 correction |
| Runtime Validation (Step 3C) | ⏳ Pending — after migration execution |
| Production Readiness | ⏳ Pending Step 3C |

### Development Environment Execution Strategy

AGRIFLOW-AI follows a governance-first implementation workflow. Architecture, ADRs, Alembic migrations, and implementation documentation are completed before runtime execution. Migrations accumulated during Phase 12 will be executed together when the platform team authorises runtime activation.

---

## 2. Migration Overview

### 2.1 Revision Chain

```
f1e2d3c4b5a6  enable_timescaledb_extension
        ↓
c9d8e7f6a5b4  convert_time_series_tables_to_hypertables  (ADR-002)
        ↓
d4f5e6a7b8c9  enable_hypertable_compression_policies      (ADR-003)
        ↓
e5f6a7b8c9d0  create_continuous_aggregates                (ADR-004) ← this step
```

### 2.2 Migration File

| Attribute | Value |
|---|---|
| **File** | `backend/app/db/migrations/versions/e5f6a7b8c9d0_create_continuous_aggregates.py` |
| **Revision ID** | `e5f6a7b8c9d0` |
| **Revises** | `d4f5e6a7b8c9` |
| **Transactional** | Yes — Alembic wraps `upgrade()` / `downgrade()` in a transaction |
| **DDL execution** | Direct `op.execute()` per `CREATE MATERIALIZED VIEW` (TimescaleDB best practice) |
| **Policy idempotency** | Refresh policies use remove-then-add before registration |

### 2.3 Migration Corrections History

#### v1.1 — Direct DDL execution

The initial implementation (v1.0) wrapped each `CREATE MATERIALIZED VIEW … WITH (timescaledb.continuous)` inside a `DO $$ … EXECUTE` procedural block. This was replaced with direct `op.execute()` per aggregate to allow TimescaleDB to intercept the DDL at parse/plan time. This was a correct improvement but did not resolve the runtime failure.

#### v1.2 — COMMENT ON VIEW (root cause fix)

**Runtime failure:**

```
alembic upgrade head
→ WrongObjectTypeError: "ca_sensor_hourly" is not a materialized view
→ failure on: COMMENT ON MATERIALIZED VIEW ca_sensor_hourly
→ Alembic rolled back to revision d4f5e6a7b8c9
→ timescaledb_information.continuous_aggregates: 0 rows
→ pg_matviews: 0 rows
```

**Root cause investigation:**

A minimal continuous aggregate was created directly against the live database (TimescaleDB 2.28.1 / PostgreSQL 17.10) and inspected:

```sql
CREATE MATERIALIZED VIEW _debug_ca_test
WITH (timescaledb.continuous) AS
SELECT time_bucket(INTERVAL '1 hour', recorded_at) AS bucket,
       field_id, COUNT(*) AS cnt
FROM sensor_readings GROUP BY bucket, field_id
WITH NO DATA;

SELECT relname, relkind FROM pg_class WHERE relname = '_debug_ca_test';
-- relkind = 'v'   ← VIEW, not materialized view

SELECT COUNT(*) FROM pg_matviews WHERE matviewname = '_debug_ca_test';
-- 0 rows

SELECT COUNT(*) FROM pg_views WHERE viewname = '_debug_ca_test';
-- 1 row

COMMENT ON MATERIALIZED VIEW _debug_ca_test IS 'test';
-- ERROR:  "_debug_ca_test" is not a materialized view
```

**Root cause — confirmed:** Despite using `CREATE MATERIALIZED VIEW … WITH (timescaledb.continuous)` as creation syntax, TimescaleDB 2.28.1 stores continuous aggregates in `pg_class` with `relkind = 'v'` (VIEW), **not** `relkind = 'm'` (MATERIALIZED VIEW). This is intentional TimescaleDB design, confirmed in [timescale/timescaledb issue #5194](https://github.com/timescale/timescaledb/issues/5194):

> "This is an intentional design and not a bug. We leverage the materialized view concept and API because it is a good match for continuous aggregates, but unfortunately, the internals of a materialized view object wasn't a good match for implementing continuous aggregates."

**Why `COMMENT ON MATERIALIZED VIEW` fails:** PostgreSQL's `COMMENT ON MATERIALIZED VIEW` performs a native catalog lookup that strictly requires `pg_class.relkind = 'm'`. Since TimescaleDB CAs are stored as `relkind = 'v'`, PostgreSQL raises `WrongObjectTypeError (42809)`. TimescaleDB does not intercept this DDL.

**Why `DROP MATERIALIZED VIEW` succeeds:** TimescaleDB intercepts `DROP MATERIALIZED VIEW` specifically for CAs and enforces its use — confirmed by the hint: *"Use DROP MATERIALIZED VIEW to drop a continuous aggregate."* `DROP MATERIALIZED VIEW` in the downgrade is therefore correct and must not be changed.

**Fix applied:** `COMMENT ON MATERIALIZED VIEW` → `COMMENT ON VIEW`. No other changes.

| DDL Statement | Works? | Reason |
|---|---|---|
| `CREATE MATERIALIZED VIEW … WITH (timescaledb.continuous)` | ✅ | TimescaleDB intercepts |
| `COMMENT ON VIEW <ca_name>` | ✅ | CA is `relkind='v'`; PostgreSQL accepts `COMMENT ON VIEW` |
| `DROP MATERIALIZED VIEW <ca_name>` | ✅ | TimescaleDB intercepts |
| `COMMENT ON MATERIALIZED VIEW <ca_name>` | ❌ | PostgreSQL native check requires `relkind='m'`; CA is `relkind='v'` |
| `DROP VIEW <ca_name>` | ❌ | TimescaleDB rejects with hint to use `DROP MATERIALIZED VIEW` |

**Unchanged by this correction:** All eight aggregate definitions, refresh policy tiers (T1–T4), comment text, downgrade order, and ADR-004 architecture. Only the comment DDL command was corrected.

#### v1.3 — Refresh window minimum (policy compatibility fix)

**Runtime failure after v1.2:**

```
alembic upgrade head
→ All eight continuous aggregates created successfully
→ COMMENT ON VIEW — all eight succeeded
→ InvalidParameterValueError: policy refresh window too small
→ DETAIL: The start and end offsets must cover at least two buckets.
→ Failing policy: ca_weather_weekly
```

**TimescaleDB requirement:**

`add_continuous_aggregate_policy()` requires:

```
start_offset − end_offset  ≥  2 × bucket_width
```

Only complete buckets can be materialised. The refresh window must therefore span at least two full bucket widths to guarantee at least one bucket can be recomputed.

**Full policy audit (PostgreSQL interval arithmetic — confirmed live against TimescaleDB 2.28.1):**

| Aggregate | Bucket | start_offset | end_offset | Window | Minimum (2×bucket) | Passes |
|---|---|---|---|---|---|---|
| `ca_sensor_hourly` | 1 hour | 3 days | 1 hour | 71 hours | 2 hours | ✅ |
| `ca_sensor_daily` | 1 day | 7 days | 1 day | 6 days | 2 days | ✅ |
| `ca_weather_daily` | 1 day | 7 days | 1 day | 6 days | 2 days | ✅ |
| `ca_satellite_daily` | 1 day | 30 days | 1 day | 29 days | 2 days | ✅ |
| `ca_weather_weekly` | 1 week | ~~7 days~~ → **21 days** | 1 day | ~~6 days~~ → **20 days** | 14 days | ~~❌~~ → **✅** |
| `ca_irrigation_monthly` | 1 month | 90 days | 1 day | 89 days | 2 months | ✅ |
| `ca_disease_weekly` | 1 week | 60 days | 1 day | 59 days | 14 days | ✅ |
| `ca_yield_seasonal` | 90 days | 365 days | 1 day | 364 days | 180 days | ✅ |

**Root cause for `ca_weather_weekly`:** ADR-004 §6 recorded `start_offset = 7 days` for the weather domain, derived from the late-arrival risk table. That value is correct for the daily weather aggregate (`ca_weather_daily`, 1-day bucket). When applied to `ca_weather_weekly` (1-week bucket), the window becomes `7 days − 1 day = 6 days`, which is less than the 14-day minimum (2 × 1 week).

**Why `ca_irrigation_monthly` passes:** PostgreSQL interval arithmetic evaluates `INTERVAL '89 days' ≥ INTERVAL '2 months'` as TRUE (TimescaleDB uses PostgreSQL's native `interval_cmp`, which approximates 1 month = 30 days for comparison: 89 days > 60 days). Confirmed on live database.

**Fix applied:** `ca_weather_weekly` `start_offset` changed from `7 days` to `21 days`.

- Window = 21 days − 1 day = **20 days ≥ 14 days minimum** ✅
- 21 days = 3 × 7 days — a clean multiple of the bucket width; three complete weekly buckets
- The ADR-004 late-arrival allowance for `weather_records` is 7 days. With a weekly bucket, re-processing the previous week on late data arrival requires one full bucket (7 days). 21 days provides the 2-bucket minimum (14 days) plus a full third-bucket late-arrival margin (7 days), exactly preserving the ADR-004 intent
- ADR-004 architectural intent (cover late-arriving weather data within the refresh window) is unchanged; only the minimum-valid value is adjusted for the weekly bucket width

**Unchanged by this correction:** Aggregate definitions, all other policy parameters, downgrade behaviour, and ADR-004 architecture.

### 2.4 Scope Boundaries

| In Scope | Out of Scope |
|---|---|
| `CREATE MATERIALIZED VIEW … WITH (timescaledb.continuous)` | Hypertable DDL changes |
| `add_continuous_aggregate_policy()` per ADR-004 tiers | Compression policy changes |
| `COMMENT ON MATERIALIZED VIEW` per aggregate | Retention policies (ADR-005) |
| Downgrade: policy removal → view drop | Repository / service / API changes |
| | SQLAlchemy model changes |

### 2.5 Rollout Sequence (ADR-004 §4)

The migration creates aggregates in phased order:

| Phase | Aggregates | Source Hypertables |
|---|---|---|
| **Phase 1** | `ca_sensor_hourly`, `ca_sensor_daily`, `ca_weather_daily`, `ca_satellite_daily` | `sensor_readings`, `weather_records`, `satellite_observations` |
| **Phase 2** | `ca_weather_weekly`, `ca_irrigation_monthly` | `weather_records`, `irrigation_events` |
| **Phase 3** | `ca_disease_weekly`, `ca_yield_seasonal` | `disease_observations`, `yield_records` |

---

## 3. Aggregate Implementation

All eight aggregates follow the approved naming convention `ca_{domain}_{interval}` per ADR-004 §5.

### 3.1 Phase 1 — Core Analytics

#### `ca_sensor_hourly` (T1)

| Attribute | Value |
|---|---|
| **Source** | `sensor_readings` |
| **Bucket** | `time_bucket('1 hour', recorded_at)` |
| **Grouping** | `field_id`, `sensor_type` |
| **Metrics** | `avg_sensor_value`, `min_sensor_value`, `max_sensor_value`, `reading_count` |

#### `ca_sensor_daily` (T2)

| Attribute | Value |
|---|---|
| **Source** | `sensor_readings` (raw — not hierarchical from hourly) |
| **Bucket** | `time_bucket('1 day', recorded_at)` |
| **Grouping** | `field_id`, `sensor_type` |
| **Metrics** | `avg_sensor_value`, `min_sensor_value`, `max_sensor_value`, `stddev_sensor_value`, `reading_count` |

**Implementation decision:** ADR-004 permits optional hierarchical sourcing from `ca_sensor_hourly`. This migration sources both sensor aggregates directly from `sensor_readings` to avoid refresh dependency chains and simplify Step 3C validation.

#### `ca_weather_daily` (T2)

| Attribute | Value |
|---|---|
| **Source** | `weather_records` |
| **Bucket** | `time_bucket('1 day', recorded_at)` |
| **Grouping** | `field_id` |
| **Metrics** | `avg_temperature_c`, `min_temperature_c`, `max_temperature_c`, `total_rainfall_mm`, `avg_humidity_percent`, `total_solar_radiation_wm2` |

Nullable P1 columns (`temperature_min_c`, `temperature_max_c`, `solar_radiation_wm2`) use `COALESCE` to handle partially populated CDD rows.

#### `ca_satellite_daily` (T3)

| Attribute | Value |
|---|---|
| **Source** | `satellite_observations` |
| **Bucket** | `time_bucket('1 day', observed_at)` |
| **Grouping** | `field_id`, `spectral_index` |
| **Metrics** | `avg_index_value`, `min_index_value`, `max_index_value`, `avg_cloud_cover_percent` |

### 3.2 Phase 2 — Extended Analytics

#### `ca_weather_weekly` (T3)

| Attribute | Value |
|---|---|
| **Source** | `weather_records` |
| **Bucket** | `time_bucket('1 week', recorded_at)` |
| **Grouping** | `field_id` |
| **Metrics** | `total_rainfall_mm`, `avg_temperature_c`, `frost_day_count` |

**Implementation assumption:** `frost_day_count` uses `SUM(CASE WHEN temperature_min_c <= 0 …)` over raw observations. At one-observation-per-day granularity (CDD weather pattern), this equals frost-day count. Multiple intraday observations would over-count without a hierarchical daily intermediate — acceptable for Step 3C validation scope.

#### `ca_irrigation_monthly` (T3)

| Attribute | Value |
|---|---|
| **Source** | `irrigation_events` |
| **Bucket** | `time_bucket('1 month', started_at)` |
| **Grouping** | `field_id`, `irrigation_method` |
| **Metrics** | `total_water_volume_liters`, `event_count`, `total_duration_minutes` |

### 3.3 Phase 3 — Sparse Domains

#### `ca_disease_weekly` (T3)

| Attribute | Value |
|---|---|
| **Source** | `disease_observations` |
| **Bucket** | `time_bucket('1 week', observed_at)` |
| **Grouping** | `field_id`, `crop_id` |
| **Metrics** | `max_severity`, `observation_count`, `avg_affected_area_percent` |

`MAX(severity)` operates on the ordered `disease_severity` enum (LOW → CRITICAL).

#### `ca_yield_seasonal` (T4)

| Attribute | Value |
|---|---|
| **Source** | `yield_records` |
| **Bucket** | `time_bucket('90 days', recorded_at)` |
| **Grouping** | `field_id`, `crop_id` |
| **Metrics** | `avg_yield_value_tons_ha`, `max_yield_value_tons_ha`, `harvest_event_count` |

**Implementation assumption:** ADR-004 defines interval as "1 crop season". TimescaleDB requires a fixed `time_bucket` interval; `90 days` is used as a crop-season proxy aligned with the `yield_records` hypertable chunk interval (ADR-002). Crop-calendar-aligned bucketing remains a Feature Store responsibility if finer season semantics are required.

---

## 4. Refresh Policy Implementation

### 4.1 Tier Summary

| Tier | Aggregates | `schedule_interval` | `end_offset` | `start_offset` |
|---|---|---|---|---|
| **T1** | `ca_sensor_hourly` | 15 minutes | 1 hour | 3 days |
| **T2** | `ca_sensor_daily`, `ca_weather_daily` | 1 hour | 1 day | 7 days |
| **T3** | `ca_weather_weekly` | 1 day | 1 day | 21 days |
| **T3** | `ca_satellite_daily` | 1 day | 1 day | 30 days |
| **T3** | `ca_irrigation_monthly` | 1 day | 1 day | 90 days |
| **T3** | `ca_disease_weekly` | 1 day | 1 day | 60 days |
| **T4** | `ca_yield_seasonal` | 1 day | 1 day | 365 days |

T3 `start_offset` values match ADR-004 §6 late-arrival risk table per domain.

### 4.2 T4 Implementation Assumption

ADR-004 defines T4 as "Post-harvest trigger / manual" with "Full season window" offsets. TimescaleDB `add_continuous_aggregate_policy()` requires automated schedule parameters. This migration approximates T4 intent with:

- `schedule_interval = 1 day` — daily refresh check (lowest automated cadence)
- `start_offset = 365 days` — full-season lookback window
- `end_offset = 1 day` — buffer for in-flight harvest writes

True post-harvest event triggers are an operational concern outside Alembic scope. Step 3C may validate whether this approximation meets lag requirements for sparse yield data; manual `CALL refresh_continuous_aggregate()` remains available for on-demand refresh.

### 4.3 Policy Registration Pattern

```sql
SELECT remove_continuous_aggregate_policy('ca_sensor_hourly', if_exists => true);
SELECT add_continuous_aggregate_policy(
    'ca_sensor_hourly',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '15 minutes'
);
```

Policies are registered after all materialized views are created. The remove-then-add pattern ensures idempotent re-registration.

### 4.4 Compression Synergy

All `start_offset` values for mutable hypertables exceed ADR-003 compression age thresholds:

| Hypertable | Compression After | CA `start_offset` | Margin |
|---|---|---|---|
| `satellite_observations` | 14 days | 30 days | ✅ |
| `irrigation_events` | 60 days | 90 days | ✅ |
| `disease_observations` | 60 days | 60 days | ✅ (equals threshold) |
| `yield_records` | 180 days | 365 days | ✅ |

PATCH operations within the refresh window will trigger bucket recomputation before compressed chunks become immutable for correction.

---

## 5. Rollback Strategy

### 5.1 Downgrade Path

Migration `e5f6a7b8c9d0` downgrade executes in reverse rollout order:

1. `remove_continuous_aggregate_policy()` for each aggregate (Phase 3 → Phase 1)
2. `DROP MATERIALIZED VIEW IF EXISTS <name> CASCADE` for each aggregate

### 5.2 Preserved Objects

| Object Class | Downgrade Behaviour |
|---|---|
| Six hypertables | Unchanged |
| Compression policies (ADR-003) | Unchanged |
| Compression settings per hypertable | Unchanged |
| Raw hypertable data (CDD v1.0.0) | Unchanged |
| Relational tables | Unchanged |
| Application code | Unchanged |

### 5.3 Rollback Command

```bash
cd backend && alembic downgrade d4f5e6a7b8c9
```

### 5.4 Tier 2 Recovery

If downgrade fails due to TimescaleDB catalogue corruption, restore from the pre-migration `pg_dump` backup documented in §1.

---

## 6. Runtime Verification Plan (Step 3C)

Step 3C validation executes after `alembic upgrade head`. The following checks form the verification matrix.

### 6.1 Infrastructure Checks

```sql
-- Confirm eight continuous aggregates registered
SELECT view_name, materialization_hypertable_name, compression_enabled
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;

-- Confirm eight refresh policies active
SELECT application_name, schedule_interval, config
FROM timescaledb_information.jobs
WHERE proc_name = 'policy_refresh_continuous_aggregate'
ORDER BY application_name;
```

**Expected:** 8 rows in `continuous_aggregates`; 8 refresh policy jobs.

### 6.2 Refresh Job Health

```sql
SELECT j.application_name, js.last_run_status, js.last_successful_finish,
       js.total_runs, js.total_failures
FROM timescaledb_information.jobs j
JOIN timescaledb_information.job_stats js ON j.job_id = js.job_id
WHERE j.proc_name = 'policy_refresh_continuous_aggregate';
```

**Expected:** All jobs reach `Success` within 2× their `schedule_interval` after migration.

### 6.3 Initial Materialisation

```sql
-- Trigger manual refresh for validation (optional — policies handle automatically)
CALL refresh_continuous_aggregate('ca_sensor_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('ca_sensor_daily', NULL, NULL);
-- ... repeat for all eight aggregates
```

### 6.4 Aggregation Correctness (CDD v1.0.0)

| Scenario | Validation Query Pattern | Pass Criteria |
|---|---|---|
| Hourly sensor avg | Compare `ca_sensor_hourly` vs raw `sensor_readings` for sample `(field_id, sensor_type, 24h window)` | `avg_sensor_value` within numeric tolerance |
| Daily weather summary | Compare `ca_weather_daily` vs raw `weather_records` for sample `field_id, 7d window` | Temperature and rainfall totals match |
| Daily NDVI mean | Compare `ca_satellite_daily` (NDVI) vs raw for sample field | `avg_index_value` matches |
| Weekly weather | Compare `ca_weather_weekly` rainfall SUM vs raw weekly grouping | Totals match |
| Monthly irrigation | Compare `ca_irrigation_monthly` volume SUM vs raw monthly grouping | Totals match |
| Weekly disease | Compare `ca_disease_weekly` MAX severity vs raw weekly grouping | Severity matches |
| Seasonal yield | Compare `ca_yield_seasonal` vs raw 90-day bucket grouping | Yield metrics match |

### 6.5 Incremental Refresh

1. INSERT new `sensor_readings` row within T1 refresh window.
2. Wait for T1 policy cycle (≤ 15 minutes) or call `refresh_continuous_aggregate`.
3. Confirm new bucket appears in `ca_sensor_hourly`.

### 6.6 PATCH Invalidation (Mutable Hypertables)

1. PATCH a `satellite_observations` row within 30-day `start_offset`.
2. Confirm affected `ca_satellite_daily` bucket recomputes.

### 6.7 Performance Baseline

| Query | Target |
|---|---|
| `SELECT * FROM ca_sensor_daily WHERE field_id = $1 AND bucket >= now() - interval '90 days'` | < 50 ms at CDD scale |
| `SELECT * FROM ca_weather_daily WHERE field_id = $1 AND bucket >= now() - interval '365 days'` | < 50 ms at CDD scale |

### 6.8 Application Regression

| Check | Expected |
|---|---|
| `GET /api/v1/health/live` | `200 alive` |
| Existing repository `list_by_field` queries | Unchanged behaviour |
| API response schemas | No new fields |

---

## 7. Lessons Learned

1. **Governance-first delivery remains effective.** Authoring CA DDL against an approved ADR catalogue (ADR-004) before runtime execution eliminates scope creep and ensures Step 3C has a fixed validation target.

2. **Fixed-interval bucketing limits seasonal semantics.** `ca_yield_seasonal` cannot express crop-calendar-aligned seasons natively in TimescaleDB `time_bucket()`. The 90-day proxy is sufficient for lagged yield features at CDD scale; crop-specific season alignment belongs in the Feature Store layer.

3. **T4 event-driven refresh requires operational complement.** `add_continuous_aggregate_policy()` cannot express post-harvest triggers. Daily schedule with full-season `start_offset` is the correct migration-scope approximation; harvest-event hooks are a future operational enhancement.

4. **Hierarchical sensor CAs are optional.** Sourcing `ca_sensor_daily` from raw `sensor_readings` simplifies the dependency graph and avoids cascading refresh failures from `ca_sensor_hourly` — a worthwhile trade-off at current CDD scale.

5. **TimescaleDB CAs are `relkind = 'v'` (VIEW), not `relkind = 'm'` (MATERIALIZED VIEW).** Although CAs are created with `CREATE MATERIALIZED VIEW … WITH (timescaledb.continuous)`, TimescaleDB stores them internally as PostgreSQL views. `COMMENT ON MATERIALIZED VIEW` uses a native PostgreSQL catalog check requiring `relkind = 'm'` and raises `WrongObjectTypeError (42809)`. The correct DDL is `COMMENT ON VIEW`. `DROP MATERIALIZED VIEW` remains correct because TimescaleDB intercepts that specific command. This is intentional TimescaleDB design (timescale/timescaledb#5194).

6. **Refresh window minimum applies per-bucket-width, not per-domain.** `add_continuous_aggregate_policy()` enforces `start_offset − end_offset ≥ 2 × bucket_width`. ADR-004 derived `start_offset` values from the late-arrival risk table keyed by domain, but a single domain can have multiple aggregates at different bucket widths. `ca_weather_daily` (1-day bucket) and `ca_weather_weekly` (1-week bucket) share the same source domain but require different minimum start_offsets. Minimum start_offsets must be validated per-aggregate against `2 × bucket_width + end_offset`, not per-domain.

---

## 8. Future Work

| Item | Phase / Step | Notes |
|---|---|---|
| Step 3C runtime validation report | Step 3C | Execute verification matrix §6 against CDD v1.0.0 |
| Repository CA read methods | Step 3C / subsequent ADR | Additive `time_bucket()` query paths if authorised |
| Hierarchical `ca_sensor_daily` | Optional optimisation | Re-source from `ca_sensor_hourly` if refresh CPU becomes bottleneck |
| Post-harvest refresh trigger | Operational | Application-level `refresh_continuous_aggregate()` on yield INSERT |
| Crop-calendar season bucketing | Feature Store (Phase 13) | Replace 90-day proxy if model requires planting-date alignment |
| CA compression policies | Post-3C | Compress materialisation hypertables after cardinality profiling |
| Retention policies | ADR-005 (Step 4) | Govern CA storage lifecycle alongside raw hypertables |
| Monitoring dashboards | Step 3C runbook | `timescaledb_information.job_stats` alerting per ADR-004 §9 |

---

## Architecture Traceability

```
Step 1 Foundation (ADR-001, ADR-002)
        ↓
Compression (ADR-003 — d4f5e6a7b8c9)
        ↓
CDD Population (Step 2C-C) + Runtime Validation (Step 2C-D)
        ↓
Step 3A — Continuous Aggregate Architecture Assessment
        ↓
ADR-004 — Continuous Aggregate Strategy (Approved)
        ↓
Step 3B — Continuous Aggregate Implementation (This Report)
   Migration e5f6a7b8c9d0 authored.
   Runtime execution pending manual authorisation.
        ↓
Step 3C — Continuous Aggregate Validation (Pending)
        ↓
Step 4 — Retention Policies (ADR-005)
        ↓
Phase 13 — AI Feature Store
```

---

## Decision Register Update

| Entry | Prior Status | New Status |
|---|---|---|
| P12-D012 — Continuous Aggregate Strategy | Approved (ADR-004) | **Implementation authored — pending runtime execution** |

---

*PHASE12_STEP3B_CONTINUOUS_AGGREGATE_IMPLEMENTATION_REPORT.md v1.3 — 2026-06-30 — Phase 12 Step 3B*
