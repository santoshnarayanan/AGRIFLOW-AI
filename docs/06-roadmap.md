# AGRIFLOW-AI Roadmap

## Vision

AGRIFLOW-AI is being built as an AI-enabled agricultural intelligence platform that helps farmers, agronomists, cooperatives, and agricultural service providers improve crop productivity, soil health, operational efficiency, and sustainability through data-driven recommendations.

---

# Phase 1 – Foundation

Status: Completed

Completed:

* FastAPI Foundation
* PostgreSQL Integration
* Alembic Migration Framework
* Docker Foundation
* Farm Domain Model
* Farm Table Creation
* Health APIs
* Version APIs

Outcome:

* Backend foundation established
* Database migration strategy established
* Domain-driven architecture established

---

# Phase 2 – Field Domain

Status: Completed

Completed:

* Field ORM Model
* Farm ↔ Field Relationship
* Field Schemas
* Repository Layer
* Service Layer
* API Layer
* CRUD Endpoints
* Dependency Injection Framework

Outcome:

Farm
└── Field

Business Capability:

* Farm management
* Field management
* Field-level geospatial foundation

---

# Phase 3 – Crop Domain

Status: Completed

Completed:

* Crop ORM Model
* Crop Migration
* Crop Schema Layer
* Crop Repository Layer
* Crop Service Layer
* Crop API Layer

Outcome:

Farm
└── Field
└── Crop

Business Capability:

* Crop lifecycle management
* Crop history tracking
* Crop planning foundation

---

# Phase 4 – Soil Intelligence Domain

Status: Completed

Completed:

* SoilProfile ORM Model
* SoilProfile Database Migration
* SoilProfile Schema Layer
* SoilProfile Repository Layer
* SoilProfile Service Layer
* SoilProfile API Layer
* Dependency Injection Integration
* Integration & Validation Testing

Outcome:

Farm
└── Field
├── Crop
└── SoilProfile

Business Capability:

* Soil profile management
* Soil nutrient tracking
* Soil health foundation
* Soil intelligence foundation
* Precision agriculture readiness

Implemented Business Rules:

* Field must exist before SoilProfile creation
* Only one SoilProfile allowed per Field
* SoilProfile existence validation before update
* SoilProfile existence validation before delete

Delivered APIs:

* POST   /api/v1/fields/{field_id}/soil-profile
* GET    /api/v1/fields/{field_id}/soil-profile
* PATCH  /api/v1/soil-profiles/{soil_profile_id}
* DELETE /api/v1/soil-profiles/{soil_profile_id}

Backlog Coverage:

BACKLOG-001

* Soil Profile Management

Business Value:

* Early soil degradation detection
* Fertilizer optimization foundation
* Soil health visibility
* Sustainable farming support

---

# Phase 5 – Weather Intelligence Domain

Status: Completed

Completed:

* WeatherRecord ORM Model
* WeatherRecord Database Migration
* WeatherRecord Schema Layer
* WeatherRecord Repository Layer
* WeatherRecord Service Layer
* WeatherRecord API Layer
* Dependency Injection Integration
* Integration & Validation Testing
* Historical Weather Observation Foundation

Outcome:

Farm
└── Field
├── Crop
├── SoilProfile
└── WeatherRecord

Business Capability:

* Historical weather tracking
* Field-level weather intelligence
* Climate observation foundation
* Time-series agricultural data foundation
* Weather intelligence readiness

Implemented Business Rules:

* Field must exist before WeatherRecord creation
* WeatherRecord existence validation before update
* WeatherRecord existence validation before delete
* Future timestamp validation
* Humidity validation
* Rainfall validation
* Wind speed validation

Delivered APIs:

* POST   /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/weather-records/{weather_record_id}
* PATCH  /api/v1/weather-records/{weather_record_id}
* DELETE /api/v1/weather-records/{weather_record_id}

Backlog Coverage:

BACKLOG-003

* Weather Intelligence

BACKLOG-004

* Climate Risk Monitoring

Business Value:

* Better planting decisions
* Irrigation optimization
* Weather-based risk mitigation
* Foundation for predictive weather analytics

---

# Phase 6 – AI Readiness Foundation

Status: Completed

Objectives:

* AI Data Readiness Assessment (`docs/AI_DATA_READINESS_ASSESSMENT.md`)
* P1 AI Schema Enhancement (10 attributes across 4 domains)
* AI Attribute Expansion Across Field, Crop, SoilProfile, WeatherRecord
* Alembic Migration 005: P1 AI Readiness Columns
* Validation and Stabilization Pass
* Router Exception Handling Hardening
* Backward Compatibility Verification

Delivered AI Attributes:

Field:
* elevation_m

Crop:
* actual_yield_tons_ha
* expected_yield_tons_ha
* seeding_rate_kg_ha
* growth_stage

SoilProfile:
* soil_depth_cm
* cation_exchange_capacity_meq

WeatherRecord:
* solar_radiation_wm2
* temperature_min_c
* temperature_max_c

AI Coverage Improvement:

| Use Case | Before Phase 6 | After Phase 6 |
|---|---|---|
| Yield Prediction | 18% | 82% |
| Disease Prediction | 15% | 40% |
| Irrigation Optimization | 25% | 55% |
| Weather Intelligence | 35% | 65% |

Backlog Coverage:

BACKLOG-005

* AI Data Readiness Foundation

Business Value:

* Yield prediction model training now unblocked (82% feature coverage)
* Disease risk model foundation established
* Irrigation model inputs partially satisfied
* Platform data quality elevated for all future AI use cases

---

# Phase 7 – SensorReading Domain

Status: Completed

Objectives:

* SensorType shared enum module (`app/core/enums.py`)
* SensorReading ORM Model
* Alembic Migration 006: `sensor_readings` table, `sensor_type` PostgreSQL enum, 5 indexes
* SensorReading Pydantic Schemas (`SensorReadingCreate`, `SensorReadingResponse` — no Update schema)
* SensorReadingRepository with `create`, `get_by_id`, `list_by_field`, `delete`
* SensorReadingService with field existence validation, timezone-aware timestamp validation, future timestamp rejection
* SensorReading API Router (POST, GET list, GET single, DELETE)
* `SensorReadingServiceDep` dependency injection registration

Delivered APIs:

* POST   /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/sensor-readings/{sensor_reading_id}
* DELETE /api/v1/sensor-readings/{sensor_reading_id}

No PATCH. No PUT. SensorReading is append-only telemetry (ADR-007-32).

Architectural Decisions Established (ADR-007 series):

* Telemetry is append-only and immutable (ADR-007-27)
* Timezone-naive timestamps rejected at service layer (ADR-007-25)
* Future timestamps rejected (ADR-007-24)
* `DOUBLE PRECISION` for sensor values; `NUMERIC` inappropriate for ADC outputs (ADR-007)
* `ON DELETE CASCADE` on `field_id` FK for referential integrity
* Compound indexes on `(field_id, recorded_at)` and `(sensor_type, recorded_at)`
* Service layer marked as future Redpanda / Digital Twin / Temporal boundary (ADR-007-26)

Backlog Coverage:

BACKLOG-006

* Sensor Monitoring
* Real-time Telemetry Foundation

Business Value:

* IoT sensor data persistence for precision agriculture
* Soil moisture, leaf wetness, air temperature, and EC data available for AI models
* Foundation for Digital Twin field state (future)
* Foundation for real-time alert and recommendation engine (future)
* TimescaleDB hypertable upgrade path established (zero application code changes required)

---

# Cross-Cutting Capabilities

Implemented:

* PostgreSQL
* SQLAlchemy
* Alembic
* Repository Pattern
* Service Layer
* Dependency Injection
* FastAPI
* Farm Domain
* Field Domain
* Crop Domain
* Soil Intelligence Domain
* Weather Intelligence Domain
* SensorReading Domain (Phase 7)
* Shared Enum Module (`app/core/enums.py`)
* Telemetry Immutability Pattern
* Compound Index Strategy

Near-Term (Phases 8–11):

* TimescaleDB (sensor_readings hypertable promotion)
* Redpanda (event streaming for SensorReadingCreated events)
* Redis (Digital Twin field state cache)
* PostGIS (field boundary polygon support)
* Authentication and Authorization

Future:

* Cassandra (high-scale telemetry horizontal scaling)
* CQRS (read/write repository split for sensor telemetry)
* Temporal Workflows (alert evaluation, irrigation recommendation pipelines)
* Digital Twin (continuously updated virtual field model)
* Generative-As-A-Service / GaaS (LLM-powered Farm Copilot)
* Data Lake Integration
* MLOps Platform
* Observability Platform

---

# Current Domain Hierarchy (Post Phase 7)

```
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord
     └── SensorReading   ← Phase 7 Complete
```

# Target Domain Hierarchy (Long-Term)

```
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

# Long-Term Vision

AGRIFLOW-AI evolves from a farm management system into a comprehensive Agricultural Intelligence Platform capable of supporting precision agriculture, predictive analytics, sustainability initiatives, and AI-driven decision-making.


# Updated Strategic Roadmap

✅ Phase 1  – Foundation
✅ Phase 2  – Field Domain
✅ Phase 3  – Crop Domain
✅ Phase 4  – Soil Intelligence Domain
✅ Phase 5  – Weather Intelligence Domain
✅ Phase 6  – AI Readiness Foundation
✅ Phase 7  – SensorReading Domain

🔜 Phase 8  – Irrigation Domain
🔜 Phase 9  – Yield Domain
🔜 Phase 10 – Disease Observation Domain
🔜 Phase 11 – Satellite Observation Domain

AI Layer (Post Phase 11)
- Yield Prediction Engine
- Disease Prediction Engine
- Irrigation Recommendation Engine
- Farm Intelligence Platform

---

# Future Architecture Roadmap

## TimescaleDB

The `sensor_readings` table was designed for zero-friction TimescaleDB promotion. A single `create_hypertable('sensor_readings', 'recorded_at')` call converts it to a time-partitioned hypertable. No application code changes are required.

Capabilities unlocked:
* Automatic weekly chunk partitioning on `recorded_at`
* Chunk exclusion for time-range queries (skip irrelevant chunks entirely)
* Continuous aggregates: hourly/daily average per sensor type per field
* Columnar compression for cold data (20–100× storage reduction)
* Automatic data retention policies

## Apache Cassandra

For deployments at agricultural scale (thousands of farms, billions of sensor readings per year), Cassandra provides linear horizontal scaling that PostgreSQL cannot match.

The Cassandra partition model maps directly to the existing compound index:
* Partition key: `field_id`
* Clustering key: `recorded_at DESC`

Migration path: CQRS split with Redpanda projecting writes from PostgreSQL to Cassandra asynchronously. No service or API changes required.

## CQRS

As AI inference services, dashboards, and Digital Twin consumers scale, the read and write patterns for sensor data diverge:
* **Write side**: single reading validated, appended, event published
* **Read side**: latest reading per type, hourly aggregates, anomaly windows, AI feature vectors

CQRS splits `SensorReadingRepository` into separate `Write` and `Read` repository implementations backed by different storage engines (PostgreSQL for writes, TimescaleDB aggregates or Cassandra for reads).

The service layer is already the correct boundary for this split. No service code changes are required.

## Redpanda

The `SensorReadingService.create_sensor_reading()` method contains a documented extension point marking the future Redpanda publishing boundary (ADR-007-26).

Event: `SensorReadingCreated` published to topic `sensor.readings.created`

Downstream consumers:
* Digital Twin field state updater
* AI anomaly detection pipeline
* Alert evaluation engine
* CQRS read-model projector

## Temporal

Stateful agricultural workflows (e.g. sustained soil moisture deficit → irrigation recommendation → operator notification → auto-escalation) require durable execution with timers and retries.

Temporal integration point: `SensorReadingService.create_sensor_reading()` extension point triggers a `SoilMoistureAlertWorkflow` when `sensor_type == SOIL_MOISTURE` and value falls below threshold.

## Digital Twin

A continuously updated virtual model of every field, updated from:
* New sensor readings (`SensorReadingCreated` events via Redpanda)
* AI inference results
* Crop lifecycle updates

The `SensorType` shared enum (`app/core/enums.py`) maps directly to the Digital Twin field state properties. No enum refactoring required at integration time.

## Generative-As-A-Service (GaaS)

The AGRIFLOW-AI REST API is already GaaS-ready. A future GaaS agent uses the existing endpoints as tools to answer natural language queries:

* "Should I irrigate Field 5 today?"
* "What is the disease risk for my wheat crop?"
* "How will next week's weather affect my harvest schedule?"

The agent combines: sensor telemetry (Phase 7), weather records (Phase 5), soil profiles (Phase 4), crop data (Phase 3), and AI inference outputs to generate contextual recommendations.
