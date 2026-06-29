# AGRIFLOW-AI — Phase 12 Step 1E-A

## Hypertable Architecture Assessment & Primary Key Strategy

**Document Type:** Architecture Assessment (Read-Only)  
**Version:** 1.0  
**Date:** 2026-06-29  
**Scope:** Phase 12 Step 1E-A — Hypertable Architecture Assessment; Primary Key Strategy; ADR-002 Preparation  
**Status:** Approved Architecture Assessment 
**Author:** Senior Platform Architecture  
**Governance References:**

| Document | Version | Status |
|---|---|---|
| `PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md` | 1.3 | ✅ Approved Architecture Baseline |
| `PHASE12_STEP1B_TIMESCALEDB_INFRASTRUCTURE_PLAN.md` | 1.1 | ✅ Approved Infrastructure Plan |
| `PHASE12_STEP1C_IMPLEMENTATION_REPORT.md` | 1.0 | ✅ Approved Infrastructure Execution |
| `PHASE12_STEP1D_EXTENSION_ENABLEMENT_REPORT.md` | 1.0 | ✅ Approved Extension Enablement |
| `PHASE12_DECISION_REGISTER.md` | 1.2 | Active |
| `docs/adr/ADR-001-timescaledb-extension-enablement.md` | Accepted | Active |

**Read-Only Activity Notice:** This document is a pre-implementation architecture review. No schema changes, migrations, Docker modifications, or application code modifications were made during its preparation.

---

## 1. Executive Summary

AGRIFLOW-AI has completed Phase 12 Steps 1B through 1D. TimescaleDB 2.28.1 is active in the `agriflow` PostgreSQL 17 database. The system is now ready for hypertable architecture evaluation.

This assessment examines all ten domain tables to determine hypertable suitability. It resolves the central deferred question from Step 1A — **primary key strategy for hypertable conversion** — with evidence drawn from the live schema, codebase, and current TimescaleDB 2.28.x behavior.

### Central Finding: Composite Primary Key is the Approved Path

All six hypertable candidate tables carry a `PRIMARY KEY (id)` where `id` is a UUID v4. TimescaleDB 2.28.x requires that **every unique constraint — including primary keys — must include the partitioning column**. The current UUID-only primary key prevents `create_hypertable()` from succeeding.

This assessment determines that **Composite Primary Key Strategy (Option A)** — changing each time-series table's primary key from `(id)` to `(id, time_col)` — is the architecturally sound, lowest-risk path. Critically:

- `BaseRepository.get_by_id` uses `WHERE id = :id` (not `session.get()`), meaning **repository code requires zero changes**
- No other domain table holds a foreign key reference to any of the six time-series tables
- All API contracts, service interfaces, repository interfaces, and Pydantic schemas remain unchanged
- The migration is reversible and can be executed per table

### Six Tables Recommended for Hypertable Conversion

| Table | Priority | Partition Key | Rationale |
|---|---|---|---|
| `sensor_readings` | P1 — Critical | `recorded_at` | Highest insert frequency; IoT telemetry; AI Feature Store backbone |
| `weather_records` | P1 — Critical | `recorded_at` | Required for ET₀/GDD calculations; continuous ingestion |
| `satellite_observations` | P1 — Critical | `observed_at` | Multi-spectral time series; AI training data source |
| `irrigation_events` | P2 — High | `started_at` | Agricultural intervention history; water management analytics |
| `yield_records` | P2 — High | `recorded_at` | Yield Prediction Engine; crop performance history |
| `disease_observations` | P3 — Standard | `observed_at` | Disease Risk Scoring Engine; lower insert frequency |

### Four Tables Remain Relational

`farms`, `fields`, `crops`, `soil_profiles` — static reference data with no time-series growth characteristics. These tables remain standard PostgreSQL tables permanently.

### ADR-002 Readiness

This assessment provides sufficient evidence to draft and approve ADR-002 (Hypertable Primary Key Strategy & Conversion Sequence). The recommendation is clear and evidence-based. A separate ADR-002 preparation session is warranted to complete the formal decision record before Step 1E-B execution.

---

## 2. Implementation Traceability

```
Architecture Baseline
        ↓
     Step 1A
  Infrastructure Plan
        ↓
     Step 1B
Infrastructure Execution
        ↓
     Step 1C
Extension Enablement
        ↓
     Step 1D
Hypertable Architecture Assessment
        ↓
     Step 1E-A  ← Current (Read-Only Assessment)
Hypertable Conversion Migration
        ↓
     Step 1E-B  (Pending Architecture Approval)
Decision Register
        ↓
  Version 1.2 → 1.3 (pending)
```

---

## 3. Current Platform State

| Attribute | Value |
|---|---|
| Database | PostgreSQL 17.10 |
| TimescaleDB | 2.28.1 (active in `agriflow` database) |
| Alembic head | `f1e2d3c4b5a6` (enable_timescaledb_extension) |
| Domain tables | 10 (+ `alembic_version`) |
| Active hypertables | 0 |
| Compression policies | 0 |
| Continuous aggregates | 0 |
| Primary key strategy | UUID-only (`id` UUID NOT NULL) on all domain tables |

---

## 4. Domain Model Assessment

This section evaluates every domain table against the hypertable suitability criteria.

---

### 4.1 `farms`

| Attribute | Detail |
|---|---|
| **Domain role** | Root aggregate — top of the `Farm → Field → Crop` hierarchy |
| **Primary key** | `id UUID` (only) |
| **Time column** | `created_at` (audit only; not a measurement timestamp) |
| **Data growth** | Low — typically tens to hundreds of farms per deployment |
| **Insert frequency** | Very low — farms are rarely created or modified |
| **Query patterns** | Lookup by `id`; lookup by `farm_code`; list all active farms |
| **AI usage** | Metadata / context; Farm Copilot reads farm attributes; not a feature source |
| **Reporting usage** | Farm directory; ownership summaries |
| **Time-series suitability** | None — no repetitive temporal measurement |
| **Hypertable verdict** | **Not Recommended** |
| **Justification** | Master data entity with no time-series growth pattern. Unique constraint on `farm_code` would be incompatible with hypertable partitioning. No performance benefit from chunking. |

---

### 4.2 `fields`

| Attribute | Detail |
|---|---|
| **Domain role** | Second-level aggregate — child of Farm; parent of all telemetry domains |
| **Primary key** | `id UUID` (only) |
| **Time column** | `created_at` (audit only) |
| **Data growth** | Low — typically tens to hundreds of fields per farm |
| **Insert frequency** | Very low — fields are rarely created or restructured |
| **Query patterns** | Lookup by `id`; list by `farm_id` |
| **AI usage** | Spatial metadata; feature engineering context (area, elevation, coordinates) |
| **Reporting usage** | Field directory; farm summary reports |
| **Time-series suitability** | None — reference data entity |
| **Hypertable verdict** | **Not Recommended** |
| **Justification** | Master data entity. All time-series data anchors *on* fields via FK — the field itself is the dimension, not the measurement. |

---

### 4.3 `crops`

| Attribute | Detail |
|---|---|
| **Domain role** | Third-level aggregate — crop cycle per field (`Farm → Field → Crop`) |
| **Primary key** | `id UUID` (only) |
| **Time columns** | `planting_date` (DATE), `actual_harvest_date` (DATE) — lifecycle dates, not observation times |
| **Data growth** | Low to medium — one to a few crop cycles per field per year |
| **Insert frequency** | Low — one record per crop season per field |
| **Query patterns** | Lookup by `id`; list by `field_id`; filter by `status` |
| **AI usage** | Crop cycle context for Yield Prediction Engine; actual_yield_tons_ha is target variable; growth_stage is phenological feature |
| **Reporting usage** | Crop calendar; harvest reporting |
| **Time-series suitability** | Low — individual crop records are not repeated high-frequency observations; planting_date/harvest_date are lifecycle milestones, not a partition key for high-frequency data |
| **Hypertable verdict** | **Not Recommended** |
| **Justification** | Lifecycle management entity. Crop cycles are counted in years per field, not millions of rows. The domain-level time data (planting, harvest) is date-only, not TIMESTAMPTZ. Hypertable overhead is not justified. |

---

### 4.4 `soil_profiles`

| Attribute | Detail |
|---|---|
| **Domain role** | One-to-one companion to `fields` — soil chemistry profile |
| **Primary key** | `id UUID` (only) |
| **Unique constraint** | `UNIQUE INDEX (field_id)` — enforces one-to-one with `fields` |
| **Time column** | `created_at` (audit only) |
| **Data growth** | Exactly one row per field — bounded by field count |
| **Insert frequency** | Extremely low — profile updated on field characterization or lab analysis |
| **Query patterns** | Lookup by `field_id`; single row per field |
| **AI usage** | Static soil feature vector (pH, organic matter, N, P, K, texture class, depth) for Yield Prediction Engine |
| **Reporting usage** | Soil health reports; field characterization |
| **Time-series suitability** | None — static profile updated infrequently |
| **Hypertable verdict** | **Not Recommended** |
| **Justification** | One-to-one with `fields`; bounded row count; static profile data. The UNIQUE constraint on `field_id` (enforcing one-to-one) cannot include a time partition column since there is no time dimension to the soil profile. Hypertable conversion would destroy the one-to-one constraint semantics. |

---

### 4.5 `weather_records`

| Attribute | Detail |
|---|---|
| **Domain role** | Meteorological time-series attached to a Field |
| **Primary key** | `id UUID` (only); `PRIMARY KEY (id)` |
| **Partition column** | `recorded_at` TIMESTAMPTZ NOT NULL |
| **Foreign key** | `field_id → fields.id` (ON DELETE no action) |
| **Indexes** | `ix_weather_records_field_id` (single), `ix_weather_records_recorded_at` (single); **no compound index** |
| **Data growth** | High — weather stations ingest 1–24 records per field per day continuously |
| **Insert frequency** | Medium–High — sub-hourly for automated stations, daily for manual entries |
| **Query patterns** | `list_by_field` ordered `recorded_at DESC`; date-range queries for GDD/ET₀ calculations |
| **AI usage** | Temperature min/max for Growing Degree Days; solar radiation for Penman-Monteith ET₀; humidity for disease pressure models; direct feature input for Yield Prediction Engine |
| **Reporting usage** | Weather history; crop season meteorological summaries |
| **Time-series suitability** | **Excellent** — continuous meteorological time-series; field-specific; accessed by date range |
| **Hypertable verdict** | **✅ Recommended — P1 Critical** |
| **Justification** | Classic time-series domain. Weather data accumulates indefinitely at high frequency. `recorded_at` is the natural partition key. Field-scoped access pattern matches TimescaleDB chunk exclusion. GDD/ET₀ calculations benefit from `time_bucket()` aggregation. |
| **Gap identified** | **Missing compound index `(field_id, recorded_at)`** — all other Field-anchored time-series tables have this compound index. This should be added in the Step 1E-B migration. |
| **Recommended chunk interval** | 7 days (daily–sub-daily data; 1-week chunk aligns with agro-meteorological query windows) |

---

### 4.6 `sensor_readings`

| Attribute | Detail |
|---|---|
| **Domain role** | IoT telemetry time-series — the highest-frequency data domain |
| **Primary key** | `id UUID` (only); `PRIMARY KEY (id)` |
| **Partition column** | `recorded_at` TIMESTAMPTZ NOT NULL |
| **Foreign key** | `field_id → fields.id` (ON DELETE CASCADE) |
| **Indexes** | Individual: `field_id`, `sensor_type`, `recorded_at`; Compound: `(field_id, recorded_at)`, `(sensor_type, recorded_at)` |
| **Mutability** | Append-only (ADR-007-19) — no UPDATE surfaced in repository |
| **Data growth** | Very High — IoT sensors generate 1–12 readings per sensor per hour; a 100-field farm with 10 sensors per field produces ~10M–100M rows/year |
| **Insert frequency** | Very High — continuous IoT ingestion |
| **Query patterns** | `list_by_field` ordered `recorded_at DESC`; sensor-type filtering; time-window scans for feature extraction |
| **AI usage** | Primary Feature Store source — soil moisture, temperature, humidity, conductivity form the core agronomic sensor feature vector for all AI models |
| **Reporting usage** | Sensor dashboards; anomaly detection; irrigation scheduling |
| **Time-series suitability** | **Excellent — the most natural hypertable candidate in the domain** |
| **Hypertable verdict** | **✅ Recommended — P1 Critical** |
| **Justification** | Highest insert frequency; append-only semantics align perfectly with immutable hypertable chunks; chunk exclusion eliminates full table scans for time-window queries; compression on cold chunks provides major storage savings for IoT history. This table benefits the most from hypertable conversion. |
| **Recommended chunk interval** | 7 days (matches telemetry dashboard query windows; allows efficient compression on 1-week-old chunks) |

---

### 4.7 `irrigation_events`

| Attribute | Detail |
|---|---|
| **Domain role** | Agricultural intervention time-series — water management |
| **Primary key** | `id UUID` (only); `PRIMARY KEY (id)` |
| **Partition column** | `started_at` TIMESTAMPTZ NOT NULL |
| **Foreign key** | `field_id → fields.id` (ON DELETE CASCADE) |
| **Indexes** | Individual: `field_id`, `started_at`; Compound: `(field_id, started_at)` |
| **Mutability** | Mutable — PATCH supported (human-logged intervention may need correction) |
| **Data growth** | Medium — typically 3–7 irrigation events per field per week during growing season; seasonal pattern |
| **Insert frequency** | Low–Medium — human-triggered or schedule-driven |
| **Query patterns** | `list_by_field` ordered `started_at DESC`; date-range queries for irrigation scheduling analytics |
| **AI usage** | Irrigation volume, method, and frequency as feature inputs for water stress models; training data for Irrigation Optimization Engine |
| **Reporting usage** | Irrigation history; water consumption reports; FAO-56 water balance calculations |
| **Time-series suitability** | **Good** — temporal event series; lower frequency than sensor data |
| **Hypertable verdict** | **✅ Recommended — P2 High** |
| **Justification** | Clear time-series semantics with `started_at` as the event anchor. Field-scoped access pattern matches TimescaleDB chunk exclusion. Although insert frequency is lower than sensor/weather data, long-term accumulation (years of irrigation history per field) justifies hypertable partitioning. |
| **Mutable note** | TimescaleDB supports UPDATE on hypertables. Mutable semantics are compatible. |
| **Recommended chunk interval** | 1 month (irrigation events are seasonal; monthly chunks align with water management reporting periods) |

---

### 4.8 `yield_records`

| Attribute | Detail |
|---|---|
| **Domain role** | Crop yield measurement — grandchild of Crop; `Farm → Field → Crop → YieldRecord` |
| **Primary key** | `id UUID` (only); `PRIMARY KEY (id)` |
| **Partition column** | `recorded_at` TIMESTAMPTZ NOT NULL |
| **Foreign keys** | `crop_id → crops.id` (CASCADE), `field_id → fields.id` (CASCADE) — dual FK |
| **Indexes** | Individual: `crop_id`, `field_id`, `recorded_at`; Compound: `(crop_id, recorded_at)` |
| **Mutability** | Mutable — PATCH supported |
| **Data growth** | Low–Medium — yield measurements are infrequent (one or a few per crop cycle per field); seasonal pattern |
| **Insert frequency** | Low — harvest-time events; typically 1–5 records per crop cycle |
| **Query patterns** | `list_by_crop` ordered `recorded_at DESC`; `list_by_field` ordered `recorded_at DESC`; multi-crop comparison |
| **AI usage** | **Target variable** for Yield Prediction Engine — `yield_value_tons_ha` is the primary prediction output; historical yield data trains the model |
| **Reporting usage** | Harvest reports; field productivity history; crop comparison |
| **Time-series suitability** | **Moderate** — low insert frequency; strong temporal identity; multi-crop parent |
| **Hypertable verdict** | **✅ Recommended — P2 High** |
| **Justification** | Despite low insert frequency, yield history accumulates over many seasons and years. Long-term historical access patterns (feature engineering over multi-year yield history) benefit from time partitioning. `recorded_at` aligns with the AI Yield Prediction Engine's time-window feature extraction. |
| **Dual FK note** | Both `crop_id → crops` and `field_id → fields` FK constraints are foreign key references TO `crops` and `fields`, not FROM external tables TO `yield_records`. No FK impact from PK change. |
| **Recommended chunk interval** | 3 months (harvest measurements are sparse; quarterly chunks avoid over-partitioning on low-frequency data) |

---

### 4.9 `disease_observations`

| Attribute | Detail |
|---|---|
| **Domain role** | Disease pressure time-series — grandchild of Crop; `Farm → Field → Crop → DiseaseObservation` |
| **Primary key** | `id UUID` (only); `PRIMARY KEY (id)` |
| **Partition column** | `observed_at` TIMESTAMPTZ NOT NULL |
| **Foreign keys** | `crop_id → crops.id` (CASCADE), `field_id → fields.id` (CASCADE) — dual FK |
| **Indexes** | Individual: `crop_id`, `field_id`, `observed_at`, `disease_name`, `severity`; Compound: `(crop_id, observed_at)` |
| **Mutability** | Mutable — PATCH supported |
| **Data growth** | Low–Medium — disease observations are episodic; driven by crop health events |
| **Insert frequency** | Low — event-driven; 0–50 observations per crop cycle typical |
| **Query patterns** | `get_by_crop` ordered `observed_at DESC`; `get_by_field` ordered `observed_at DESC`; severity filtering |
| **AI usage** | Disease pressure feature for Disease Risk Scoring Engine; treatment efficacy time series; `IMAGE_AI` diagnosis method drives computer vision feedback loops |
| **Reporting usage** | Disease history; crop protection reports |
| **Time-series suitability** | **Moderate** — temporal event series; lower than sensor/weather data |
| **Hypertable verdict** | **✅ Recommended — P3 Standard** |
| **Justification** | Temporal semantics are clear; `observed_at` is the natural partition key. Lower priority than sensor/weather/satellite data given insert frequency, but valuable for long-term disease history analytics and AI model training. |
| **Recommended chunk interval** | 1 month |

---

### 4.10 `satellite_observations`

| Attribute | Detail |
|---|---|
| **Domain role** | Satellite imagery time-series — direct child of Field |
| **Primary key** | `id UUID` (only); `PRIMARY KEY (id)` |
| **Partition column** | `observed_at` TIMESTAMPTZ NOT NULL |
| **Foreign key** | `field_id → fields.id` (ON DELETE CASCADE) |
| **Indexes** | Individual: `field_id`, `observed_at`, `satellite_provider`, `spectral_index`, `scene_id`; Compound: `(field_id, observed_at)`, `(spectral_index, observed_at)` |
| **Mutability** | Mutable — PATCH supported (processing level corrections) |
| **Data growth** | High — 8 spectral indices × 2–5 passes per field per week → significant accumulation over multiple growing seasons |
| **Insert frequency** | Medium–High — automated satellite ingestion pipeline; multiple providers (Sentinel-2 ~5-day revisit, Landsat ~16-day, Planet ~daily) |
| **Query patterns** | `list_by_field` ordered `observed_at DESC`; `list_by_field_and_date_range`; `get_latest_by_field_and_spectral_index`; `list_by_provider`; `list_by_processing_level` |
| **AI usage** | **Primary AI training source** — NDVI, EVI, NDWI, SAVI spectral indices form the core remote sensing feature vector; cloud-filtered ARD/L2A observations train multi-temporal vegetation models; `list_by_field_and_spectral_index` is the direct Phase 12 AI feature extraction query |
| **Reporting usage** | NDVI time series charts; vegetation health dashboards; seasonal productivity maps |
| **Time-series suitability** | **Excellent** — structured temporal time-series with multiple spectral dimensions; AI-optimized access patterns already coded |
| **Hypertable verdict** | **✅ Recommended — P1 Critical** |
| **Justification** | The most architecturally mature hypertable candidate: compound indexes pre-aligned with TimescaleDB access patterns; `list_by_field_and_date_range` directly maps to hypertable time-window scan; multiple provider ingestion at high frequency; very high AI training data value. |
| **Recommended chunk interval** | 7 days (Sentinel-2 5-day revisit means 2+ observations per chunk; aligns with weekly feature extraction windows) |

---

## 5. Hypertable Suitability Matrix

| Table | Verdict | Priority | Partition Key | Data Growth | AI Usage | Reporting Usage | Chunk Interval |
|---|---|---|---|---|---|---|---|
| `farms` | ❌ Not Recommended | — | — | Very Low | Metadata only | Low | — |
| `fields` | ❌ Not Recommended | — | — | Very Low | Spatial metadata | Low | — |
| `crops` | ❌ Not Recommended | — | — | Low | Target variable (attributes) | Moderate | — |
| `soil_profiles` | ❌ Not Recommended | — | — | Static | Static feature vector | Low | — |
| `sensor_readings` | ✅ Recommended | P1 — Critical | `recorded_at` | Very High | AI Feature Store backbone | High | 7 days |
| `weather_records` | ✅ Recommended | P1 — Critical | `recorded_at` | High | GDD / ET₀ / precipitation features | High | 7 days |
| `satellite_observations` | ✅ Recommended | P1 — Critical | `observed_at` | High | Multi-spectral AI training source | High | 7 days |
| `irrigation_events` | ✅ Recommended | P2 — High | `started_at` | Medium | Irrigation optimization features | Medium | 1 month |
| `yield_records` | ✅ Recommended | P2 — High | `recorded_at` | Low–Medium | Yield Prediction Engine target | High | 3 months |
| `disease_observations` | ✅ Recommended | P3 — Standard | `observed_at` | Low–Medium | Disease Risk Scoring features | Medium | 1 month |

**Summary:** 4 tables remain relational; 6 tables convert to hypertables (3 P1, 2 P2, 1 P3).

---

## 6. Primary Key Assessment

### 6.1 Current State — UUID-Only Primary Keys

Every domain table (including all six hypertable candidates) inherits the same primary key pattern from `AuditableModel`:

```
PRIMARY KEY (id)   -- id is UUID v4, globally unique, application-level identity
```

The partition columns (`recorded_at`, `started_at`, `observed_at`) are **NOT** included in any primary key or unique constraint.

**Live schema evidence (queried 2026-06-29):**

| Table | Primary Key Columns | Partition Column | In PK? |
|---|---|---|---|
| `sensor_readings` | `id` | `recorded_at` | ❌ No |
| `weather_records` | `id` | `recorded_at` | ❌ No |
| `satellite_observations` | `id` | `observed_at` | ❌ No |
| `irrigation_events` | `id` | `started_at` | ❌ No |
| `yield_records` | `id` | `recorded_at` | ❌ No |
| `disease_observations` | `id` | `observed_at` | ❌ No |

### 6.2 TimescaleDB 2.28.x Constraint Requirement

TimescaleDB 2.28.x enforces the following rule:

> **Any UNIQUE constraint (including PRIMARY KEY) on a hypertable must include the partitioning column.**

Attempting `SELECT create_hypertable('sensor_readings', 'recorded_at')` on the current schema will fail with:

```sql
ERROR:  cannot create a unique index without the column "recorded_at" (used in partitioning)
DETAIL:  Adding a hypertable constraint requires the partitioning column "recorded_at" to be included
         in the unique constraint definition.
```

This is the constraint failure referenced in Step 1A §5.5 and documented as a deferred decision in the Decision Register (P12-D deferred PK strategy).

### 6.3 Available Primary Key Strategies

Four strategies were evaluated. Each is documented with impact assessment.

---

#### Strategy A — Composite Primary Key: `PRIMARY KEY (id, time_col)` ✅ RECOMMENDED

**Description:** Alter each time-series table's primary key to include both `id` (UUID) and the partition column.

| Table | Current PK | Proposed PK |
|---|---|---|
| `sensor_readings` | `(id)` | `(id, recorded_at)` |
| `weather_records` | `(id)` | `(id, recorded_at)` |
| `irrigation_events` | `(id)` | `(id, started_at)` |
| `yield_records` | `(id)` | `(id, recorded_at)` |
| `disease_observations` | `(id)` | `(id, observed_at)` |
| `satellite_observations` | `(id)` | `(id, observed_at)` |

**Migration pattern (per table):**
```sql
ALTER TABLE sensor_readings DROP CONSTRAINT pk_sensor_readings;
ALTER TABLE sensor_readings ADD CONSTRAINT pk_sensor_readings PRIMARY KEY (id, recorded_at);
SELECT create_hypertable('sensor_readings', 'recorded_at', migrate_data => TRUE, if_not_hypertable => TRUE);
```

**TimescaleDB satisfaction:** UUID `id` is globally unique within the table; `id` alone still uniquely identifies any row. Including `recorded_at` in the PK satisfies TimescaleDB's partition constraint requirement.

**Application impact assessment:**

| Layer | Impact | Justification |
|---|---|---|
| `BaseRepository.get_by_id` | **NONE** | Uses `select().where(Model.id == id)` — WHERE clause, not PK lookup |
| `BaseRepository.create` / `delete` / `update` | **NONE** | No PK-based session operations |
| All domain repositories | **NONE** | All queries use `.where(Model.column == value)` |
| SQLAlchemy ORM models | **Model class requires composite PK declaration** | `id` and `time_col` both declared as `mapped_column(primary_key=True)` |
| Pydantic schemas | **NONE** | Schemas use UUID as identity; no DB constraint coupling |
| API routes | **NONE** | All routes use UUID as path parameter |
| Services | **NONE** | Business logic unaffected |
| Foreign keys TO these tables | **NONE** | No external table holds a FK reference to any time-series table |

**Critical repository finding:** `BaseRepository.get_by_id` uses:
```python
select(self._model).where(self._model.id == record_id)
```
This is a **predicate filter** on the `id` column, not a primary key composite tuple lookup (`session.get(Model, (uuid, datetime))`). The WHERE clause executes identically regardless of PK composition. **Zero repository code changes required.**

**Risk:** **LOW** — well-documented TimescaleDB pattern; reversible; no FK cascades affected.

---

#### Strategy B — Drop PK, Composite UNIQUE Index

**Description:** Drop the `PRIMARY KEY` constraint; replace with `UNIQUE INDEX (id, time_col)` to satisfy TimescaleDB; add a non-unique `INDEX (id)` for UUID lookup performance.

**Assessment:**
- TimescaleDB requirement is satisfied (UNIQUE index includes partition column)
- UUID uniqueness preserved at DB level via the composite unique index
- Application queries unchanged
- **Risk: MEDIUM** — no true primary key loses relational integrity semantics; makes FK references to these tables semantically weak (though no such FKs exist today); some ORM operations may behave differently without a PK constraint; not all tooling (pgAdmin, BI tools) handles PK-less tables gracefully

**Verdict: NOT RECOMMENDED** — Strategy A is superior with no additional risk.

---

#### Strategy C — Integer Surrogate PK + UUID Application Identity

**Description:** Add a `BIGSERIAL` column `_pk`; change primary key to `(_pk, time_col)`; UUID `id` becomes a NOT NULL UNIQUE column.

**Assessment:**
- Requires adding a new column to every time-series table
- UUID-only UNIQUE constraint still fails TimescaleDB requirement → UUID uniqueness must be expressed as `UNIQUE (id, time_col)` anyway
- ORM models require significant restructuring
- API routing (currently UUID-based) unchanged but ORM identity semantics change
- Adds storage overhead (8 bytes per row for BIGSERIAL)
- **Risk: HIGH** — unnecessary complexity; no advantage over Strategy A

**Verdict: NOT RECOMMENDED** — Strategy A achieves the same TimescaleDB compatibility without introducing a surrogate identity field.

---

#### Strategy D — Remove All Unique Constraints (No PK, No Unique Indexes)

**Description:** Drop all primary key and unique constraints on time-series tables; allow TimescaleDB to create hypertables without constraint restriction.

**Assessment:**
- Technically viable — TimescaleDB does not require unique constraints on hypertables
- UUID uniqueness is no longer enforced at the database level
- Duplicate rows can be inserted; application-level deduplication required
- `get_by_id` could return multiple rows
- **Risk: VERY HIGH** — destroys data integrity guarantees; incompatible with AGRIFLOW's relational integrity requirements

**Verdict: NOT RECOMMENDED** — Fundamentally incompatible with production-grade architecture.

---

### 6.4 Primary Key Strategy Conclusion

**Recommended strategy: Strategy A — Composite Primary Key `(id, time_col)`**

This is the correct approach for AGRIFLOW-AI because:

1. **TimescaleDB satisfaction:** Partition column included in PK — `create_hypertable()` succeeds.
2. **UUID identity preserved:** `id` is still part of the PK and globally unique within the table.
3. **Zero repository changes:** All queries use `WHERE id = :id` predicate, not PK tuple lookup.
4. **No FK impact:** No external table references any time-series table via FK.
5. **API contracts unchanged:** Routes use `/{id}` UUID path parameters — unchanged.
6. **Services unchanged:** Business logic has no PK-structure coupling.
7. **Pydantic schemas unchanged:** No database constraint representation in schemas.
8. **Reversible:** Drop composite PK → restore UUID-only PK → tables convert back to standard PostgreSQL.
9. **Standard pattern:** Widely documented as the canonical approach for UUID-keyed applications adopting TimescaleDB.

**The ORM model change required:** Each time-series SQLAlchemy model must declare both `id` and the time column with `primary_key=True`. This is a model-layer change, not a repository-interface change. The approved baseline (Step 1A §2.1) states "ORM definitions unchanged per approved baseline; any PK strategy is migration-level DDL only — subject to follow-on review." Strategy A satisfies this constraint if the composite PK is expressed at the DDL migration level and the ORM models are updated to reflect the new PK definition.

**ADR-002 is required** before Step 1E-B implementation to formally record this decision.

---

## 7. TimescaleDB Best Practices Evaluation

This section evaluates current TimescaleDB 2.28.x guidance against AGRIFLOW-AI's specific requirements.

### 7.1 Hypertable Partitioning

| Best Practice | Applies to AGRIFLOW? | Assessment |
|---|---|---|
| Single-dimension time partitioning (default) | ✅ Yes | All six candidates have a single TIMESTAMPTZ partition column. Space partitioning (second dimension) is not required at current scale. |
| Partition column must be `NOT NULL TIMESTAMPTZ` | ✅ Satisfied | All six partition columns are already `TIMESTAMPTZ NOT NULL` (verified in live schema). |
| Choose chunk interval based on ingest rate and query pattern | ✅ Applies | Recommendations provided per table (§5). P1 tables: 7 days; P2/P3: 1–3 months. |
| Avoid hypertables for tables with < 100K rows per year | ✅ Considered | `yield_records` and `disease_observations` are borderline — included for long-term AI history value. |

### 7.2 UUID Primary Keys in TimescaleDB 2.28.x

| Topic | Finding |
|---|---|
| Can UUID primary keys remain? | **Yes** — as composite `(id, time_col)`. UUID identity is preserved. |
| Does TimescaleDB 2.28.x require composite keys? | **Yes** — not composite keys specifically, but ALL unique constraints must include the partition column. Composite PK is the cleanest solution. |
| Are alternative strategies available? | **Yes** — Strategies B, C, D evaluated above. None are superior to Strategy A for AGRIFLOW. |
| Can unique indexes satisfy requirements? | **Partially** — a `UNIQUE INDEX (id, time_col)` satisfies TimescaleDB, but a composite PK is preferred for referential integrity and tooling compatibility. |
| Can partitioning preserve current DDD design? | **Yes** — Strategy A requires no change to API, service, repository interfaces, schemas, or business logic. |

### 7.3 Compression

| Topic | Recommendation |
|---|---|
| Target tables | `sensor_readings`, `weather_records`, `satellite_observations` — highest row accumulation |
| Compression strategy | Columnar compression on chunks older than 1 week (P1 tables) / 1 month (P2/P3 tables) |
| Ordered compression | `ORDER BY (field_id, recorded_at)` for `sensor_readings` aligns with the dominant query pattern |
| Segmentation | `SEGMENTBY field_id` or `sensor_type` depending on access pattern |
| SQLAlchemy impact | Reads on compressed chunks are transparent; compressed chunks cannot be `UPDATE`-ed without decompression |
| Applicability to AGRIFLOW | Append-only `sensor_readings` is the ideal compression candidate. Mutable tables (`irrigation_events`, `yield_records`, `disease_observations`) require careful configuration — only old chunks should be compressed. |
| When to enable | After successful hypertable conversion validation (Step 1E-C) — not in Step 1E-B |

### 7.4 Continuous Aggregates

| Topic | Recommendation |
|---|---|
| Use case | Pre-computed aggregates for `time_bucket()` queries over large hypertables |
| Primary candidates | Hourly average sensor readings by field/type; daily NDVI mean by field/spectral_index; daily weather summaries (GDD, rainfall totals, ET₀) |
| TimescaleDB mechanism | `CREATE MATERIALIZED VIEW ... WITH (timescaledb.continuous)` + `add_continuous_aggregate_policy` |
| Refresh policy | Real-time continuous aggregate refresh or scheduled refresh |
| AGRIFLOW AI readiness | AI Feature Store queries over multi-season windows benefit dramatically from continuous aggregates |
| When to implement | After Step 1E-B (hypertable conversion) — in a subsequent Phase 12 sub-step |

### 7.5 Retention Policies

| Table | Proposed Retention | Rationale |
|---|---|---|
| `sensor_readings` | No automatic deletion — retain full history | IoT history is the AI training data source; deletion loses model training signal |
| `weather_records` | No automatic deletion — retain full history | Historical weather data has scientific value; 10+ year windows for climate analysis |
| `satellite_observations` | No automatic deletion — retain full history | Satellite imagery history is irreplaceable and high-value for multi-season AI training |
| `irrigation_events` | Consider 5-year retention for very high-frequency deployments | Irrigation records are agronomically valuable for multi-season analysis |
| `yield_records` | No automatic deletion — retain full history | Yield history is the primary AI model training target |
| `disease_observations` | No automatic deletion — retain full history | Disease history informs disease risk scoring model training |
| **Overall recommendation** | **Do not enable automatic retention deletion policies** for AGRIFLOW at this stage | All time-series data is AI training material; archiving to cold storage (S3/Azure Blob) is preferable to deletion; retention policies should be configured only if storage costs become a production concern |

### 7.6 Space Partitioning (Second Dimension)

Space partitioning (partitioning by a second column such as `field_id` or `sensor_type`) is evaluated but **not recommended for AGRIFLOW's current scale:**

- Space partitioning is beneficial when a single time chunk exceeds the PostgreSQL memory limit for index lookups
- At development scale (0 rows), this is not relevant
- At production scale, a 100-farm / 1000-field / 100 sensors-per-field deployment generates ~100K-1M rows/week in `sensor_readings` — well within single-dimension hypertable performance envelope
- Space partitioning adds query complexity and should be deferred unless query profiling demonstrates a need

---

## 8. AI Readiness Assessment

### 8.1 Feature Store Foundation

Hypertable conversion establishes the storage foundation for the Phase 13 AI Feature Store:

| AI System | Tables Used | Hypertable Benefit |
|---|---|---|
| **Yield Prediction Engine** | `sensor_readings`, `weather_records`, `yield_records`, `satellite_observations`, `soil_profiles` | `time_bucket()` aggregation over sensor/weather histories enables efficient feature vector construction; chunk exclusion limits I/O to the feature extraction window (e.g., 90-day growing season) |
| **Disease Risk Scoring Engine** | `disease_observations`, `sensor_readings`, `weather_records`, `satellite_observations` | Time-windowed disease incidence, environmental co-occurrence features, and NDVI trajectories all benefit from hypertable scan efficiency |
| **Farm Copilot (Conversational AI)** | All time-series tables | Real-time conversational queries over "last N days" data windows align with TimescaleDB chunk exclusion for fast response |
| **Digital Twin** | `sensor_readings`, `satellite_observations`, `irrigation_events`, `weather_records` | Digital Twin state reconstruction requires efficient multi-domain time-window queries; hypertable chunk exclusion minimizes I/O |
| **Satellite Analytics** | `satellite_observations` | NDVI/EVI/NDWI time series over multi-season windows; `(spectral_index, observed_at)` compound index + hypertable chunk exclusion = efficient feature extraction |
| **Sensor Analytics** | `sensor_readings` | Soil moisture trends; temperature anomaly detection; append-only writes + hypertable = optimal IoT analytics |
| **Time-Series ML** | All P1 tables | `time_bucket()` continuous aggregates serve as the primary materialized feature layer; direct input to Python ML pipelines via SQLAlchemy async queries |

### 8.2 Architectural Benefits for Phase 13

1. **Chunk exclusion eliminates full-table scans** for all time-window feature extraction queries. A query for "last 90 days of sensor data for field X" accesses only 13 chunks (7-day interval), not the entire table.

2. **Parallel query execution** across chunks enables efficient multi-field feature extraction for batch AI training pipelines.

3. **Continuous aggregates** pre-compute `time_bucket()` aggregations (hourly averages, daily summaries) that feed directly into the Feature Store without ad-hoc aggregation overhead.

4. **Compression** on cold chunks (data older than compression policy threshold) reduces AI training data storage by 10–30× while keeping hot (recent) chunks uncompressed and fast.

5. **`list_by_field_and_date_range` → direct hypertable optimization:** The `SatelliteObservationRepository.list_by_field_and_date_range` method, which is the primary Phase 12 AI feature extraction query, maps directly to an optimized hypertable scan with no code changes required.

6. **Append-only `sensor_readings`** maps perfectly to TimescaleDB's immutable historical chunk model — cold IoT data is never updated, making compression lossless.

---

## 9. Performance Assessment

*No benchmarking was performed. Assessment is based on TimescaleDB 2.28.x architecture documentation and query pattern analysis.*

### 9.1 Expected Benefits by Query Type

| Query Type | Expected Improvement | Mechanism |
|---|---|---|
| `WHERE recorded_at BETWEEN :start AND :end` | High | Chunk exclusion eliminates irrelevant time ranges from scan |
| `WHERE field_id = :id AND recorded_at > :cutoff` | High | Compound index `(field_id, recorded_at)` + chunk exclusion |
| `ORDER BY recorded_at DESC LIMIT 100` | High | TimescaleDB returns most recent chunk first; early termination |
| `time_bucket('1 hour', recorded_at)` aggregations | Very High | Columnar format within chunks optimized for aggregate functions |
| `COUNT(*) / SUM() / AVG()` over time windows | Very High | Chunk-level metadata; compressed columnar storage |
| Point lookup by UUID (`WHERE id = :uuid`) | Low | Sequential scan within matching chunk(s); UUID is not the partition key |
| Cross-table JOIN for AI feature assembly | Moderate | Each table benefits independently; JOIN performance unchanged |

### 9.2 Storage Efficiency

| Table | Estimated Annual Row Volume | Compression Ratio | Estimated Storage Saving |
|---|---|---|---|
| `sensor_readings` | 10M–100M (100 fields, 10 sensors) | 10–30× | Very High |
| `weather_records` | 50K–500K (24 readings/day/field) | 8–15× | High |
| `satellite_observations` | 500K–2M (8 indices × 5 passes/week) | 8–20× | High |
| `irrigation_events` | 5K–50K | 3–8× | Medium |
| `yield_records` | 1K–10K | 2–5× | Low |
| `disease_observations` | 5K–50K | 3–8× | Medium |

### 9.3 Weather Records — Missing Compound Index

An architectural gap was identified: `weather_records` is the only time-series table that lacks the `(field_id, recorded_at)` compound index. All other Field-anchored time-series tables have this index established in their original migrations.

**Impact without the compound index:**
- `list_by_field` queries scan `ix_weather_records_field_id` (field predicate only), then sort by `recorded_at`
- With hypertable but no compound index: chunk exclusion helps for time predicates; field predicate uses single index
- The repository's `list_by_field` query will benefit from a compound index after hypertable conversion

**Recommendation:** Add `ix_weather_records_field_id_recorded_at` compound index in the Step 1E-B migration, parallel to the hypertable conversion for `weather_records`.

---

## 10. Risk Assessment

### 10.1 Primary Key Migration Risk

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| `ALTER TABLE DROP CONSTRAINT` fails (constraint in use) | Low | Very Low | No other table references time-series tables via FK — verified in live schema |
| Composite PK adds storage overhead | Low | Certain | UUID (16 bytes) + TIMESTAMPTZ (8 bytes) = 24 bytes per row for PK; minor increase vs 16 bytes UUID-only |
| `session.get(Model, uuid)` breaks | Medium | Low | Repositories use `select().where()` exclusively — `session.get()` is not used; confirmed by codebase review |
| ORM model composite PK declaration error | Medium | Medium | Requires careful SQLAlchemy `mapped_column(primary_key=True)` declaration on both columns; testable on empty dev database |
| Migration fails mid-table on non-empty tables | High | Low | Empty database currently; tables have 0 rows — zero data migration risk at this stage |

### 10.2 `create_hypertable()` Execution Risk

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| `create_hypertable()` fails due to remaining constraints | High | Low | Only after composite PK migration; verify no other unique constraints; use `IF NOT EXISTS` parameter |
| Brief ACCESS EXCLUSIVE lock during conversion | Medium | Certain | Expected behavior; tables are empty — lock duration is milliseconds |
| Alembic async runner incompatibility with `create_hypertable()` | Low | Low | `op.execute("SELECT create_hypertable(...)")` works via `op.execute()` — same pattern as `CREATE EXTENSION` in Step 1D |
| Space partitioning not configured | Low | Very Low | Single-dimension partitioning is correct for current scale |

### 10.3 Repository Compatibility Risk

| Risk | Severity | Mitigation |
|---|---|---|
| `get_by_id` returns multiple rows on duplicate UUID | Medium | UUID is still unique within the composite PK; no duplicate UUIDs possible |
| `update()` on compressed chunks | Medium | Compression policy should not be applied to chunks containing recent data; mutable tables (irrigation, yield, disease) must have compression age threshold > expected UPDATE window |
| `delete()` on compressed chunks | Medium | Same as update; compress only cold/immutable chunks |
| `list_by_field` full-table scan without compound index (weather_records) | Low | Add compound index in Step 1E-B migration |

### 10.4 Foreign Key Impact Assessment

This is a critical assessment finding:

**No foreign key constraint in the schema references any time-series table as a parent.**

All FK references flow in one direction:
```
sensor_readings.field_id → fields.id
weather_records.field_id → fields.id
irrigation_events.field_id → fields.id
satellite_observations.field_id → fields.id
yield_records.crop_id → crops.id
yield_records.field_id → fields.id
disease_observations.crop_id → crops.id
disease_observations.field_id → fields.id
```

The time-series tables are always FK **children**, never FK **parents**. This means:
- Primary key changes on time-series tables have **zero FK cascade impact**
- No constraint violation is possible from the PK migration
- No `ALTER TABLE` on reference tables is required

### 10.5 SQLAlchemy Compatibility

| Concern | Assessment |
|---|---|
| Composite PK in SQLAlchemy 2.0 ORM | Fully supported via `mapped_column(primary_key=True)` on both columns |
| `identity_key()` semantics with composite PK | Not used in AGRIFLOW — identity is managed via `WHERE id = :id` queries |
| `expire_on_commit=False` session config | Unchanged; no interaction with PK composition |
| `autoflush=False` session config | Unchanged |
| Alembic autogenerate with composite PK | Works correctly; `compare_type=True` in env.py ensures type changes are detected |

### 10.6 Alembic Migration Risk

| Risk | Severity | Mitigation |
|---|---|---|
| Existing migration history immutability | None | New forward migrations only; existing 12 migrations untouched |
| Composite PK migration not reversible | Medium | Downgrade drops composite PK, restores UUID-only PK, then drops hypertable (`drop_chunks` if needed) |
| `create_hypertable()` in Alembic downgrade | High | Downgrade must explicitly remove hypertable objects before reverting PK; document governance like Step 1D downgrade |
| Migration branch conflict | None | Linear history maintained; single new revision per step |

### 10.7 Neo4j Synchronization Impact

*Note: Neo4j graph synchronization is referenced in the assessment scope. AGRIFLOW-AI's current codebase does not yet contain Neo4j synchronization code (no Neo4j connectors, adapters, or sync services were found in the reviewed codebase). This risk is therefore assessed as "Future — Design-Time".*

| Concern | Assessment |
|---|---|
| FK cascade behavior changes | None — PK changes do not alter FK CASCADE behavior |
| UUID identity for graph node IDs | UUID is preserved as the primary application identifier; Neo4j node IDs can continue to use UUID |
| Hypertable chunking transparency | TimescaleDB hypertables appear as standard PostgreSQL tables to application code; no Neo4j sync code changes required |
| Time-window queries for graph construction | Hypertable chunk exclusion benefits sync queries that construct graph edges over time windows |

---

## 11. Implementation Recommendation for Step 1E-B

### 11.1 Pre-Implementation Requirements

Before Step 1E-B execution:

1. **ADR-002 must be drafted and approved** — formalizes the Composite Primary Key decision and hypertable conversion sequence.
2. **Step 1E-B migration plan must be reviewed** — verify PK migration DDL per table before execution.
3. **Pre-migration backup** — `pg_dump` custom format backup following P12-D003 protocol.
4. **Empty table confirmation** — all six tables currently have 0 rows; execution carries no data migration risk at this stage. Future executions in non-empty environments require `migrate_data => TRUE`.

### 11.2 Recommended Conversion Order

Convert tables in priority order, with validation between each group:

**Group 1 — P1 Critical (execute together, empty tables):**
1. `sensor_readings` — highest AI value; append-only
2. `weather_records` — add compound index simultaneously
3. `satellite_observations` — richest repository; most complex access patterns

**Group 2 — P2 High (after Group 1 validation):**
4. `irrigation_events`
5. `yield_records`

**Group 3 — P3 Standard (after Group 2 validation):**
6. `disease_observations`

*All six tables are currently empty, so groups could be merged into a single migration. The priority order is recommended to isolate rollback scope if an issue arises.*

### 11.3 Per-Table Migration Pattern

Each table follows this four-step pattern in a single Alembic migration:

```python
# Step 1: Drop UUID-only primary key
op.drop_constraint("pk_<table>", "<table>", type_="primary")

# Step 2: Add composite primary key (id + partition column)
op.create_primary_key("pk_<table>", "<table>", ["id", "<time_col>"])

# Step 3: Create hypertable
op.execute(
    "SELECT create_hypertable('<table>', '<time_col>', "
    "migrate_data => TRUE, if_not_hypertable => TRUE);"
)

# Step 4 (weather_records only): Add missing compound index
op.create_index("ix_weather_records_field_id_recorded_at", "weather_records", ["field_id", "recorded_at"])
```

**Downgrade pattern:**
```python
# For each table in reverse order:
op.execute("SELECT decompress_chunk(c) FROM show_chunks('<table>') c;")  # if compression active
op.execute("SELECT drop_hypertable('<table>', cascade => FALSE);")
op.drop_constraint("pk_<table>", "<table>", type_="primary")
op.create_primary_key("pk_<table>", "<table>", ["id"])
```

*Downgrade governance: same restriction as Step 1D — hypertable removal is destructive after data exists in chunks. Post-production deployment: use Tier 2 backup restore.*

### 11.4 Rollback Considerations

| Scenario | Rollback Path |
|---|---|
| Before any conversion | P12-D005 Tier 3: Alembic downgrade |
| After partial conversion (tables empty) | Alembic downgrade per group |
| After data ingestion begins on hypertables | P12-D005 Tier 2: pg_dump restore |
| After compression enabled | Must decompress all chunks before downgrade |

### 11.5 Testing Strategy

| Test | Method |
|---|---|
| `create_hypertable()` succeeds | Verify `timescaledb_information.hypertables` shows all 6 tables |
| `get_by_id(uuid)` returns correct row | Repository smoke test after migration |
| `list_by_field()` returns rows in time order | Repository smoke test with sample data |
| Composite PK rejects duplicate `(id, time_col)` | Insert same UUID + time twice → expect constraint violation |
| FK cascades still function | Delete a `fields` record → verify `sensor_readings` cascade delete |
| Backend starts and Swagger accessible | `GET /docs` → HTTP 200 |
| All existing API endpoints respond | Spot-check GET endpoints for each domain |

---

## 12. Decision Preparation for ADR-002

The following architectural decisions require formal recording in ADR-002 before Step 1E-B implementation.

| Decision Topic | Recommendation | Status Required for Step 1E-B |
|---|---|---|
| **Primary Key Strategy** | Composite PK `(id, time_col)` — Strategy A | **Needs ADR-002 — Required** |
| **Hypertable candidates** | Six tables: sensor_readings, weather_records, satellite_observations, irrigation_events, yield_records, disease_observations | **Needs ADR-002 — Required** |
| **Tables remaining relational** | farms, fields, crops, soil_profiles | **Needs ADR-002 — Required** |
| **Chunk interval — P1 tables** | 7 days (sensor_readings, weather_records, satellite_observations) | **Needs ADR-002 — Required** |
| **Chunk interval — P2 tables** | 1 month (irrigation_events, disease_observations); 3 months (yield_records) | **Needs ADR-002 — Required** |
| **Compression policy** | Deferred to Step 1E-C (after successful hypertable conversion) | Deferred |
| **Retention policy** | No automatic deletion; archiving policy to be designed separately | Deferred |
| **Continuous aggregates** | Deferred to Step 1E-D (after compression confirmed) | Deferred |
| **Repository analytics — `time_bucket()` methods** | Deferred to Step 1E-E (requires separate ADR per repository) | Deferred |
| **Space partitioning** | Not required at current scale; defer until query profiling demonstrates need | Deferred |
| **weather_records compound index** | Add `(field_id, recorded_at)` in Step 1E-B migration | **Needs ADR-002 — Required** |

---

## 13. Summary of Findings

### Architecture Findings

1. **Six tables are strong hypertable candidates.** All six have `TIMESTAMPTZ NOT NULL` partition columns, compound indexes aligned with TimescaleDB access patterns, and repository queries ordered by the partition column.

2. **Four tables must remain relational.** `farms`, `fields`, `crops`, and `soil_profiles` are reference data entities with no time-series growth characteristics. Hypertable conversion would provide no benefit and would break `soil_profiles`'s one-to-one unique constraint semantics.

3. **UUID primary keys can be preserved.** Composite PK `(id, time_col)` satisfies TimescaleDB's constraint requirement while preserving UUID as the application-level identity. No API, service, repository interface, schema, or business logic changes are required.

4. **`BaseRepository.get_by_id` requires no changes.** The predicate-based query pattern (`WHERE id = :id`) is the correct implementation and is completely insensitive to PK composition.

5. **No foreign key impact.** All FK references in AGRIFLOW-AI flow from time-series tables to reference tables — never in the reverse direction. Composite PK changes on time-series tables have zero FK cascade impact.

6. **`weather_records` has a missing compound index.** All other Field-anchored time-series tables have `(field_id, time_col)` compound indexes. This gap should be corrected in Step 1E-B.

7. **Migration risk is low.** All six tables currently have 0 rows. The migration period before data ingestion begins is the optimal window for hypertable conversion.

### Decisions Approved for Implementation (Pending ADR-002)

- Six tables → hypertables (names, partition columns, chunk intervals per §5)
- Composite PK Strategy A for all six tables
- Add missing `weather_records` compound index in Step 1E-B

### Decisions Remaining Deferred

- Compression policies (Step 1E-C)
- Continuous aggregates (Step 1E-D)
- Retention policies (design-time decision)
- Repository `time_bucket()` analytics methods (Step 1E-E — separate ADR per domain)
- Space partitioning (defer pending production query profiling)

---

## 14. Compliance Statement

This assessment is read-only. No schema changes, migrations, Docker modifications, or application code changes were made.

| Constraint | Compliant |
|---|---|
| Step 1A approved baseline | ✅ |
| Step 1B infrastructure plan | ✅ |
| Decision Register v1.2 | ✅ |
| No hypertables created | ✅ |
| No `create_hypertable()` executed | ✅ |
| No primary keys modified | ✅ |
| No migrations created | ✅ |
| No Docker modifications | ✅ |
| No SQLAlchemy model modifications | ✅ |
| No repository modifications | ✅ |
| No service modifications | ✅ |
| No API modifications | ✅ |
| No schema modifications | ✅ |

---

*Assessment v1.0 — Phase 12 Step 1E-A Hypertable Architecture Assessment*  
*Status: Draft — Pending Architecture Review Approval*  
*Executed: 2026-06-29 — Read-only activity*
