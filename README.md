# AGRIFLOW-AI

## AI-Powered Agricultural Intelligence Platform

AGRIFLOW-AI is an Agricultural Intelligence Platform designed to help farmers, agronomists, cooperatives, and agricultural enterprises manage farm operations, monitor crop lifecycles, analyze soil health, and build toward AI-driven agricultural decision intelligence.

The platform combines farm management, field management, crop management, soil intelligence, weather intelligence, sensor integration, and future AI-powered recommendations into a unified agricultural operating platform.

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

## Current Platform Status

### Completed Phases

✅ Phase 1 – Foundation

✅ Phase 2 – Field Domain

✅ Phase 3 – Crop Domain

✅ Phase 4 – Soil Intelligence Domain

✅ Phase 5 – Weather Intelligence Domain

✅ Phase 6 – AI Readiness Foundation

✅ Phase 7 – SensorReading Domain (Telemetry)

---

### Current Domain Hierarchy

```text
Farm
 └── Field
      ├── Crop
      ├── SoilProfile
      ├── WeatherRecord
      └── SensorReading   (Phase 7 — append-only telemetry)
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
```

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
| Database            | PostgreSQL     |
| ORM                 | SQLAlchemy 2.x |
| Migration Framework | Alembic        |
| Validation          | Pydantic       |
| Containerization    | Docker         |
| Version Control     | Git + GitHub   |

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

---

## Phase 7 Completion Summary

Phase 7 introduced AGRIFLOW-AI's first telemetry domain: SensorReading.

Completed:

* Shared enum module (`app/core/enums.py`) with `SensorType` enum (11 sensor categories)
* SensorReading ORM model with `DOUBLE PRECISION` sensor value and `TIMESTAMPTZ` recorded_at
* Alembic migration 006: `sensor_readings` table, `sensor_type` PostgreSQL enum, 5 indexes (3 individual, 2 compound)
* SensorReading Pydantic schemas — `SensorReadingCreate`, `SensorReadingResponse` (no Update schema — immutable by design)
* SensorReadingRepository with create, list, get, delete operations
* SensorReadingService with field existence validation, timezone-aware timestamp validation, future timestamp rejection
* SensorReading API Router — 4 endpoints (no PATCH, no PUT)
* Full dependency injection registration in `app/api/deps.py`

New sensor types supported:

* SOIL_MOISTURE, SOIL_TEMPERATURE, AIR_TEMPERATURE, AIR_HUMIDITY
* LIGHT_INTENSITY, LEAF_WETNESS, ELECTRICAL_CONDUCTIVITY
* SOIL_SALINITY, WATER_LEVEL, BATTERY_STATUS, DEVICE_HEALTH

Architectural decisions introduced (ADR-007 series):

* Telemetry is append-only and immutable
* Timezone-naive timestamps are rejected (422 Unprocessable Entity)
* Future timestamps are rejected (422 Unprocessable Entity)
* Service layer marked as future boundary for Redpanda, Digital Twin, Temporal

---

## Phase 6 Completion Summary

Phase 6 focused on establishing the AI Readiness Foundation for AGRIFLOW-AI.

Completed:

* AI Data Readiness Assessment
* P1 AI Schema Enhancement
* AI-focused attribute expansion across Field, Crop, SoilProfile, and WeatherRecord domains
* Validation & Stabilization Pass
* Router exception-handling hardening
* Backward compatibility verification

New AI-ready attributes include:

### Field

* elevation_m

### Crop

* actual_yield_tons_ha
* expected_yield_tons_ha
* seeding_rate_kg_ha
* growth_stage

### SoilProfile

* soil_depth_cm
* cation_exchange_capacity_meq

### WeatherRecord

* solar_radiation_wm2
* temperature_min_c
* temperature_max_c


---

## Current API Coverage

### Health APIs

```http
GET /api/v1/health/live
GET /api/v1/health/ready
```

### Version API

```http
GET /api/v1/version
```

### Field APIs

```http
POST   /api/v1/farms/{farm_id}/fields
GET    /api/v1/farms/{farm_id}/fields
GET    /api/v1/fields/{field_id}
PATCH  /api/v1/fields/{field_id}
DELETE /api/v1/fields/{field_id}
```

### Crop APIs

```http
POST   /api/v1/fields/{field_id}/crops
GET    /api/v1/fields/{field_id}/crops
GET    /api/v1/crops/{crop_id}
PATCH  /api/v1/crops/{crop_id}
DELETE /api/v1/crops/{crop_id}
```

### Soil Profile APIs

```http
POST   /api/v1/fields/{field_id}/soil-profile
GET    /api/v1/fields/{field_id}/soil-profile
PATCH  /api/v1/soil-profiles/{soil_profile_id}
DELETE /api/v1/soil-profiles/{soil_profile_id}
```

### Weather Record APIs

```http
POST   /api/v1/fields/{field_id}/weather-records
GET    /api/v1/fields/{field_id}/weather-records
GET    /api/v1/weather-records/{weather_record_id}
PATCH  /api/v1/weather-records/{weather_record_id}
DELETE /api/v1/weather-records/{weather_record_id}
```

### Sensor Reading APIs (Phase 7)

```http
POST   /api/v1/fields/{field_id}/sensor-readings
GET    /api/v1/fields/{field_id}/sensor-readings
GET    /api/v1/sensor-readings/{sensor_reading_id}
DELETE /api/v1/sensor-readings/{sensor_reading_id}
```

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
│   ├── core
│   ├── db
│   ├── schemas
│   ├── services
│   └── main.py
├── Dockerfile
├── alembic.ini
└── requirements.txt
```

---

## Documentation

| Document                          | Description                          |
| --------------------------------- | ------------------------------------ |
| docs/01-vision.md                 | Product Vision & Strategic Direction |
| docs/02-architecture.md           | Technical Architecture               |
| docs/03-database.md               | Database Design                      |
| docs/04-api-design.md             | API Design                           |
| docs/05-local-setup.md            | Local Development Setup              |
| docs/06-roadmap.md                | Product Roadmap                      |
| docs/07-phase-history.md          | Implementation History               |
| docs/08-phase-architecture-handbook.md | Phase Architecture Handbook (authoritative reference) |
| docs/AI_DATA_READINESS_ASSESSMENT.md | AI Data Readiness Assessment (Phase 6) |

---

## Getting Started

### Clone Repository

```bash
git clone <repository-url>
cd AGRIFLOW-AI
```

### Start Services

```bash
docker compose up -d
```

### Run Database Migrations

```bash
alembic upgrade head
```

### Start Backend

```bash
uvicorn app.main:app --reload
```

### API Documentation

```text
http://localhost:8000/docs
```

---

## Roadmap Summary

### Current Next Phase

Phase 8 – Irrigation Domain

### Future Phases

Phase 9 – Yield Domain

Phase 10 – Disease Observation Domain

Phase 11 – Satellite Observation Domain

Phase 12 – Yield Prediction Engine

Phase 13 – Disease Prediction Engine

Phase 14 – Irrigation Recommendation Engine

Phase 15 – Farm Intelligence Platform

For the detailed roadmap see:

```text
docs/06-roadmap.md
```

---

## Current Agricultural Intelligence Platform (Post Phase 7)

```text
Farm
 └── Field
      ├── Crop                ✅ Phase 3
      ├── SoilProfile         ✅ Phase 4
      ├── WeatherRecord       ✅ Phase 5
      └── SensorReading       ✅ Phase 7 (IoT Telemetry)
```

## Target Agricultural Intelligence Platform

```text
Farm
 └── Field
      ├── Crop
      ├── SoilProfile
      ├── WeatherRecord
      ├── SensorReading
      ├── IrrigationEvent
      ├── YieldRecord
      └── SatelliteObservation
```

---

## Long-Term Goal

AGRIFLOW-AI seeks to become the operating system for modern agriculture by combining operational data, environmental intelligence, predictive analytics, and artificial intelligence into a single platform that helps agricultural organizations improve productivity, sustainability, and decision-making.

The long-term evolution can be summarized as:

```text
Reactive Farming
      ↓
Data-Driven Farming
      ↓
Predictive Farming
      ↓
Intelligent Farming
      ↓
Autonomous Agriculture
```

---

## License

To be defined.
