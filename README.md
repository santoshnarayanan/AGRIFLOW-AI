# AGRIFLOW-AI

## AI-Powered Agricultural Intelligence Platform

AGRIFLOW-AI is an Agricultural Intelligence Platform designed to help farmers, agronomists, cooperatives, and agricultural enterprises manage farm operations, monitor crop lifecycles, analyze soil health, track irrigation events, record yield measurements, log disease observations, and build toward AI-driven agricultural decision intelligence.

The platform combines farm management, field management, crop management, soil intelligence, weather intelligence, sensor telemetry, irrigation management, yield tracking, disease observation, satellite observation, and future AI-powered recommendations into a unified agricultural operating platform.

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
docs/01-vision.md
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

### Current Phase

🔜 Phase 12 – TimescaleDB Time-Series Foundation (Planned)

### Phase 11 Implementation Status

| Status | Detail |
|---|---|
| Implementation | ✅ Domain implemented (Model, Schema, Repository, Service, Router) |
| Validation | ⏳ Deferred — comprehensive API validation planned for Phase 16 |
| Testing | ⏳ Deferred — automated test suite planned for Phase 16 |

---

### Current Domain Hierarchy

```text
Farm
 └── Field
      ├── Crop
      │    ├── YieldRecord           (Phase 9 — mutable, grandchild domain)
      │    └── DiseaseObservation    (Phase 10 — mutable, grandchild domain)
      ├── SoilProfile
      ├── WeatherRecord
      ├── SensorReading       (Phase 7 — append-only telemetry)
      ├── IrrigationEvent     (Phase 8 — mutable operational events)
      └── SatelliteObservation (Phase 11 — mutable Earth observation)
```

---

### Current Database Tables

```text
alembic_version
farms
fields
crops
soil_profiles
weather_records
sensor_readings
irrigation_events
yield_records
disease_observations
satellite_observations
```

Current migration head: `a1b2c3d4e5f6_create_satellite_observations_table`

#### Phase 12 Hypertable Candidates

The following tables were intentionally designed using time-oriented schemas, `TIMESTAMPTZ` primary time keys, and compound `(parent_id, time_key)` indexes to support future TimescaleDB hypertable conversion in Phase 12:

* `weather_records`
* `sensor_readings`
* `irrigation_events`
* `yield_records`
* `disease_observations`
* `satellite_observations`

No schema redesign is required — Phase 12 activates TimescaleDB as a PostgreSQL extension and promotes these tables to hypertables for enterprise-scale time-series analytics.

---

## Current Architecture

AGRIFLOW-AI follows a layered architecture.

```text
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

**Persistence evolution (Phase 12 — planned):** Phase 12 introduces **TimescaleDB as a PostgreSQL extension**. PostgreSQL 17 remains the primary relational database for all domain entities, migrations, and transactional workloads. TimescaleDB enhances time-series capabilities — hypertables, compression, continuous aggregates, retention policies, and `time_bucket()` analytics — rather than replacing PostgreSQL. TimescaleDB is **not yet implemented**; the current stack uses standard PostgreSQL 17 for all persistence.

```text
API Layer
    ↓
Service Layer
    ↓
Repository Layer
    ↓
SQLAlchemy ORM
    ↓
PostgreSQL 17  ←  primary relational database (current)
    +
TimescaleDB extension  ←  time-series analytics layer (Phase 12 — planned)
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
| Backend API         | FastAPI                             |
| Language            | Python 3.12                         |
| Database            | PostgreSQL 17                       |
| Time-Series Engine  | TimescaleDB (Planned — Phase 12)    |
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

* Farm registration
* Farm geolocation
* Farm administration

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
* Designed for TimescaleDB hypertable conversion in Phase 12 to support scalable time-series analytics, compression, continuous aggregates, retention policies, and AI feature engineering

### Sensor Telemetry (Phase 7)

* IoT sensor data persistence
* 11 sensor types: SOIL_MOISTURE, SOIL_TEMPERATURE, AIR_TEMPERATURE, AIR_HUMIDITY, LIGHT_INTENSITY, LEAF_WETNESS, ELECTRICAL_CONDUCTIVITY, SOIL_SALINITY, WATER_LEVEL, BATTERY_STATUS, DEVICE_HEALTH
* Append-only — immutable telemetry record
* Timezone-aware timestamp validation
* Designed for TimescaleDB hypertable conversion in Phase 12 to support scalable time-series analytics, compression, continuous aggregates, retention policies, and AI feature engineering

### Irrigation Management (Phase 8)

* Irrigation event logging per field
* 8 delivery methods: DRIP, SPRINKLER, FLOOD, FURROW, CENTER_PIVOT, SUBSURFACE, MANUAL, AUTOMATED
* 5 water sources: GROUNDWATER, SURFACE_WATER, RAINWATER, MUNICIPAL, RECYCLED_WATER
* Duration and water volume tracking
* Timezone-aware timestamp validation with cross-field ordering guard
* Mutable — operators can correct records after logging
* Designed for TimescaleDB hypertable conversion in Phase 12 to support scalable time-series analytics, compression, continuous aggregates, retention policies, and AI feature engineering

### Yield Intelligence (Phase 9)

* Discrete yield observation records per crop cycle
* 7 measurement methods: MANUAL_SCALE, COMBINE_MONITOR, YIELD_MAP, REMOTE_SENSING, CROP_CUT, LABORATORY_ANALYSIS, ESTIMATED
* Grain quality attributes: moisture content, test weight, quality grade
* Harvested area tracking
* Server-side `field_id` resolution from crop record
* Mutable — operators can correct measurements after logging
* Primary training label source for Phase 13 Yield Prediction Engine
* Designed for TimescaleDB hypertable conversion in Phase 12 to support scalable time-series analytics, compression, continuous aggregates, retention policies, and AI feature engineering

### Disease Observation (Phase 10)

* Disease pressure observation records per crop cycle
* 4 severity levels: LOW, MEDIUM, HIGH, CRITICAL
* 5 diagnosis methods: VISUAL_INSPECTION, LAB_ANALYSIS, IMAGE_AI, AGRONOMIST, SENSOR_DETECTED
* Affected area percentage tracking
* Treatment and operator notes
* Server-side `field_id` resolution from crop record
* Mutable — operators can correct observations after logging
* Crop-scoped and field-scoped list endpoints with pagination
* Primary training label source for Phase 13 Disease Risk Scoring Engine
* DiseaseObservation CRUD APIs
* Designed for TimescaleDB hypertable conversion in Phase 12 to support scalable time-series analytics, compression, continuous aggregates, retention policies, and AI feature engineering

### Satellite Observation (Phase 11)

* Derived spectral index observations per field (NDVI, EVI, NDWI, SAVI, NDRE, LAI, MSAVI, GNDVI)
* 8 satellite providers: SENTINEL_2, LANDSAT_8, LANDSAT_9, PLANET, MODIS, SPOT, WORLDVIEW, UNKNOWN
* 4 processing levels: L1C, L2A, ARD, DERIVED
* Field-anchored — satellite imagery persists across crop cycles
* AI-oriented query endpoints: date range, latest by spectral index, filter by provider/processing level
* Mutable — operators and data engineers can correct records after reprocessing
* Primary feature source for Phase 13 Yield Prediction and Disease Risk engines
* Designed for TimescaleDB hypertable conversion in Phase 12 to support scalable time-series analytics, compression, continuous aggregates, retention policies, and AI feature engineering

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

---

## Project Structure

```text
AGRIFLOW-AI
├── backend
├── docs
├── frontend (planned)
├── images
└── infrastructure
```

### Backend Structure

```text
backend/
├── app
│   ├── api
│   │   ├── crops/
│   │   ├── disease_observations/ ← Phase 10
│   │   ├── satellite_observations/ ← Phase 11
│   │   ├── fields/
│   │   ├── irrigation_events/
│   │   ├── sensor_readings/
│   │   ├── soil_profiles/
│   │   ├── weather_records/
│   │   ├── yield_records/       ← Phase 9
│   │   ├── deps.py
│   │   └── router.py
│   ├── core
│   │   └── enums.py             ← SensorType, IrrigationMethod, WaterSource, YieldMeasurementMethod, DiseaseSeverity, DiagnosisMethod, SatelliteProvider, SpectralIndex, ProcessingLevel
│   ├── db
│   │   ├── migrations/versions/
│   │   ├── models/              ← ORM models (Farm, Field, Crop, SoilProfile, WeatherRecord, SensorReading, IrrigationEvent, YieldRecord, DiseaseObservation, SatelliteObservation)
│   │   └── repositories/        ← Repository layer per domain
│   ├── schemas/                 ← Pydantic schemas per domain
│   ├── services/                ← Service layer per domain
│   └── main.py
├── Dockerfile
├── alembic.ini
└── requirements.txt
```

---

## Documentation

| Document | Description |
| --- | --- |
| `docs/01-vision.md` | Product Vision & Strategic Direction |
| `docs/02-architecture.md` | Technical Architecture (Phase 1–11 complete) |
| `docs/03-database.md` | Database Design & Schema Reference |
| `docs/04-api-design.md` | API Design & Endpoint Catalog |
| `docs/05-local-setup.md` | Local Development Setup |
| `docs/06-roadmap.md` | Product Roadmap (Phase 1–11 complete) |
| `docs/07-phase-history.md` | Phase-by-Phase Implementation History |
| `docs/08-phase-architecture-handbook.md` | Phase Architecture Handbook (authoritative ADR reference) |
| `docs/09-architecture-diagrams.md` | Architecture Diagrams (current and target state, Mermaid) |
| `docs/plan/AI_DATA_READINESS_ASSESSMENT.md` | AI Data Readiness Assessment (Phase 6) |
| `docs/AGRIFLOW_PALANTIR_ALIGNMENT.md` | Palantir Foundry Alignment Assessment (Phases 1–11) |
| `docs/plan/phase_9_yield_domain_93352ec2.plan.md` | Phase 9 Yield Domain — Implementation Plan |

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

### Current Phase

🔜 Phase 12 – TimescaleDB Time-Series Foundation (Planned)

### Planned Phases

🔜 **Phase 13 – AI Feature Store & Recommendation Services**

* Yield Recommendation Engine
* Irrigation Recommendation Engine
* Disease Recommendation Engine
* Fertilizer Recommendation Engine
* AI Feature Store
* Unified Recommendation Services API layer

🔜 **Phase 14 – Predictive Agriculture**

* Yield Prediction
* Disease Risk Prediction
* Irrigation Optimization
* Fertilizer Recommendation

🔜 **Phase 15 – Digital Twin & Farm Copilot**

* Digital Twin (continuously updated virtual field model)
* Farm Copilot (natural language decision support)
* Generative AI as a Service (GaaS)

⏳ **Phase 16 – Platform Stabilization & Quality Engineering**

* Complete test suite, CI/CD quality gates, production readiness

For the detailed roadmap see `docs/06-roadmap.md`

### Phase 12 – TimescaleDB Time-Series Foundation (Planned)

Phase 12 is an **infrastructure and data-platform phase** — not a business domain phase. It upgrades the existing PostgreSQL time-series tables to TimescaleDB hypertables before AI services begin. There are **no business domain changes** and **no API breaking changes**.

**Objectives:**

* Install TimescaleDB
* Enable TimescaleDB extension
* Convert eligible PostgreSQL tables into hypertables
* Configure automatic chunking
* Configure compression policies
* Configure retention policies
* Implement continuous aggregates
* Introduce `time_bucket()` based analytics
* Build repository support for optimized time-series queries
* Prepare the platform for AI feature engineering

**Tables prepared for hypertable conversion:**

These tables were designed with time-based primary query patterns and are now being upgraded for high-performance analytics:

* `weather_records`
* `sensor_readings`
* `irrigation_events`
* `yield_records`
* `disease_observations`
* `satellite_observations`

**Business value:**

* Enterprise-scale time-series storage
* High-performance historical analytics
* Efficient telemetry storage
* AI-ready feature engineering foundation
* Long-term scalability
* Foundation for predictive agriculture (Phase 14+)

---

## Current Agricultural Intelligence Platform (Post Phase 11)

```text
Farm
 └── Field
      ├── Crop                ✅ Phase 3
      │    ├── YieldRecord           ✅ Phase 9 (Harvest Intelligence — mutable, grandchild)
      │    └── DiseaseObservation    ✅ Phase 10 (Plant Health — mutable, grandchild)
      ├── SoilProfile         ✅ Phase 4
      ├── WeatherRecord       ✅ Phase 5
      ├── SensorReading       ✅ Phase 7 (IoT Telemetry — append-only)
      ├── IrrigationEvent     ✅ Phase 8 (Operational Management Events — mutable)
      └── SatelliteObservation ✅ Phase 11 (Earth Observation — mutable, field-anchored)
```

### Implemented Domains

| Domain | Phase | Entities | Notes |
|---|---|---|---|
| Farm | 1 | Farm | Root aggregate |
| Field | 2 | Field | Farm ↔ Field hierarchy |
| Crop | 3 | Crop | Lifecycle management |
| Soil Intelligence | 4 | SoilProfile | 1:1 per Field |
| Weather Intelligence | 5 | WeatherRecord | Time-series observations |
| AI Readiness | 6 | (attributes) | Cross-domain AI features |
| Sensor Telemetry | 7 | SensorReading | Append-only IoT data |
| Irrigation Management | 8 | IrrigationEvent | Mutable operational events |
| Yield | 9 | YieldRecord | Mutable, grandchild (Crop-anchored) |
| Disease Observation | 10 | DiseaseObservation | Mutable, grandchild (Crop-anchored) |
| Satellite Observation | 11 | SatelliteObservation | Mutable, field-anchored |

## Target Agricultural Intelligence Platform

```text
Farm
 └── Field
      ├── Crop
      │    ├── YieldRecord           ✅ Phase 9 Complete
      │    └── DiseaseObservation    ✅ Phase 10 Complete
      ├── SoilProfile
      ├── WeatherRecord
      ├── SensorReading
      ├── IrrigationEvent
      └── SatelliteObservation       ✅ Phase 11 Complete
```

---

## Long-Term Goals

AGRIFLOW-AI seeks to become the operating system for modern agriculture by combining operational data, environmental intelligence, predictive analytics, and artificial intelligence into a single platform that helps agricultural organizations improve productivity, sustainability, and decision-making.

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
(Phase 12 — TimescaleDB)
      ↓
AI Intelligence Platform
(Phase 13–15)
      ↓
Digital Twin & Farm Copilot
(Phase 15)
      ↓
Platform Stabilization & Production Readiness
(Phase 16)
```

Phase 12 exists because the observational domain model (Phases 7–11) generates high-volume time-series data that standard PostgreSQL indexing cannot scale indefinitely. TimescaleDB activation converts six pre-designed tables into hypertables, enabling compression, continuous aggregates, and `time_bucket()` analytics — the data platform required before AI Feature Store and Recommendation Services begin in Phase 13.

### AI Layer Goals (Phase 13+)

Phase 13 is the first AI implementation phase. AI capabilities depend on the TimescaleDB foundation delivered in Phase 12:

```text
TimescaleDB (Phase 12)
      ↓
Continuous Aggregates
      ↓
Feature Engineering
      ↓
AI Feature Store (Phase 13)
      ↓
Recommendation Services (Phase 13)
      ↓
Prediction Models (Phase 14)
      ↓
Farm Copilot / GaaS (Phase 15)
```

**Phase 13 deliverables:**

* **Yield Recommendation Engine** — supervised model trained on YieldRecord time-series (Phase 9 foundation) and SatelliteObservation NDVI features
* **Irrigation Recommendation Engine** — FAO-56 water balance optimization using IrrigationEvent history and soil moisture telemetry
* **Disease Recommendation Engine** — risk scoring using DiseaseObservation labels (Phase 10 foundation), sensor telemetry, weather patterns, and satellite NDVI trends
* **Fertilizer Recommendation Engine** — nutrient management recommendations from soil profiles and crop growth stage
* **AI Feature Store** — pre-computed feature vectors from TimescaleDB continuous aggregates (Phase 12 foundation)
* **Recommendation Services** — unified API layer exposing AI inference endpoints to the platform and GaaS

Phase 14 extends recommendation engines into full **Predictive Agriculture** (yield prediction, disease risk prediction, irrigation optimization, fertilizer recommendation). Phase 15 delivers the **Digital Twin**, **Farm Copilot**, and **Generative AI as a Service (GaaS)**.

### Infrastructure Goals

Infrastructure components are ordered by planned implementation sequence:

1. **PostgreSQL 17** — primary relational database for all domain entities, transactional workloads, Alembic migrations, and referential integrity (current — Phases 1–11)
2. **TimescaleDB (Phase 12)** — PostgreSQL extension for hypertable conversion, compression, continuous aggregates, retention policies, and `time_bucket()` analytics across six time-series tables; establishes the enterprise time-series platform before AI services
3. **PostGIS (Phase 14–15)** — field boundary polygon support for precision agriculture, satellite imagery spatial overlay, and variable-rate prescription zones
4. **Redpanda (Phase 13–14)** — event streaming for real-time Digital Twin state updates, AI pipeline triggers, and decoupled downstream consumers (`SensorReadingCreated`, `DiseaseObservationCreated`, etc.)
5. **Temporal (Phase 14–15)** — stateful agricultural workflow orchestration (soil moisture alerts, irrigation scheduling, harvest planning, alert escalation)
6. **Azure (Phase 15+)** — enterprise and cooperative deployment target (AKS container orchestration, Azure OpenAI for GaaS, Azure AI Search for agronomic knowledge retrieval)

---

## License

To be defined.
