# AGRIFLOW-AI Technical Architecture

## Overview

AGRIFLOW-AI is an Agricultural Intelligence Platform built using a layered architecture that emphasizes maintainability, scalability, separation of concerns, and domain-driven development.

The platform currently implements Farm, Field, Crop, Soil Intelligence, Weather Intelligence, Sensor Telemetry, Irrigation Management, and Yield domains across nine completed phases, following a Clean Architecture approach with clearly separated responsibilities across API, Service, Repository, and Database layers.

---

# Architecture Principles

AGRIFLOW-AI follows the following design principles:

* Clean Architecture
* SOLID Principles
* Repository Pattern
* Service Layer Pattern
* Separation of Concerns
* Dependency Injection
* Domain-Driven Design
* Migration-Driven Database Evolution
* API-First Development

---

# Technology Stack

| Layer                | Technology      |
| -------------------- | --------------- |
| Backend API          | FastAPI         |
| Language             | Python 3.12     |
| ORM                  | SQLAlchemy 2.x  |
| Database             | PostgreSQL      |
| Migration Framework  | Alembic         |
| Validation           | Pydantic        |
| Dependency Injection | FastAPI Depends |
| Containerization     | Docker          |
| Version Control      | Git + GitHub    |
| IDE                  | Cursor          |

---

# High-Level System Architecture

```text
Frontend
    │
    ▼
FastAPI API Layer
    │
    ▼
Service Layer
    │
    ▼
Repository Layer
    │
    ▼
SQLAlchemy ORM
    │
    ▼
PostgreSQL
```

---

# Current Domain Hierarchy

```text
Farm
 └── Field
      ├── Crop
      │    └── YieldRecord   ← Phase 9 (Grandchild Domain, Mutable)
      ├── SoilProfile
      ├── WeatherRecord
      ├── SensorReading      ← Phase 7 (Telemetry, append-only)
      └── IrrigationEvent    ← Phase 8 (Operational Management Events)
```

Current business domains:

* Farm Management
* Field Management
* Crop Management
* Soil Intelligence
* Weather Intelligence
* Sensor Telemetry (Phase 7)
* Irrigation Management (Phase 8)

Future domains:
* Irrigation Intelligence (Phase 8 — ✅ Complete)
* Yield Intelligence (Phase 9)
* Disease Observation (Phase 10)
* Satellite Observation (Phase 11)

Future AI Layer:
* Yield Prediction Engine
* Disease Prediction Engine
* Irrigation Recommendation Engine
* Farm Intelligence Platform

---

# Backend Project Structure

```text
backend/
├── app
│   ├── api
│   │   ├── farms
│   │   ├── fields
│   │   ├── crops
│   │   ├── soil_profiles
│   │   ├── weather_records
│   │   ├── sensor_readings   ← Phase 7
│   │   ├── irrigation_events ← Phase 8
│   │   ├── health
│   │   └── version
│   │
│   ├── core
│   │   ├── config
│   │   ├── enums.py          ← Phase 7 (SensorType) + Phase 8 (IrrigationMethod, WaterSource)
│   │   ├── logging
│   │   └── security
│   │
│   ├── db
│   │   ├── migrations
│   │   ├── models
│   │   ├── repositories
│   │   └── session
│   │
│   ├── schemas
│   ├── services
│   └── main.py
│
├── Dockerfile
├── alembic.ini
└── requirements.txt
```

---

# Layered Architecture

AGRIFLOW-AI uses five primary layers.

## API Layer

Responsibilities:

* HTTP endpoint definitions
* Request handling
* Response handling
* Exception translation
* Dependency injection

Examples:

```text
app/api/fields
app/api/crops
app/api/soil_profiles
app/api/weather_records
app/api/sensor_readings
app/api/irrigation_events
```

The API layer should not contain business logic.

---

## Schema Layer

Responsibilities:

* Request validation
* Response serialization
* API contracts

Examples:

```text
FieldCreate / FieldUpdate / FieldResponse
CropCreate / CropUpdate / CropResponse
SoilProfileCreate / SoilProfileUpdate / SoilProfileResponse
WeatherRecordCreate / WeatherRecordUpdate / WeatherRecordResponse
SensorReadingCreate / SensorReadingResponse  (no Update — immutable)
IrrigationEventCreate / IrrigationEventUpdate / IrrigationEventResponse
```

The schema layer defines what data enters and exits the application.

---

## Service Layer

Responsibilities:

* Business rules
* Validation
* Domain orchestration
* Cross-domain coordination

Examples:

```text
FieldService
CropService
SoilProfileService
WeatherRecordService
SensorReadingService
IrrigationEventService
```

Business rules belong here.

Examples:

* Farm must exist before Field creation
* Field must exist before Crop creation
* Field must exist before SoilProfile creation
* Only one SoilProfile allowed per Field
* Harvest date validation
* `recorded_at` must be timezone-aware and not in the future (SensorReading)
* `started_at` must be timezone-aware and not in the future (IrrigationEvent)
* `ended_at`, when supplied, must be ≥ `started_at` including sparse PATCH updates (IrrigationEvent)

---

## Repository Layer

Responsibilities:

* Database access
* CRUD operations
* Query execution
* Persistence

Examples:

```text
FarmRepository
FieldRepository
CropRepository
SoilProfileRepository
WeatherRecordRepository
SensorReadingRepository
IrrigationEventRepository
```

Repositories should not contain business rules.

---

## Model Layer

Responsibilities:

* Database entity definitions
* Table mapping
* Relationships

Examples:

```text
Farm
Field
Crop
SoilProfile
WeatherRecord
SensorReading
IrrigationEvent
```

Models represent PostgreSQL tables.

---

# Request Lifecycle

```text
Client Request
      │
      ▼
FastAPI Router
      │
      ▼
Pydantic Schema Validation
      │
      ▼
Service Layer
      │
      ▼
Repository Layer
      │
      ▼
SQLAlchemy ORM
      │
      ▼
PostgreSQL
```

Response Flow:

```text
PostgreSQL
      │
      ▼
SQLAlchemy ORM
      │
      ▼
Repository Layer
      │
      ▼
Service Layer
      │
      ▼
Response Schema
      │
      ▼
Client Response
```

---

# Dependency Injection Architecture

AGRIFLOW-AI uses FastAPI dependency injection.

```text
HTTP Request
      │
      ▼
Router
      │
      ▼
Dependency Provider
      │
      ▼
Service
      │
      ▼
Repository
      │
      ▼
AsyncSession
      │
      ▼
PostgreSQL
```

Benefits:

* Centralized transaction management
* Reduced coupling
* Improved testability
* Cleaner service construction

---

# Repository Pattern

AGRIFLOW-AI implements a generic repository architecture.

```text
BaseRepository
      │
      ├── FarmRepository
      ├── FieldRepository
      ├── CropRepository
      ├── SoilProfileRepository
      ├── WeatherRecordRepository
      ├── SensorReadingRepository     ← Phase 7
      └── IrrigationEventRepository   ← Phase 8
```

Benefits:

* Reduced code duplication
* Consistent CRUD implementation
* Reusable query patterns
* Easier maintenance

---

# Database Architecture

Current tables:

```text
alembic_version
farms
fields
crops
soil_profiles
weather_records
sensor_readings     ← Phase 7 (append-only telemetry)
irrigation_events   ← Phase 8 (operational management events)
```

Relationships:

```text
Farm (1)
   │
   ▼
Field (N)
   ├────────────► Crop (N)
   ├────────────► WeatherRecord (N)
   ├────────────► SensorReading (N, append-only)   ← Phase 7
   ├────────────► IrrigationEvent (N)              ← Phase 8
   │
   └────────────► SoilProfile (1)
```

---

# Database Migration Architecture

AGRIFLOW-AI uses Alembic for schema evolution.

Migration sequence:

```text
001_create_farms_table
002_create_fields_table
003_create_crops_table
004_create_weather_records_table
13aabbe35d51_add_soil_profiles_table
005_add_p1_ai_readiness_columns
006_create_sensor_readings_table      ← Phase 7 (sensor_type enum + sensor_readings + 5 indexes)
235a51cdf901_create_irrigation_events ← Phase 8 (irrigation_method + water_source enums + 3 indexes)
```

Migration flow:

```text
Model Change
      │
      ▼
Alembic Revision
      │
      ▼
Migration Script
      │
      ▼
Database Upgrade
```

Benefits:

* Version-controlled schema changes
* Repeatable deployments
* Environment consistency

---

# Current API Architecture

Implemented APIs:

## Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

## Version

* GET /api/v1/version

## Fields

* POST   /api/v1/farms/{farm_id}/fields
* GET    /api/v1/farms/{farm_id}/fields
* GET    /api/v1/fields/{field_id}
* PATCH  /api/v1/fields/{field_id}
* DELETE /api/v1/fields/{field_id}

## Crops

* POST   /api/v1/fields/{field_id}/crops
* GET    /api/v1/fields/{field_id}/crops
* GET    /api/v1/crops/{crop_id}
* PATCH  /api/v1/crops/{crop_id}
* DELETE /api/v1/crops/{crop_id}

## Soil Profiles

* POST   /api/v1/fields/{field_id}/soil-profile
* GET    /api/v1/fields/{field_id}/soil-profile
* PATCH  /api/v1/soil-profiles/{soil_profile_id}
* DELETE /api/v1/soil-profiles/{soil_profile_id}

## Weather Records

* POST   /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/weather-records/{weather_record_id}
* PATCH  /api/v1/weather-records/{weather_record_id}
* DELETE /api/v1/weather-records/{weather_record_id}

## Sensor Readings (Phase 7)

* POST   /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/sensor-readings/{sensor_reading_id}
* DELETE /api/v1/sensor-readings/{sensor_reading_id}

## Irrigation Events (Phase 8)

* POST   /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/irrigation-events/{event_id}
* PATCH  /api/v1/irrigation-events/{event_id}
* DELETE /api/v1/irrigation-events/{event_id}

---

# Current Platform Status

Completed Domains:

* Farm Domain
* Field Domain
* Crop Domain
* Soil Intelligence Domain
* Weather Intelligence Domain
* AI Readiness Foundation (Phase 6)
* Sensor Telemetry Domain — SensorReading (Phase 7)
* Irrigation Management Domain — IrrigationEvent (Phase 8)

Implemented Architecture:

* Model Layer
* Schema Layer
* Repository Layer
* Service Layer
* API Layer
* Dependency Injection
* PostgreSQL Integration
* Alembic Migration Framework
* Shared Enum Module (`app/core/enums.py`) — Phase 7 (SensorType) + Phase 8 (IrrigationMethod, WaterSource)
* Telemetry Immutability Pattern — Phase 7
* Compound Index Strategy — Phase 7 + Phase 8
* Operational Event Mutable Pattern — Phase 8

---

# Future Architecture Evolution

Planned domains:

```text
Farm
 └── Field
      ├── Crop
      ├── SoilProfile
      ├── Weather Records
      ├── Sensor Readings
      ├── Irrigation Events
      ├── Yield Records
      └── Satellite Observations
```

Future architectural capabilities:

* PostGIS Integration
* Event-Driven Architecture
* Message Queues
* AI Recommendation Engine
* Data Lake Integration
* MLOps Platform
* Digital Twin Architecture
* Farm Copilot
* Advanced Observability

---

# Architectural Vision

AGRIFLOW-AI is evolving from a farm management platform into a comprehensive Agricultural Intelligence Platform.

The architecture is designed to support the long-term vision of:

* Precision Agriculture
* Predictive Agriculture
* AI-Assisted Farming
* Agricultural Digital Twins
* Autonomous Agricultural Intelligence

while maintaining clear separation of concerns, scalability, and maintainability.

---

# Telemetry Architecture (Phase 7)

## Immutability Contract

`SensorReading` is the first domain in AGRIFLOW-AI with an explicit immutability contract. This is a deliberate architectural decision reflecting the nature of telemetry data.

Telemetry is a factual record of what a sensor reported at a specific moment. It must not be mutated — corrections are expressed as new readings.

This contract is enforced at three layers:
1. **Schema layer**: No `SensorReadingUpdate` schema exists.
2. **Service layer**: No `update_sensor_reading()` method exists.
3. **API layer**: No PATCH or PUT endpoint is registered (ADR-007-32).

## Append-Only Pattern

All sensor readings flow in a single direction: create → persist → event-publish (future).

```text
IoT Device / Ingestion Gateway
            │
            ▼
    POST /api/v1/fields/{field_id}/sensor-readings
            │
            ▼
    SensorReadingService (validate)
            │
            ▼
    SensorReadingRepository (persist)
            │
            ▼
    PostgreSQL sensor_readings table
            │
            ▼
    [Future: Redpanda event publish]
```

## Timestamp Validation

All sensor timestamps must satisfy two conditions (ADR-007-24 and ADR-007-25):

1. **Timezone-aware**: Naive `datetime.now()` is rejected with `InvalidSensorTimestampError` → HTTP 422.
2. **Not in the future**: Future timestamps are rejected with `InvalidSensorTimestampError` → HTTP 422.

Validation order is deliberate: timezone-awareness is checked first because a naive datetime cannot be safely compared to a UTC-aware timestamp.

## DOUBLE PRECISION for Sensor Values

`sensor_value` uses `DOUBLE PRECISION` (IEEE 754 64-bit float), unlike all other numeric columns in the platform which use `NUMERIC(p,s)`.

Rationale: Sensor ADC outputs and physical measurements (mV, µS/cm, lux, kPa) operate in floating-point space. Fixed-scale `NUMERIC` would silently truncate high-resolution readings. `DOUBLE PRECISION` is the correct type for sensor physics; `NUMERIC` is correct for accounting.

## Compound Index Strategy

Phase 7 introduced the first compound indexes in the project:

| Index | Columns | Primary Use Case |
|---|---|---|
| `ix_sensor_readings_field_id_recorded_at` | `(field_id, recorded_at)` | Time-ordered telemetry for a field |
| `ix_sensor_readings_sensor_type_recorded_at` | `(sensor_type, recorded_at)` | Cross-field type-scoped time queries |

These compound indexes cover the two dominant telemetry access patterns without requiring additional query planning overhead.

---

# Shared Enum Module

`app/core/enums.py` was established in Phase 7 as the canonical location for cross-domain enumerations.

Prior to Phase 7, enums (`CropStatus`, `SoilType`) were defined within their respective ORM model files. This pattern works for enums that belong exclusively to one domain.

`SensorType` was placed in `app/core/enums.py` because it will be consumed by future domains beyond `SensorReading`:
* `SensorDevice` — IoT device registry
* `SensorAlert` — alert rule definitions
* Digital Twin field state model
* AI Recommendation Engine feature pipeline

Importing enums from ORM model files creates circular import chains as cross-domain usage grows. `app/core/enums.py` is the neutral import point that prevents this.

All future cross-domain enumerations should be placed here.

---

# Architecture Decision Register (Summary)

Full ADR details are maintained in `docs/08-phase-architecture-handbook.md` (Section 19).

Key decisions by phase:

| ADR | Phase | Decision |
|---|---|---|
| ADR-001-01 | 1 | UUID v4 as universal primary key |
| ADR-001-02 | 1 | `AuditableModel` mixin on all tables |
| ADR-001-03 | 1 | Alembic as sole schema change mechanism |
| ADR-002-01 | 2 | Repository owns persistence only |
| ADR-002-02 | 2 | Transaction commit belongs to session dependency |
| ADR-002-03 | 2 | Domain exceptions are `ValueError` subclasses |
| ADR-002-04 | 2 | Routers translate domain exceptions to HTTP |
| ADR-003-01 | 3 | All enums inherit `str` for VARCHAR storage |
| ADR-004-01 | 4 | One-to-one enforced at DB level (UNIQUE) and service level |
| ADR-005-01 | 5 | Time-series entities use `TIMESTAMPTZ NOT NULL` |
| ADR-006-01 | 6 | P1 AI attributes are nullable ADD COLUMN — no backfill |
| ADR-007-19 | 7 | SensorReading supports DELETE but not UPDATE |
| ADR-007-25 | 7 | Timezone-naive datetimes rejected |
| ADR-007-26 | 7 | Service layer is the future event publishing boundary |
| ADR-007-27 | 7 | Historical telemetry cannot be mutated |
| ADR-007-32 | 7 | No PATCH or PUT endpoint for SensorReading |

---

# Future Architecture Evolution

## TimescaleDB

The `sensor_readings` table is designed for zero-friction TimescaleDB promotion. `recorded_at TIMESTAMPTZ NOT NULL` satisfies the hypertable partition key requirement.

Activation: `SELECT create_hypertable('sensor_readings', 'recorded_at', chunk_time_interval => INTERVAL '1 week');`

No application code changes are required. Continuous aggregates (hourly averages per sensor type per field) will be implemented as materialised views queried by a future `SensorAggregationRepository`.

## Apache Cassandra

High-scale deployments will migrate telemetry reads to Cassandra with `field_id` as the partition key and `recorded_at DESC` as the clustering key — matching the compound index already established. Migration occurs via a CQRS split with Redpanda projecting writes asynchronously.

## CQRS

Write side (`create`, `delete`) and read side (`list_by_field`, `get_by_id`) will be separated into distinct repository implementations backed by different storage engines. The service layer is the correct split boundary — no service code changes required.

## Redpanda

`SensorReadingService.create_sensor_reading()` contains a documented extension point (ADR-007-26) for publishing `SensorReadingCreated` events to the Redpanda topic `sensor.readings.created`. Downstream consumers: Digital Twin updater, AI anomaly detector, alert evaluator, CQRS projector.

## Temporal Workflows

Stateful agricultural alert workflows (sustained soil moisture deficit → irrigation recommendation → operator notification → escalation) will be triggered from the `create_sensor_reading` service extension point, launching Temporal workflows with durable timers and retry policies.

## Digital Twin

A continuously updated virtual model of every field will be maintained, sourced from `SensorReadingCreated` events (Redpanda), AI inference results, and crop lifecycle updates. The `SensorType` enum values map directly to Digital Twin field state properties.

## Generative-As-A-Service (GaaS)

The AGRIFLOW-AI REST API surface (fully documented in OpenAPI via FastAPI auto-generation) is already GaaS-ready. A future LLM agent will use AGRIFLOW-AI endpoints as tools to answer natural language queries from farmers and agronomists. Phase 7 sensor telemetry is a key context source for irrigation and crop health queries.

---

# Irrigation Management Architecture (Phase 8)

## Mutable Operational Event Pattern

`IrrigationEvent` is the first domain in AGRIFLOW-AI explicitly designed as a **mutable operational event**. Unlike `SensorReading` (which is append-only), irrigation events represent human-logged management actions that may require post-hoc correction.

Full CRUD surface (including PATCH) is provided by the API. This is a deliberate architectural contrast:

| Domain | Pattern | PATCH? | Rationale |
|---|---|---|---|
| SensorReading | Append-only telemetry | ✗ | Sensor measurement is a fact — immutable |
| IrrigationEvent | Mutable operational event | ✓ | Operator log — correctible after the fact |

## Timestamp Architecture

`started_at` is the primary time key:
- `TIMESTAMPTZ NOT NULL` — timezone-aware mandatory
- Serves as the TimescaleDB hypertable partition key in future phases
- Indexed individually and in compound with `field_id`
- Must not be in the future (service-layer validation → HTTP 400)

`ended_at` is optional and nullable:
- Supports cases where duration is known but exact end time is not
- When present, must be timezone-aware and ≥ `started_at`
- Sparse PATCH guard: when only one timestamp is present in the update payload, the service merges with the existing record before ordering validation

## Enum Lifecycle Fix (ADR-008-01)

Phase 8 introduced a critical PostgreSQL/SQLAlchemy compatibility fix. Prior migrations (`003` and `13aabbe35d51`) used `sa.Enum` to define PostgreSQL ENUM types. In SQLAlchemy 2.0.x, `sa.Enum._copy()` — invoked internally by `op.create_table()` — does not forward `create_type=False`, causing `DuplicateObjectError` on fresh databases.

**Resolution**: Use `postgresql.ENUM` (from `sqlalchemy.dialects.postgresql`) with `create_type=False` and explicit `.create()` / `.drop()` calls. This separates enum type lifecycle management from table DDL entirely.

This pattern is now the authoritative standard for all future migrations that introduce new PostgreSQL ENUM types.

## Index Strategy

Three indexes support the `irrigation_events` table:

| Index | Columns | Primary Use Case |
|---|---|---|
| `ix_irrigation_events_field_id` | `(field_id)` | All events for a given field |
| `ix_irrigation_events_started_at` | `(started_at)` | Events within a time window (cross-field) |
| `ix_irrigation_events_field_id_started_at` | `(field_id, started_at)` | Field-scoped irrigation history + AI feature pipelines |

The compound index is the primary AI access pattern for FAO-56 water balance computations.

## TimescaleDB Readiness

`irrigation_events.started_at TIMESTAMPTZ NOT NULL` satisfies the hypertable partition key requirement. Future activation:

```sql
SELECT create_hypertable('irrigation_events', 'started_at', chunk_time_interval => INTERVAL '1 month');
```

## Architecture Decision Register — Phase 8 Additions

| ADR | Decision |
|---|---|
| ADR-008-01 | Use `postgresql.ENUM` with `create_type=False` + explicit lifecycle for all new ENUM types |
| ADR-008-02 | IrrigationEvent is mutable — PATCH is permitted to allow operator correction |
| ADR-008-03 | `started_at` TIMESTAMPTZ is the TimescaleDB partition key candidate — indexed individually and in compound |
| ADR-008-04 | Sparse PATCH ordering guard: service merges payload with persisted record before `ended_at >= started_at` check |
| ADR-008-05 | `IrrigationMethod` and `WaterSource` placed in `app/core/enums.py` for future reuse by AI models and Digital Twin |

---

# Yield Domain Architecture (Phase 9)

Phase 9 introduced `YieldRecord` — the first grandchild entity in AGRIFLOW-AI — establishing a dedicated time-series observation log for crop yield measurements, separate from the scalar summary columns on the `Crop` model.

## Grandchild Domain Pattern

`YieldRecord` is anchored to `crop_id` as its primary FK because yield is a per-crop-cycle measurement, not a per-field point-in-time event (ADR-009-01):

```
Farm → Field → Crop → YieldRecord
```

`field_id` is **denormalized** directly onto `yield_records` (ADR-009-02) to enable field-scoped queries (`list_by_field`) without a JOIN through `crops`. Both FKs carry `ON DELETE CASCADE`.

## Mutable Domain

`YieldRecord` is mutable (ADR-009-04). PATCH is permitted so operators can correct measurement values (recalibrated moisture content, corrected harvested area) after logging. `crop_id` is the one immutable field (ADR-009-05) — the schema's `Update` model excludes it.

## Service-Side `field_id` Resolution

`YieldRecordService.create_yield_record()` accepts `crop_id` (from the URL path) and resolves `field_id` from the crop ORM instance before building the insert data. The caller never supplies `field_id` — this guarantees the denormalized column is always consistent.

## Dual-Parent Response Schema

`YieldRecordResponse` is the first response schema in the project that exposes two parent FKs (`crop_id` and `field_id`). This reflects the dual-anchor design and makes the denormalized path transparent to API consumers.

## Shared Enum Growth

`app/core/enums.py` now holds four shared enum types:

| Enum | Phase | Domain |
|---|---|---|
| `SensorType` | Phase 7 | SensorReading |
| `IrrigationMethod` | Phase 8 | IrrigationEvent |
| `WaterSource` | Phase 8 | IrrigationEvent |
| `YieldMeasurementMethod` | Phase 9 | YieldRecord, Phase 12 Yield Prediction Engine |

## Index Strategy

Four indexes support the `yield_records` table:

| Index | Columns | Primary Use Case |
|---|---|---|
| `ix_yield_records_crop_id` | `(crop_id)` | All records for a crop cycle |
| `ix_yield_records_field_id` | `(field_id)` | All records for a field (direct path) |
| `ix_yield_records_recorded_at` | `(recorded_at)` | Time-range queries across all fields |
| `ix_yield_records_crop_id_recorded_at` | `(crop_id, recorded_at)` | Compound — primary AI feature pipeline access |

## TimescaleDB Readiness

`yield_records.recorded_at TIMESTAMPTZ NOT NULL` satisfies the hypertable partition key requirement. Future activation:

```sql
SELECT create_hypertable('yield_records', 'recorded_at', chunk_time_interval => INTERVAL '1 season');
```

## Architecture Decision Register — Phase 9 Additions

| ADR | Decision |
|---|---|
| ADR-009-01 | `YieldRecord` anchors to `crop_id` as primary FK — yield is per crop cycle |
| ADR-009-02 | `field_id` denormalized on `yield_records` for direct field-scoped queries without JOIN |
| ADR-009-03 | `recorded_at TIMESTAMPTZ NOT NULL` is the primary time key and TimescaleDB partition key candidate |
| ADR-009-04 | `YieldRecord` is mutable — PATCH permitted for operator measurement corrections |
| ADR-009-05 | `crop_id` is immutable after creation — excluded from `YieldRecordUpdate` schema |
| ADR-009-06 | `area_harvested_ha > 0` (not `>= 0`) when supplied — Pydantic `ge=0` tightened at service layer |
| ADR-009-07 | `YieldMeasurementMethod` placed in `app/core/enums.py` for Phase 12 Yield Prediction Engine reuse |
| ADR-009-08 | `CropNotFoundError` imported from `app.services.crop` — shared domain exception, not re-declared |
