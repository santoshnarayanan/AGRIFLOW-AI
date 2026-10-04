# AGRIFLOW-AI — Phase 12 Decision Register

**Document Type:** Architecture & Infrastructure Decision Register  
**Version:** 1.1  
**Phase:** 12 — TimescaleDB Time-Series Foundation  
**Status:** Active  
**Governance Reference:** `docs/report/PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md` v1.3

This register records formal decisions made during Phase 12. Decisions affecting API contracts, domain models, repository interfaces, service interfaces, primary key strategy, or database architecture require an **Architecture Decision Review (ADR)** per Step 1A Section 2.4 before implementation.

---

## Decision Index

| ID | Title | Step | Status | Date |
|---|---|---|---|---|
| P12-D001 | TimescaleDB Docker Image Selection | 1B | ✅ Approved for Implementation | June 2026 |
| P12-D002 | TimescaleDB Version Pinning Strategy | 1B | ✅ Approved for Implementation | June 2026 |
| P12-D003 | Pre-Migration Backup Strategy | 1B | ✅ Approved for Implementation | June 2026 |
| P12-D004 | TimescaleDB Extension Enablement Strategy | 1C | ✅ Approved for Implementation | June 2026 |
| P12-D005 | Infrastructure Rollback Strategy | 1B / 1C | ✅ Approved for Implementation | June 2026 |
| P12-D006 | shared_preload_libraries Configuration Gap Resolution | 1D | ✅ Implemented | 2026-06-29 |
| P12-D007 | Hypertable Primary Key Strategy | 1E-B | ✅ Implemented | 2026-06-29 |
| P12-D008 | Hypertable Candidate Tables & Conversion Sequence | 1E-B | ✅ Implemented | 2026-06-29 |
| P12-D009 | Hypertable Chunk Interval Strategy | 1E-B | ✅ Implemented | 2026-06-29 |
| P12-D010 | Compression Policy Strategy | 2B | ✅ Implemented | 2026-06-29 |
| P12-D011 | Retention Policy Strategy | 1E-A | ⏳ Deferred — Design-Time Decision | 2026-06-29 |
| P12-D012 | Continuous Aggregate Strategy | 1E-A | ⏳ Deferred to Step 1E-D | 2026-06-29 |

---

## P12-D001 — TimescaleDB Docker Image Selection

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D001 |
| **Step** | 1B |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §2.1 — PostgreSQL 17; TimescaleDB as PostgreSQL extension; Docker Compose primary dev runtime |
| **Deciders** | Senior Platform Architecture (Step 1B Planning) |

### Context

AGRIFLOW-AI runs PostgreSQL 17 via `postgres:17-alpine` in Docker Compose on macOS Apple Silicon. Phase 12 requires a TimescaleDB-enabled PostgreSQL 17 image without introducing a separate database technology.

### Decision

Adopt the official **`timescale/timescaledb`** Docker image (Alpine-based, lightweight) with a **pinned semver tag** on the PostgreSQL 17 platform.

**Image reference (implementation target):**

```text
timescale/timescaledb:<semver>-pg17
```

**Implemented pin:** `timescale/timescaledb:2.28.1-pg17` (recorded 2026-06-25 — see P12-D002 § Implemented Pin Record).

**Example at time of planning:** `timescale/timescaledb:2.28.0-pg17` — illustrative only; see P12-D002 for version selection policy.

### Alternatives Considered

| Alternative | Rejected Because |
|---|---|
| `timescale/timescaledb-ha:pg17` | Ubuntu-based HA image with Patroni, Toolkit, PostGIS — operational overhead not required for local dev; exceeds Step 1B scope |
| `timescale/timescaledb:latest-pg17` | Violates Step 1A pinning requirement; `latest-*` tags can shift TimescaleDB minor versions unexpectedly |
| `postgres:17-alpine` + manual extension install | Not supported in standard Postgres image; extension must ship with database container |
| `timescale/timescaledb:<semver>-pg17-oss` | Valid fallback for OSS-only licensing; full image selected for complete TimescaleDB feature set needed in Phase 12E |

### Rationale

1. Official Timescale-maintained image based on the [official PostgreSQL Docker image](https://hub.docker.com/_/postgres) — same environment variables, data directory layout, and `pg_isready` health check semantics.
2. PostgreSQL 17 platform tag aligns with approved Step 1A baseline.
3. Multi-architecture builds (amd64 + arm64) support macOS Apple Silicon via Docker Desktop.
4. TimescaleDB ships as a pre-installed extension binary — no Python dependency changes required.

### Consequences

* Only `docker-compose.yml` `db.image` (and optional header comment) changes in Step 1B.
* Backend Dockerfile and `requirements.txt` remain unchanged.
* Existing `postgres_data` volume remains mounted at `/var/lib/postgresql/data`.

### Compliance

✅ Compliant with Step 1A approved baseline. No conflict identified.

---

## P12-D002 — TimescaleDB Version Pinning Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D002 |
| **Step** | 1B |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §12 Recommendation #1 — pin image tag; do not use `latest` |

### Context

TimescaleDB intentionally omits a bare `latest` tag to prevent unexpected PostgreSQL major version upgrades. AGRIFLOW-AI requires reproducible dev environments and controlled upgrade paths.

### Decision

Pin the Docker image to an **exact semver tag** encoding both TimescaleDB and PostgreSQL platform versions:

```text
<timescaledb-version>-pg17
```

### Version Selection Policy

| Rule | Detail |
|---|---|
| Selection criterion | Latest stable TimescaleDB release for PostgreSQL 17 available at implementation time |
| Prohibited tags | `latest`, `latest-pg17` |
| Pin requirement | Always commit an explicit semantic version — never a rolling tag |
| Verification gate | Confirm selected tag exists on [Docker Hub — timescale/timescaledb tags](https://hub.docker.com/r/timescale/timescaledb/tags) before Step 1B image swap; re-verify before Step 1C |
| Record keeping | Record the exact implemented pin in § Implemented Pin Record below |

### Implemented Pin Record

| Field | Value |
|---|---|
| **Implemented pin** | `timescale/timescaledb:2.28.1-pg17` |
| **Implementation date** | 2026-06-25 |
| **Verified on Docker Hub** | Yes — `2.28.1-pg17` confirmed as latest stable `*-pg17` semver at implementation time |
| **Step 1C infrastructure execution** | Completed — image swap validated; extension not enabled |
| **Example (planning reference only)** | `2.28.0-pg17` |

### Upgrade Policy

| Environment | Policy |
|---|---|
| Local development | Update pin deliberately; document in this register with new decision entry |
| Shared / staging | Requires backup + smoke test before pin bump |
| Production (future) | Requires change window, pg_dump, and rollback plan |

### Consequences

* Image upgrades are explicit, reviewable diffs in `docker-compose.yml`.
* Team must record pin changes as new register entries or amendments to P12-D002.

### Compliance

✅ Compliant with Step 1A approved baseline.

---

## P12-D003 — Pre-Migration Backup Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D003 |
| **Step** | 1B (before image swap); repeated before Step 1C |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §6.6, §12 Recommendation #2 — pg_dump before image switch |

### Context

Step 1B replaces the database container image while retaining the `postgres_data` Docker volume. Although TimescaleDB images are PostgreSQL-compatible, a point-in-time logical backup is mandatory before any infrastructure change.

### Decision

Execute a **custom-format pg_dump** from the host before Step 1B image swap and before Step 1C extension migration.

**Standard backup command:**

```bash
docker compose exec db pg_dump \
  -U agriflow \
  -d agriflow \
  -F c \
  -f /tmp/pre_phase12_step1b_$(date +%Y%m%d_%H%M%S).dump

docker compose cp db:/tmp/pre_phase12_step1b_*.dump ./backups/
```

**Host-native alternative (current port mapping):**

```bash
pg_dump -h localhost -p 25432 -U agriflow -d agriflow \
  -F c -f "./backups/pre_phase12_step1b_$(date +%Y%m%d_%H%M%S).dump"
```

### Backup Storage

| Requirement | Detail |
|---|---|
| Location | `./backups/` (gitignored) or operator secure storage |
| Retention | Retain until Step 1C validated; minimum 30 days for shared environments |
| Naming | `pre_phase12_step1b_YYYYMMDD_HHMMSS.dump`, `pre_phase12_step1c_YYYYMMDD_HHMMSS.dump` |
| Verification | `pg_restore --list <dumpfile>` confirms readable archive |

### Consequences

* Backup is a **mandatory gate** before Step 1B and Step 1C execution — not optional.
* Empty/dev environments should still practice the backup workflow to validate runbook.

### Compliance

✅ Compliant with Step 1A approved baseline.

---

## P12-D004 — TimescaleDB Extension Enablement Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D004 |
| **Step** | 1C |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §2.3 Step 1C Approved; §8 Step 1C actions; immutable Alembic history |

### Context

TimescaleDB must be activated as a PostgreSQL extension in the `agriflow` database. Step 1A approves extension enablement via forward Alembic migration without application-layer changes.

### Decision

Enable TimescaleDB through a **new forward-only Alembic migration** executed after Step 1B image validation:

**Upgrade DDL:**

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

**Downgrade DDL (Alembic completeness — governance restricted):**

```sql
DROP EXTENSION IF EXISTS timescaledb CASCADE;
```

**Downgrade governance (see Step 1B plan §7.1.1):**

| Rule | Detail |
|---|---|
| Purpose | Satisfies Alembic migration reversibility — not a production rollback procedure |
| Permitted use | Development environments **before any hypertables exist** (pre-Step 1D) |
| After Step 1D | Extension removal is **not** a normal rollback strategy |
| Post-Step 1D rollback | Restore from pg_dump backup (P12-D003 / P12-D005 Tier 2) |

**Verification queries:**

```sql
-- Extension installed in AGRIFLOW database
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Extension binaries available in database image
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name = 'timescaledb';
```

Both queries should be executed — `pg_available_extensions` confirms binaries in the image; `pg_extension` confirms installation in `agriflow`.

### Constraints

| Constraint | Detail |
|---|---|
| No historical migration edits | Migrations `001` through `a1b2c3d4e5f6` remain immutable |
| No schema changes beyond extension | Existing tables, indexes, enums unchanged in Step 1C |
| No application code changes | API, Service, Repository, Schema layers unchanged |
| Privilege requirement | `POSTGRES_USER` (`agriflow`) must have `CREATE` privilege on database — default superuser in dev Compose |

### Note on Image Auto-Enablement

The `timescale/timescaledb` image may pre-enable the extension in the default `postgres` database. The `agriflow` database (set via `POSTGRES_DB`) requires explicit `CREATE EXTENSION` — the Alembic migration ensures extension state is version-controlled and reproducible across environments.

### Consequences

* Step 1C is fully specified — no additional architectural decisions required for extension enablement.
* Hypertable conversion (Step 1D) remains deferred pending Architecture Approval for primary key strategy.

### Compliance

✅ Compliant with Step 1A approved baseline. Does not implement deferred Step 1D/1E items.

---

## P12-D005 — Infrastructure Rollback Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D005 |
| **Step** | 1B / 1C |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §6.6 Rollback Risks; §12 Recommendation #8 |

### Context

Infrastructure changes must be reversible without data loss. Rollback procedures must be defined before execution.

### Decision

Adopt a **three-tier rollback model**:

#### Tier 1 — Image Revert (Step 1B failure)

1. `docker compose down`
2. Revert `docker-compose.yml` `db.image` to `postgres:17-alpine`
3. `docker compose up -d`
4. Validate: health check passes, APIs respond, data intact

**Data impact:** None — same volume, compatible PostgreSQL 17.

#### Tier 2 — Logical Restore (data corruption or migration failure)

1. `docker compose down`
2. Remove volume: `docker volume rm agriflow-ai_postgres_data` (destructive)
3. Restore: `docker compose up -d db` then `pg_restore` from P12-D003 backup
4. Revert compose image if needed
5. Validate schema and row counts

#### Tier 3 — Extension Rollback (Step 1C failure — pre-Step 1D only)

1. `alembic downgrade -1` (runs `DROP EXTENSION IF EXISTS timescaledb CASCADE`)
2. Validate: extension absent; existing tables operational
3. If downgrade fails: Tier 2 logical restore

**Governance:** Tier 3 is valid only **before Step 1D introduces hypertables**. After hypertables exist, rollback uses Tier 2 backup restore — not extension removal.

### Rollback Decision Matrix

| Failure Scenario | Rollback Tier | Estimated Recovery |
|---|---|---|
| TimescaleDB image fails to start | Tier 1 | < 5 minutes |
| Data present but APIs fail | Tier 1 + logs review | < 15 minutes |
| Volume corruption | Tier 2 | 15–60 minutes |
| Extension migration fails | Tier 3 → Tier 2 if needed | 15–60 minutes |

### Consequences

* Rollback runbook must be executed in practice during Step 1B validation on a disposable copy before shared-environment changes.
* `DROP EXTENSION ... CASCADE` via Alembic downgrade is a **dev-only, pre-Step 1D** rollback path — not applicable after hypertables exist (Step 1D deferred).

### Compliance

✅ Compliant with Step 1A approved baseline.

---

---

## P12-D006 — shared_preload_libraries Configuration Gap Resolution

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D006 |
| **Step** | 1D |
| **Status** | ✅ Implemented |
| **Date** | 2026-06-29 |
| **Baseline Reference** | Step 1C §9 Known Issues; P12-D004 |

### Context

During Step 1D extension enablement, `CREATE EXTENSION timescaledb CASCADE` failed because `shared_preload_libraries` was empty in the existing `postgresql.conf`. This occurred because the Docker volume was originally initialised by `postgres:17-alpine`, which does not include timescaledb. The Step 1C image swap to `timescale/timescaledb:2.28.1-pg17` reused the existing volume; the timescale image's initialisation scripts (which set `shared_preload_libraries`) run only on a fresh data directory and were therefore skipped.

Step 1C detected that TimescaleDB binaries were present (`default_version = 2.28.1`, `installed_version = NULL`) but did not verify or configure `shared_preload_libraries`. This was an operational gap, not an architecture conflict.

### Decision

Apply the PostgreSQL configuration change via `ALTER SYSTEM SET shared_preload_libraries = 'timescaledb'` executed inside the running container, followed by a single `docker compose restart db`. This writes to `postgresql.auto.conf` inside the existing volume.

This is a **database configuration operation**. No changes were made to:
- `docker-compose.yml`
- Backend Dockerfile
- Backend Python code
- SQLAlchemy models
- Alembic migration history
- Application APIs, services, repositories, or schemas

### Alternatives Considered

| Alternative | Rejected Because |
|---|---|
| Destroy volume and reinitialise | Destructive; existing schema and row data lost; not justified for a config-only fix |
| Mount custom `postgresql.conf` via docker-compose volume override | Requires Docker Compose modification — prohibited by Step 1D constraints |
| Set `timescaledb.telemetry_level=off` workaround | Not relevant; issue is `shared_preload_libraries`, not telemetry |

### Consequences

* `postgresql.auto.conf` now contains `shared_preload_libraries = 'timescaledb'`.
* All future container restarts will load TimescaleDB as a preload library.
* TimescaleDB extension was successfully enabled via Alembic migration `f1e2d3c4b5a6`.
* No application behaviour changed.

### Implementation Record

| Field | Value |
|---|---|
| **Command executed** | `ALTER SYSTEM SET shared_preload_libraries = 'timescaledb'` |
| **Container restart** | `docker compose restart db` |
| **Verification** | `SHOW shared_preload_libraries;` → `timescaledb` |
| **Date** | 2026-06-29 |

### Compliance

✅ Compliant with Step 1A approved baseline. Does not constitute Docker infrastructure modification.

---

## Step 1D Implementation Record

| Field | Value |
|---|---|
| **Migration revision ID** | `f1e2d3c4b5a6` |
| **Extension installed** | timescaledb 2.28.1 |
| **Pre-extension backup** | `backups/pre_phase12_step1d_20260629_115426.dump` (67 KB, 210 TOC entries) |
| **Backup integrity** | ✅ Verified via `pg_restore --list` |
| **Validation completed** | ✅ All checks passed |
| **Date implemented** | 2026-06-29 |
| **Alembic head (post-migration)** | `f1e2d3c4b5a6` |
| **ADR created** | `docs/adr/ADR-001-timescaledb-extension-enablement.md` |

---

---

## P12-D007 — Hypertable Primary Key Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D007 |
| **Step** | 1E-A (Assessment) → 1E-B (Implementation pending ADR-002) |
| **Status** | ⏳ Assessed — Pending ADR-002 Approval |
| **Date** | 2026-06-29 |
| **Baseline Reference** | Step 1A §5.5 — Deferred PK strategy; Step 1E-A Assessment §6 |

### Context

All six hypertable candidate tables carry `PRIMARY KEY (id)` (UUID v4 only). TimescaleDB 2.28.x requires all unique constraints (including primary keys) to include the partitioning column. `create_hypertable()` fails with `ERROR: cannot create a unique index without the column "<time_col>" (used in partitioning)`.

### Assessment Finding

**Recommended: Composite Primary Key Strategy A** — `PRIMARY KEY (id, time_col)`.

Four strategies were evaluated in Step 1E-A §6.3. Strategy A is the recommended approach because:
- TimescaleDB constraint satisfied (partition column included in PK)
- UUID identity preserved (application-level identity unchanged)
- `BaseRepository.get_by_id` uses `WHERE id = :id` predicate — zero code changes required
- No FK impact (no external table references time-series tables via FK)
- API, service, repository interface, schema, business logic unchanged

### Implementation Requirement

Each time-series table migration:
1. `ALTER TABLE <table> DROP CONSTRAINT pk_<table>;`
2. `ALTER TABLE <table> ADD CONSTRAINT pk_<table> PRIMARY KEY (id, <time_col>);`
3. `SELECT create_hypertable('<table>', '<time_col>', migrate_data => TRUE, if_not_hypertable => TRUE);`

### Status

Assessment complete. ADR-002 must be approved before Step 1E-B implementation.

---

## P12-D008 — Hypertable Candidate Tables & Conversion Sequence

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D008 |
| **Step** | 1E-A (Assessment) → 1E-B (Implementation pending ADR-002) |
| **Status** | ⏳ Assessed — Pending ADR-002 Approval |
| **Date** | 2026-06-29 |
| **Baseline Reference** | Step 1A §5.1; Step 1E-A Assessment §4, §5 |

### Assessment Finding

**Six tables recommended for hypertable conversion:**

| Priority | Table | Partition Key | Reason |
|---|---|---|---|
| P1 Critical | `sensor_readings` | `recorded_at` | Highest insert frequency; IoT telemetry; AI Feature Store backbone |
| P1 Critical | `weather_records` | `recorded_at` | Continuous meteorological ingestion; GDD/ET₀ features |
| P1 Critical | `satellite_observations` | `observed_at` | Multi-spectral AI training; high-frequency satellite ingestion |
| P2 High | `irrigation_events` | `started_at` | Agricultural intervention history; seasonal water management |
| P2 High | `yield_records` | `recorded_at` | Yield Prediction Engine target variable history |
| P3 Standard | `disease_observations` | `observed_at` | Disease Risk Scoring Engine features |

**Four tables remain relational permanently:**

| Table | Reason |
|---|---|
| `farms` | Root master data; no time-series growth |
| `fields` | Spatial dimension entity; time-series data anchors ON fields, not IN fields |
| `crops` | Lifecycle entity; planting/harvest dates are milestones, not measurements |
| `soil_profiles` | Static profile; one-to-one with fields; UNIQUE (field_id) constraint incompatible with hypertable |

**Additional finding:** `weather_records` is missing the `(field_id, recorded_at)` compound index present on all other Field-anchored time-series tables. This gap should be corrected in Step 1E-B.

### Status

Assessment complete. ADR-002 must be approved before Step 1E-B implementation.

---

## P12-D009 — Hypertable Chunk Interval Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D009 |
| **Step** | 1E-A (Assessment) → 1E-B (Implementation pending ADR-002) |
| **Status** | ⏳ Assessed — Pending ADR-002 Approval |
| **Date** | 2026-06-29 |
| **Baseline Reference** | Step 1E-A Assessment §7.1, §5 |

### Assessment Finding

| Table | Recommended Chunk Interval | Rationale |
|---|---|---|
| `sensor_readings` | 7 days | Sub-hourly IoT data; 1-week chunks align with telemetry dashboard windows |
| `weather_records` | 7 days | Daily–sub-daily data; weekly chunks match agro-meteorological query windows |
| `satellite_observations` | 7 days | 5–16 day satellite revisit; weekly chunks contain 1–2 passes per provider |
| `irrigation_events` | 1 month | Weekly–seasonal frequency; monthly chunks align with water management reporting |
| `disease_observations` | 1 month | Episodic; monthly chunks appropriate for disease season analysis |
| `yield_records` | 3 months | Harvest-time only; quarterly chunks avoid over-partitioning sparse data |

### Status

Assessment complete. ADR-002 must be approved before Step 1E-B implementation.

---

## P12-D010 — Compression Policy Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D010 |
| **Step** | 1E-A (Identified) → 2B (Implemented) |
| **Status** | ✅ Implemented |
| **Date** | 2026-06-29 |

### Context

TimescaleDB columnar compression on cold hypertable chunks provides 10–30× storage savings for IoT and satellite data. Compression should be enabled only after successful hypertable conversion validation.

### Key Considerations

- Append-only `sensor_readings` is the primary compression target
- Mutable tables (`irrigation_events`, `yield_records`, `disease_observations`) require careful age thresholds to avoid compressing recently-written chunks
- Compression ORDER BY and SEGMENTBY configuration requires access pattern analysis
- `weather_records` and `satellite_observations` are also strong compression candidates

### Status

✅ **Implemented** — Step 2B (2026-06-29). Governing ADR: `docs/adr/ADR-003-timescaledb-compression-policy-strategy.md`. Migration `d4f5e6a7b8c9`. See Step 2B Implementation Record below.

---

## P12-D011 — Retention Policy Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D011 |
| **Step** | 1E-A (Identified) → Future |
| **Status** | ⏳ Deferred — Design-Time Decision |
| **Date** | 2026-06-29 |

### Context

TimescaleDB retention policies auto-delete chunks older than a configured interval. This requires explicit business decision about data lifecycle.

### Assessment Finding

**Do not enable automatic retention deletion policies at this stage.** All AGRIFLOW-AI time-series data is AI training material. Automatic deletion would degrade AI model quality over time. Recommended alternative: archive cold data to Azure Blob Storage / S3 via TimescaleDB's tiered storage or application-level archiving before deletion.

### Status

Deferred pending business data lifecycle decision. Not required for Phase 12 baseline.

---

## P12-D012 — Continuous Aggregate Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D012 |
| **Step** | 1E-A (Identified) → 1E-D |
| **Status** | ⏳ Deferred to Step 1E-D |
| **Date** | 2026-06-29 |

### Context

Continuous aggregates pre-compute `time_bucket()` aggregations over hypertables for efficient Phase 13 AI Feature Store queries.

### Assessment Finding

Primary continuous aggregate candidates:
- Hourly average sensor readings by `(field_id, sensor_type)`
- Daily weather summary (min/max/avg temperature, total rainfall, total solar radiation) by `field_id`
- Daily NDVI/EVI mean by `(field_id, spectral_index)` filtered to ARD/L2A processing levels
- Monthly irrigation volume total by `field_id`

These require hypertables to exist (Step 1E-B), and ideally compression to be active (Step 1E-C), before materialized views are established.

### Status

Deferred to Step 1E-D. Requires Step 1E-B and ADR-002 approval.

---

## Deferred Decisions (Not in This Register)

The following remain **deferred pending Architecture Decision Review** per Step 1A §2.2. They must **not** be implemented based on Step 1B planning alone:

| Topic | Register Status |
|---|---|
| Composite Primary Key migration | ⏳ Awaiting ADR |
| UUID Primary Key migration strategy | ⏳ Awaiting ADR |
| Hypertable primary key strategy | ⏳ Awaiting ADR — investigation scoped to Step 1D |
| Repository-level analytics methods | ⏳ Awaiting ADR |
| `time_bucket()` repository implementations | ⏳ Awaiting ADR |
| Primary key / `create_hypertable()` compatibility investigation | ⏳ Deferred to Step 1D — not in Step 1B scope |

---

---

## Step 1E-B Implementation Record

| Field | Value |
|---|---|
| **Migration revision ID** | `c9d8e7f6a5b4` |
| **Migration name** | `convert_time_series_tables_to_hypertables` |
| **Pre-migration backup** | `backups/pre_phase12_step1eb_20260629_140549.dump` (76 KB, 247 TOC entries) |
| **Backup integrity** | ✅ Verified via `pg_restore --list` |
| **Hypertables created** | 6 |
| **Governing ADR** | `docs/adr/ADR-002-hypertable-primary-key-conversion-strategy.md` |
| **Date implemented** | 2026-06-29 |
| **Alembic head (post-migration)** | `c9d8e7f6a5b4` |

### Hypertables Created

| Table | Partition Column | Chunk Interval | PK Strategy |
|---|---|---|---|
| `sensor_readings` | `recorded_at` | 7 days | Composite `(id, recorded_at)` |
| `weather_records` | `recorded_at` | 7 days | Composite `(id, recorded_at)` |
| `satellite_observations` | `observed_at` | 7 days | Composite `(id, observed_at)` |
| `irrigation_events` | `started_at` | 30 days (1 month) | Composite `(id, started_at)` |
| `yield_records` | `recorded_at` | 90 days (3 months) | Composite `(id, recorded_at)` |
| `disease_observations` | `observed_at` | 30 days (1 month) | Composite `(id, observed_at)` |

### Additional Change

`ix_weather_records_field_id_recorded_at` compound index added to `weather_records` (gap identified in Step 1E-A §9.3).

### SQLAlchemy Models Updated

Six models updated with `primary_key=True` on the time column to reflect composite PK:
`SensorReading`, `WeatherRecord`, `SatelliteObservation`, `IrrigationEvent`, `YieldRecord`, `DiseaseObservation`.

### Validation Status

| Check | Result |
|---|---|
| 6 hypertables in `timescaledb_information.hypertables` | ✅ |
| Composite PKs `(id, time_col)` on all 6 tables | ✅ |
| Relational tables (farms, fields, crops, soil_profiles) unchanged | ✅ |
| All FK constraints preserved | ✅ |
| All existing indexes preserved | ✅ |
| `weather_records` compound index added | ✅ |
| Alembic history linear: `c9d8e7f6a5b4` (head) | ✅ |
| Backend `GET /api/v1/health/live` → alive | ✅ |
| Swagger UI `GET /docs` → HTTP 200 | ✅ |
| All 25 API routes present in OpenAPI spec | ✅ |
| `BaseRepository.get_by_id` — predicate query unchanged | ✅ |
| No compression enabled | ✅ |
| No continuous aggregates created | ✅ |
| No retention policies set | ✅ |

### Decisions Updated

P12-D007, P12-D008, P12-D009 status updated from "Assessed — Pending ADR-002 Approval" to "Implemented".

---

## Step 2B Implementation Record

| Field | Value |
|---|---|
| **Migration revision ID** | `d4f5e6a7b8c9` |
| **Migration name** | `enable_hypertable_compression_policies` |
| **Pre-migration backup** | `backups/agriflow_phase12_step1_complete.dump` (49 KB, verified readable) |
| **Backup integrity** | ✅ Verified via `pg_restore --list` |
| **Compression policies created** | 6 |
| **Governing ADR** | `docs/adr/ADR-003-timescaledb-compression-policy-strategy.md` v1.1 |
| **Date implemented** | 2026-06-29 |
| **Alembic head (post-migration)** | `d4f5e6a7b8c9` |

### Compression Policies Implemented (ADR-003 §4)

| Hypertable | Compress After | Segment By | Order By | Rollout Phase |
|---|---|---|---|---|
| `sensor_readings` | 7 days | `field_id`, `sensor_type` | `recorded_at DESC` | Phase 1 |
| `weather_records` | 7 days | `field_id` | `recorded_at DESC` | Phase 1 |
| `satellite_observations` | 14 days | `field_id`, `spectral_index` | `observed_at DESC` | Phase 1 |
| `irrigation_events` | 60 days | `field_id` | `started_at DESC` | Phase 2 |
| `yield_records` | 180 days | `crop_id` | `recorded_at DESC` | Phase 2 |
| `disease_observations` | 60 days | `crop_id` | `observed_at DESC` | Phase 3 |

### Validation Status

| Check | Result |
|---|---|
| TimescaleDB extension active (2.28.1) | ✅ |
| 6 hypertables `compression_enabled = true` | ✅ |
| 6 `policy_compression` jobs registered | ✅ |
| `compress_segmentby` / `compress_orderby` match ADR-003 | ✅ |
| Alembic history linear: `d4f5e6a7b8c9` (head) | ✅ |
| Backend `GET /api/v1/health/live` → alive | ✅ |
| Swagger UI `GET /docs` → HTTP 200 | ✅ |
| No repository changes | ✅ |
| No service changes | ✅ |
| No API changes | ✅ |
| No SQLAlchemy model changes | ✅ |
| No continuous aggregates created | ✅ |
| No retention policies set | ✅ |

### Decisions Updated

P12-D010 status updated from "Deferred to Step 1E-C" to "Implemented".

---

**Version 1.5**

**Revision Summary (v1.5 — 2026-06-29):**

* Updated P12-D010 status to ✅ Implemented.
* Updated Decision Index table to reflect Step 2B compression implementation.
* Added Step 2B Implementation Record (migration revision ID, 6 compression policies, validation status).
* No existing architectural decisions were modified.

**Version 1.4**

**Revision Summary (v1.4 — 2026-06-29):**

* Updated P12-D007, P12-D008, P12-D009 status to ✅ Implemented.
* Updated Decision Index table to reflect Step 1E-B implementation.
* Added Step 1E-B Implementation Record (migration revision ID, 6 hypertables, backup, validation status).
* No existing decisions were modified.

**Version 1.3**

**Revision Summary (v1.3 — 2026-06-29):**

* Added P12-D007: Hypertable Primary Key Strategy — assessed; pending ADR-002 approval.
* Added P12-D008: Hypertable Candidate Tables & Conversion Sequence — six tables recommended; four remain relational; weather_records compound index gap identified.
* Added P12-D009: Hypertable Chunk Interval Strategy — per-table interval recommendations.
* Added P12-D010: Compression Policy Strategy — deferred to Step 1E-C.
* Added P12-D011: Retention Policy Strategy — deferred; no automatic deletion recommended.
* Added P12-D012: Continuous Aggregate Strategy — deferred to Step 1E-D.
* Updated Decision Index table with new entries.
* No existing decisions were modified.

**Revision Summary (v1.2 — 2026-06-29):**

* Added P12-D006: shared_preload_libraries Configuration Gap Resolution (Step 1D).
* Added Step 1D Implementation Record (migration revision ID, extension version, backup filename, validation status).
* No existing decisions were modified.

**Revision Summary (v1.1):**

* Generalized version pinning policy (P12-D001, P12-D002).
* Added Implemented Pin Record to P12-D002.
* Clarified Alembic downgrade governance (P12-D004, P12-D005).
* Strengthened extension validation queries (P12-D004).
* Explicitly deferred PK / hypertable investigation to Step 1D.

No architectural decisions were changed.

---

*Decision Register v1.5 — Step 2B compression implementation recorded: 2026-06-29*
