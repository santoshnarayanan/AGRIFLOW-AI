# AGRIFLOW-AI — Phase 12 Step 1A

## Infrastructure Assessment & Architecture Review

**Document Type:** Architecture Assessment (Read-Only)  
**Version:** 1.3  
**Date:** June 2026  
**Scope:** Phase 12 Step 1A — TimescaleDB Time-Series Foundation (Pre-Implementation)  
**Status:** ✅ Approved — Architectural Baseline for Steps 1B–1E  
**Author:** Senior Solutions Architecture Review  
**Architect Review:** Approved — June 2026

---

## 1. Executive Summary

AGRIFLOW-AI has completed Phases 1–11 and operates a production-grade Clean Architecture backend on **PostgreSQL 17** inside **Docker Compose**, with **11 Alembic migrations**, **10 domain ORM models**, and **51+ REST API endpoints**. Phase 12 introduces **TimescaleDB as a PostgreSQL extension** to activate hypertables, compression, continuous aggregates, and time-bucket analytics across six pre-designed time-series tables — without changing business domain logic or breaking existing APIs.

This assessment concludes that the **application architecture is well-suited** for TimescaleDB introduction. Domain models, migrations, repositories, and services were deliberately designed with TimescaleDB partition keys, compound indexes, and append-only/mutable semantics documented in code comments and ADRs. The **infrastructure layer requires targeted modification** (Docker image, extension enablement, hypertable DDL migrations) but the **API → Service → Repository → SQLAlchemy stack can remain unchanged** for Phase 12 baseline activation.

**Critical finding (open — deferred):** All six hypertable candidate tables use a **UUID-only primary key** (`id`) that does **not** include the proposed partition column (`recorded_at`, `started_at`, or `observed_at`). TimescaleDB requires unique constraints (including primary keys) to **include the partitioning column**. Hypertable conversion therefore requires a **dedicated migration strategy** — identified in this assessment but **deferred pending Architecture Decision Review** (see Section 2). Step 1D requires Architecture Approval for primary key strategy before execution.

**Overall Phase 12 Readiness Score: 7.5 / 10** — strong architectural preparation; Step 1B–1C may proceed per approved baseline; Step 1D–1E pending Architecture Approval for deferred PK and analytics decisions. All Phase 12 work is governed by Section 2.4 (pause on conflict; ADR required for protected change areas).

---

## 2. Architect Review Outcome — Approved Baseline

This assessment has been **reviewed and approved** as the architectural baseline for Phase 12 Step 1. The following decisions are binding for all subsequent implementation steps (Step 1B through Step 1E).

### 2.1 Approved Decisions

| Decision | Status |
|---|---|
| PostgreSQL 17 remains the database version for Phase 12 | ✅ Approved |
| Docker Compose remains the primary development runtime | ✅ Approved |
| TimescaleDB introduced as a **PostgreSQL extension**, not a separate database technology | ✅ Approved |
| Existing API contracts must remain unchanged | ✅ Approved |
| Existing Service layer must remain unchanged | ✅ Approved |
| Existing Repository **interfaces** must remain unchanged | ✅ Approved |
| Existing Pydantic schemas must remain unchanged | ✅ Approved |
| Existing business logic must remain unchanged | ✅ Approved |
| Existing Alembic migration history is **immutable** | ✅ Approved |
| Backend Dockerfile remains unchanged unless a critical infrastructure issue is discovered | ✅ Approved |
| Python dependencies remain unchanged unless strictly required | ✅ Approved |

These approved constraints mean Steps 1B and 1C (Docker image swap and extension enablement) may proceed without application-layer changes. Steps 1D and 1E must respect the deferred decisions listed below.

### 2.2 Deferred Architectural Decisions

The following topics were identified in this assessment but **require further technical investigation during Step 1B** and **require Architecture Decision Review before implementation** — they may not proceed based solely on this document:

| Topic | Status | Notes |
|---|---|---|
| Composite Primary Key migration | ⏳ Deferred | Requires Approved ADR |
| UUID Primary Key migration strategy | ⏳ Deferred | Pending Architecture Decision Review; alternative approaches to be evaluated |
| Hypertable primary key strategy | ⏳ Deferred | Requires Architecture Approval before Step 1D execution |
| Repository-level analytics methods | ⏳ Deferred | Requires Architecture Approval for new repository methods |
| `time_bucket()` repository implementations | ⏳ Deferred | Step 1E analytics layer requires Architecture Approval |

**Implementation guardrail:** Step 1D hypertable conversion migration and Step 1E repository analytics work require Architecture Approval via follow-on review document or formal ADR before execution (Section 2.4).

### 2.3 Impact on Step Sequence

| Step | Governance Status | Condition |
|---|---|---|
| **Step 1B** — TimescaleDB Docker image | ✅ Approved | Per approved decisions; pg_dump backup required |
| **Step 1C** — Extension enablement | ✅ Approved | After Step 1B validation; no schema change beyond extension |
| **Step 1D** — Hypertable conversion | ⏳ Requires Architecture Approval | Primary key strategy pending Architecture Decision Review |
| **Step 1E** — Policies, aggregates, analytics | ⏳ Partial scope — requires Architecture Approval | Compression/retention/aggregates may proceed after 1D; repository analytics deferred pending ADR |

### 2.4 Phase 12 Governance Principle

This document serves as the **architectural baseline for Phase 12**. The following governance rules are binding for all implementation work throughout Phase 12 (Steps 1B–1E and any subsequent Phase 12 sub-steps).

**Conflict resolution:** If any future implementation step conflicts with this document, **implementation must pause** and the architecture must be reviewed before proceeding.

**Precedence:** Implementation convenience shall **never** override the approved architecture.

**Architecture Decision Review (ADR) required:** Any proposed change affecting the following areas requires an **Architecture Decision Review (ADR)** before implementation:

| Change Area | ADR Required |
|---|---|
| API contracts | ✅ Yes |
| Domain Models | ✅ Yes |
| Repository interfaces | ✅ Yes |
| Service interfaces | ✅ Yes |
| Primary Key strategy | ✅ Yes |
| Database architecture | ✅ Yes |

**Scope:** This governance principle remains in effect **throughout Phase 12**. Deferred decisions listed in Section 2.2 are subject to this same ADR gate — a follow-on review document or formal ADR is required before any deferred item may be implemented.

---

## 3. Current Infrastructure

### 3.1 Docker Compose Architecture

| Component | Configuration | Evidence |
|---|---|---|
| Database service | `db` — `postgres:17-alpine` | `docker-compose.yml` line 20 |
| Backend service | `backend` — multi-stage Dockerfile, target `runtime` | `docker-compose.yml` lines 38–42 |
| Network | Default Compose bridge; backend connects via service name `db` | `POSTGRES_HOST: db` override |
| Host port mapping | `25432:5432` (host → container) | Enables pgAdmin/Postman from macOS host |
| Persistence | Named volume `postgres_data` → `/var/lib/postgresql/data` | Survives container restarts |
| Health check | `pg_isready` every 10s, 5 retries | Backend `depends_on: condition: service_healthy` |
| Dev reload | Backend source mounted `./backend:/app` with `--reload` | Hot reload; not production pattern |

**Note:** The compose file header comment references "PostgreSQL 18" but the **actual image is `postgres:17-alpine`**. Documentation and runtime are aligned at PostgreSQL 17; the comment is stale and should be corrected in a future documentation pass (not in scope for Step 1A implementation).

### 3.2 Backend Container

| Attribute | Value |
|---|---|
| Base image | `python:3.12-slim` (builder + runtime) |
| Python | 3.12 |
| User | Non-root `appuser` (uid 1000) |
| Runtime libs | `libpq5` (PostgreSQL client) |
| Default CMD | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Dev override | `--reload` via compose `command` |

### 3.3 Environment Configuration

Configuration is centralized in `backend/app/core/config/settings.py` via **Pydantic BaseSettings**:

| Variable | Purpose |
|---|---|
| `POSTGRES_HOST` | Hostname (`localhost` on host; `db` in Compose) |
| `POSTGRES_PORT` | Port (`5432` internal; `25432` on host) |
| `POSTGRES_DB` | Database name: `agriflow` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | Credentials (password required) |
| `DATABASE_URL` | Auto-assembled: `postgresql+asyncpg://...` |

Alembic reads the same `DATABASE_URL` via `app/core/config` in `env.py` — **single source of truth** for app and migrations.

### 3.4 Database Startup Process

1. `docker compose up` starts `db` service.
2. PostgreSQL initializes data directory on first run (volume empty).
3. Health check passes → `backend` starts.
4. Migrations are **not** auto-run on startup (by design).
5. Operator runs: `docker compose run --rm backend alembic upgrade head`

### 3.5 Migration Execution Process

| Step | Mechanism |
|---|---|
| Config | `backend/alembic.ini` → `script_location = app/db/migrations` |
| Engine | Async via `async_engine_from_config` + `run_sync(do_run_migrations)` |
| Metadata | `Base.metadata` with all models imported in `app/db/models/__init__.py` |
| URL injection | `settings.DATABASE_URL` overrides `alembic.ini` placeholder |
| Current head | `a1b2c3d4e5f6_create_satellite_observations_table` |

### 3.6 Development Environment (macOS Apple Silicon)

| Tool | Role |
|---|---|
| Docker Desktop | Runs Linux containers (arm64-compatible images) |
| Cursor / VS Code | IDE |
| pgAdmin 4 | Connects to `localhost:25432` |
| Postman | API testing |
| Local PostgreSQL 18 | Installed but **not used** by this project |

Apple Silicon compatibility for TimescaleDB is **favorable**: official `timescale/timescaledb` Docker images publish **multi-architecture** builds (amd64 + arm64). The recommended Phase 12 approach is switching the `db` service image to a TimescaleDB-enabled PostgreSQL 17 image rather than installing extensions on the host.

---

## 4. Database Architecture Review

### 4.1 SQLAlchemy Configuration

| Aspect | Implementation | Assessment |
|---|---|---|
| ORM | SQLAlchemy 2.0.36 with `Mapped` / `mapped_column` | Modern, type-safe |
| Driver | `asyncpg` via `postgresql+asyncpg://` | Non-blocking; TimescaleDB-compatible |
| Engine | Module-level singleton in `app/db/session.py` | `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=1800` |
| Session factory | `async_sessionmaker` with `expire_on_commit=False`, `autoflush=False` | Correct async pattern |
| Base model | `AuditableModel` — UUID PK + `created_at` / `updated_at` TIMESTAMPTZ | Universal across domains |

### 4.2 Session Lifecycle

`app/api/deps.py` implements request-scoped transactions:

```text
AsyncSessionFactory() → session.begin() → yield → auto commit/rollback → close
```

Repositories receive the session via DI; **no repository calls `commit()`** — transaction boundary is exclusively in `get_session()`. This pattern is stable for TimescaleDB because hypertable operations are transparent to standard INSERT/SELECT/UPDATE/DELETE at the SQLAlchemy layer.

### 4.3 Repository Pattern

| Repository | Time-Series Domain | Partition Key Column | Compound Index |
|---|---|---|---|
| `WeatherRecordRepository` | Yes | `recorded_at` | `field_id` + time (partial) |
| `SensorReadingRepository` | Yes | `recorded_at` | `(field_id, recorded_at)`, `(sensor_type, recorded_at)` |
| `IrrigationEventRepository` | Yes | `started_at` | `(field_id, started_at)` |
| `YieldRecordRepository` | Yes | `recorded_at` | `(crop_id, recorded_at)` |
| `DiseaseObservationRepository` | Yes | `observed_at` | `(crop_id, observed_at)` |
| `SatelliteObservationRepository` | Yes | `observed_at` | `(field_id, observed_at)`, `(spectral_index, observed_at)` |

All time-series repositories document TimescaleDB readiness in module docstrings. Query patterns (`ORDER BY time_col DESC`, date-range filters) align with hypertable chunk exclusion.

`BaseRepository` provides generic CRUD; domain repositories add time-ordered list methods. **No raw SQL or database-specific dialect usage** exists in repositories today — a positive factor for backward compatibility.

### 4.4 Migration Strategy (Existing)

| Characteristic | Status |
|---|---|
| Linear revision chain | 11 migrations, no branches |
| Enum lifecycle | `postgresql.ENUM` + `create_type=False` pattern (Phase 8+) |
| Index strategy | Individual time indexes + compound `(parent_id, time_key)` |
| Downgrade support | All migrations include `downgrade()` |
| Autogenerate | Configured via `compare_type=True` in `env.py` |

### 4.5 Relational (Non-Hypertable) Tables

These tables are **not** Phase 12 hypertable candidates and require **no modification**:

* `farms`, `fields`, `crops`, `soil_profiles`

---

## 5. TimescaleDB Compatibility Assessment

### 5.1 Hypertable Candidate Summary

| Table | Partition Key | NOT NULL | Individual Time Index | Compound Index | ORM Model Ready |
|---|---|---|---|---|---|
| `weather_records` | `recorded_at` | ✅ | ✅ | Partial (`field_id` only) | ✅ |
| `sensor_readings` | `recorded_at` | ✅ | ✅ | ✅ `(field_id, recorded_at)` | ✅ |
| `irrigation_events` | `started_at` | ✅ | ✅ | ✅ `(field_id, started_at)` | ✅ |
| `yield_records` | `recorded_at` | ✅ | ✅ | ✅ `(crop_id, recorded_at)` | ✅ |
| `disease_observations` | `observed_at` | ✅ | ✅ | ✅ `(crop_id, observed_at)` | ✅ |
| `satellite_observations` | `observed_at` | ✅ | ✅ | ✅ `(field_id, observed_at)` | ✅ |

All six tables satisfy TimescaleDB's **NOT NULL TIMESTAMPTZ partition column** requirement.

### 5.2 Already Compatible (No Application Code Change Required for Baseline)

| Area | Compatibility |
|---|---|
| SQLAlchemy ORM models | Partition columns defined; no schema change needed for baseline reads/writes |
| asyncpg driver | Full PostgreSQL wire-protocol compatibility with TimescaleDB |
| Service layer business rules | Time validation, immutability contracts unchanged |
| API layer / Pydantic schemas | No time-series-specific DB coupling |
| Repository CRUD + list queries | Standard SQLAlchemy `select()` — works on hypertables |
| Alembic async migration runner | Can execute `CREATE EXTENSION` and `create_hypertable()` via `op.execute()` |
| Docker volume persistence | Same PostgreSQL data directory model |
| Connection pooling | No change required |

### 5.3 Requires Modification (Infrastructure & Migrations)

| Area | Modification | Phase |
|---|---|---|
| `docker-compose.yml` | Switch `db` image from `postgres:17-alpine` to TimescaleDB-enabled image (e.g. `timescale/timescaledb:latest-pg17`) | Step 1B |
| Database extension | `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;` | Step 1C |
| Primary key / unique constraints | **Deferred** — hypertable PK strategy requires Architecture Decision Review before Step 1D | Step 1D |
| Hypertable DDL | `SELECT create_hypertable(...)` for each of six tables — requires Architecture Approval (primary key strategy) | Step 1D |
| Compression / retention policies | `add_compression_policy`, `add_retention_policy` — after hypertables exist | Step 1E |
| Continuous aggregates | Materialized views + refresh policies — after hypertables exist | Step 1E |
| Repository analytics (`time_bucket()`) | **Deferred** — requires Architecture Decision Review | Step 1E |

### 5.4 Requires No Modification

| Area | Reason |
|---|---|
| FastAPI routers | No database engine awareness |
| Pydantic schemas | Domain validation only |
| Service layer (Phase 12 baseline) | Business rules independent of storage engine |
| Non-time-series models | `farms`, `fields`, `crops`, `soil_profiles` remain standard PostgreSQL tables |
| Existing Phases 1–11 migrations | Historical record; remain valid — new forward migrations add TimescaleDB artifacts |
| `requirements.txt` (baseline) | No TimescaleDB-specific Python package required; extension lives in PostgreSQL |

### 5.5 Primary Key Constraint — Open Investigation (Deferred)

Every domain table inherits `UUIDPrimaryKeyMixin` → `PRIMARY KEY (id)` where `id` is UUID v4 **without** the time partition column.

TimescaleDB enforces: **all UNIQUE and PRIMARY KEY constraints on a hypertable must include the partitioning column**.

**Implication:** Calling `create_hypertable('sensor_readings', 'recorded_at')` on the current schema will **fail** unless an approved primary key strategy is applied first.

**Assessment finding (not an approved implementation plan):** This assessment identified composite primary keys, alternative UUID strategies, and TimescaleDB-specific workarounds as candidate approaches. **Each requires Architecture Decision Review before implementation.** Per Architect Review Outcome (Section 2.2), the following are explicitly deferred:

* Composite Primary Key migration
* UUID Primary Key migration strategy
* Hypertable primary key strategy

A **dedicated architecture review** must evaluate options, document trade-offs against the approved constraint that existing API, Service, Repository interface, Schema, and business logic layers remain unchanged, and produce an approved Step 1D migration design (via ADR) before hypertable DDL is executed.

**Step 1B investigation scope:** During Docker image validation (Step 1B), the team should reproduce the PK constraint failure in a disposable environment and catalogue viable strategies for the follow-on review — without applying any PK or hypertable migration to shared development data.

---

## 6. Risk Assessment

### 6.1 Infrastructure Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Docker image switch breaks existing volume | Medium | Test on copy of volume; TimescaleDB images are PostgreSQL-compatible for existing data |
| Stale compose comment (PG 18 vs 17) | Low | Documentation correction only |
| Dev volume mount + image upgrade mismatch | Medium | Run `alembic upgrade head` after image switch; verify extension |
| `POSTGRES_PASSWORD` required at compose start | Low | Already enforced via `${POSTGRES_PASSWORD:?...}` |

### 6.2 Database Migration Risks

| Risk | Severity | Mitigation |
|---|---|---|
| PK constraint incompatible with hypertable | **High** | **Deferred** — requires Architecture Decision Review before Step 1D; composite PK requires Approved ADR — not based on this assessment alone |
| `create_hypertable()` on non-empty tables locks table briefly | Medium | Schedule during maintenance window; test on staging copy after PK strategy approved |
| Enum types unaffected but migration order matters | Low | Extension migration before hypertable migration |
| Downgrade complexity (hypertable → regular table) | Medium | Document `downgrade()` with `SELECT decompress_chunk` / drop policies first |

### 6.3 Docker Compatibility

| Risk | Severity | Mitigation |
|---|---|---|
| TimescaleDB image size vs alpine | Low | Accept larger image for dev; use pinned tag |
| Apple Silicon arm64 support | Low | Use official multi-arch TimescaleDB image |
| Health check unchanged | Low | `pg_isready` works on TimescaleDB images |

### 6.4 Alembic Compatibility

| Risk | Severity | Mitigation |
|---|---|---|
| Async migration runner + DDL extensions | Low | Use `op.execute("CREATE EXTENSION ...")` in sync context |
| Autogenerate may not detect hypertables | Low | Hypertable DDL is manual migration, not autogenerate |
| `create_hypertable` not reversible via autogenerate | Medium | Explicit downgrade: `SELECT drop_chunks` / revert hypertable |

### 6.5 Application Layer Risks

| Risk | Severity | Mitigation |
|---|---|---|
| SQLAlchemy PK strategy change (if approved in follow-on review) | Medium | Test all `get_by_id()` paths after approved Step 1D migration |
| No TimescaleDB-aware queries yet | Low | Expected — repository `time_bucket()` methods **deferred** per Section 2.2 |
| Connection pool to TimescaleDB | Low | Transparent — same asyncpg URL |

### 6.6 Rollback Risks

| Scenario | Rollback Path |
|---|---|
| Image switch fails | Revert `docker-compose.yml` to `postgres:17-alpine`; volume data preserved |
| Extension migration fails | `DROP EXTENSION timescaledb CASCADE` (destructive — avoid in prod) |
| Hypertable migration fails | Alembic downgrade; may require manual chunk decompression |
| PK migration fails | Alembic downgrade to restore UUID-only PK |

**Recommendation:** Take a **pg_dump backup** before Step 1B on any environment with non-disposable data.

### 6.7 Future Upgrade Risks

| Risk | Notes |
|---|---|
| TimescaleDB version pinning | Pin image tag (e.g. `2.x-pg17`) to avoid surprise upgrades |
| PostgreSQL major version jump | Stay on PG 17 line for Phase 12; PG 18 local install irrelevant |
| Continuous aggregate schema drift | New migrations for aggregate view changes in later phases |

---

## 7. Files Impact Assessment

### 7.1 Files Requiring Modification (Step 1B–1E)

| File | Reason | Risk Level | Step |
|---|---|---|---|
| `docker-compose.yml` | Switch `db` service image to TimescaleDB-enabled PostgreSQL 17 | Medium | **1B — Approved** |
| `backend/app/db/migrations/versions/<new>_enable_timescaledb_extension.py` | `CREATE EXTENSION timescaledb` | Low | **1C — Approved** |
| `backend/app/db/migrations/versions/<new>_convert_*_to_hypertables.py` | PK strategy + `create_hypertable()` for six tables | **High** | **1D — Requires Architecture Approval** (Primary Key Strategy) |
| `backend/app/db/migrations/versions/<new>_timescaledb_compression_retention.py` | Compression and retention policies | Medium | **1E — After 1D** |
| `backend/app/db/migrations/versions/<new>_timescaledb_continuous_aggregates.py` | Continuous aggregate views + policies | Medium | **1E — After 1D** |
| `backend/.env.example` | Optional: document TimescaleDB-related env vars if introduced | Low | Optional |
| `docs/03-database.md` | Document TimescaleDB activation (documentation phase) | Low | Post-implementation |
| `docs/06-roadmap.md` | Phase 12 completion status (documentation phase) | Low | Post-implementation |
| `README.md` | Infrastructure status update post-implementation | Low | Post-implementation |

**Step 1E repository analytics — deferred (Section 2.2):**

| File | Reason | Status |
|---|---|---|
| `backend/app/db/repositories/sensor_reading.py` | `time_bucket()` aggregate queries | ⏳ Deferred Pending Architecture Review |
| `backend/app/db/repositories/weather_record.py` | Aggregate query methods | ⏳ Deferred Pending Architecture Review |
| `backend/app/db/repositories/irrigation_event.py` | Aggregate query methods | ⏳ Deferred Pending Architecture Review |
| `backend/app/db/repositories/yield_record.py` | Aggregate query methods | ⏳ Deferred Pending Architecture Review |
| `backend/app/db/repositories/disease_observation.py` | Aggregate query methods | ⏳ Deferred Pending Architecture Review |
| `backend/app/db/repositories/satellite_observation.py` | Aggregate query methods | ⏳ Deferred Pending Architecture Review |
| `backend/app/services/*` (time-series domains) | Pass-through to new repository methods | ⏳ Deferred Pending Architecture Review |
| `backend/app/api/*` (optional new analytics endpoints) | New analytics endpoints | ⏳ Deferred Pending Architecture Review |

### 7.2 Files That MUST Remain Untouched (Approved Baseline)

| File / Area | Reason |
|---|---|
| `backend/app/api/**/*.py` (existing routers) | Phase 12 requires no API breaking changes for baseline activation |
| `backend/app/schemas/**/*.py` | Request/response contracts unchanged |
| `backend/app/services/**/*.py` (business logic) | Domain rules independent of hypertable storage |
| `backend/app/core/enums.py` | Shared vocabulary — no TimescaleDB coupling |
| `backend/app/db/models/*.py` | ORM definitions unchanged per approved baseline; any PK strategy is migration-level DDL only — subject to follow-on review |
| `backend/app/db/migrations/versions/001_*.py` through `a1b2c3d4e5f6_*.py` | Immutable historical migrations — never rewrite |
| `backend/Dockerfile` | Backend container has no TimescaleDB dependency |
| `backend/requirements.txt` | No new Python package required for extension-based TimescaleDB |
| `backend/app/main.py` | Application bootstrap unchanged |

### 7.3 Files Requiring Verification Only

| File | Reason |
|---|---|
| `backend/app/db/session.py` | Confirm pool settings adequate under TimescaleDB load |
| `backend/app/db/migrations/env.py` | Confirm `op.execute()` DDL runs correctly in async runner |
| `backend/app/api/deps.py` | Confirm transaction boundaries unaffected |
| `backend/app/db/repositories/base.py` | Confirm CRUD on hypertables after Step 1D (post Architecture Approval for PK strategy) |
| `backend/alembic.ini` | No URL change expected |
| `backend/app/core/config/settings.py` | Connection string format unchanged |
| All existing migration `downgrade()` functions | Confirm rollback path documented before production |
| `docker-compose.yml` backend service | Verify backend still connects after db image switch |

---

## 8. Migration Strategy Recommendation

### Recommended Step Sequence (Guided by Approved Baseline — Section 2)

#### Step 1B — Infrastructure: TimescaleDB Docker Image ✅ Approved

**Objective:** Replace PostgreSQL-only container with TimescaleDB-enabled PostgreSQL 17.

**Actions (recommended):**

1. Pin TimescaleDB image tag (e.g. `timescale/timescaledb:2.17.2-pg17` — verify latest stable at implementation time).
2. Update `docker-compose.yml` `db.image` only.
3. Backup existing volume: `pg_dump -h localhost -p 25432 -U agriflow -d agriflow -F c -f pre_timescale_backup.dump`.
4. Restart stack: `docker compose down && docker compose up -d`.
5. Verify PostgreSQL starts and existing data intact.
6. Run existing migrations: `alembic upgrade head` (should be no-op if already at head).
7. **Investigation (non-destructive):** In a disposable database copy, attempt `create_hypertable()` on one candidate table to confirm PK constraint failure and document findings for the deferred PK strategy review (Section 5.5).

**Success criteria:** Application connects; all existing APIs respond; no schema change yet.

---

#### Step 1C — Extension Enablement Migration ✅ Approved

**Objective:** Activate TimescaleDB extension in the `agriflow` database.

**Actions (recommended):**

1. Create new Alembic migration: `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;`.
2. Include downgrade: `DROP EXTENSION IF EXISTS timescaledb CASCADE;` (with warning — destructive if hypertables exist).
3. Apply via `alembic upgrade head`.
4. Verify: `SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';`.

**Success criteria:** Extension active; no application code changes; all existing queries work.

---

#### Step 1D — Hypertable Conversion Migration ⏳ Requires Architecture Approval (Primary Key Strategy)

**Objective:** Convert six time-series tables to hypertables.

**Status:** **Deferred Pending Architecture Approval.** Hypertable primary key strategy, composite PK migration, and UUID PK migration strategy are deferred (Section 2.2). A dedicated architecture review must produce an approved migration design (ADR) before this step executes.

**Pre-conditions for Step 1D implementation (requires Architecture Approval):**

1. Dedicated architecture review completed and approved.
2. PK strategy validated against approved constraints (API, Service, Repository interface, Schema, business logic unchanged).
3. Disposable-environment proof that `create_hypertable()` succeeds with approved PK design.
4. Full pg_dump backup of target environment.

**Assessment reference material (for follow-on review only — not an approved plan):**

The original assessment identified six hypertable candidates with partition columns: `weather_records` / `sensor_readings` / `yield_records` (`recorded_at`); `irrigation_events` (`started_at`); `disease_observations` / `satellite_observations` (`observed_at`). Suggested chunk intervals for evaluation: 1 week (weather, sensor); 1 month (irrigation, disease, satellite); ~3 months (yield). These parameters remain **candidates for Architecture Decision Review**, pending Architecture Approval.

**Success criteria (when approved):** All six tables are hypertables; existing API behavior unchanged; Alembic head advanced.

---

#### Step 1E — Policies, Aggregates & Analytics Foundation ⏳ Partial Scope — Analytics Requires Architecture Approval

**Objective:** Activate enterprise time-series capabilities for Phase 13 AI Feature Store.

**Approved scope (after Step 1D completes):**

1. Enable compression on hypertables (columnar compression for cold chunks).
2. Configure retention policies per domain (telemetry vs operational events).
3. Create continuous aggregates (examples):
   * Hourly avg soil moisture per field
   * Daily NDVI mean per field and spectral index
   * Daily irrigation water volume per field
4. Document aggregate views for Phase 13 Feature Store consumption.

**Deferred scope (Section 2.2 — requires Architecture Decision Review):**

* Repository-level analytics methods
* `time_bucket()` repository implementations
* Any new API endpoints exposing analytics queries

**Success criteria:** Compression and at least one continuous aggregate operational; no API breaking changes; repository analytics deferred pending Architecture Approval.

---

## 9. Backward Compatibility Assessment

| Layer | Unchanged? | Evidence / Notes |
|---|---|---|
| **Existing APIs** | ✅ Yes (baseline Phase 12) | No router modifications required for hypertable activation |
| **Existing repositories** | ✅ Yes (baseline) | Standard SQLAlchemy queries work on hypertables; new analytics methods **deferred** (Section 2.2) |
| **Existing services** | ✅ Yes | Business rules in service layer; no DB engine coupling |
| **Existing schemas** | ✅ Yes | Pydantic models independent of storage engine |
| **Existing migrations** | ✅ Valid | Historical chain preserved; forward migrations only |
| **Existing data** | ✅ Safe (with backup) | TimescaleDB is PostgreSQL-compatible; pg_dump before image switch |
| **Connection URL** | ✅ Unchanged | Same `postgresql+asyncpg://` scheme |
| **Docker volume** | ✅ Compatible | Same data directory mount path |

**Caveat:** Any Step 1D primary key strategy (when approved in follow-on review) may modify database constraints but must not alter API contracts, service method signatures, repository interfaces, or Pydantic schemas per the approved baseline (Section 2.1).

---

## 10. Enterprise Architecture Review

### 10.1 Clean Architecture — ✅ Confirmed

```text
API (FastAPI Routers)
  → Service (Business Rules)
    → Repository (Persistence)
      → SQLAlchemy ORM
        → PostgreSQL / TimescaleDB
```

Dependencies point inward. Routers do not import repositories directly. Services do not import FastAPI. **TimescaleDB slots beneath SQLAlchemy without violating layer boundaries.**

### 10.2 Domain-Driven Design — ✅ Confirmed

* Clear bounded contexts per domain (Farm, Field, Crop, SensorReading, etc.).
* Aggregate roots (`Farm`, `Field`) with consistent FK hierarchies.
* Ubiquitous language in enums (`app/core/enums.py`).
* Grandchild domains (`YieldRecord`, `DiseaseObservation`) and field-anchored domains (`SatelliteObservation`) follow documented patterns.

### 10.3 Repository Pattern — ✅ Confirmed

* `BaseRepository[T]` generic CRUD contract.
* Domain-specific query methods co-located with repositories.
* TimescaleDB readiness documented in repository module docstrings.

### 10.4 Service Layer Pattern — ✅ Confirmed

* All business rules enforced in services (timezone validation, immutability, cross-field PATCH guards).
* Domain exceptions raised in services; HTTP mapping in routers.

### 10.5 SOLID Principles — ✅ Observed

| Principle | Observation |
|---|---|
| Single Responsibility | Each service/repository owns one domain |
| Open/Closed | TimescaleDB extension via new migrations, not modification of Phase 1–11 logic |
| Liskov Substitution | Repository interfaces consistent via `BaseRepository` |
| Interface Segregation | DI provides only required repositories per service |
| Dependency Inversion | `deps.py` composition root injects abstractions |

### 10.6 Dependency Injection — ✅ Confirmed

`app/api/deps.py` is the sole composition root. TimescaleDB introduction requires **no DI changes** for baseline activation.

### 10.7 Observations Relevant to TimescaleDB

1. **Forward-compatible design is intentional** — model and repository comments reference TimescaleDB partition keys since Phase 7.
2. **Analytics queries appropriately deferred** — repository `time_bucket()` methods require Architecture Decision Review (Section 2.2).
3. **Async-first** — consistent with FastAPI; TimescaleDB benefits apply at SQL level regardless of async wrapper.
4. **PK constraint gap** — identified in assessment; resolution deferred pending Architecture Decision Review before Step 1D.

**No unrelated refactoring recommended.**

---

## 11. Phase 12 Readiness Score

| Dimension | Score (1–10) | Rationale |
|---|---|---|
| **Infrastructure** | 7 | Docker Compose solid; TimescaleDB image swap approved for Step 1B |
| **Database** | 8 | Schema time-keys, indexes, enums well-designed; PK strategy deferred to follow-on review |
| **Docker** | 8 | Multi-stage backend Dockerfile unchanged per approved baseline; db service change is isolated |
| **Architecture** | 9 | Clean Architecture strictly followed; TimescaleDB fits below ORM without layer violation |
| **Migration Readiness** | 7 | Steps 1B–1C approved; Step 1D requires Architecture Approval for PK strategy |
| **AI Readiness** | 8 | Six time-series domains with AI-oriented indexes; Feature Store awaits Step 1E (aggregates approved; repository analytics deferred pending ADR) |
| **Overall Phase 12 Readiness** | **7.5** | Strong foundation; Step 1B approved to proceed; Step 1D governed via Architecture Decision Review |

---

## 12. Recommendations for Step 1B

1. **Pin the TimescaleDB Docker image tag** — do not use `latest` in any environment that holds non-disposable data.
2. **Take a full pg_dump backup** before changing the `db` service image.
3. **Validate on Apple Silicon** using the official multi-arch TimescaleDB image; confirm `docker compose up` health check passes.
4. **Do not modify the backend Dockerfile or requirements.txt** — TimescaleDB is a database extension, not a Python dependency.
5. **Keep PostgreSQL 17 alignment** — select a TimescaleDB image based on PG 17 (not PG 18) to match current migration and documentation baseline.
6. **Fix the stale "PostgreSQL 18" comment** in `docker-compose.yml` during Step 1B as a documentation hygiene item (optional, low priority).
7. **Verify existing Alembic head** (`a1b2c3d4e5f6`) applies cleanly on the new image before proceeding to Step 1C.
8. **Establish a rollback procedure** documented in the team runbook: image revert + volume restore from dump.
9. **Deferred items require Architecture Approval** — composite PK migration, hypertable PK strategy, repository analytics, and `time_bucket()` methods require Architecture Decision Review before implementation (Section 2.2).
10. **Use Step 1B to gather PK constraint evidence** — reproduce the hypertable PK failure in a disposable database copy to inform the Architecture Decision Review; do not apply PK or hypertable migrations to shared dev data until Architecture Approval is granted.

---

## 13. Conclusion

AGRIFLOW-AI is **architecturally ready** for Phase 12 TimescaleDB introduction. Phases 1–11 deliberately established time-oriented schemas, compound indexes, append-only telemetry semantics, and repository query patterns that map directly to hypertable partition keys and chunk exclusion strategies. The Clean Architecture stack — API, Service, Repository, SQLAlchemy — requires **no structural refactoring** for baseline TimescaleDB activation.

This assessment is **approved as the architectural baseline** for Steps 1B–1E (Section 2). The approved critical path is:

1. **Step 1B** — TimescaleDB Docker image ✅ *Approved — proceed*
2. **Step 1C** — Extension enablement ✅ *Approved — after 1B validation*
3. **Step 1D** — Hypertable conversion ⏳ *Requires Architecture Approval — primary key strategy pending ADR*
4. **Step 1E** — Compression, retention, continuous aggregates ⏳ *Partial scope — repository analytics requires Architecture Approval*

Existing APIs, services, repository interfaces, schemas, and business rules remain unchanged throughout per architect approval. Comprehensive automated testing remains deferred to Phase 16 per project strategy; Steps 1B–1E should use manual validation, smoke testing, and Swagger verification at each step.

Phase 12 transforms AGRIFLOW-AI from a **PostgreSQL operational and observational platform** into an **enterprise time-series data platform** — the prerequisite for Phase 13 AI Feature Store and Recommendation Services. **Proceed to Step 1B** per the approved baseline. Step 1D requires Architecture Approval — hypertable primary key strategy must receive explicit approval via follow-on architecture review or ADR before implementation proceeds.

All Phase 12 implementation is governed by Section 2.4: conflicts with this baseline require a pause and architecture review; changes to API contracts, domain models, repository or service interfaces, primary key strategy, or database architecture require an ADR before implementation.

---

**Version 1.3**

**Revision Summary:**

* Refined governance terminology.
* Replaced implementation-blocking language with architecture governance language.
* No technical recommendations were changed.

---

*Assessment v1.3 — Phase 12 Step 1A approved as architectural baseline*  
*Architect review outcome and governance principle incorporated: June 2026*  
*Governance terminology refined: June 2026*  
*No application source code, Docker configuration, or migrations were modified during Step 1A.*
