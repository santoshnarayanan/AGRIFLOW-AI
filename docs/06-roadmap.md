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

# Phase 8 – Irrigation Management Domain

Status: ✅ Complete

Objectives:

* IrrigationMethod and WaterSource enums added to `app/core/enums.py`
* IrrigationEvent ORM Model
* Alembic Migration `235a51cdf901`: `irrigation_events` table, `irrigation_method` enum (8 values), `water_source` enum (5 values), 3 indexes
* IrrigationEvent Pydantic Schemas (`IrrigationEventCreate`, `IrrigationEventUpdate`, `IrrigationEventResponse`)
* `IrrigationEventRepository` with `create`, `get_by_id`, `list_by_field` (ordered `started_at DESC`), `update`, `delete`, `exists`
* `IrrigationEventService` with field existence validation, future timestamp rejection, sparse PATCH cross-field ordering guard
* IrrigationEvent API Router (POST, GET list with pagination, GET single, PATCH, DELETE)
* `IrrigationEventServiceDep` dependency injection registration
* PostgreSQL ENUM lifecycle fix applied (`postgresql.ENUM` with `create_type=False`)
* Swagger documentation validated end-to-end

Delivered APIs:

* POST   /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/irrigation-events/{event_id}
* PATCH  /api/v1/irrigation-events/{event_id}
* DELETE /api/v1/irrigation-events/{event_id}

Architectural Decisions Established (ADR-008 series):

* `postgresql.ENUM` with `create_type=False` + explicit lifecycle is the authoritative enum migration pattern (ADR-008-01)
* IrrigationEvent is mutable — PATCH is permitted to allow operator correction (ADR-008-02)
* `started_at TIMESTAMPTZ` is the TimescaleDB partition key candidate (ADR-008-03)
* Sparse PATCH ordering guard: service merges payload with persisted record before `ended_at >= started_at` check (ADR-008-04)
* `IrrigationMethod` and `WaterSource` placed in `app/core/enums.py` for Digital Twin and AI reuse (ADR-008-05)

Outcome:

```text
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading   ← Phase 7 (append-only)
     └── IrrigationEvent ← Phase 8 (mutable operational events)
```

Business Capability:

* Irrigation event logging per field
* Delivery method classification (DRIP, SPRINKLER, FLOOD, FURROW, CENTER_PIVOT, SUBSURFACE, MANUAL, AUTOMATED)
* Water source tracking (GROUNDWATER, SURFACE_WATER, RAINWATER, MUNICIPAL, RECYCLED_WATER)
* Water volume and duration tracking for FAO-56 water balance
* Operator-correctable event log (mutable CRUD)
* AI feature pipeline inputs for irrigation optimization models
* TimescaleDB hypertable upgrade path established (zero code changes required)

---

# Phase 9 – Yield Domain

Status: ✅ Complete

Objectives:

* `YieldMeasurementMethod` enum added to `app/core/enums.py` (7 values: MANUAL_SCALE, COMBINE_MONITOR, YIELD_MAP, REMOTE_SENSING, CROP_CUT, LABORATORY_ANALYSIS, ESTIMATED)
* YieldRecord ORM Model — first grandchild domain (Farm → Field → Crop → YieldRecord)
* Alembic Migration `b7e2a9f4c8d3`: `yield_records` table, `yield_measurement_method` PostgreSQL enum, 4 indexes
* YieldRecord Pydantic Schemas (`YieldRecordCreate`, `YieldRecordUpdate`, `YieldRecordResponse`)
* `YieldRecordRepository` with `create`, `get_by_id`, `list_by_crop` (ordered `recorded_at DESC`), `list_by_field`, `update`, `delete`, `exists`
* `YieldRecordService` with crop existence validation, server-side `field_id` resolution, future timestamp rejection, `area_harvested_ha > 0` guard, `test_weight_kg_hl > 0` guard
* YieldRecord API Router (POST, GET list by crop, GET single, PATCH, DELETE)
* `YieldRecordServiceDep` dependency injection registration

Delivered APIs:

* POST   /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/yield-records/{yield_record_id}
* PATCH  /api/v1/yield-records/{yield_record_id}
* DELETE /api/v1/yield-records/{yield_record_id}

Architectural Decisions Established (ADR-009 series):

* `YieldRecord` anchors to `crop_id` as primary FK — yield is per crop cycle, not per field point-in-time (ADR-009-01)
* `field_id` is denormalized directly on `yield_records` to enable field-scoped queries without JOIN through `crops` (ADR-009-02)
* `recorded_at TIMESTAMPTZ NOT NULL` is the primary time key and TimescaleDB partition key candidate (ADR-009-03)
* `YieldRecord` is mutable — PATCH is permitted to allow operator correction (ADR-009-04)
* `crop_id` is immutable after creation — excluded from `YieldRecordUpdate` schema (ADR-009-05)
* `area_harvested_ha > 0` (not `>= 0`) when supplied — Pydantic allows 0; service tightens to > 0 (ADR-009-06)
* `YieldMeasurementMethod` placed in `app/core/enums.py` for Phase 12 Yield Prediction Engine reuse (ADR-009-07)
* `CropNotFoundError` imported from `app.services.crop` — not re-declared in yield service (ADR-009-08)
* `postgresql.ENUM` with `create_type=False` pattern applied (mandatory ADR-008-01 successor) (ADR-009-11)

Outcome:

```text
Farm
└── Field
     ├── Crop
     │    └── YieldRecord ← Phase 9 (grandchild domain, mutable)
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading     ← Phase 7 (append-only)
     └── IrrigationEvent   ← Phase 8 (mutable operational events)
```

Business Capability:

* Discrete yield observations per crop cycle with measurement method provenance
* Multiple measurement passes per harvest (plot sections, replication trials)
* Grain quality attributes alongside quantity (moisture content, test weight, grade)
* Field-lifetime yield history via denormalized `field_id` direct query path
* AI feature pipeline inputs for Phase 12 Yield Prediction Engine (primary training labels)
* Water-use efficiency calculations: IrrigationEvent water volume ÷ YieldRecord value
* TimescaleDB hypertable upgrade path established (zero code changes required)
* GaaS YieldAdvisor tool foundation (list-by-field query pattern)

AI Coverage Improvement (Post Phase 9):

| Use Case | After Phase 8 | After Phase 9 |
|---|---|---|
| Yield Prediction | 82% | 100% (granular time-series labels added) |
| Irrigation Optimization | 72% | 85% (water-use efficiency now computable) |

---

# Phase 10 – Disease Observation Domain

Status: ✅ Complete

Objectives:

* `DiseaseSeverity` enum added to `app/core/enums.py` (LOW, MEDIUM, HIGH, CRITICAL)
* `DiagnosisMethod` enum added to `app/core/enums.py` (VISUAL_INSPECTION, LAB_ANALYSIS, IMAGE_AI, AGRONOMIST, SENSOR_DETECTED)
* DiseaseObservation ORM Model — second grandchild domain (Farm → Field → Crop → DiseaseObservation)
* Alembic Migration `d3e7b2a9f1c4`: `disease_observations` table, `disease_severity` + `diagnosis_method` PostgreSQL enums, 6 indexes
* DiseaseObservation Pydantic Schemas (`CreateDiseaseObservationRequest`, `UpdateDiseaseObservationRequest`, `DiseaseObservationResponse`)
* `DiseaseObservationRepository` with `create`, `get_by_id`, `get_by_crop` (ordered `observed_at DESC`), `get_by_field`, `update`, `delete`
* `DiseaseObservationService` with crop existence validation, server-side `field_id` resolution, future `observed_at` rejection
* DiseaseObservation API Router (POST, GET list by crop, GET list by field, GET single, PATCH, DELETE)
* `DiseaseObservationServiceDep` dependency injection registration
* Swagger validation for `DiseaseSeverity` and `DiagnosisMethod` enum exposure

Delivered APIs:

* POST   /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/fields/{field_id}/disease-observations
* GET    /api/v1/disease-observations/{observation_id}
* PATCH  /api/v1/disease-observations/{observation_id}
* DELETE /api/v1/disease-observations/{observation_id}

Architectural Decisions Established (ADR-010 series):

* `DiseaseObservation` anchors to `crop_id` as primary FK — disease pressure is per crop cycle (ADR-010-01)
* `field_id` is denormalized directly on `disease_observations` for direct field-scoped queries without JOIN through `crops` (ADR-010-02)
* `observed_at TIMESTAMPTZ NOT NULL` is the primary time key and TimescaleDB partition key candidate (ADR-010-03)
* `DiseaseObservation` is mutable — PATCH is permitted to allow operator correction (ADR-010-04)
* `crop_id` is immutable after creation — excluded from `UpdateDiseaseObservationRequest` schema (ADR-010-05)
* `DiseaseSeverity` and `DiagnosisMethod` placed in `app/core/enums.py` for Disease Risk Scoring Engine and GaaS reuse (ADR-010-06)

Outcome:

```text
Farm
└── Field
     ├── Crop
     │    ├── YieldRecord
     │    └── DiseaseObservation
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading     (append-only)
     └── IrrigationEvent   (mutable operational events)
```

Business Value:

* Disease monitoring and crop health intelligence per crop cycle
* Field-scoped disease history via denormalized `field_id` direct query path
* Yield loss analysis foundation — disease pressure correlated with yield records
* Disease forecasting foundation — primary training labels for Phase 13 Disease Risk Scoring Engine
* GaaS PlantHealthAdvisor tool foundation
* TimescaleDB hypertable upgrade path established (zero code changes required)

AI Coverage Improvement (Post Phase 10):

| Use Case | After Phase 9 | After Phase 10 |
|---|---|---|
| Disease Prediction | 40% | 75% (observation labels + severity classification added) |

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
* Shared Enum Module (`app/core/enums.py`) — SensorType, IrrigationMethod, WaterSource, YieldMeasurementMethod, DiseaseSeverity, DiagnosisMethod
* Telemetry Immutability Pattern
* Compound Index Strategy (time-series domains)
* Operational Event Mutable Pattern (IrrigationEvent, YieldRecord, DiseaseObservation)
* IrrigationEvent Domain
* Grandchild Domain Pattern (YieldRecord, DiseaseObservation anchor on Crop)
* Denormalized FK Pattern (`field_id` on `yield_records` and `disease_observations` for direct field-scoped queries)
* YieldRecord Domain
* Disease Observation Domain

Near-Term (Phases 11–15):

* TimescaleDB (sensor_readings, irrigation_events, yield_records, disease_observations hypertable promotion)
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

# Current Domain Hierarchy (Post Phase 10)

```text
Farm
└── Field
     ├── Crop
     │    ├── YieldRecord
     │    └── DiseaseObservation
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading       (append-only)
     └── IrrigationEvent     (mutable operational events)
```

# Target Domain Hierarchy (Long-Term)

```text
Farm
└── Field
     ├── Crop
     │    ├── YieldRecord           ✅ implemented
     │    └── DiseaseObservation    ✅ implemented
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading
     ├── IrrigationEvent
     └── SatelliteObservation       🔜 Phase 11
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
✅ Phase 8  – Irrigation Management Domain
✅ Phase 9  – Yield Domain
✅ Phase 10 – Disease Observation Domain

🔜 Phase 11 – Satellite Observation Domain

AI Layer (Post Phase 11)
- Yield Prediction Engine
- Disease Prediction Engine
- Irrigation Recommendation Engine
- Farm Intelligence Platform

---

# Future Architecture Roadmap

## TimescaleDB

The `sensor_readings`, `irrigation_events`, `yield_records`, and `disease_observations` tables were designed for zero-friction TimescaleDB promotion. A single `create_hypertable(...)` call converts each to a time-partitioned hypertable. No application code changes are required.

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

The agent combines: sensor telemetry, weather records, soil profiles, crop data, yield records, disease observations, and AI inference outputs to generate contextual recommendations.
