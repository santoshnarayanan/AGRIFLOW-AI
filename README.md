# AGRIFLOW-AI

## AI-Powered Agricultural Intelligence Platform

AGRIFLOW-AI is an Agricultural Intelligence Platform designed to help farmers, agronomists, cooperatives, and agricultural enterprises manage farm operations, monitor crop lifecycles, analyze soil health, track irrigation events, record yield measurements, log disease observations, and build toward AI-driven agricultural decision intelligence.

The platform combines farm management, field management, crop management, soil intelligence, weather intelligence, sensor telemetry, irrigation management, yield tracking, disease observation, satellite observation, structured recommendations and alerts (Phase 13 decision intelligence), and a React operational UI into a unified agricultural operating platform.

---

## Vision

AGRIFLOW-AI aims to evolve from a farm management platform into a comprehensive Agricultural Intelligence Platform capable of supporting:

* Precision Agriculture
* Predictive Agriculture
* Digital Twin Agriculture
* AI-Assisted Decision Making
* Sustainable Farming
* Autonomous Agriculture

For the complete strategic vision, see:

```text
docs/reference/01-vision.md
```

---

## Project Status

### Completed Phases

✅ Phase 1 – Foundation

✅ Phase 2 – Field Domain

✅ Phase 3 – Crop Domain

✅ Phase 4 – Soil Intelligence Domain

✅ Phase 5 – Weather Intelligence Domain

✅ Phase 6 – AI Readiness Foundation

✅ Phase 7 – SensorReading Domain (Telemetry)

✅ Phase 8 – Irrigation Management Domain

✅ Phase 9 – Yield Domain

✅ Phase 10 – Disease Observation Domain

✅ Phase 11 – Satellite Observation Domain

✅ Phase 12 – TimescaleDB Time-Series Foundation

✅ Phase 13 – Enterprise Decision & Recommendation Platform

### Current Phase

🔜 Phase 14 – Event-Driven Enterprise Platform

---

### Current Domain Hierarchy

```text
Farm                                         (PostgreSQL — relational; Farm CRUD API — Phase 13)
 └── Field                                   (PostgreSQL — relational)
      ├── Crop                               (PostgreSQL — relational)
      │    ├── YieldRecord                   (Phase 9 — TimescaleDB hypertable)
      │    └── DiseaseObservation            (Phase 10 — TimescaleDB hypertable)
      ├── SoilProfile                        (PostgreSQL — relational)
      ├── WeatherRecord                      (Phase 5 — TimescaleDB hypertable)
      ├── SensorReading                      (Phase 7 — TimescaleDB hypertable)
      ├── IrrigationEvent                    (Phase 8 — TimescaleDB hypertable)
      ├── SatelliteObservation               (Phase 11 — TimescaleDB hypertable)
      ├── Recommendation                     (Phase 13 — PostgreSQL — relational)
      └── Alert                              (Phase 13 — PostgreSQL — relational)

Phase 12: TimescaleDB 2.28.1 · 6 hypertables · compression · continuous aggregates · retention
Phase 13: Decision layer (recommendations · alerts) on standard PostgreSQL tables
```

---

### Current Database Tables

```text
PostgreSQL (relational)
alembic_version
farms
fields
crops
soil_profiles
recommendations          (Phase 13)
alerts                   (Phase 13)

TimescaleDB hypertables (Phase 12)
weather_records
sensor_readings
irrigation_events
yield_records
disease_observations
satellite_observations
```

Current migration head: `h2i3j4k5l6m7_create_alerts_table` (Phase 13)

#### Phase 12 Hypertable Candidates

Six time-series tables were converted to TimescaleDB hypertables in Phase 12 (ADR-002). Each uses a composite primary key `(id, time_column)`; reference tables remain standard PostgreSQL relations:

* `weather_records` — hypertable, partition key `recorded_at`
* `sensor_readings` — hypertable, partition key `recorded_at`
* `irrigation_events` — hypertable, partition key `started_at`
* `yield_records` — hypertable, partition key `recorded_at`
* `disease_observations` — hypertable, partition key `observed_at`
* `satellite_observations` — hypertable, partition key `observed_at`

Phase 12 also enabled compression policies, eight continuous aggregates, and eleven retention policies on the analytical platform. No application-layer API or repository interface changes were required.

---

## Current Architecture

AGRIFLOW-AI follows a layered architecture. A **React + TypeScript** client (`frontend/`) consumes the FastAPI REST API for dashboards, domain CRUD, and Phase 13 intelligence screens.

```text
React Frontend (Vite · TanStack Query)
    ↓
API Layer
    ↓
Service Layer
    ↓
Repository Layer
    ↓
SQLAlchemy ORM
    ↓
PostgreSQL 17
```

**Persistence (Phase 12 — complete):** Phase 12 activated **TimescaleDB 2.28.1 as a PostgreSQL extension** on PostgreSQL 17.10. PostgreSQL 17 remains the primary relational database for all domain entities, migrations, and transactional workloads. TimescaleDB enhances time-series capabilities — hypertables, compression, continuous aggregates, retention policies, and `time_bucket()` analytics — rather than replacing PostgreSQL. Six time-series tables are operational hypertables; reference tables remain standard PostgreSQL relations.

```text
API Layer
    ↓
Service Layer
    ↓
Repository Layer
    ↓
SQLAlchemy ORM
    ↓
PostgreSQL 17  ←  primary relational database
    +
TimescaleDB 2.28.1 extension  ←  time-series analytics layer (Phase 12 — complete)
```

### Architectural Principles

* Clean Architecture
* SOLID Principles
* Repository Pattern
* Service Layer Pattern
* Dependency Injection
* Separation of Concerns
* Domain-Driven Design

---

## Technology Stack

| Layer               | Technology                          |
| ------------------- | ----------------------------------- |
| Frontend            | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query |
| Backend API         | FastAPI                             |
| Language            | Python 3.12                         |
| Database            | PostgreSQL 17                       |
| Time-Series Engine  | TimescaleDB 2.28.1 (Phase 12 — complete) |
| ORM                 | SQLAlchemy 2.x                      |
| Migration Framework | Alembic                             |
| Validation          | Pydantic                            |
| Containerization    | Docker                              |
| Version Control     | Git + GitHub                        |

---

## Development Environment

This section documents the officially supported development environment for AGRIFLOW-AI.

### Python

* **Python 3.12.x** (recommended)

> **Note:** Python 3.14 is currently not supported. `pydantic-core` and its native compiled extensions do not yet fully support Python 3.14. Use Python 3.12.x for all development until upstream support is confirmed.

### Database

The development database is:

* **PostgreSQL 17**
* Running inside **Docker Desktop**
* Exposed on **`localhost:25432`**

A local PostgreSQL installation is optional and is **not** used by the application during normal development. All database connectivity is handled through the Docker-managed container.

### Docker

Docker Compose starts the following services:

* **PostgreSQL** — development database
* **FastAPI Backend** — application server

Containers communicate internally using Docker service names (e.g., `db`). Host-to-container connectivity uses `localhost:25432`.

### Operating Systems

AGRIFLOW-AI has been verified on:

* **Windows 11**
* **macOS** (Apple Silicon — M1/M2)

---

## Initial Project Setup

Complete the following steps to set up a local development environment from scratch.

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AGRIFLOW-AI
```

### 2. Create a Python Virtual Environment

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Backend Environment File

Copy the example environment file and populate it with your local credentials:

```text
backend/.env.example
→
backend/.env
```

### 5. Configure Database Credentials

Edit `backend/.env` and set your PostgreSQL connection string to match the Docker Compose configuration. By default:

```text
DATABASE_URL=postgresql+psycopg2://agriflow:agriflow@localhost:25432/agriflow
```

### 6. Start Docker

```bash
docker compose up -d
```

This starts PostgreSQL and the FastAPI backend as Docker containers.

### 7. Run Alembic Migrations

```bash
cd backend
alembic upgrade head
```

### 8. Start FastAPI (Local Development)

```bash
cd backend
uvicorn app.main:app --reload
```

### API Documentation

```text
http://localhost:8000/docs
```

### 9. Start the Frontend (Local Development)

```bash
cd frontend
npm install
npm run dev
```

```text
http://localhost:3000
```

The Vite dev server proxies `/api` to the backend (default `http://localhost:8000`). Set `VITE_API_URL` if the API base differs. See `docs/reference/phase-implementations/frontend-ui.md` for routes and API client mapping.

---

## Python Version Management

The repository contains a `.python-version` file at the repository root:

```text
.python-version
```

Its contents:

```text
3.12
```

This file is recognized by `pyenv` and compatible version managers to automatically select the correct Python interpreter. It standardizes the development environment across Windows, macOS, and Linux, ensuring that all contributors build against the same Python runtime.

---

## Database Architecture

```text
Docker Desktop
      ↓
PostgreSQL 17 (container: db, exposed on localhost:25432)
      ↓
AGRIFLOW-AI Backend
      ↓
pgAdmin (optional, connects to localhost:25432)
```

### Connection Reference

| Client                                    | Host        | Port  |
| ----------------------------------------- | ----------- | ----- |
| pgAdmin (host machine)                    | `localhost` | 25432 |
| FastAPI running on the host machine       | `localhost` | 25432 |
| FastAPI running inside Docker (container) | `db`        | 5432  |

When FastAPI runs inside a Docker container, it resolves the database using the Docker Compose service name `db` on the default PostgreSQL port 5432. When running directly on the host (e.g., during local development with `uvicorn --reload`), it connects via `localhost:25432`.

---

## Backup and Restore

### Creating a Backup

Use `pg_dump` to create a logical backup of the development database:

```bash
pg_dump -h localhost -p 25432 -U agriflow -d agriflow -F c -f agriflow_backup.dump
```

For a plain SQL export:

```bash
pg_dump -h localhost -p 25432 -U agriflow -d agriflow > agriflow_backup.sql
```

### Restoring a Backup

```bash
pg_restore -h localhost -p 25432 -U agriflow -d agriflow -F c agriflow_backup.dump
```

### Important

> **SQL backups must NOT be committed to Git.** Database dumps contain environment-specific data and potentially sensitive credentials. Store all backups outside the repository, in a secure location (e.g., local filesystem, encrypted cloud storage, or a dedicated backup volume).

---

## Git Ignore Recommendations

The following file types and directories must never be committed to version control:

| Pattern             | Reason                                            |
| ------------------- | ------------------------------------------------- |
| `.env`              | Contains secrets and environment-specific config  |
| `.venv/`            | Python virtual environment — machine-specific     |
| `*.sql`             | Database dump files — may contain sensitive data  |
| `*.dump`            | Binary database backups                           |
| `*.backup`          | Alternative backup file extensions                |
| `*.pg_dump`         | PostgreSQL-specific dump files                    |

Verify these patterns are present in `.gitignore` before committing any new file types.

---

## Current Features

### Farm Management

* Farm registration and full CRUD API (Phase 13 — completed deferred Phase 1 API surface)
* Farm geolocation and `farm_code` uniqueness validation
* Farm administration (soft delete via `is_active`)

### Field Management

* Field lifecycle management
* Farm ↔ Field relationship management
* Field geospatial tracking
* Field CRUD APIs

### Crop Management

* Crop lifecycle tracking
* Crop status management
* Planting and harvest tracking
* Crop CRUD APIs

### Soil Intelligence

* Soil profile management
* Soil nutrient tracking
* Soil pH tracking
* Organic matter tracking
* Soil health foundation
* SoilProfile CRUD APIs

### Weather Intelligence

* Historical weather observations
* Temperature tracking
* Humidity tracking
* Rainfall tracking
* Wind speed tracking
* WeatherRecord CRUD APIs
* Time-series weather data foundation
* TimescaleDB hypertable (Phase 12) — chunk-partitioned storage with compression, continuous aggregates, retention policies, and AI-ready time-series analytics

### Sensor Telemetry (Phase 7)

* IoT sensor data persistence
* 11 sensor types: SOIL_MOISTURE, SOIL_TEMPERATURE, AIR_TEMPERATURE, AIR_HUMIDITY, LIGHT_INTENSITY, LEAF_WETNESS, ELECTRICAL_CONDUCTIVITY, SOIL_SALINITY, WATER_LEVEL, BATTERY_STATUS, DEVICE_HEALTH
* Append-only — immutable telemetry record
* Timezone-aware timestamp validation
* TimescaleDB hypertable (Phase 12) — chunk-partitioned storage with compression, continuous aggregates, retention policies, and AI-ready time-series analytics

### Irrigation Management (Phase 8)

* Irrigation event logging per field
* 8 delivery methods: DRIP, SPRINKLER, FLOOD, FURROW, CENTER_PIVOT, SUBSURFACE, MANUAL, AUTOMATED
* 5 water sources: GROUNDWATER, SURFACE_WATER, RAINWATER, MUNICIPAL, RECYCLED_WATER
* Duration and water volume tracking
* Timezone-aware timestamp validation with cross-field ordering guard
* Mutable — operators can correct records after logging
* TimescaleDB hypertable (Phase 12) — chunk-partitioned storage with compression, continuous aggregates, retention policies, and AI-ready time-series analytics

### Yield Intelligence (Phase 9)

* Discrete yield observation records per crop cycle
* 7 measurement methods: MANUAL_SCALE, COMBINE_MONITOR, YIELD_MAP, REMOTE_SENSING, CROP_CUT, LABORATORY_ANALYSIS, ESTIMATED
* Grain quality attributes: moisture content, test weight, quality grade
* Harvested area tracking
* Server-side `field_id` resolution from crop record
* Mutable — operators can correct measurements after logging
* Primary training label source for future yield prediction ML engines (Phase 15+)
* TimescaleDB hypertable (Phase 12) — chunk-partitioned storage with compression, continuous aggregates, retention policies, and AI-ready time-series analytics

### Disease Observation (Phase 10)

* Disease pressure observation records per crop cycle
* 4 severity levels: LOW, MEDIUM, HIGH, CRITICAL
* 5 diagnosis methods: VISUAL_INSPECTION, LAB_ANALYSIS, IMAGE_AI, AGRONOMIST, SENSOR_DETECTED
* Affected area percentage tracking
* Treatment and operator notes
* Server-side `field_id` resolution from crop record
* Mutable — operators can correct observations after logging
* Crop-scoped and field-scoped list endpoints with pagination
* Primary training label source for future disease risk ML engines (Phase 15+)
* DiseaseObservation CRUD APIs
* TimescaleDB hypertable (Phase 12) — chunk-partitioned storage with compression, continuous aggregates, retention policies, and AI-ready time-series analytics

### Satellite Observation (Phase 11)

* Derived spectral index observations per field (NDVI, EVI, NDWI, SAVI, NDRE, LAI, MSAVI, GNDVI)
* 8 satellite providers: SENTINEL_2, LANDSAT_8, LANDSAT_9, PLANET, MODIS, SPOT, WORLDVIEW, UNKNOWN
* 4 processing levels: L1C, L2A, ARD, DERIVED
* Field-anchored — satellite imagery persists across crop cycles
* AI-oriented query endpoints: date range, latest by spectral index, filter by provider/processing level
* Mutable — operators and data engineers can correct records after reprocessing
* Primary feature source for future yield and disease risk ML engines (Phase 15+)
* TimescaleDB hypertable (Phase 12) — chunk-partitioned storage with compression, continuous aggregates, retention policies, and AI-ready time-series analytics

### Decision Intelligence (Phase 13)

* **Recommendation** domain — field-anchored agronomic decisions with type, status, priority, confidence, validity window, and engine provenance
* **Alert** domain — operational alerts with severity, acknowledgement lifecycle, and optional link to a recommendation
* Farm, Recommendation, and Alert REST APIs (15 new endpoints; Phases 1–12 domain APIs unchanged)
* React UI: `/recommendations`, `/alerts`, dashboard stats, and header notification bell — see `docs/reference/phase-implementations/frontend-ui.md`

### Frontend Application

* React + TypeScript SPA with 13 feature routes (farms, fields, crops, soil, weather, sensors, irrigation, yield, disease, satellite, recommendations, alerts, dashboard)
* Axios API clients aligned with FastAPI OpenAPI contracts (`frontend/src/api/`)
* Local dev on port 3000 with API proxy to the backend

---

## Testing Strategy

Comprehensive automated testing is intentionally deferred until **Phase 16 – Platform Stabilization & Quality Engineering**. Business rules continue to evolve across phases; writing large test suites before the domain model and infrastructure layers stabilise would require repeated rewrites.

**Phases 12–15 — incremental verification:**

* Manual validation of new infrastructure and AI capabilities
* Smoke testing of critical API paths
* Swagger/OpenAPI contract verification
* Incremental functional verification as each phase delivers new capabilities

**Phase 16 — comprehensive quality engineering:**

* Complete API validation across all domains
* Unit testing (Repository, Service, Schema layers)
* Repository testing and Service layer testing
* Integration testing and end-to-end workflow validation
* Regression testing
* Performance benchmarking
* Security validation
* CI/CD quality gates and code coverage reporting
* Production readiness assessment

This staged approach reduces rework while the domain model, TimescaleDB layer, and AI services continue to evolve. Until Phase 16, domain and infrastructure implementation proceeds phase-by-phase with Swagger/OpenAPI documentation as the primary contract verification mechanism during Phases 12–15.

---

## Business Rules Implemented

### Field Domain

* Farm must exist before Field creation
* Field names must be unique within a Farm

### Crop Domain

* Field must exist before Crop creation
* Harvest date validation
* Crop lifecycle management

### Soil Profile Domain

* Field must exist before SoilProfile creation
* Only one SoilProfile allowed per Field
* SoilProfile existence validation before update
* SoilProfile existence validation before delete

### Weather Record Domain

* Field must exist before WeatherRecord creation
* WeatherRecord existence validation before update
* WeatherRecord existence validation before delete
* Future timestamp validation
* Humidity validation
* Rainfall validation
* Wind speed validation

### SensorReading Domain (Phase 7)

* Field must exist before sensor reading creation
* `recorded_at` must be timezone-aware (naive datetimes rejected → 422)
* `recorded_at` must not be in the future (future timestamps rejected → 422)
* SensorReading is immutable — no update or patch operation permitted
* Telemetry list returned ordered by `recorded_at DESC` (most recent first)
* Administrative deletion supported; modification is not

### IrrigationEvent Domain (Phase 8)

* Field must exist before IrrigationEvent creation
* `started_at` must be timezone-aware and not in the future
* `ended_at`, when supplied, must be timezone-aware and ≥ `started_at`
* Cross-field ordering validated after sparse PATCH (effective values merged before check)
* `duration_minutes` must be non-negative
* `water_volume_liters` must be non-negative
* IrrigationEvent is mutable — operators can correct records after the fact

### YieldRecord Domain (Phase 9)

* Crop must exist before YieldRecord creation
* `field_id` resolved server-side from the crop record — not supplied by the caller
* `crop_id` is immutable after creation — excluded from update schema
* `recorded_at` must be timezone-aware and not in the future
* `yield_value_tons_ha` must be ≥ 0 (Pydantic); contextually > 0 enforced by service
* `area_harvested_ha`, when supplied, must be > 0
* `test_weight_kg_hl`, when supplied, must be > 0
* `moisture_content_percent`, when supplied, must be within [0, 100]
* `quality_grade`, when supplied, max length 50 characters
* YieldRecord is mutable — operators can correct measurements after logging

### DiseaseObservation Domain (Phase 10)

* Crop must exist before DiseaseObservation creation
* `field_id` resolved server-side from the crop record — not supplied by the caller
* `crop_id` is immutable after creation — excluded from update schema
* `observed_at` must be timezone-aware and not in the future
* `affected_area_percent`, when supplied, must be within [0, 100]
* `disease_name` max length 255 characters
* DiseaseObservation is mutable — operators can correct observations after logging

### SatelliteObservation Domain (Phase 11)

* Field must exist before SatelliteObservation creation
* `field_id` supplied through route path on create — not in request body
* `observed_at` must be timezone-aware and not in the future
* `index_value` validated against contextual range for `spectral_index` (ratio indices in [-1.0, 1.0]; LAI > 0)
* `resolution_m`, when supplied, must be > 0
* `cloud_cover_percent`, when supplied, must be within [0, 100]
* `field_id` immutable after creation — excluded from update schema
* SatelliteObservation is mutable — operators can correct records after reprocessing

### Phase 12 – Time-Series Data Platform Rules

* Time-series data is stored in TimescaleDB hypertables; master and reference data remains in standard PostgreSQL tables
* Only approved time-series domains are hypertables: `sensor_readings`, `weather_records`, `satellite_observations`, `irrigation_events`, `disease_observations`, `yield_records`
* Historical telemetry automatically transitions through: ingestion → chunking → compression → continuous aggregates → retention
* Continuous aggregates are the preferred source for analytical dashboards and AI feature generation — not repeated scans of raw telemetry
* Raw telemetry retention follows approved domain-specific policies
* `yield_records` are retained permanently — ground-truth agricultural outcomes required for historical analytics and AI model training
* Reference and master data (`farms`, `fields`, `crops`, `soil_profiles`, etc.) is not governed by TimescaleDB retention policies
* All Phase 12 persistence behaviour is governed by ADR-001 through ADR-005 — see `docs/adr/` for implementation detail

### Recommendation Domain (Phase 13)

* Field must exist before Recommendation creation
* Optional `crop_id` for crop-scoped context; SET NULL on crop delete preserves recommendation history
* Validity window and status lifecycle enforced in the service layer
* Mutable — operators can update recommendations after creation

### Alert Domain (Phase 13)

* Field must exist before Alert creation
* Optional `crop_id` and optional `recommendation_id` (soft link; alert survives recommendation deletion)
* Acknowledgement and resolution tracked via service-layer state transitions
* Mutable — operators can update alerts after creation

### Farm Domain (Phase 13 API completion)

* `farm_code` must be unique across active farms
* DELETE performs soft deactivation (`is_active = false`)

---

## Project Structure

```text
AGRIFLOW-AI
├── backend
├── docs
├── frontend                 (React + TypeScript operational UI)
├── images
└── infrastructure
```

### Backend Structure

```text
backend/
├── app
│   ├── api
│   │   ├── alerts/              ← Phase 13
│   │   ├── crops/
│   │   ├── disease_observations/ ← Phase 10
│   │   ├── farms/               ← Phase 13 (Farm CRUD)
│   │   ├── fields/
│   │   ├── irrigation_events/
│   │   ├── recommendations/     ← Phase 13
│   │   ├── satellite_observations/ ← Phase 11
│   │   ├── sensor_readings/
│   │   ├── soil_profiles/
│   │   ├── weather_records/
│   │   ├── yield_records/       ← Phase 9
│   │   ├── deps.py
│   │   └── router.py
│   ├── core
│   │   └── enums.py             ← domain enums incl. RecommendationType/Status/Priority, AlertType/Severity (Phase 13)
│   ├── db
│   │   ├── migrations/versions/
│   │   ├── models/              ← ORM models incl. Recommendation, Alert (Phase 13)
│   │   └── repositories/        ← Repository layer per domain
│   ├── schemas/                 ← Pydantic schemas per domain
│   ├── services/                ← Service layer per domain
│   └── main.py
├── Dockerfile
├── alembic.ini
└── requirements.txt
```

### Frontend Structure

```text
frontend/
├── src
│   ├── api/                     ← Axios clients per domain
│   ├── components/              ← layout, UI primitives, charts
│   ├── pages/                   ← route-level screens (Dashboard, Farms, … Recommendations, Alerts)
│   ├── types/                   ← shared TypeScript contracts
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

---

## Documentation

| Document | Description |
| --- | --- |
| `docs/reference/01-vision.md` | Product Vision & Strategic Direction |
| `docs/reference/02-architecture.md` | Technical Architecture (Phases 1–13 complete) |
| `docs/reference/03-database.md` | Database Design & Schema Reference |
| `docs/reference/04-api-design.md` | API Design & Endpoint Catalog |
| `docs/reference/05-local-setup.md` | Local Development Setup |
| `docs/reference/06-roadmap.md` | Product Roadmap |
| `docs/reference/07-phase-history.md` | Phase-by-Phase Implementation History |
| `docs/reference/08-architecture-handbook.md` | Phase Architecture Handbook |
| `docs/reference/09-architecture-diagrams.md` | Architecture Diagrams (Mermaid) |
| `docs/phases/phase13/phase-summary.md` | Phase 13 — Decision & Recommendation Platform summary |
| `docs/reference/phase-implementations/13-decision-intelligence.md` | Phase 13 implementation map (backend) |
| `docs/reference/phase-implementations/frontend-ui.md` | React UI routes, API clients, and dev setup |
| `docs/phases/phase06/ai-data-readiness-assessment.md` | AI Data Readiness Assessment (Phase 6) |
| `docs/reference/palantir-alignment.md` | Palantir Foundry Alignment Assessment |
| `ONBOARDING.md` | Single-page repository onboarding guide |

---

## Roadmap Summary

### Completed

✅ Phase 1 – Foundation  
✅ Phase 2 – Field Domain  
✅ Phase 3 – Crop Domain  
✅ Phase 4 – Soil Intelligence Domain  
✅ Phase 5 – Weather Intelligence Domain  
✅ Phase 6 – AI Readiness Foundation  
✅ Phase 7 – SensorReading Domain  
✅ Phase 8 – Irrigation Management Domain  
✅ Phase 9 – Yield Domain  
✅ Phase 10 – Disease Observation Domain  
✅ Phase 11 – Satellite Observation Domain  
✅ Phase 12 – TimescaleDB Time-Series Foundation  
✅ Phase 13 – Enterprise Decision & Recommendation Platform  

### Current Phase

🔜 Phase 14 – Event-Driven Enterprise Platform

### Planned Phases

🔜 **Phase 14 – Event-Driven Enterprise Platform** *(current)*

* Redpanda integration, domain events, outbox pattern, event catalog and consumers
* Foundation for real-time ML pipeline triggers and distributed services

🔜 **Phase 15 – Enterprise Intelligence Platform**

* CQRS, read models, dashboard projections
* Feature Store and AI feature registry
* Digital Twin foundation and AI-ready query services

⏳ **Phase 16 – Enterprise AI Platform & Production Readiness**

* Temporal workflows, Farm Copilot, Generative AI as a Service (GaaS)
* Full test suite, CI/CD quality gates, security hardening, production readiness

For the detailed roadmap see `docs/reference/06-roadmap.md`

### Phase 12 – TimescaleDB Time-Series Foundation (Complete)

Phase 12 is an **infrastructure and data-platform phase** — not a business domain phase. It upgraded six existing PostgreSQL time-series tables to TimescaleDB hypertables before AI services begin. There were **no business domain changes** and **no API breaking changes**.

**Delivered:**

* TimescaleDB 2.28.1 extension enabled via Alembic (`f1e2d3c4b5a6`)
* Six tables converted to hypertables with composite primary keys (`c9d8e7f6a5b4`)
* Six compression policies registered (`d4f5e6a7b8c9`)
* Eight continuous aggregates with refresh policies (`e5f6a7b8c9d0`)
* Eleven retention policies registered (`f6a7b8c9d0e1`)
* Canonical Development Dataset (CDD v1.0.0) for deterministic platform validation
* `time_bucket()` analytics foundation for AI feature engineering

**Hypertables implemented:**

* `weather_records` — partition key `recorded_at`
* `sensor_readings` — partition key `recorded_at`
* `irrigation_events` — partition key `started_at`
* `yield_records` — partition key `recorded_at`
* `disease_observations` — partition key `observed_at`
* `satellite_observations` — partition key `observed_at`

**Business value delivered:**

* Enterprise-scale time-series storage
* High-performance historical analytics
* Efficient telemetry storage with columnar compression
* AI-ready feature engineering foundation
* Long-term scalability with governed data lifecycle
* Foundation for predictive agriculture (Phase 14+)

---

## Current Agricultural Intelligence Platform (Post Phase 13)

```text
Farm                              ✅ Phase 1 model · Phase 13 CRUD API
 └── Field
      ├── Crop                ✅ Phase 3
      │    ├── YieldRecord           ✅ Phase 9 (Harvest Intelligence — TimescaleDB hypertable)
      │    └── DiseaseObservation    ✅ Phase 10 (Plant Health — TimescaleDB hypertable)
      ├── SoilProfile         ✅ Phase 4
      ├── WeatherRecord       ✅ Phase 5 (TimescaleDB hypertable)
      ├── SensorReading       ✅ Phase 7 (IoT Telemetry — TimescaleDB hypertable)
      ├── IrrigationEvent     ✅ Phase 8 (Operational Events — TimescaleDB hypertable)
      ├── SatelliteObservation ✅ Phase 11 (Earth Observation — TimescaleDB hypertable)
      ├── Recommendation      ✅ Phase 13 (Decision layer — PostgreSQL)
      └── Alert                 ✅ Phase 13 (Alert layer — PostgreSQL)

TimescaleDB analytical platform  ✅ Phase 12 (compression · continuous aggregates · retention)
React operational UI             ✅ frontend/ (13 routes — see phase-implementations/frontend-ui.md)
```

### Implemented Domains

| Domain | Phase | Entities | Notes |
|---|---|---|---|
| Farm | 1 / 13 API | Farm | Root aggregate; CRUD API completed Phase 13 |
| Field | 2 | Field | Farm ↔ Field hierarchy |
| Crop | 3 | Crop | Lifecycle management |
| Soil Intelligence | 4 | SoilProfile | 1:1 per Field |
| Weather Intelligence | 5 | WeatherRecord | TimescaleDB hypertable |
| AI Readiness | 6 | (attributes) | Cross-domain AI features |
| Sensor Telemetry | 7 | SensorReading | TimescaleDB hypertable |
| Irrigation Management | 8 | IrrigationEvent | TimescaleDB hypertable |
| Yield | 9 | YieldRecord | TimescaleDB hypertable |
| Disease Observation | 10 | DiseaseObservation | TimescaleDB hypertable |
| Satellite Observation | 11 | SatelliteObservation | TimescaleDB hypertable |
| TimescaleDB Platform | 12 | (6 hypertables) | Compression, CAs, retention — no API changes |
| Decision Intelligence | 13 | Recommendation, Alert | Standard PostgreSQL; engines produce structured records |
| Frontend UI | — | (SPA) | React client for all operational and intelligence screens |

## Target Agricultural Intelligence Platform

Phases 1–13 delivered the **operational data platform**, **TimescaleDB analytics layer**, **decision records** (recommendations and alerts), and a **production-style React UI**. Phases 14–16 add event-driven infrastructure, ML engines and Feature Store, Digital Twin, Farm Copilot, and enterprise production readiness — without redesigning the Phase 12 persistence foundation.

---

## Long-Term Goals

AGRIFLOW-AI seeks to become the operating system for modern agriculture by combining operational data, environmental intelligence, predictive analytics, and artificial intelligence into a single platform that helps agricultural organizations improve productivity, sustainability, and decision-making. Phase 12 completed the analytical persistence layer; Phase 13 delivered the decision layer and Farm CRUD API; Phases 14–16 will add event-driven processing, ML engines and Feature Store, Digital Twin, Farm Copilot, and production-grade platform quality — with future infrastructure (Redpanda, CQRS, Temporal) introduced incrementally per the approved roadmap.

### Platform Evolution

```text
Operational Data Platform
(Phase 1–5)
      ↓
AI Data Foundation
(Phase 6)
      ↓
Telemetry & Observation Platform
(Phase 7–11)
      ↓
Time-Series Data Platform
(Phase 12 — TimescaleDB ✅ Complete)
      ↓
Decision Intelligence Layer
(Phase 13 ✅ — recommendations · alerts · Farm API)
      ↓
Event-Driven & ML Platform
(Phase 14–15)
      ↓
Digital Twin & Farm Copilot
(Phase 15–16)
      ↓
Platform Stabilization & Production Readiness
(Phase 16)
```

Phase 12 delivered the observational data platform required before decision intelligence. Phase 13 added structured **Recommendation** and **Alert** domains plus the Farm CRUD API on top of TimescaleDB continuous aggregates and relational master data.

### AI & Intelligence Roadmap (Post Phase 13)

```text
TimescaleDB (Phase 12 ✅)
      ↓
Continuous Aggregates
      ↓
Decision Records (Phase 13 ✅)
      ↓
Domain Events / Redpanda (Phase 14)
      ↓
Feature Store & ML Engines (Phase 15)
      ↓
Digital Twin · Farm Copilot · GaaS (Phase 16)
```

**Phase 13 delivered:**

* **Recommendation domain** — lifecycle-managed decision records per field (and optional crop context)
* **Alert domain** — severity-based operational alerts with acknowledgement and optional recommendation linkage
* **Farm CRUD API** — completed the Farm vertical slice deferred since Phase 1
* **React UI** — operational and intelligence screens consuming the REST API

**Upcoming (Phases 14–16):** event-driven architecture (Phase 14), Feature Store and predictive ML engines (Phase 15), Digital Twin and Farm Copilot / GaaS with full production readiness (Phase 16). See `docs/reference/06-roadmap.md`.

### Infrastructure Goals

Infrastructure components are ordered by planned implementation sequence:

1. **PostgreSQL 17** — primary relational database for all domain entities, transactional workloads, Alembic migrations, and referential integrity (Phases 1–13)
2. **TimescaleDB 2.28.1 (Phase 12 ✅)** — PostgreSQL extension operational with six hypertables, six compression policies, eight continuous aggregates, eleven retention policies, and `time_bucket()` analytics
3. **React frontend (`frontend/`)** — operational UI for all domains and Phase 13 intelligence screens (Vite dev proxy to FastAPI)
4. **Redpanda (Phase 14)** — event streaming for real-time pipeline triggers and decoupled downstream consumers
5. **CQRS / Feature Store (Phase 15)** — read models, dashboard projections, and versioned ML feature vectors
6. **Temporal & Azure (Phase 16+)** — workflow orchestration and enterprise deployment (AKS, Azure OpenAI for GaaS)

---

## License

To be defined.
