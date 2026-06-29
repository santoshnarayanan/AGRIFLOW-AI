# ADR-002 — Hypertable Primary Key & Conversion Strategy

**Status:** Approved  
**Date:** 2026-06-29  
**Phase:** 12 — TimescaleDB Time-Series Foundation  
**Step:** 1E-A (Assessment) → 1E-B (Implementation Authorized)  
**Decision Makers:** Senior Platform Architecture  
**Governance References:** `PHASE12_DECISION_REGISTER.md` P12-D007, P12-D008, P12-D009

---

## Related ADRs

| ADR | Title | Relationship |
|---|---|---|
| ADR-001 | TimescaleDB Extension Enablement | Prerequisite — TimescaleDB 2.28.1 active in `agriflow` database as a direct result of ADR-001. ADR-002 depends on ADR-001 having been executed. |

---

## Context

### Existing PostgreSQL Architecture

AGRIFLOW-AI operates on PostgreSQL 17.10 running inside the `timescale/timescaledb:2.28.1-pg17` Docker image (adopted in Phase 12 Step 1C). The database schema contains ten domain tables organised around a Domain-Driven Design (DDD) aggregate hierarchy:

```
Farm → Field → Crop
         ↓
  SensorReading     WeatherRecord     SatelliteObservation
  IrrigationEvent   YieldRecord       DiseaseObservation
  SoilProfile
```

Every domain table inherits from `AuditableModel`, which assigns a UUID v4 primary key (`id UUID NOT NULL`) as the application-level identity. All FK references flow from time-series tables toward reference tables — no external table holds a FK reference to any time-series table.

### TimescaleDB Extension Active

As formalised in ADR-001, TimescaleDB 2.28.1 was enabled in the `agriflow` database via Alembic migration `f1e2d3c4b5a6` on 2026-06-29. The migration history is linear and version-controlled. Zero hypertables exist at the time of this ADR.

### Need for Efficient Time-Series Storage

Six of the ten domain tables are high-frequency temporal measurement domains:

- **`sensor_readings`** — continuous IoT telemetry (sub-hourly)
- **`weather_records`** — meteorological observations (daily to sub-hourly)
- **`satellite_observations`** — multi-spectral satellite imagery (5–16-day revisit per provider)
- **`irrigation_events`** — agricultural water management events
- **`yield_records`** — crop harvest measurements
- **`disease_observations`** — crop disease and pathogen pressure events

These tables accumulate time-ordered rows unboundedly across growing seasons. Their dominant query patterns are time-windowed range scans anchored by field (`WHERE field_id = :id AND time_col BETWEEN :start AND :end`). Standard PostgreSQL table scans become increasingly expensive as historical data grows; TimescaleDB hypertable partitioning eliminates irrelevant time ranges from all such queries through chunk exclusion.

### Existing UUID-Based DDD Model

The UUID-only primary key pattern is foundational to AGRIFLOW-AI's architecture. All API routes use `/{id}` path parameters. All repository `get_by_id` methods resolve identity via `WHERE id = :id` predicate queries. All Pydantic response schemas expose UUID as the resource identifier. This pattern must be preserved without modification at the API, service, repository interface, or schema layers.

### Importance of Preserving Backward Compatibility

`BaseRepository.get_by_id` is implemented as:

```python
select(self._model).where(self._model.id == record_id)
```

This is a predicate filter on the `id` column, not a primary key composite tuple lookup (`session.get(Model, (uuid, datetime))`). This distinction is architecturally critical: primary key composition changes at the database layer have zero impact on this query form.

### AI Roadmap Requiring Scalable Historical Data

Phase 13 introduces the AI Feature Store, which constructs feature vectors over multi-season time windows. Phase 14 deploys the Yield Prediction Engine, which trains on multi-year yield, weather, and satellite history. Phase 15 (Farm Copilot) and Phase 16 (Digital Twin) depend on sub-second response to time-window queries over sensor and satellite archives. These capabilities require TimescaleDB's chunk exclusion, `time_bucket()` aggregation, and columnar compression — none of which are available without hypertable conversion.

---

## Problem Statement

The Step 1E-A Architecture Assessment identified the following questions requiring formal resolution before Step 1E-B implementation:

1. **Which tables should become hypertables?** Ten domain tables exist. Not all tables have time-series growth characteristics. Indiscriminate conversion would break reference data integrity constraints.

2. **Which tables must remain relational?** Reference data entities (farms, fields, crops, soil profiles) do not exhibit time-series growth patterns and carry unique constraints that are semantically incompatible with hypertable partitioning.

3. **How should UUID primary keys be handled?** TimescaleDB 2.28.x enforces that every unique constraint — including primary keys — must include the partitioning column. The current `PRIMARY KEY (id)` on all six time-series candidates prevents `create_hypertable()` from succeeding.

4. **How should foreign keys be preserved?** FK references that point to time-series tables as parents would require modification if the PK composition changes. This needed explicit audit.

5. **How should the Repository and Service layers remain unchanged?** The architecture requires that hypertable conversion be transparent to all code above the migration layer.

6. **How should future AI capabilities be supported?** The approved PK and partition strategy must support `time_bucket()` aggregations, Feature Store extraction windows, compression on cold chunks, and multi-season model training data access — without requiring further architectural changes.

---

## Alternatives Considered

### Option 1 — Convert Every Table to Hypertables

**Description:** Apply `create_hypertable()` to all ten domain tables, including `farms`, `fields`, `crops`, and `soil_profiles`.

**Why Rejected:**

- `soil_profiles` carries a `UNIQUE INDEX (field_id)` that enforces a one-to-one relationship with `fields`. This unique constraint cannot include a time partition column because `soil_profiles` has no meaningful time dimension. Hypertable conversion would require dropping the uniqueness constraint, destroying the one-to-one semantics.
- `farms` has a `UNIQUE (farm_code)` business key constraint. Including a time partition column in this unique constraint has no meaningful interpretation — farms do not have a time dimension by which they would be naturally partitioned.
- `crops` has lifecycle date columns (`planting_date DATE`, `actual_harvest_date DATE`) that are domain milestones, not measurement timestamps. A single farm field produces one to a few crop cycles per year — hypertable chunking on crop records produces no performance benefit and adds partitioning overhead on an inherently low-cardinality table.
- `fields` is the spatial dimension entity. Time-series data is anchored *on* fields via FK — the field record itself is not a measurement.
- Converting reference data entities to hypertables provides no query benefit (no time-range scans) while adding unnecessary complexity and potentially breaking unique constraint semantics.

---

### Option 2 — Preserve Relational Model Only

**Description:** Do not convert any tables to hypertables. Retain standard PostgreSQL for all ten tables and rely on standard index scans for time-window queries.

**Why Rejected:**

- PostgreSQL B-tree index scans on multi-million-row time-series tables require full index traversal for range predicates. As `sensor_readings` grows toward 10M–100M rows per year across a 100-field deployment, range scans become proportionally expensive.
- `time_bucket()` aggregation — required by the AI Feature Store, GDD/ET₀ calculations, and Yield Prediction Engine — is only available on TimescaleDB hypertables. The Phase 12 objective explicitly requires TimescaleDB hypertable storage.
- Columnar compression (10–30× storage reduction on cold IoT and satellite data) is not available on standard PostgreSQL tables.
- The Phase 12 approved baseline in Step 1A §2.3 explicitly specifies hypertable conversion as a Phase 12 deliverable. This option conflicts with the approved architecture baseline.

---

### Option 3 — Selective Hypertable Adoption ✅ Approved

**Description:** Convert the six time-series measurement tables to hypertables. Retain the four reference data tables as standard PostgreSQL relations permanently.

**Why Approved:**

- Targets only tables with genuine time-series growth characteristics and time-window query patterns.
- Preserves all unique constraint semantics on reference data entities.
- Maps precisely to AGRIFLOW-AI's domain separation: reference data (farms, fields, crops, soil profiles) vs. measurement data (sensor, weather, satellite, irrigation, yield, disease).
- Provides the TimescaleDB capabilities required by the AI roadmap (chunk exclusion, `time_bucket()`, compression) on the tables that need them.
- Consistent with TimescaleDB best practice guidance: do not convert tables that do not exhibit time-series growth or whose data volumes do not justify chunking.

---

### Primary Key Strategy Alternatives

All six hypertable candidates carry `PRIMARY KEY (id)` where `id` is UUID v4. TimescaleDB 2.28.x requires that any UNIQUE constraint (including PRIMARY KEY) on a hypertable must include the partitioning column. Four strategies were evaluated.

---

#### Strategy A — Composite Primary Key `(id, time_col)` ✅ Approved

**Description:** Alter each time-series table's primary key from `(id)` to `(id, time_col)`.

| Table | Current PK | Approved PK |
|---|---|---|
| `sensor_readings` | `(id)` | `(id, recorded_at)` |
| `weather_records` | `(id)` | `(id, recorded_at)` |
| `satellite_observations` | `(id)` | `(id, observed_at)` |
| `irrigation_events` | `(id)` | `(id, started_at)` |
| `yield_records` | `(id)` | `(id, recorded_at)` |
| `disease_observations` | `(id)` | `(id, observed_at)` |

**Why Approved:**

- TimescaleDB constraint satisfied: partition column is now part of the primary key.
- UUID identity fully preserved: `id` remains in the primary key and is globally unique within the table. No UUID is ever duplicated for the same `time_col` value.
- `BaseRepository.get_by_id` uses `select().where(Model.id == id)` — a WHERE clause predicate, not a composite PK tuple lookup. The repository executes identically regardless of PK composition.
- No external table holds a FK reference to any time-series table. PK composition changes have zero FK cascade impact (verified against live schema on 2026-06-29).
- API routes, service interfaces, repository interfaces, and Pydantic schemas are all unchanged — they operate on UUID as the application identity.
- Reversible: composite PK can be dropped and UUID-only PK restored as a downgrade migration.
- Standard pattern: documented as the canonical approach for UUID-keyed applications adopting TimescaleDB.

---

#### Strategy B — Drop PK, Replace with Composite UNIQUE Index

**Description:** Drop the PRIMARY KEY constraint. Add `UNIQUE INDEX (id, time_col)` to satisfy TimescaleDB. Add a non-unique `INDEX (id)` for lookup performance.

**Why Not Recommended:**

- No true PRIMARY KEY constraint means the table lacks formal relational identity semantics. Some database tooling (pgAdmin, BI tools, ORM introspection) handles PK-less tables poorly.
- Semantically weaker than Strategy A with no additional benefit. Strategy A achieves TimescaleDB compatibility while retaining full relational integrity.

---

#### Strategy C — Integer Surrogate PK + UUID Application Identity

**Description:** Add a `BIGSERIAL` column `_pk`. Change primary key to `(_pk, time_col)`. Retain UUID `id` as a NOT NULL column with a `UNIQUE (id, time_col)` constraint.

**Why Rejected:**

- Requires adding a new column to every time-series table — a larger schema change than Strategy A.
- UUID-only `UNIQUE (id)` still fails TimescaleDB's requirement; the UUID uniqueness must anyway be expressed as `UNIQUE (id, time_col)`, negating the rationale for a surrogate key.
- ORM models require restructuring (surrogate key as identity field).
- Adds 8 bytes per row storage overhead with no architectural benefit over Strategy A.

---

#### Strategy D — Remove All Unique Constraints

**Description:** Drop primary keys and all unique constraints on time-series tables. `create_hypertable()` does not require unique constraints.

**Why Rejected:**

- UUID uniqueness is no longer enforced at the database layer. Duplicate rows can be inserted. `get_by_id` could return multiple rows.
- Fundamentally incompatible with production-grade architecture. Destroys data integrity guarantees that every layer above the database depends on.

---

## Approved Decisions

### Hypertable Candidate Tables

The following six tables are approved for hypertable conversion in Step 1E-B:

| Priority | Table | Timestamp Column | Domain Role |
|---|---|---|---|
| P1 — Critical | `sensor_readings` | `recorded_at` | IoT telemetry; highest insert frequency; AI Feature Store backbone |
| P1 — Critical | `weather_records` | `recorded_at` | Meteorological time-series; GDD and ET₀ calculation source |
| P1 — Critical | `satellite_observations` | `observed_at` | Multi-spectral remote sensing; primary AI training data source |
| P2 — High | `irrigation_events` | `started_at` | Agricultural water management events; irrigation analytics |
| P2 — High | `yield_records` | `recorded_at` | Harvest measurements; Yield Prediction Engine target variable |
| P3 — Standard | `disease_observations` | `observed_at` | Disease pressure events; Disease Risk Scoring Engine features |

All six timestamp columns are `TIMESTAMPTZ NOT NULL` — verified in the live schema prior to this assessment.

An additional schema correction is approved for `weather_records`: the compound index `(field_id, recorded_at)` is missing from the original migration. This index is present on all other Field-anchored time-series tables. It must be added in the Step 1E-B migration alongside the `weather_records` hypertable conversion.

---

### Relational Tables

The following four tables must remain standard PostgreSQL relations permanently:

| Table | Reason for Remaining Relational |
|---|---|
| `farms` | Root aggregate master data. No time-series growth pattern. Carries `UNIQUE (farm_code)` business key. Very low row count (tens to hundreds per deployment). |
| `fields` | Spatial dimension entity. All time-series measurement data anchors *on* fields via FK — the field record itself is not a measurement. No time-series growth. |
| `crops` | Lifecycle management entity. `planting_date` and `actual_harvest_date` are DATE-type milestones, not TIMESTAMPTZ measurement timestamps. Low row count (one to a few records per field per year). |
| `soil_profiles` | Static one-to-one companion to `fields`. Bounded row count (exactly one per field). Carries `UNIQUE (field_id)` which enforces the one-to-one constraint — this constraint cannot include a time partition column as no time dimension exists for soil profiles. |

---

### Primary Key Strategy

**Approved strategy: Composite Primary Key `(id, time_col)` — Strategy A.**

For each of the six hypertable candidate tables, the primary key must be altered from `PRIMARY KEY (id)` to `PRIMARY KEY (id, <partition_column>)` before `create_hypertable()` is invoked.

The per-table migration pattern authorised by this ADR:

```sql
-- Step 1: Drop the UUID-only primary key
ALTER TABLE <table> DROP CONSTRAINT pk_<table>;

-- Step 2: Add composite primary key including the partition column
ALTER TABLE <table> ADD CONSTRAINT pk_<table> PRIMARY KEY (id, <time_col>);

-- Step 3: Create the hypertable
SELECT create_hypertable('<table>', '<time_col>',
    migrate_data => TRUE,
    if_not_hypertable => TRUE
);
```

UUID `id` remains the application-level identity. All API routes, service methods, repository interfaces, and Pydantic schemas continue to use UUID as the resource identifier without modification.

---

### Chunk Interval Strategy

Chunk intervals are sized to match each table's ingest rate and the dominant time-window query pattern, following TimescaleDB guidance that chunk size should be approximately one-fifth to one-twentieth of the total data retention window for the most recent data.

| Table | Approved Chunk Interval | Rationale |
|---|---|---|
| `sensor_readings` | 7 days | Sub-hourly IoT data. 7-day chunks align with telemetry dashboard and Feature Store extraction windows. Enables compression on 1-week-old cold chunks. |
| `weather_records` | 7 days | Daily to sub-daily data. Weekly chunks match agro-meteorological query windows (GDD and ET₀ accumulated over growing season segments). |
| `satellite_observations` | 7 days | Sentinel-2 5-day revisit produces 1–2 passes per 7-day chunk. Weekly chunks align with vegetation index time-series feature extraction. |
| `irrigation_events` | 1 month | Weekly to seasonal ingest frequency. Monthly chunks align with water management reporting periods and FAO-56 water balance calculation windows. |
| `disease_observations` | 1 month | Episodic ingest (0–50 observations per crop cycle). Monthly chunks are appropriate for disease season analysis. |
| `yield_records` | 3 months | Harvest-time only; sparse ingest (1–5 records per crop cycle per field). Quarterly chunks avoid over-partitioning on low-frequency data. |

Space partitioning (second-dimension partitioning by `field_id` or `sensor_type`) is intentionally deferred. Single-dimension time partitioning is the correct choice for AGRIFLOW-AI's current and projected scale. Space partitioning should be reconsidered only if production query profiling demonstrates that single-dimension chunks exceed PostgreSQL's memory limits for index lookups.

---

### Future Compression

Columnar compression on cold hypertable chunks is **intentionally deferred to Step 1E-C**.

Rationale for deferral:
- Compression must not be enabled until hypertable conversion has been successfully validated (hypertables exist, all API endpoints respond, repository smoke tests pass).
- Mutable tables (`irrigation_events`, `yield_records`, `disease_observations`) require careful age-threshold configuration to avoid compressing chunks that may still receive UPDATE operations. This configuration requires a separate design review.
- Primary compression targets are `sensor_readings`, `weather_records`, and `satellite_observations` — the highest-volume append-only or near-immutable tables.
- Step 1E-B must not include any `add_compression_policy()` or `ALTER TABLE ... SET (timescaledb.compress)` DDL.

---

### Future Continuous Aggregates

Continuous aggregates (`CREATE MATERIALIZED VIEW ... WITH (timescaledb.continuous)`) are **intentionally deferred to Step 1E-D**.

Rationale for deferral:
- Continuous aggregates require hypertables to exist (Step 1E-B) and ideally compression to be confirmed (Step 1E-C) before materialised views are established.
- Primary candidates include hourly average sensor readings by `(field_id, sensor_type)`, daily weather summaries by `field_id`, and daily NDVI/EVI means by `(field_id, spectral_index)`.
- Each continuous aggregate introduces a separate DDL object and refresh policy that requires its own architectural review and migration.
- Step 1E-B must not include any continuous aggregate DDL.

---

### Future Retention Policies

Automatic retention deletion policies are **intentionally deferred and explicitly not recommended for the Phase 12 baseline**.

Rationale:
- All AGRIFLOW-AI time-series data is AI model training material. Automatic deletion would degrade AI model quality by removing historical signal that cannot be recovered.
- Retention policy decisions are business data lifecycle decisions, not infrastructure decisions. They require explicit product owner approval specifying which data is deletable and at what age.
- The recommended long-term approach is archival to Azure Blob Storage or equivalent cold storage before any deletion, preserving model training data while managing primary database storage costs.
- Step 1E-B must not include any `add_retention_policy()` DDL.

---

## Architectural Principles

The approved hypertable conversion strategy is explicitly designed to preserve AGRIFLOW-AI's architectural foundations:

**Domain-Driven Design:** The six hypertable tables correspond precisely to measurement domain entities. The four reference data tables remain relational. The DDD aggregate hierarchy (`Farm → Field → Crop → ...`) is unchanged in structure and semantics.

**Clean Architecture:** The hypertable conversion is entirely a persistence infrastructure concern. No change propagates to the domain model, application services, or API layer.

**Repository Pattern:** All six domain repositories use `select().where(Model.id == id)` predicate queries throughout. The `BaseRepository` interface is unchanged. Repository callers are unaware of the underlying hypertable partitioning.

**Service Layer:** Service methods operate on domain objects and UUID identifiers. The hypertable conversion introduces no new service-layer concepts or method signatures.

**API Contracts:** All existing API routes continue to use `/{id}` UUID path parameters. No API versioning is required. No response schema changes are required.

**SQLAlchemy Compatibility:** SQLAlchemy 2.0 fully supports composite primary keys via `mapped_column(primary_key=True)` on multiple columns. The ORM session's `expire_on_commit=False` and `autoflush=False` configurations are unaffected. Identity key tuple semantics (`session.get(Model, (uuid, datetime))`) are not used anywhere in the codebase — all identity resolution uses WHERE predicate queries.

**Alembic Governance:** Hypertable conversion is implemented exclusively through forward Alembic migrations with downgrade paths. No migration in the existing linear chain is modified. All DDL remains version-controlled.

**Neo4j Integration:** AGRIFLOW-AI's Neo4j graph integration (future) will use UUID as the graph node identifier — the same UUID that remains the application-level identity after composite PK adoption. TimescaleDB hypertables appear as standard PostgreSQL tables to application code; no Neo4j synchronisation changes are required.

---

## Consequences

### Positive Outcomes

- **Query performance:** Chunk exclusion eliminates irrelevant time ranges from all time-window scans. A "last 90 days" query on `sensor_readings` with a 7-day chunk interval accesses 13 chunks instead of the full table — regardless of total historical row count.
- **AI Feature Store enablement:** `time_bucket()` aggregation becomes available on all six time-series tables. This is the prerequisite for Phase 13 Feature Store materialisation pipelines.
- **Storage efficiency foundation:** Once compression is enabled (Step 1E-C), estimated storage reduction of 10–30× on `sensor_readings`, 8–15× on `weather_records`, and 8–20× on `satellite_observations`.
- **Operational transparency:** Hypertable conversion is invisible to all existing API consumers. The system continues to function identically from the application perspective immediately after migration.
- **Zero code changes required:** No API, service, repository, Pydantic schema, or business logic changes are needed for Step 1E-B.

### Accepted Trade-offs

- **Composite PK storage overhead:** Each row in the six time-series tables gains 8 bytes in PK storage (UUID 16 bytes → composite `(UUID, TIMESTAMPTZ)` 24 bytes). At current data volumes this is negligible. At 100M rows in `sensor_readings`, the overhead is approximately 800 MB — offset by the 10–30× compression ratio once Step 1E-C is executed.
- **ORM model update required:** Each of the six SQLAlchemy models must declare both `id` and the time column with `primary_key=True`. This is a model-layer change, not a repository-interface change. It is a one-time update per table required to keep the ORM and database schema consistent.
- **`create_hypertable()` is non-transactional:** The function modifies TimescaleDB internal catalog state and cannot be rolled back within an Alembic transaction. The approved mitigation is the pre-migration `pg_dump` backup per P12-D003.
- **ACCESS EXCLUSIVE lock during conversion:** `create_hypertable()` takes an ACCESS EXCLUSIVE lock for the duration of the conversion. For empty tables (current state), this lock duration is milliseconds. For future non-empty tables, this must be planned as a maintenance window operation.

### Future Work

- Step 1E-C: Design and implement compression policies for P1 tables.
- Step 1E-D: Design and implement continuous aggregates for Feature Store materialisation.
- Step 1E-E: Implement `time_bucket()` repository analytics methods (separate ADR per domain).
- Retention and archival policy: Design-time business decision; requires product owner approval.
- Space partitioning: Evaluate after production query profiling.

---

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `ALTER TABLE DROP CONSTRAINT` fails — constraint referenced by FK | Low | Confirmed: no external table holds a FK reference to any time-series table (verified against live schema 2026-06-29). Zero FK cascade risk. |
| `create_hypertable()` fails due to remaining unique constraints | Medium | Drop composite PK first; verify no other unique indexes on the partition column before executing `create_hypertable()`. Use `if_not_hypertable => TRUE` parameter. |
| ORM composite PK declaration error causes SQLAlchemy runtime failure | Medium | ORM models must declare both `id` and `time_col` with `primary_key=True`. Test immediately after migration against all six repositories before declaring Step 1E-B complete. |
| `session.get(Model, uuid)` silently passes composite PK tuple | Low | Confirmed: `session.get()` is not used in any domain repository. All lookups use `select().where()`. Verify with codebase search before Step 1E-B execution. |
| Alembic async runner incompatibility with `create_hypertable()` | Low | `op.execute("SELECT create_hypertable(...)")` is the same execution pattern used successfully for `CREATE EXTENSION` in Step 1D (migration `f1e2d3c4b5a6`). |
| Migration rolled back after partial conversion leaves schema in inconsistent state | Medium | Execute per-table migration groups with validation checkpoints. Pre-migration backup per P12-D003 is a mandatory gate. |
| Future `UPDATE` on compressed chunks fails silently | Medium | Deferred until Step 1E-C. Compression age thresholds on mutable tables must be set above the expected UPDATE recency window. Not a risk for Step 1E-B (no compression). |

---

## Decision Traceability

The following decision chain produced this ADR:

```
Step 1A — Infrastructure Assessment
   ↓
   Established PostgreSQL 17 + TimescaleDB architecture baseline.
   Identified hypertable conversion as a Phase 12 deliverable.
   Deferred primary key strategy to a follow-on Architecture Decision Review.
   Reference: PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md §2.3, §5.5
        ↓
Step 1B — TimescaleDB Infrastructure Plan
   ↓
   Selected timescale/timescaledb:2.28.1-pg17 image (P12-D001, P12-D002).
   Established pre-migration backup protocol (P12-D003).
   Defined three-tier rollback model (P12-D005).
   Reference: PHASE12_STEP1B_TIMESCALEDB_INFRASTRUCTURE_PLAN.md §7
        ↓
Step 1C — Infrastructure Execution
   ↓
   Executed Docker image swap from postgres:17-alpine to timescale/timescaledb:2.28.1-pg17.
   TimescaleDB binaries confirmed present; extension not yet installed.
   Reference: PHASE12_STEP1C_IMPLEMENTATION_REPORT.md §8, §9
        ↓
Step 1D — Extension Enablement (ADR-001)
   ↓
   TimescaleDB 2.28.1 enabled via Alembic migration f1e2d3c4b5a6.
   shared_preload_libraries configuration gap resolved (P12-D006).
   TimescaleDB API now available; zero hypertables; primary key question deferred.
   Reference: PHASE12_STEP1D_EXTENSION_ENABLEMENT_REPORT.md; ADR-001
        ↓
Step 1E-A — Hypertable Architecture Assessment
   ↓
   Evaluated all ten domain tables against hypertable suitability criteria.
   Identified six candidates; confirmed four remain relational.
   Identified UUID-only PK incompatibility with TimescaleDB 2.28.x unique constraint requirement.
   Evaluated four primary key strategies (A, B, C, D); recommended Strategy A.
   Confirmed zero repository code changes required (WHERE predicate pattern).
   Confirmed zero FK cascade impact (no external FK to time-series tables).
   Defined per-table chunk interval recommendations.
   Identified weather_records missing compound index gap.
   Reference: PHASE12_STEP1EA_HYPERTABLE_ARCHITECTURE_ASSESSMENT.md
        ↓
ADR-002 — Hypertable Primary Key & Conversion Strategy (This Document)
   ↓
   Formalises approved decisions from Step 1E-A assessment.
   Authorises Step 1E-B implementation.
```

| Step | Contribution to Final Architecture |
|---|---|
| Step 1A | Defined the architecture baseline. Identified TimescaleDB as the time-series layer. Deferred PK strategy, requiring a formal ADR before execution — ensuring the decision would be evidence-based rather than ad-hoc. |
| Step 1B | Established the infrastructure approach (official image, pinned version, backup protocol, rollback model) that made Steps 1C and 1D safe to execute. |
| Step 1C | Confirmed the Docker infrastructure was ready to host TimescaleDB. Revealed the `shared_preload_libraries` gap that was resolved in Step 1D. |
| Step 1D | Activated TimescaleDB in the `agriflow` database. Established that `op.execute()` within Alembic migrations can successfully invoke TimescaleDB DDL — the same pattern used for `create_hypertable()` in Step 1E-B. |
| Step 1E-A | Provided the complete evidence base for this ADR: live schema analysis, repository code review, FK audit, TimescaleDB compatibility assessment, and per-table suitability analysis. Confirmed Strategy A with zero application-layer impact. |
| ADR-002 | Formalises the evidence-based decisions. Establishes the governance record for future developers to understand the design without needing to reconstruct the full assessment trail. |

---

## Impact on Future Phases

### Phase 12 — TimescaleDB Time-Series Foundation

ADR-002 unblocks Step 1E-B (hypertable conversion migration), Step 1E-C (compression policies), and Step 1E-D (continuous aggregates). It establishes the storage foundation that all subsequent Phase 12 sub-steps build upon.

### Phase 13 — AI Feature Store

The hypertable conversion enables the Feature Store to use `time_bucket()` aggregation over multi-season time windows without full-table scans. Chunk exclusion limits I/O to the feature extraction window (e.g., 90-day growing season = 13 chunks at 7-day interval). The `sensor_readings` and `satellite_observations` hypertables are the primary Feature Store data sources. Continuous aggregates (Step 1E-D) provide materialised hourly and daily summary layers that feed directly into Feature Store pipelines.

### Phase 14 — Yield Prediction Engine

The Yield Prediction Engine trains on `yield_records`, `sensor_readings`, `weather_records`, and `satellite_observations`. Multi-year training windows (5–10 growing seasons) become efficient to scan with hypertable partitioning. `time_bucket()` aggregation enables batch feature vector construction. The `yield_records.yield_value_tons_ha` target variable is efficiently accessible across historical crop cycles via the `(id, recorded_at)` composite PK.

### Phase 15 — Farm Copilot (Conversational AI)

The Farm Copilot issues real-time conversational queries over "last N days" time windows (e.g., "how has soil moisture changed this week?"). These queries benefit directly from chunk exclusion: a query over the last 7 days on `sensor_readings` accesses exactly one chunk. Response latency at conversational speeds requires this efficiency at production data volumes.

### Phase 16 — Digital Twin

The Digital Twin reconstructs field state by replaying time-ordered events from `sensor_readings`, `satellite_observations`, `irrigation_events`, and `weather_records`. Multi-domain time-window queries across all four tables benefit from hypertable chunk exclusion independently on each table. The composite PK pattern ensures each event is addressable by UUID for state reconciliation.

### Future Generative AI

Multi-modal generative AI models over AGRIFLOW-AI data will require efficient access to large historical archives. The hypertable storage model — chunk exclusion, columnar compression, continuous aggregate materialisation — provides the I/O efficiency required to serve large context windows for in-context learning and retrieval-augmented generation over agricultural history data.

---

## Implementation Guidance

**ADR-002 authorises the implementation of Step 1E-B.**

Implementation must comply with the decisions recorded in this ADR. The following constraints apply to Step 1E-B:

1. The six approved hypertable candidate tables (`sensor_readings`, `weather_records`, `satellite_observations`, `irrigation_events`, `yield_records`, `disease_observations`) must be converted using the Composite Primary Key pattern (Strategy A) — no other strategy is authorised.

2. The four relational tables (`farms`, `fields`, `crops`, `soil_profiles`) must not be modified in any Step 1E-B migration.

3. Chunk intervals must follow the values approved in this ADR. Changes to chunk intervals require a Decision Register update.

4. No compression policies, continuous aggregates, retention policies, or `time_bucket()` repository methods should be introduced in Step 1E-B. These are deferred to subsequent steps as documented.

5. No additional architectural decisions should be introduced during Step 1E-B execution. If a new decision is required, it must be recorded in the Decision Register and, where applicable, a new ADR created before implementation proceeds.

6. A pre-migration `pg_dump` backup must be taken before Step 1E-B migration execution, per P12-D003 protocol.

7. SQLAlchemy ORM models for the six time-series tables must be updated to declare composite primary keys (`primary_key=True` on both `id` and the time column) to maintain ORM-schema consistency.

---

## References

* `PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md` v1.3 — §2.3, §5.5
* `PHASE12_STEP1B_TIMESCALEDB_INFRASTRUCTURE_PLAN.md` v1.1 — §7
* `PHASE12_STEP1C_IMPLEMENTATION_REPORT.md` v1.0 — §8, §9
* `PHASE12_STEP1D_EXTENSION_ENABLEMENT_REPORT.md` v1.0
* `PHASE12_STEP1EA_HYPERTABLE_ARCHITECTURE_ASSESSMENT.md` v1.0 — §4 through §12
* `PHASE12_DECISION_REGISTER.md` v1.3 — P12-D007, P12-D008, P12-D009, P12-D010, P12-D011, P12-D012
* `docs/adr/ADR-001-timescaledb-extension-enablement.md` — Accepted 2026-06-29
* [TimescaleDB 2.x Hypertable Documentation](https://docs.timescale.com/use-timescale/latest/hypertables/)

---

*ADR-002 — Approved: 2026-06-29 — Phase 12 Step 1E-A → Step 1E-B*
