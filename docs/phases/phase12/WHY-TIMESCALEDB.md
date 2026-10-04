# Why TimescaleDB — Phase 12 Strategic Decision Record

**Document Type:** Strategic Decision Rationale  
**Phase:** 12 — Time-Series Foundation  
**Date:** October 2026  
**Status:** Permanent Record  
**Audience:** Developers, architects, client stakeholders, future contributors  
**ADR Cross-References:** ADR-001 · ADR-002 · ADR-003 · ADR-004 · ADR-005

---

## 1. Bottom Line Up Front

By Phase 11, AGRIFLOW-AI had 10 domain models, 51+ REST endpoints, and a clean architecture that worked correctly. However, six of those domains — `WeatherRecord`, `SensorReading`, `IrrigationEvent`, `YieldRecord`, `DiseaseObservation`, `SatelliteObservation` — are time-series domains: high-frequency, append-only, timestamp-anchored data that grows without bound and is queried almost exclusively by time range.

Plain PostgreSQL handles this correctly at small scale. It stops performing acceptably at agricultural production scale.

Phase 12 introduced **TimescaleDB as a PostgreSQL extension** — not a replacement database — to solve this at the persistence layer while preserving every API contract, every repository interface, and every service layer built in Phases 1–11. Zero breaking changes. Zero application rewrites. A platform that now scales to enterprise deployments.

---

## 2. The Problem: Time-Series Data at Agricultural Scale

### What we collect

| Domain | Write frequency (typical) | Rows per farm per year |
|--------|--------------------------|------------------------|
| `sensor_readings` | Every 5–15 min per sensor | 52,560 – 210,240 |
| `weather_records` | Hourly | 8,760 |
| `irrigation_events` | Per event (avg daily in season) | 120 – 360 |
| `satellite_observations` | Every 5 days per field | 73 |
| `disease_observations` | Per observation | 20 – 100 |
| `yield_records` | Per harvest cycle | 1 – 4 |

A single farm with 20 sensors generates approximately **1.1 million rows per year** in `sensor_readings` alone. A cooperative managing 200 farms reaches **220 million sensor rows in year one**.

### What queries look like

Time-series data is almost never queried by primary key. The real queries are:

- *"Last 30 days of soil moisture for this field"* — range scan over `recorded_at`
- *"Hourly average temperature for the last week"* — aggregation over a time window
- *"Which fields had NDVI below 0.4 in the last 14 days?"* — multi-field time-range filter
- *"Training data for yield prediction: all sensor readings from planting through harvest"* — large range with cross-domain join

### Why plain PostgreSQL degrades at this scale

Standard PostgreSQL stores all rows in a single heap. A range query such as `WHERE recorded_at BETWEEN '2025-01-01' AND '2025-06-30'` must:

1. Scan the B-tree index to identify matching tuple IDs
2. Follow each tuple ID into the heap (random I/O, cache-unfriendly)
3. Filter rows against the time predicate

At tens of millions of rows this produces query latency that climbs from milliseconds to seconds to minutes. Composite indexes help but do not change the fundamental storage access pattern. PostgreSQL's native table partitioning is an option, but it requires manual partition DDL per table, provides no columnar compression, has no concept of continuous aggregates, and offers no automatic chunk exclusion — leaving the maintenance burden entirely on the application team.

---

## 3. Why TimescaleDB Specifically

### Alternatives considered

| Option | What it is | Why rejected |
|--------|-----------|--------------|
| **Plain PostgreSQL + manual partitioning** | Range partition by month/year per table | No columnar compression, no `time_bucket()`, manual partition DDL per table per month, high ongoing maintenance |
| **InfluxDB** | Purpose-built time-series database | Requires a separate stack and client library, cannot JOIN with relational domains (`farms`, `fields`, `crops`), breaks existing ORM entirely |
| **Apache Cassandra** | Wide-column distributed store | Designed for extreme write throughput at distributed scale; no SQL joins; complete query model redesign required; appropriate at Phase 15+ when truly needed at scale |
| **TimescaleDB** | PostgreSQL extension | ✅ Selected — see below |

### Why TimescaleDB won

**1. Zero database replacement.**
TimescaleDB is installed as a PostgreSQL extension. The database is still PostgreSQL. `asyncpg` still works. Alembic still works. SQLAlchemy ORM still works. Every repository, service, and API endpoint built in Phases 1–11 continued to function without a single line of application code change. This was the non-negotiable constraint: Phase 12 could not break existing contracts.

**2. Automatic time partitioning (hypertables).**
A hypertable transparently partitions data into time-bounded chunks. A range query on `recorded_at` then touches only the chunks that overlap the requested window — sequential reads against a bounded chunk rather than a full-table heap scan. At 200 million rows, this is the difference between a 30-second query and a 30-millisecond query.

**3. Columnar compression on cold chunks.**
Chunks older than a configurable threshold are compressed using columnar storage. Agricultural sensor data from last quarter is infrequently accessed but must be retained for AI model training. Columnar compression reduces storage 80–95% for time-series data while keeping all data queryable via standard SQL. No application change needed to read compressed chunks.

**4. Continuous aggregates for AI feature engineering.**
The most expensive queries for AI model training are time-windowed aggregates — hourly averages, daily max/min, weekly NDVI trends. TimescaleDB materialises these as `time_bucket()` rollups that refresh incrementally in the background. Phase 13+ AI services query pre-computed aggregate tables rather than re-aggregating millions of raw rows at inference time.

**5. Retention policies for data lifecycle management.**
Agricultural data has natural tiers: raw sensor readings lose marginal value after 2 years, but aggregate trends remain valuable indefinitely, and harvest yield records must be retained permanently. Retention policies automate this lifecycle without custom cron jobs or ad-hoc DELETE statements — reducing operational risk.

**6. The schema was already designed for it.**
This is the key architectural insight. Phases 5–11 deliberately included:
- A `NOT NULL TIMESTAMPTZ` partition key column on every time-series table
- Compound `(parent_id, time_column)` indexes on every time-series table
- An explicit ADR note at each phase documenting the hypertable upgrade path

The migration to TimescaleDB required zero application code changes because the schema was already correct. Phase 12 was the execution of a plan that had been prepared across seven prior phases.

---

## 4. What Phase 13+ AI Gets From It

TimescaleDB is not an end in itself. It is the persistence foundation that makes AI decision intelligence viable at production latency.

| AI Capability (Phase 13+) | What it needs from Phase 12 |
|--------------------------|----------------------------|
| Yield prediction model | Daily `time_bucket()` aggregates of soil moisture, temperature, solar radiation → structured feature vectors |
| Disease risk scoring | Rolling 7-day average leaf wetness and temperature from the `sensor_readings` continuous aggregate |
| Irrigation recommendation | Historical water-use efficiency: IrrigationEvent volume ÷ YieldRecord ÷ NDWI trend over the growing season |
| Frost / heat alert engine | Hourly temperature rollups for threshold detection at field level, sub-100ms latency |
| Digital Twin field state | Latest-value-per-sensor-type queries against compressed hypertable without full-table scan |

Without TimescaleDB, every one of these queries would aggregate over raw heap tables at query time. At production scale that is architecturally non-viable — the recommendation engine would be gated by database latency, not by model inference. A recommendation that takes 8 seconds to generate from raw data is not a recommendation engine; it is a batch report.

**Phase 12 was sequenced before Phase 13 precisely because AI services that cannot be served within 200ms are not production-grade.**

---

## 5. What Was Delivered

| Component | Detail |
|-----------|--------|
| Extension | TimescaleDB 2.28.1 on PostgreSQL 17.10 |
| Hypertables | 6 tables converted: `weather_records`, `sensor_readings`, `irrigation_events`, `yield_records`, `disease_observations`, `satellite_observations` |
| Compression policies | 6 policies — cold chunks compressed after 7–30 days depending on domain write frequency |
| Continuous aggregates | 8 incremental `time_bucket()` rollups (hourly / daily / weekly per domain) |
| Retention policies | 11 policies — raw data tiered by domain; `yield_records` permanently retained as irreplaceable harvest labels |
| API breaking changes | **Zero** — all Phase 1–11 contracts preserved |
| Validation corpus | CDD v1.0.0 — 458,645-row deterministic dataset validated at Steps 2C, 3C, and 4C |
| Background jobs | 27 automated background jobs (compression, CA refresh, retention) |

---

## 6. What Would Have Happened Without It

If Phase 12 had been skipped and the platform had proceeded directly to Phase 13 AI recommendations:

| Problem | Impact |
|---------|--------|
| Range queries aggregating 12 months of sensor data | 10–60 seconds per field at 1M row scale — unusable for real-time recommendations |
| No continuous aggregates | AI feature pipelines would re-aggregate raw rows on every training run — hours per model retraining cycle |
| No compression | Storage grows linearly; a 200-farm deployment accumulates 500GB+ raw sensor data within 2 years |
| No retention policies | Data lifecycle requires custom cron jobs; legal and contractual requirements become manual obligations |
| AI services blocked on database latency | Recommendation quality would be bounded by database performance, not model quality |

Phase 12 eliminated all five of these blockers before Phase 13 began.

---

## 7. ADR Cross-References

Each implementation decision within Phase 12 is recorded as a formal ADR:

| ADR | Decision captured |
|-----|-------------------|
| [ADR-001](../../adr/ADR-001-timescaledb-extension-enablement.md) | Enable TimescaleDB via forward Alembic migration, not manual SQL or container init script |
| [ADR-002](../../adr/ADR-002-hypertable-primary-key-conversion-strategy.md) | Composite `(id, time_col)` primary key required by TimescaleDB hypertable constraint |
| [ADR-003](../../adr/ADR-003-timescaledb-compression-policy-strategy.md) | Columnar compression on cold chunks per domain; compression interval tuned to write frequency |
| [ADR-004](../../adr/ADR-004-timescaledb-continuous-aggregate-strategy.md) | `time_bucket()` continuous aggregates as AI feature engineering foundation |
| [ADR-005](../../adr/ADR-005-timescaledb-retention-policy-strategy.md) | Domain-tiered retention; `yield_records` permanently retained as irreplaceable training labels |

---

## 8. One-Sentence Summary

> AGRIFLOW-AI adopted TimescaleDB because six of its ten domains produce time-series data at agricultural scale — and a platform that cannot serve AI recommendations in under 200ms is not an AI platform.
