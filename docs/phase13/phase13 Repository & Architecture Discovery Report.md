# AGRIFLOW-AI Phase 13A
## Repository & Architecture Discovery Report

**Document Type:** Read-Only Architecture Discovery  
**Date:** August 9, 2026  
**Scope:** Current repository state prior to Phase 13 implementation  
**Status:** Discovery Complete — No repository changes made during inspection

---

### 1. Executive Summary

**FACT:** AGRIFLOW-AI is a **backend-only** Python 3.12 / FastAPI monolith with PostgreSQL 17.10 + TimescaleDB 2.28.1, organized in a **Clean Architecture** stack: API → Schemas → Services → Repositories → SQLAlchemy ORM → PostgreSQL/TimescaleDB.

**FACT:** Phases 1–12 are implemented. The repository contains **10 agricultural domains** (Farm through SatelliteObservation), **16 Alembic migrations** (head: `f6a7b8c9d0e1`), **6 hypertables**, **8 continuous aggregates**, **6 compression policies**, and **11 retention policies**. Phase 12 explicitly preserved existing repository interfaces, service behavior, and API contracts.

**FACT:** Phase 13 capabilities from the roadmap — Enterprise Ontology, Recommendation, Alert, Task, Decision Services, Operational Timeline, Business Event Catalog, AI-ready semantic layer — are **largely not implemented in code**. What exists today is a **governed data platform** with documented extension points, shared enums, AI-readiness columns, TimescaleDB analytics at the DB layer, and a Canonical Development Dataset (CDD) generator.

**INFERENCE:** Phase 13 should be treated as a **greenfield intelligence layer** atop a stable persistence foundation, not an extension of existing recommendation/decision code.

**FACT:** Testing is minimal (`backend/app/tests/test_health.py` only). No frontend, no CI/CD workflows, no authentication enforcement. Security settings exist (`SECRET_KEY`, JWT-related deps in `requirements.txt`) but `app/core/security/__init__.py` is a stub.

**Recommended next step:** Stop after discovery. Do not implement Phase 13 yet.

---

### 2. Repository Structure

#### Top-level tree (relevant portions)

```text
AGRIFLOW-AI/
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── api/                      # HTTP routers + deps.py DI
│   │   ├── cdd/                      # Canonical Development Dataset (Phase 12)
│   │   ├── core/                     # config, enums, logging, security stub
│   │   ├── db/                       # models, repositories, migrations, session
│   │   ├── schemas/                  # Pydantic request/response models
│   │   ├── services/                 # business logic layer
│   │   ├── tests/                    # pytest (minimal)
│   │   └── main.py                   # FastAPI entry point
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── backups/                          # DB dumps (agriflow_backup.dump, SQL)
├── docs/
│   ├── adr/                          # ADR-001 through ADR-005 (TimescaleDB)
│   ├── plan/                         # Phase design plans
│   ├── report/                       # Phase 12 implementation reports
│   ├── reports/                      # Domain design reports
│   ├── phase10/
│   ├── research/
│   └── 01-vision.md … 13-phase12-platform-bootstrap-guide.md
├── images/                           # Architecture diagrams
├── docker-compose.yml
├── README.md
└── .gitignore
```

#### Directory purposes

| Directory | Purpose |
|---|---|
| `backend/app/api/` | FastAPI routers; aggregated in `router.py` |
| `backend/app/services/` | Domain business rules, validation, exception types |
| `backend/app/db/models/` | SQLAlchemy ORM models |
| `backend/app/db/repositories/` | Data access; `BaseRepository` + domain extensions |
| `backend/app/db/migrations/` | Alembic migrations (incl. TimescaleDB DDL) |
| `backend/app/schemas/` | Pydantic API contracts |
| `backend/app/core/` | Settings, shared enums, structlog logging |
| `backend/app/cdd/` | Deterministic dev dataset generation/persistence/validation |
| `docs/adr/` | Formal architecture decisions (TimescaleDB only) |
| `docs/report/` | Phase 12 step reports and decision register |
| `backups/` | Database backup artifacts |

#### Directories that should **NOT** be modified during normal Phase 13 application work

| Path | Reason |
|---|---|
| `backend/.venv/` | Local virtualenv (vendor) |
| `backups/` | Data artifacts, not application source |
| `docs/report/PHASE12_*` | Historical Phase 12 evidence |
| `docs/adr/ADR-00[1-5]*` | Approved TimescaleDB decisions — amend via new ADR only |
| Phase 12 TimescaleDB migrations (`c9d8e7f6a5b4`, `d4f5e6a7b8c9`, `e5f6a7b8c9d0`, `f6a7b8c9d0e1`) | Unless explicitly justified and ADR-governed |
| `backend/app/db/migrations/versions/001`–`a1b2c3d4e5f6` (domain schema) | Existing domain tables — extend via **new** migrations only |

**FACT:** No `frontend/`, `scripts/`, `.github/` (CI/CD), or `conftest.py` exist.

---

### 3. Current Architecture

#### Implemented dependency flow

**FACT:** The repository follows the documented layered pattern:

```text
Client (HTTP)
    ↓
FastAPI Router          (backend/app/api/*/router.py)
    ↓
Pydantic Schema         (backend/app/schemas/)
    ↓
Service                 (backend/app/services/)
    ↓
Repository              (backend/app/db/repositories/)
    ↓
SQLAlchemy ORM Model    (backend/app/db/models/)
    ↓
PostgreSQL / TimescaleDB
```

**Representative wiring:** `backend/app/api/deps.py` constructs services with injected repositories bound to a request-scoped `AsyncSession` via `get_session()`.

#### Layer inventory

| Layer | Location | Responsibilities | Key files |
|---|---|---|---|
| **API** | `backend/app/api/` | HTTP mapping, exception→status translation | `router.py`, `deps.py`, domain routers |
| **Schemas** | `backend/app/schemas/` | Request/response validation | `common.py`, domain schemas |
| **Services** | `backend/app/services/` | Business rules, domain exceptions | 9 service modules + `__init__.py` |
| **Repositories** | `backend/app/db/repositories/` | DB queries, CRUD | `base.py`, 10 domain repos |
| **Models** | `backend/app/db/models/` | ORM mapping | 10 models in `__init__.py` |
| **Core/Config** | `backend/app/core/config/settings.py` | Env-based settings | Pydantic `Settings` |
| **Core/Enums** | `backend/app/core/enums.py` | Cross-domain vocabulary | 9 shared enums |
| **Logging** | `backend/app/core/logging/logger.py` | structlog JSON/console | Used across services/routers |
| **Security** | `backend/app/core/security/__init__.py` | **Stub only** | Comment placeholder |
| **DB Session** | `backend/app/db/session.py` | asyncpg engine, pool | `create_async_engine`, `AsyncSessionFactory` |
| **Migrations** | `backend/app/db/migrations/` | Schema evolution | Alembic + TimescaleDB DDL |

#### Dependency injection

**FACT:** Primary DI is in `backend/app/api/deps.py`:
- `SessionDep` → `get_session()` with explicit `session.begin()`
- `*ServiceDep` aliases for 9 domain services

**FACT:** A secondary, **unused-by-API** pattern exists in `backend/app/db/dependencies.py` (`get_db()` with commit/rollback). Exported from `backend/app/db/__init__.py` but routers use `api/deps.py`.

#### Exception handling

**FACT:** Global handler in `backend/app/main.py` catches unhandled exceptions → HTTP 500. Domain exceptions are mapped per-router (e.g., `FieldNotFoundError` → 404 in `fields/router.py`).

#### Architectural rules (observed)

1. Services accept repositories, not raw sessions.
2. Routers do not contain SQL.
3. Immutable domains: `SensorReading` (no update method/service path).
4. Mutable domains: PATCH allowed for Irrigation, Yield, Disease, Satellite, Weather, Soil, Crop, Field.
5. Parent existence validated in services before child creation.
6. PostgreSQL enum lifecycle: `postgresql.ENUM(..., create_type=False)` pattern (ADR-008-01 successor).
7. Phase 12: no changes to repository interfaces for time-series promotion.

#### Architectural exceptions / violations

| Issue | Evidence | Severity |
|---|---|---|
| Dual session DI patterns | `api/deps.py` vs `db/dependencies.py` | LOW |
| Farm incomplete vertical slice | Model + repo only; no schema/service/router | MEDIUM |
| `CropStatus`, `SoilType` not in `core/enums.py` | Defined in `crop.py`, `soil_profile.py` | LOW |
| Continuous aggregates not consumed in app code | `time_bucket` only in migration `e5f6a7b8c9d0` | MEDIUM (Phase 13 opportunity) |
| Documentation naming drift | README: "AI Feature Store"; roadmap: "Enterprise Decision & Recommendation Platform" | LOW |

---

### 4. Domain Inventory

#### Summary: 10 domains

| Domain | Model | Table | Schemas | Repository | Service | Router | DI | Mutable | TS/Relational |
|---|---|---|---|---|---|---|---|---|---|
| **Farm** | `Farm` | `farms` | ❌ | `FarmRepository` | ❌ | ❌ | indirect via `FieldService` | Yes | Relational |
| **Field** | `Field` | `fields` | ✅ | `FieldRepository` | `FieldService` | ✅ | `FieldServiceDep` | Yes | Relational |
| **Crop** | `Crop` | `crops` | ✅ | `CropRepository` | `CropService` | ✅ | `CropServiceDep` | Yes | Relational |
| **SoilProfile** | `SoilProfile` | `soil_profiles` | ✅ | `SoilProfileRepository` | `SoilProfileService` | ✅ | `SoilProfileServiceDep` | Yes | Relational (1:1) |
| **WeatherRecord** | `WeatherRecord` | `weather_records` | ✅ | `WeatherRecordRepository` | `WeatherRecordService` | ✅ | `WeatherRecordServiceDep` | Yes | Hypertable |
| **SensorReading** | `SensorReading` | `sensor_readings` | ✅ | `SensorReadingRepository` | `SensorReadingService` | ✅ | `SensorReadingServiceDep` | **Immutable** | Hypertable |
| **IrrigationEvent** | `IrrigationEvent` | `irrigation_events` | ✅ | `IrrigationEventRepository` | `IrrigationEventService` | ✅ | `IrrigationEventServiceDep` | Yes | Hypertable |
| **YieldRecord** | `YieldRecord` | `yield_records` | ✅ | `YieldRecordRepository` | `YieldRecordService` | ✅ | `YieldRecordServiceDep` | Yes | Hypertable |
| **DiseaseObservation** | `DiseaseObservation` | `disease_observations` | ✅ | `DiseaseObservationRepository` | `DiseaseObservationService` | ✅ | `DiseaseObservationServiceDep` | Yes | Hypertable |
| **SatelliteObservation** | `SatelliteObservation` | `satellite_observations` | ✅ | `SatelliteObservationRepository` | `SatelliteObservationService` | ✅ | `SatelliteObservationServiceDep` | Yes | Hypertable |

#### Per-domain detail (condensed)

**Farm**
- **Parent:** none (aggregate root)
- **Children:** `Field` (ORM cascade delete-orphan)
- **API:** none — farms referenced only as `{farm_id}` in field routes
- **Tests:** none
- **ADRs:** implicit in Phase 1; Palantir doc notes deferred Farm API

**Field**
- **FK:** `farm_id` → `farms.id`
- **Endpoints:** `POST/GET /farms/{farm_id}/fields`, `GET/PATCH/DELETE /fields/{field_id}`
- **Rules:** farm must exist; unique name per farm (case-insensitive)
- **Enums:** none from `core/enums.py`
- **Tests:** none

**Crop**
- **FK:** `field_id` → `fields.id`
- **Endpoints:** `POST/GET /fields/{field_id}/crops`, `GET/PATCH/DELETE /crops/{crop_id}`
- **Enum:** `CropStatus` (model-local, PG enum `crop_status`)
- **AI columns:** `actual_yield_tons_ha`, `expected_yield_tons_ha`, `seeding_rate_kg_ha`, `growth_stage`
- **Tests:** none

**SoilProfile**
- **FK:** `field_id` → `fields.id` (UNIQUE — 1:1)
- **Endpoints:** `POST/GET /fields/{field_id}/soil-profile`, `PATCH/DELETE /soil-profiles/{id}`
- **Enum:** `SoilType` (model-local)
- **Tests:** none

**WeatherRecord**
- **FK:** `field_id`; partition key `recorded_at`; composite PK `(id, recorded_at)`
- **Endpoints:** standard CRUD under `/fields/{field_id}/weather-records` and `/weather-records/{id}`
- **Tests:** none

**SensorReading**
- **FK:** `field_id`; append-only; partition key `recorded_at`
- **Endpoints:** POST, GET list, GET single, DELETE — **no PATCH**
- **Enum:** `SensorType` (`core/enums.py`)
- **Extension point:** `SensorReadingService.create_sensor_reading()` (ADR-007-26)
- **Tests:** none

**IrrigationEvent**
- **FK:** `field_id`; partition key `started_at`
- **Enums:** `IrrigationMethod`, `WaterSource`
- **Endpoints:** full CRUD with pagination
- **Tests:** none

**YieldRecord**
- **FK:** `crop_id` (primary), denormalized `field_id`
- **Partition key:** `recorded_at`
- **Enum:** `YieldMeasurementMethod`
- **Endpoints:** under `/crops/{crop_id}/yield-records`
- **Tests:** none

**DiseaseObservation**
- **FK:** `crop_id` + denormalized `field_id`
- **Partition key:** `observed_at`
- **Enums:** `DiseaseSeverity`, `DiagnosisMethod`
- **Endpoints:** crop-scoped + field-scoped list
- **Tests:** none

**SatelliteObservation**
- **FK:** `field_id`; partition key `observed_at`
- **Enums:** `SatelliteProvider`, `SpectralIndex`, `ProcessingLevel`
- **Endpoints:** 9 routes incl. `/range`, `/latest`, provider/processing filters
- **Repository:** richest query surface (date range, latest by index, etc.)
- **Tests:** none

**Infrastructure endpoints:** `/health/live`, `/health/ready`, `/version`

---

### 5. Domain Relationship Map

**FACT:** Verified from ORM (`field.py`, `crop.py`) and migrations:

```text
Farm (farms)                                    [PostgreSQL relational]
└── Field (fields)                              FK: farm_id
     ├── Crop (crops)                          FK: field_id
     │    ├── YieldRecord                      FK: crop_id + denormalized field_id
     │    └── DiseaseObservation              FK: crop_id + denormalized field_id
     ├── SoilProfile (soil_profiles)            FK: field_id UNIQUE (1:1)
     ├── WeatherRecord                         FK: field_id
     ├── SensorReading                         FK: field_id (append-only)
     ├── IrrigationEvent                       FK: field_id
     └── SatelliteObservation                  FK: field_id
```

#### Relationship details

| Relationship | Type | FK | Cascade | Enforced at |
|---|---|---|---|---|
| Farm → Field | 1:N | `fields.farm_id` | ORM cascade delete-orphan | DB + ORM |
| Field → Crop | 1:N | `crops.field_id` | cascade delete-orphan | DB + ORM |
| Field → SoilProfile | 1:1 | `soil_profiles.field_id` UNIQUE | cascade | DB UNIQUE + service |
| Field → time-series children | 1:N | `field_id` | cascade | DB + service (parent check) |
| Crop → YieldRecord | 1:N | `yield_records.crop_id` | CASCADE on delete | DB + service |
| Crop → DiseaseObservation | 1:N | `disease_observations.crop_id` | CASCADE | DB + service |
| Yield/Disease → Field | denormalized | `field_id` | CASCADE | Service resolves on create |

**FACT:** No FK from time-series tables to `Crop` except Yield and Disease. Weather, Sensor, Irrigation, Satellite anchor on **Field** only.

**FACT:** `crop_id` immutable after creation on Yield/Disease (excluded from update schemas per ADR-009-05 / ADR-010-05).

---

### 6. Shared Enums & Vocabulary

#### Location

**FACT:** Canonical cross-domain module: `backend/app/core/enums.py`

#### Enums in `core/enums.py` (9)

| Enum | Values (count) | Used by domains |
|---|---|---|
| `SensorType` | 11 | SensorReading |
| `IrrigationMethod` | 8 | IrrigationEvent |
| `WaterSource` | 5 | IrrigationEvent |
| `YieldMeasurementMethod` | 7 | YieldRecord |
| `DiseaseSeverity` | 4 | DiseaseObservation |
| `DiagnosisMethod` | 5 | DiseaseObservation |
| `SatelliteProvider` | 8 | SatelliteObservation |
| `SpectralIndex` | 8 | SatelliteObservation |
| `ProcessingLevel` | 4 | SatelliteObservation |

#### Model-local enums (not in `core/enums.py`)

| Enum | Location | PG type |
|---|---|---|
| `CropStatus` | `db/models/crop.py` | `crop_status` |
| `SoilType` | `db/models/soil_profile.py` | `soil_type` |

#### PostgreSQL enum lifecycle

**FACT:** Pattern from Phase 7+ migrations:
1. Explicit `postgresql.ENUM(...).create(op.get_bind())` in `upgrade()`
2. Column uses `create_type=False` to avoid duplicate `CREATE TYPE`
3. Documented in migrations `006`, `235a51cdf901`, `b7e2a9f4c8d3`, `d3e7b2a9f1c4`, `a1b2c3d4e5f6`

**FACT:** All shared enums use `str, enum.Enum` → stored as VARCHAR-compatible labels.

#### Phase 13 enum reuse assessment

**INFERENCE:** `core/enums.py` is the correct extension point for Phase 13 vocabulary (AlertType, RecommendationStatus, TaskPriority, etc.). Comments already reference future domains (`SensorAlert`, Recommendation Engine). Model-local enums should not be duplicated; new cross-cutting enums belong in `core/enums.py` with matching migration enum lifecycle.

---

### 7. Database & Alembic

#### Configuration

| Item | Location | Value |
|---|---|---|
| Engine | `db/session.py` | `postgresql+asyncpg://...` |
| Settings | `core/config/settings.py` | `DATABASE_URL` assembled from env |
| Alembic env | `db/migrations/env.py` | Async engine; imports all models |
| Base | `db/base.py` | `AuditableModel` = UUID PK + timestamps |

#### Versions (from `docker-compose.yml`, docs)

- **PostgreSQL:** 17 (via `timescale/timescaledb:2.28.1-pg17`)
- **TimescaleDB:** 2.28.1

#### Migration chain (16 revisions, head `f6a7b8c9d0e1`)

```text
8f3a1c2d9e04 (farms)
 → 3b7e9f1a2c85 (fields)
 → 5c2d8e3f7a19 (crops)
 → 13aabbe35d51 (soil_profiles)
 → 7d4f2a9b1e63 (weather_records)
 → f3a8c1d9e047 (AI readiness columns)
 → a8f3d1b6e924 (sensor_readings)
 → 235a51cdf901 (irrigation_events)
 → b7e2a9f4c8d3 (yield_records)
 → d3e7b2a9f1c4 (disease_observations)
 → a1b2c3d4e5f6 (satellite_observations)
 → f1e2d3c4b5a6 (TimescaleDB extension)
 → c9d8e7f6a5b4 (hypertables)
 → d4f5e6a7b8c9 (compression)
 → e5f6a7b8c9d0 (continuous aggregates)
 → f6a7b8c9d0e1 (retention) ← HEAD
```

#### Schema objects

**Tables (10 domain):** `farms`, `fields`, `crops`, `soil_profiles`, `weather_records`, `sensor_readings`, `irrigation_events`, `yield_records`, `disease_observations`, `satellite_observations`

**PostgreSQL enum types:** `crop_status`, `soil_type`, `sensor_type`, `irrigation_method`, `water_source`, `yield_measurement_method`, `disease_severity`, `diagnosis_method`, `satellite_provider`, `spectral_index`, `processing_level`

**Indexes:** Compound time indexes per domain (e.g., `ix_sensor_readings_field_id_recorded_at`); satellite has 7 indexes per migration

**Triggers:** none in application migrations

**Views / materialized views:** 8 TimescaleDB continuous aggregates (see §8)

**FK constraints:** Standard parent-child; yield/disease use `ON DELETE CASCADE`

---

### 8. TimescaleDB

#### Hypertables (migration `c9d8e7f6a5b4`)

| Table | Partition column | Chunk interval | Composite PK |
|---|---|---|---|
| `sensor_readings` | `recorded_at` | 7 days | `(id, recorded_at)` |
| `weather_records` | `recorded_at` | 7 days | `(id, recorded_at)` |
| `satellite_observations` | `observed_at` | 7 days | `(id, observed_at)` |
| `irrigation_events` | `started_at` | 1 month | `(id, started_at)` |
| `yield_records` | `recorded_at` | 3 months | `(id, recorded_at)` |
| `disease_observations` | `observed_at` | 1 month | `(id, observed_at)` |

**FACT:** Reference tables (`farms`, `fields`, `crops`, `soil_profiles`) remain standard PostgreSQL relations (ADR-002).

#### Compression policies (migration `d4f5e6a7b8c9`, ADR-003)

All 6 hypertables; e.g. `sensor_readings`: segmentby `field_id, sensor_type`, compress after 7 days.

#### Continuous aggregates (migration `e5f6a7b8c9d0`, ADR-004)

| View | Bucket | Source |
|---|---|---|
| `ca_sensor_hourly` | 1 hour | `sensor_readings` |
| `ca_sensor_daily` | 1 day | `sensor_readings` |
| `ca_weather_daily` | 1 day | `weather_records` |
| `ca_satellite_daily` | 1 day | `satellite_observations` |
| `ca_weather_weekly` | 1 week | `weather_records` |
| `ca_irrigation_monthly` | 1 month | `irrigation_events` |
| `ca_disease_weekly` | 1 week | `disease_observations` |
| `ca_yield_seasonal` | 90 days | `yield_records` |

Refresh policies: T1–T4 tiers (15 min to 1 day schedules).

#### Retention policies (migration `f6a7b8c9d0e1`, ADR-005)

**Raw hypertables:**
- `sensor_readings`: 24 months
- `weather_records`, `satellite_observations`: 36 months
- `irrigation_events`, `disease_observations`: 7 years
- `yield_records`: **EXEMPT** (permanent)

**CA retention:** 6 of 8 CAs have finite retention; `ca_irrigation_monthly` and `ca_yield_seasonal` exempt.

**FACT:** `TODO(AGRIFLOW-ARCHIVE-001)` — no Azure Blob archive gate before production retention activation.

#### Where represented

- Migrations: primary source of truth
- ADRs: `docs/adr/ADR-001` through `ADR-005`
- Reports: `docs/report/PHASE12_*`
- Application ORM: composite PK columns on time-series models

#### Phase 13 consumption path (no modification proposed)

**INFERENCE:** Decision/recommendation services should **read** continuous aggregates and raw hypertables via new analytical repositories or query services — **without altering** existing TimescaleDB policies, chunk intervals, or domain CRUD repositories (Phase 12 transparency principle).

---

### 9. Analytical / Query Capabilities

| Capability | Location | Type | Production? |
|---|---|---|---|
| Date-range queries | `SatelliteObservationRepository.list_by_field_and_date_range` | Repository | Yes |
| Latest-record queries | `SatelliteObservationRepository.get_latest_by_field_and_spectral_index` | Repository | Yes |
| Field/crop-scoped lists (time-ordered DESC) | All time-series repositories | Repository | Yes |
| Provider/processing filters | `SatelliteObservationRepository` | Repository | Yes |
| `time_bucket()` rollups | `e5f6a7b8c9d0_create_continuous_aggregates.py` | Migration/SQL only | DB layer |
| Deterministic cross-domain physics | `cdd/correlation/engine.py` | CDD support | Test/dev data only |
| CDD validation statistics | `cdd/statistics.py`, `cdd/validation/` | CDD support | Dev tooling |
| Scoring / risk / prediction / recommendation | — | — | **NOT PRESENT** |
| Feature extraction services | — | — | **NOT PRESENT** |
| Explainability | — | — | **NOT PRESENT** |

**FACT:** No application code queries `ca_*` views. Analytics today = repository list/filter on raw tables + DB-side continuous aggregates refreshed by TimescaleDB jobs (~27 background jobs per roadmap).

---

### 10. AI / ML Capabilities

| Category | Present? | Evidence |
|---|---|---|
| **A. Deterministic business intelligence** | **Partial** | CDD correlation engine (`compute_soil_moisture_from_rainfall`, `compute_ndvi_from_context`); AI-readiness schema columns |
| **B. Machine-learning inference** | **No** | No ML libraries in `requirements.txt` |
| **C. Generative AI** | **No** | No OpenAI/Anthropic/LangChain; `httpx` present but unused for LLM |
| **D. Agentic AI** | **No** | No agents, tools, or orchestration |
| **E. None** | — | Does not apply — (A) partially exists |

**FACT:** `requirements.txt` includes `passlib`, `python-jose`, `httpx` — security/HTTP primitives only, not AI stacks.

**FACT:** Future AI references are comments in enums, services, and documentation (Phases 13–16 roadmap).

---

### 11. Event & Workflow Infrastructure

| Component | Status | Evidence |
|---|---|---|
| Domain event models | NOT PRESENT | — |
| Event publishers/consumers | NOT PRESENT | — |
| Message brokers (Kafka/Redpanda/RabbitMQ) | NOT PRESENT | Comments only in services |
| Redis | NOT PRESENT | Roadmap Phase 15 |
| Celery / background workers | NOT PRESENT | — |
| Temporal | NOT PRESENT | Comment in `sensor_reading.py` service |
| Scheduled jobs (app-level) | NOT PRESENT | TimescaleDB internal jobs only |
| Outbox pattern | NOT PRESENT | Phase 14 roadmap |
| Event contracts | NOT PRESENT | — |

**FACT:** Documented extension points in create methods:
- `SensorReadingService.create_sensor_reading()` — ADR-007-26
- Similar comments in `yield_record.py`, `disease_observation.py`, `irrigation_event.py`, `satellite_observation.py` services

---

### 12. Alert / Task / Timeline Capabilities

| Concept | In codebase? | Form |
|---|---|---|
| Alert / Notification | No | Enum comments (`SensorAlert` future); docs only |
| Task / Action | No | — |
| Recommendation | No | Enum/docs references to "Recommendation Engine" |
| Decision | No | Roadmap/docs only |
| Workflow | No | — |
| Timeline / Activity | No | "timeline" in Phase 12 reports only |
| Operational event | Partial | `IrrigationEvent` is operational **data**, not workflow events |
| Audit event | Partial | `created_at`/`updated_at` on all auditable models; no audit log table |

---

### 13. Security & Governance

| Control | Status | Evidence |
|---|---|---|
| Authentication | **NOT ENFORCED** | No auth middleware; health/version unauthenticated by design |
| Authorization / RBAC | **NOT PRESENT** | — |
| User / tenant models | **NOT PRESENT** | — |
| JWT infrastructure | **CONFIGURED ONLY** | `SECRET_KEY`, `ALGORITHM` in settings; `python-jose` in requirements |
| Password hashing | **DEP ONLY** | `passlib` in requirements; no usage |
| CORS | Enabled | `main.py` — `ALLOWED_ORIGINS` |
| Secrets management | Env vars | `.env.example`; Azure Key Vault mentioned in settings docstring |
| Request/correlation IDs | **NOT PRESENT** | structlog without correlation middleware |
| Audit logging | **NOT PRESENT** | Timestamp columns only |
| API security | Open API | All domain endpoints publicly accessible |

**Phase 13 must respect:** No implicit security boundary exists — all data is accessible to any API caller. Multi-tenancy and farm ownership are not modeled.

---

### 14. Testing Architecture

| Aspect | Status |
|---|---|
| Framework | pytest + pytest-asyncio + httpx (`requirements.txt`) |
| Config | **No** `pytest.ini`, `pyproject.toml`, or `conftest.py` |
| Tests | `backend/app/tests/test_health.py` only (2 tests, mocked DB for readiness) |
| Domain tests | **None** |
| Integration tests | **None** |
| Migration tests | **None** |
| TimescaleDB validation | Documented in Phase 12 reports; **not automated in repo** |
| Test DB strategy | **Undefined** |
| Canonical dataset | CDD v1.0.0 (`backend/app/cdd/`) — 458,645 rows per docs |

**INFERENCE:** A Phase 13 domain should add:
- `backend/app/tests/` modules mirroring `services/`, `repositories/`, `api/`
- `conftest.py` with async session fixtures
- CDD-backed integration fixtures for decision scenarios
- Optional TimescaleDB CA query validation tests

---

### 15. Documentation & ADR Governance

#### Structure

| Type | Location | Convention |
|---|---|---|
| Master docs | `docs/01-vision.md` … `13-phase12-platform-bootstrap-guide.md` | Numbered prefixes |
| Roadmap | `docs/06-roadmap.md` | Phase sections with status |
| Phase history | `docs/07-phase-history.md` | Per-phase completion records |
| ADRs | `docs/adr/ADR-NNN-kebab-title.md` | ADR-001–005 (TimescaleDB only) |
| Phase 12 reports | `docs/report/PHASE12_*` | Step reports + `PHASE12_DECISION_REGISTER.md` |
| Plans | `docs/plan/` | Phase-specific design docs |
| Palantir alignment | `docs/AGRIFLOW_PALANTIR_ALIGNMENT.md` | Foundry comparison |
| Enum report | `docs/reports/REPORT-001-Shared-Domain-Enums.md` | Domain vocabulary |

#### ADR process

**FACT:** Phase 12 established formal ADR governance for infrastructure. Domain ADRs referenced in roadmap (ADR-007 through ADR-010 series) live in plan/history docs, not all as standalone `docs/adr/` files.

#### Documents to update after Phase 13 (eventually)

- `docs/06-roadmap.md`, `docs/07-phase-history.md`
- `docs/02-architecture.md`, `docs/04-api-design.md`, `docs/03-database.md`
- `docs/AGRIFLOW_PALANTIR_ALIGNMENT.md`
- New ADRs for recommendation/decision architecture
- `README.md` (currently says "AI Feature Store & Recommendation Services")

---

### 16. Phase 13 Capability Assessment

| Capability | Status | Evidence | Notes |
|---|---|---|---|
| Enterprise Ontology | **ARCHITECTURALLY PREPARED** | 10 ORM models, FK hierarchy, `core/enums.py`, `AGRIFLOW_PALANTIR_ALIGNMENT.md` | Implicit ontology; no formal ontology module |
| Recommendation Domain | **NOT PRESENT** | No model/table/service/router named Recommendation | Comments in enums/services only |
| Alert Domain | **NOT PRESENT** | No Alert model; `SensorType` doc mentions future `SensorAlert` | — |
| Task Domain | **NOT PRESENT** | Grep: no Task class/table | — |
| Decision Services | **NOT PRESENT** | No decision service module | — |
| Operational Timeline | **NOT PRESENT** | "Timeline" in Phase 12 benchmark reports only | — |
| Recommendation APIs | **NOT PRESENT** | `api/router.py` has no recommendation router | — |
| Recommendation Persistence | **NOT PRESENT** | No migration/table for recommendations | — |
| Business Event Catalog | **NOT PRESENT** | Phase 14 roadmap item | — |
| AI-ready Semantic Layer | **PARTIALLY IMPLEMENTED** | P1 AI columns (migration `005`), shared enums, CDD, continuous aggregates | Semantic layer as a query/API abstraction does not exist |

---

### 17. Phase 13 Extension Points

| Extension point | Why it fits | Reuse | Do not duplicate | Allowed deps | Avoid |
|---|---|---|---|---|---|
| `backend/app/core/enums.py` | Established cross-domain vocabulary pattern | `str, enum.Enum` convention | Per-domain enum copies | New Phase 13 enums | Breaking existing enum values |
| `backend/app/api/deps.py` + `router.py` | Standard DI + router registration | `SessionDep`, service factory pattern | Ad-hoc session handling | New `*ServiceDep` aliases | Direct repository injection in routers |
| `backend/app/services/` | Business rules + extension point comments | Domain exception pattern, parent validation | SQL in services | Existing domain services for reads | Coupling to TimescaleDB DDL |
| `backend/app/db/repositories/` | Data access boundary | `BaseRepository`, query patterns from `SatelliteObservationRepository` | Raw SQL scattered in services | New analytical repos for `ca_*` views | Changing existing repo interfaces |
| `backend/app/schemas/` | API contracts | `PaginatedResponse`, domain schema patterns | — | New recommendation schemas | Breaking existing schemas |
| `backend/app/db/migrations/versions/` | Schema evolution | Enum lifecycle pattern from Phase 7–11 | Editing old migrations | New tables for recommendations/alerts/tasks | Modifying Phase 12 TimescaleDB migrations |
| `backend/app/cdd/` | Deterministic validation corpus | Orchestrator, factories, validation rules | Production decision logic | Scenario fixtures for Phase 13 tests | Using CDD as runtime engine |
| Service create-method comments | Future event boundary | ADR-007-26 pattern | Implementing Redpanda in Phase 13 | Internal decision triggers (sync) | Kafka/Temporal (Phase 14+) |
| New analytical layer (recommended) | CA views not consumed by app today | TimescaleDB `ca_*` views via read-only queries | Embedding analytics in CRUD repos | Raw SQL / dedicated read repos | Mutating hypertable policies |

---

### 18. Files Likely to Change

#### A. Highly likely (new Phase 13 domains/services)

- `backend/app/db/models/` — new recommendation, alert, task, decision models
- `backend/app/db/migrations/versions/` — new migration(s) after `f6a7b8c9d0e1`
- `backend/app/schemas/` — new domain schemas
- `backend/app/db/repositories/` — new repositories (+ optional analytical repos)
- `backend/app/services/` — decision/recommendation services
- `backend/app/api/` — new routers
- `backend/app/api/router.py` — register new routers
- `backend/app/api/deps.py` — new service DI factories
- `backend/app/core/enums.py` — Phase 13 vocabulary
- `backend/app/db/models/__init__.py` — register new models for Alembic
- `backend/app/services/__init__.py` — export new services/exceptions
- `backend/app/tests/` — new test modules

#### B. Possible

- `backend/app/main.py` — middleware (correlation ID, auth if scoped)
- `backend/app/core/config/settings.py` — new feature flags
- `backend/app/cdd/` — scenarios including recommendations
- `docs/06-roadmap.md`, `docs/02-architecture.md`, etc.
- `docs/adr/` — new ADRs for Phase 13 decisions
- `README.md`

#### C. Should NOT be modified unless explicitly justified

- `backend/app/db/migrations/versions/c9d8e7f6a5b4*.py` (hypertables)
- `backend/app/db/migrations/versions/d4f5e6a7b8c9*.py` (compression)
- `backend/app/db/migrations/versions/e5f6a7b8c9d0*.py` (continuous aggregates)
- `backend/app/db/migrations/versions/f6a7b8c9d0e1*.py` (retention)
- Existing domain repository **interfaces** (Phase 12 contract)
- Existing API route paths and request/response models (Phases 1–11)
- `docker-compose.yml` TimescaleDB image pin (unless platform upgrade approved)
- `backups/` dump files

---

### 19. Architectural Risks

| Risk | Evidence | Phase 13 impact | Severity | Blocks? |
|---|---|---|---|---|
| Minimal automated test coverage | Only `test_health.py` | Regression risk for new decision layer | **HIGH** | No, but high delivery risk |
| No authentication/authorization | Open endpoints; security stub | Recommendations expose sensitive ops data | **HIGH** | No — but production blocker |
| Continuous aggregates unused by app | CAs only in migrations | Phase 13 must design read path or re-query raw data | **MEDIUM** | No |
| Farm domain incomplete | No Farm API/service/schema | Enterprise ontology may need farm-level decisions | **MEDIUM** | No |
| Dual session DI patterns | `get_db` vs `get_session` | Confusion for new contributors | **LOW** | No |
| Enum split (core vs model-local) | `CropStatus`, `SoilType` local | Inconsistent vocabulary for semantic layer | **LOW** | No |
| Composite PK + `get_by_id(id)` | BaseRepository queries by UUID only | Theoretically ambiguous if ID collision; practically UUID v4 unique | **LOW** | No |
| Documentation phase naming drift | README vs roadmap Phase 13 titles | Planning confusion | **LOW** | No |
| Retention without archive gate | `TODO(AGRIFLOW-ARCHIVE-001)` | Long-horizon decision evidence loss in prod | **MEDIUM** | No for dev; yes for prod |
| No CI/CD | No `.github/workflows` | No automated validation of Phase 13 | **MEDIUM** | No |

---

### 20. Decisions Required Before Implementation

**DECISION REQUIRED: Recommendation domain boundaries**
- What entities are recommended (irrigation, disease, yield, fertilizer)?
- Why it matters: Schema, enum design, and service decomposition depend on scope.

**DECISION REQUIRED: Recommendation lifecycle**
- Draft → active → superseded → expired?
- Why it matters: Persistence model, immutability rules, API semantics.

**DECISION REQUIRED: Recommendation ownership**
- Per field, crop, farm, or operator?
- Why it matters: FK design and authorization model.

**DECISION REQUIRED: Confidence / evidence model**
- Deterministic score, ML probability, rule ID, or composite?
- Why it matters: Cannot infer from repo — no prior art in code.

**DECISION REQUIRED: Deterministic vs ML engines**
- Phase 13 scope: rules-only, ML-ready interfaces, or full inference?
- Why it matters: Dependencies, latency, explainability requirements.

**DECISION REQUIRED: Alert ↔ Recommendation relationship**
- Alerts derived from recommendations or independent?
- Why it matters: Domain coupling and event flow.

**DECISION REQUIRED: Task ↔ Recommendation relationship**
- Tasks auto-created from recommendations?
- Why it matters: Workflow semantics and API design.

**DECISION REQUIRED: Decision persistence**
- Are decisions first-class entities or views over recommendations?
- Why it matters: Operational timeline and audit requirements.

**DECISION REQUIRED: Operational timeline semantics**
- Unified feed vs domain-specific timelines; retention; immutability.
- Why it matters: Query model and indexing strategy.

**DECISION REQUIRED: Enterprise ontology formalization**
- Code-first (existing ORM) vs separate ontology registry/graph module?
- Why it matters: "Enterprise Ontology" deliverable scope.

**DECISION REQUIRED: Semantic layer design**
- SQL views, service facades, or dedicated query API over CAs + domains?
- Why it matters: How Phase 13 consumes TimescaleDB without breaking Phase 12.

**DECISION REQUIRED: Business event catalog scope in Phase 13**
- Roadmap assigns event catalog to Phase 13 list but Phase 14 to Redpanda/events.
- Why it matters: Boundary between decision platform and event platform.

**DECISION REQUIRED: Authentication scope for Phase 13**
- Defer auth (current state) vs minimum viable RBAC?
- Why it matters: Decision APIs expose actionable intelligence.

**DECISION REQUIRED: Farm API completion**
- Implement Farm CRUD or continue field-anchored-only access?
- Why it matters: Enterprise farm management and ontology completeness.

---

### 21. Phase 13 Non-Goals

Based on roadmap (`docs/06-roadmap.md`) and repository evidence, **do not implement during Phase 13** unless explicitly approved:

| Technology / Capability | Planned phase |
|---|---|
| Redpanda / Kafka / event streaming | Phase 14 |
| Domain events / outbox / event consumers | Phase 14 |
| CQRS read/write split | Phase 15 |
| Full Feature Store | Phase 15 (roadmap); partial references in Phase 13 docs |
| Digital Twin | Phase 15–16 |
| Temporal workflows | Phase 14–16 |
| Farm Copilot / GaaS (LLM) | Phase 15–16 |
| MCP | Phase 16 |
| Cassandra horizontal scaling | Future |
| Production cloud infrastructure / observability platform | Phase 16 |
| Azure archive pipeline for retention | `AGRIFLOW-ARCHIVE-001` — before prod retention |
| Frontend / React UI | Not in repo; deferred since Phase 1 |
| Production auth/RBAC (unless Phase 13 explicitly scopes it) | Deferred since Phase 1 |

---

### 22. Current Architecture Diagram

```text
                         ┌─────────────────────────────────────┐
                         │         HTTP Clients                │
                         │    (no frontend in repository)      │
                         └─────────────────┬───────────────────┘
                                           │
                         ┌─────────────────▼───────────────────┐
                         │   FastAPI  app/main.py              │
                         │   CORS · global exception handler   │
                         │   prefix: /api/v1                   │
                         └─────────────────┬───────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
   ┌──────────▼──────────┐    ┌───────────▼──────────┐    ┌────────────▼────────────┐
   │  Domain Routers     │    │  health / version    │    │  (no auth middleware)   │
   │  fields,crops,soil, │    │  unauthenticated     │    └─────────────────────────┘
   │  weather,sensor,    │    └──────────────────────┘
   │  irrigation,yield,  │
   │  disease,satellite  │
   └──────────┬──────────┘
              │  api/deps.py (*ServiceDep, SessionDep)
   ┌──────────▼──────────┐
   │  Pydantic Schemas   │
   └──────────┬──────────┘
              │
   ┌──────────▼──────────────────────────────────────────┐
   │  Services (9) — business rules, domain exceptions   │
   │  extension-point comments on create (future events) │
   └──────────┬──────────────────────────────────────────┘
              │
   ┌──────────▼──────────────────────────────────────────┐
   │  Repositories (10) — BaseRepository + custom queries│
   └──────────┬──────────────────────────────────────────┘
              │
   ┌──────────▼──────────────────────────────────────────┐
   │  SQLAlchemy ORM Models (10)                           │
   │  AuditableModel: UUID id + created_at/updated_at      │
   └──────────┬──────────────────────────────────────────┘
              │
   ┌──────────▼──────────────────────────────────────────┐
   │  PostgreSQL 17 + TimescaleDB 2.28.1                   │
   │  ┌─────────────────────────────────────────────────┐  │
   │  │ Relational: farms, fields, crops, soil_profiles │  │
   │  └─────────────────────────────────────────────────┘  │
   │  ┌─────────────────────────────────────────────────┐  │
   │  │ Hypertables (6) + compression + retention       │  │
   │  │ Continuous Aggregates (8): ca_sensor_hourly …   │  │
   │  │ ~27 TimescaleDB background jobs                 │  │
   │  └─────────────────────────────────────────────────┘  │
   └───────────────────────────────────────────────────────┘

   Shared / cross-cutting:
   ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐
   │ core/enums.py  │  │ core/config     │  │ structlog logging│
   │ core/logging   │  │ settings (.env) │  │ security (stub)  │
   └────────────────┘  └─────────────────┘  └──────────────────┘

   Dev / validation (not runtime API):
   ┌────────────────────────────────────────────────────────────┐
   │  app/cdd/ — CDDOrchestrator, factories, validation,        │
   │             persistence (458k+ rows per docs)              │
   └────────────────────────────────────────────────────────────┘

   Migrations: Alembic (16 revisions, head f6a7b8c9d0e1)
   Tests: test_health.py only
   External integrations: none active
   Background infra (app-level): none
```

**Domain hierarchy (data model):**

```text
Farm → Field → Crop → {YieldRecord, DiseaseObservation}
              ↘ {SoilProfile 1:1, WeatherRecord, SensorReading*,
                  IrrigationEvent, SatelliteObservation}
              * append-only
```

---

### 23. Recommended Next Step

**Stop after discovery. Do not implement Phase 13 yet.**

Before implementation, recommended sequence:
1. Resolve **Decisions Required** (§20) via ADR/workshop — especially recommendation boundaries, persistence model, semantic layer vs Feature Store scope, and auth scope.
2. Author Phase 13 ADRs (separate from TimescaleDB ADR-001–005).
3. Define test strategy leveraging CDD fixtures.
4. Design analytical read layer for TimescaleDB continuous aggregates **without modifying Phase 12 infrastructure migrations**.

---

**Read-only confirmation:**
1. No files were modified during the original discovery inspection.
2. No migrations were executed during discovery.
3. No dependencies were installed during discovery.
4. This document was created as the formal deliverable of Phase 13A discovery.

DISCOVERY COMPLETE — NO REPOSITORY CHANGES MADE.
