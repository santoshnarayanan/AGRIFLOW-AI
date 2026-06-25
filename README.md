# AGRIFLOW-AI

## AI-Powered Agricultural Intelligence Platform

AGRIFLOW-AI is an Agricultural Intelligence Platform designed to help farmers, agronomists, cooperatives, and agricultural enterprises manage farm operations, monitor crop lifecycles, analyze soil health, track irrigation events, record yield measurements, log disease observations, and build toward AI-driven agricultural decision intelligence.

The platform combines farm management, field management, crop management, soil intelligence, weather intelligence, sensor telemetry, irrigation management, yield tracking, disease observation, and future AI-powered recommendations into a unified agricultural operating platform.

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

### Current Phase

🔄 Phase 11 – Satellite Observation Domain (In Progress)

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
      └── IrrigationEvent     (Phase 8 — mutable operational events)
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
```

Current migration head: `d3e7b2a9f1c4_create_disease_observations_table`

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
Model Layer
    ↓
PostgreSQL
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

| Layer               | Technology     |
| ------------------- | -------------- |
| Backend API         | FastAPI        |
| Language            | Python 3.12    |
| Database            | PostgreSQL 17  |
| ORM                 | SQLAlchemy 2.x |
| Migration Framework | Alembic        |
| Validation          | Pydantic       |
| Containerization    | Docker         |
| Version Control     | Git + GitHub   |

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

### Sensor Telemetry (Phase 7)

* IoT sensor data persistence
* 11 sensor types: SOIL_MOISTURE, SOIL_TEMPERATURE, AIR_TEMPERATURE, AIR_HUMIDITY, LIGHT_INTENSITY, LEAF_WETNESS, ELECTRICAL_CONDUCTIVITY, SOIL_SALINITY, WATER_LEVEL, BATTERY_STATUS, DEVICE_HEALTH
* Append-only — immutable telemetry record
* Timezone-aware timestamp validation
* TimescaleDB hypertable upgrade path

### Irrigation Management (Phase 8)

* Irrigation event logging per field
* 8 delivery methods: DRIP, SPRINKLER, FLOOD, FURROW, CENTER_PIVOT, SUBSURFACE, MANUAL, AUTOMATED
* 5 water sources: GROUNDWATER, SURFACE_WATER, RAINWATER, MUNICIPAL, RECYCLED_WATER
* Duration and water volume tracking
* Timezone-aware timestamp validation with cross-field ordering guard
* Mutable — operators can correct records after logging
* TimescaleDB hypertable upgrade path

### Yield Intelligence (Phase 9)

* Discrete yield observation records per crop cycle
* 7 measurement methods: MANUAL_SCALE, COMBINE_MONITOR, YIELD_MAP, REMOTE_SENSING, CROP_CUT, LABORATORY_ANALYSIS, ESTIMATED
* Grain quality attributes: moisture content, test weight, quality grade
* Harvested area tracking
* Server-side `field_id` resolution from crop record
* Mutable — operators can correct measurements after logging
* Primary training label source for Phase 12 Yield Prediction Engine
* TimescaleDB hypertable upgrade path

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
* TimescaleDB hypertable upgrade path

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
│   │   ├── fields/
│   │   ├── irrigation_events/
│   │   ├── sensor_readings/
│   │   ├── soil_profiles/
│   │   ├── weather_records/
│   │   ├── yield_records/       ← Phase 9
│   │   ├── deps.py
│   │   └── router.py
│   ├── core
│   │   └── enums.py             ← SensorType, IrrigationMethod, WaterSource, YieldMeasurementMethod, DiseaseSeverity, DiagnosisMethod
│   ├── db
│   │   ├── migrations/versions/
│   │   ├── models/              ← ORM models (Farm, Field, Crop, SoilProfile, WeatherRecord, SensorReading, IrrigationEvent, YieldRecord, DiseaseObservation)
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
| `docs/02-architecture.md` | Technical Architecture (Phase 1–10 complete) |
| `docs/03-database.md` | Database Design & Schema Reference |
| `docs/04-api-design.md` | API Design & Endpoint Catalog |
| `docs/05-local-setup.md` | Local Development Setup |
| `docs/06-roadmap.md` | Product Roadmap (Phase 1–10 complete) |
| `docs/07-phase-history.md` | Phase-by-Phase Implementation History |
| `docs/08-phase-architecture-handbook.md` | Phase Architecture Handbook (authoritative ADR reference) |
| `docs/09-architecture-diagrams.md` | Architecture Diagrams (current and target state, Mermaid) |
| `docs/plan/AI_DATA_READINESS_ASSESSMENT.md` | AI Data Readiness Assessment (Phase 6) |
| `docs/AGRIFLOW_PALANTIR_ALIGNMENT.md` | Palantir Foundry Alignment Assessment (Phases 1–8) |
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

### Current Phase

🔄 Phase 11 – Satellite Observation Domain (In Progress)

### Planned Phases

Phase 12 – Yield Prediction Engine (first AI model, uses Phase 9 YieldRecord labels)

Phase 13 – Disease Prediction Engine

Phase 14 – Irrigation Recommendation Engine

Phase 15 – Farm Intelligence Platform (Full Digital Twin + GaaS Farm Copilot)

For the detailed roadmap see `docs/06-roadmap.md`

---

## Current Agricultural Intelligence Platform (Post Phase 10)

```text
Farm
 └── Field
      ├── Crop                ✅ Phase 3
      │    ├── YieldRecord           ✅ Phase 9 (Harvest Intelligence — mutable, grandchild)
      │    └── DiseaseObservation    ✅ Phase 10 (Plant Health — mutable, grandchild)
      ├── SoilProfile         ✅ Phase 4
      ├── WeatherRecord       ✅ Phase 5
      ├── SensorReading       ✅ Phase 7 (IoT Telemetry — append-only)
      └── IrrigationEvent     ✅ Phase 8 (Operational Management Events — mutable)
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
      └── SatelliteObservation       🔄 Phase 11 (In Progress)
```

---

## Long-Term Goals

AGRIFLOW-AI seeks to become the operating system for modern agriculture by combining operational data, environmental intelligence, predictive analytics, and artificial intelligence into a single platform that helps agricultural organizations improve productivity, sustainability, and decision-making.

### Platform Evolution

```text
Phase 1–3   Reactive Farming       Farm, Field, Crop records
      ↓
Phase 4–6   Data-Driven Farming    Soil, Weather, AI-ready attributes
      ↓
Phase 7–9   Predictive Foundation  Sensor telemetry, Irrigation, Yield records
      ↓
Phase 10–11 Environmental Coverage Disease observation, Satellite imagery  ← Current
      ↓
Phase 12–14 Intelligent Farming    AI yield prediction, disease risk, irrigation optimization
      ↓
Phase 15+   Autonomous Agriculture Full Digital Twin + GaaS Farm Copilot
```

### AI Layer Goals (Phase 12+)

* **Yield Prediction Engine** — supervised model trained on YieldRecord time-series (Phase 9 foundation)
* **Disease Risk Engine** — risk scoring using DiseaseObservation labels (Phase 10 foundation), sensor telemetry, and weather patterns
* **Irrigation Recommendation Engine** — FAO-56 water balance optimization using IrrigationEvent history
* **Farm Intelligence Platform** — Digital Twin + event-driven architecture + GaaS natural language interface

### Infrastructure Goals

* **TimescaleDB** — hypertable promotion for `sensor_readings`, `irrigation_events`, `yield_records`, `disease_observations`
* **Redpanda** — event streaming for real-time Digital Twin state updates
* **PostGIS** — field boundary polygon support for precision agriculture
* **Temporal** — stateful agricultural workflow orchestration
* **Azure** — enterprise and cooperative deployment target (AKS, Azure OpenAI, Azure AI Search)

---

## License

To be defined.
