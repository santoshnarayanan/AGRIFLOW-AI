# AGRIFLOW-AI Phase History

## Phase 1 – Foundation

Status: Completed

### Completed

* FastAPI Foundation
* PostgreSQL Integration
* Alembic Migration Framework
* Farm Domain Model
* Farm Table Creation
* Docker Foundation
* Health APIs
* Version API

### Database Changes

* Added farms table
* Established UUID-based primary key strategy
* Established audit field strategy
* Established migration framework

### Architecture Established

* FastAPI Application Structure
* SQLAlchemy ORM Foundation
* PostgreSQL Integration
* Alembic Migration Workflow
* Configuration Management
* Logging Foundation

### Lessons Learned

* Cursor approval workflow
* Alembic migration workflow
* Importance of incremental domain implementation
* Importance of migration-first database evolution

### Deferred

* Frontend integration
* Docker runtime validation
* Authentication
* Automated testing

---

## Phase 2 – Field Domain

Status: Completed

### Completed

* Field Domain Design
* Field ORM Model
* Farm ↔ Field Relationship
* Field Database Schema
* Alembic Migration for Fields Table
* Field Pydantic Schemas
* Base Repository Pattern
* Farm Repository
* Field Repository
* Field Service Layer
* Domain Exception Handling
* Field API Layer
* Dependency Injection Framework
* API Router Registration
* CRUD Endpoints for Fields

### Database Changes

* Added fields table
* Added farm_id foreign key relationship
* Added field geolocation support (latitude, longitude)
* Added field area tracking (area_hectares)
* Added soil classification support

### API Endpoints Added

* POST   /api/v1/farms/{farm_id}/fields
* GET    /api/v1/farms/{farm_id}/fields
* GET    /api/v1/fields/{field_id}
* PATCH  /api/v1/fields/{field_id}
* DELETE /api/v1/fields/{field_id}

### Business Rules Implemented

* Farm must exist before field creation
* Field names must be unique within a farm
* Field existence validation before update
* Field existence validation before delete

### Architecture Established

* Model Layer
* Schema Layer
* Repository Layer
* Service Layer
* API Layer
* Dependency Injection Layer

### Lessons Learned

* Service layer should contain business rules only
* Repository layer should contain database access only
* Transaction management should be handled through dependencies
* Domain exceptions should be translated at the API layer
* Incremental domain implementation reduces complexity

### Future Considerations

* Weather integration using field coordinates
* Satellite imagery integration
* Soil sensor integration
* GIS/PostGIS support
* Field boundary polygons
* Precision agriculture capabilities

### Deferred

* Frontend integration
* Automated API tests
* GIS polygon support
* Advanced pagination
* Field analytics and reporting

---

## Phase 3 – Crop Domain

Status: Completed

### Completed

* Crop ORM Model
* Crop Database Schema
* Crop Migration
* Crop Status Enum
* Crop Pydantic Schemas
* Crop Repository Layer
* Crop Service Layer
* Crop API Layer
* Dependency Injection Extension
* API Router Registration
* CRUD Endpoints for Crops

### Database Changes

* Added crops table
* Added field_id foreign key relationship
* Added crop lifecycle tracking
* Added crop status enum
* Added planting and harvest date tracking

### Domain Hierarchy Established

Farm
└── Field
     ├── Crop
     └── SoilProfile

### API Endpoints Added

* POST   /api/v1/fields/{field_id}/crops
* GET    /api/v1/fields/{field_id}/crops
* GET    /api/v1/crops/{crop_id}
* PATCH  /api/v1/crops/{crop_id}
* DELETE /api/v1/crops/{crop_id}

### Business Rules Implemented

* Field must exist before crop creation
* Crop existence validation before update
* Crop existence validation before delete
* Harvest date validation
* Crop lifecycle management foundation

### Architecture Evolution

Repository Layer:

* BaseRepository reused for CropRepository
* Crop-specific queries separated from generic CRUD

Dependency Injection:

* CropService dependency provider added
* Shared transaction scope across repositories
* Request-scoped session management expanded

API Layer:

* Service exception translation
* HTTP error mapping
* Schema-based request validation

### Lessons Learned

* Generic repositories reduce duplicated code
* Service layer should coordinate multiple repositories
* Dependency injection simplifies service construction
* PostgreSQL enum migrations require careful handling
* Domain validation belongs in services, not repositories
* Router layers should remain thin

### Notable Technical Challenges

Crop Status Enum Migration:

Issue:

* Duplicate PostgreSQL enum creation

Resolution:

* Removed redundant enum creation logic
* Allowed SQLAlchemy to manage enum lifecycle

Outcome:

* Successful migration execution
* Cleaner migration strategy for future enums

### Future Considerations

* Multi-cropping support
* Seasonal crop planning
* Crop rotation history
* Yield tracking
* Crop disease monitoring
* AI-driven crop recommendations

### Deferred

* Automated API tests
* Crop analytics dashboards
* Yield reporting
* Crop forecasting

---

## Phase 4 – Soil Intelligence Domain

Status: Completed

### Completed

* SoilProfile Domain Design
* SoilProfile ORM Model
* SoilProfile Database Schema
* SoilProfile Migration
* SoilType Enum
* SoilProfile Pydantic Schemas
* SoilProfile Repository Layer
* SoilProfile Service Layer
* SoilProfile API Layer
* Dependency Injection Integration
* API Router Registration
* CRUD Endpoints for Soil Profiles
* Integration & Validation Testing

### Database Changes

* Added soil_profiles table
* Added field_id foreign key relationship
* Added one-to-one Field ↔ SoilProfile relationship
* Added soil nutrient tracking
* Added soil pH tracking
* Added organic matter tracking
* Added soil profile notes support

### Domain Hierarchy Established

Farm
└── Field
├── Crop
└── SoilProfile

### API Endpoints Added

* POST   /api/v1/fields/{field_id}/soil-profile
* GET    /api/v1/fields/{field_id}/soil-profile
* PATCH  /api/v1/soil-profiles/{soil_profile_id}
* DELETE /api/v1/soil-profiles/{soil_profile_id}

### Business Rules Implemented

* Field must exist before SoilProfile creation
* Only one SoilProfile allowed per Field
* SoilProfile existence validation before update
* SoilProfile existence validation before delete
* Soil nutrient validation
* Soil pH validation foundation

### Architecture Evolution

Repository Layer:

* SoilProfileRepository added
* BaseRepository reused for SoilProfileRepository
* Field-specific SoilProfile queries implemented

Dependency Injection:

* SoilProfileService dependency provider added
* Shared transaction scope across repositories
* Request-scoped session management extended

API Layer:

* SoilProfile service exception translation
* HTTP error mapping
* Schema-based request validation
* SoilProfile endpoint registration

### Lessons Learned

* One-to-one domain relationships require both service validation and database constraints
* Schema validation should remain separate from business rule validation
* Repository reuse significantly reduces implementation effort
* Vertical domain implementation (Model → Schema → Repository → Service → API) improves consistency
* Integration testing should be performed before domain closure

### Notable Technical Challenges

Docker Port Conflicts

Issue:

* PostgreSQL host port conflicts
* FastAPI host port conflicts across multiple local projects

Resolution:

* Reassigned PostgreSQL container port mappings
* Reassigned backend service port mappings
* Validated Docker networking and container health

Outcome:

* Stable local development environment
* Successful end-to-end integration validation

PostgreSQL 18 Container Compatibility

Issue:

* PostgreSQL 18 container startup conflict with existing volume layout

Resolution:

* Environment cleanup and container recreation
* Successful database initialization and health verification

Outcome:

* Stable PostgreSQL runtime configuration
* Successful migration execution

### Future Considerations

* Soil sampling history
* Soil trend analysis
* Fertility scoring
* Nutrient recommendation engine
* Precision agriculture analytics
* Soil-weather correlation analysis

### Deferred

* Automated API tests
* Soil analytics dashboards
* Soil health scoring engine
* Nutrient recommendation engine
* Historical soil trend analysis


---

## Phase 5 – Weather Intelligence Domain

Status: Completed

### Completed

* WeatherRecord Domain Design
* WeatherRecord ORM Model
* WeatherRecord Database Schema
* WeatherRecord Migration
* WeatherRecord Pydantic Schemas
* WeatherRecord Repository Layer
* WeatherRecord Service Layer
* WeatherRecord API Layer
* Dependency Injection Integration
* API Router Registration
* CRUD Endpoints for Weather Records
* Integration & Validation Testing

### Database Changes

* Added weather_records table
* Added field_id foreign key relationship
* Added recorded_at timestamp tracking
* Added temperature tracking
* Added humidity tracking
* Added rainfall tracking
* Added wind speed tracking
* Added weather data source support

### Domain Hierarchy Established

Farm
└── Field
├── Crop
├── SoilProfile
└── WeatherRecord

### API Endpoints Added

* POST   /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/weather-records/{weather_record_id}
* PATCH  /api/v1/weather-records/{weather_record_id}
* DELETE /api/v1/weather-records/{weather_record_id}

### Business Rules Implemented

* Field must exist before WeatherRecord creation
* WeatherRecord existence validation before update
* WeatherRecord existence validation before delete
* Future timestamp validation
* Humidity validation
* Rainfall validation
* Wind speed validation

### Architecture Evolution

Repository Layer:

* WeatherRecordRepository added
* BaseRepository reused for WeatherRecordRepository
* Field-specific WeatherRecord queries implemented

Dependency Injection:

* WeatherRecordService dependency provider added
* Shared transaction scope across repositories
* Request-scoped session management extended

API Layer:

* WeatherRecord service exception translation
* HTTP error mapping
* Schema-based request validation
* WeatherRecord endpoint registration

### Lessons Learned

* Time-series agricultural data requires different modeling than master data
* Historical observations should be immutable once recorded
* Vertical domain implementation improves consistency and maintainability
* Integration testing should validate complete API → Service → Repository → Database flows

### Notable Technical Challenges

Migration Execution Gap

Issue:

* Weather migration file existed but was not applied to the database

Resolution:

* Verified Alembic migration history
* Applied migration to head revision
* Validated weather_records table creation

Outcome:

* Successful schema evolution
* Weather domain fully operational

PostgreSQL Container Version Compatibility

Issue:

* PostgreSQL 18 container incompatibility with existing volume layout

Resolution:

* Reverted to PostgreSQL 17 container image
* Recreated runtime environment
* Validated database health and startup

Outcome:

* Stable development environment
* Successful WeatherRecord integration validation

### Future Considerations

* Weather forecast ingestion
* Climate trend analysis
* Drought monitoring
* Weather anomaly detection
* Weather-crop correlation analysis
* Predictive weather intelligence

### Deferred

* Automated API tests
* Weather analytics dashboards
* Forecast provider integrations
* Climate risk scoring


## Current Platform Status

### Domain Hierarchy

Farm
└── Field
    ├── Crop
    ├── SoilProfile
    └── WeatherRecord

### Current Database Tables

* alembic_version
* farms
* fields
* crops
* soil_profiles
* weather_records

### Current Architecture

Model
↓
Schema
↓
Repository
↓
Service
↓
API

---
### Current API Coverage

Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

Version

* GET /api/v1/version

Fields

* POST   /api/v1/farms/{farm_id}/fields
* GET    /api/v1/farms/{farm_id}/fields
* GET    /api/v1/fields/{field_id}
* PATCH  /api/v1/fields/{field_id}
* DELETE /api/v1/fields/{field_id}

Crops

* POST   /api/v1/fields/{field_id}/crops
* GET    /api/v1/fields/{field_id}/crops
* GET    /api/v1/crops/{crop_id}
* PATCH  /api/v1/crops/{crop_id}
* DELETE /api/v1/crops/{crop_id}

Soil Profiles

* POST   /api/v1/fields/{field_id}/soil-profile
* GET    /api/v1/fields/{field_id}/soil-profile
* PATCH  /api/v1/soil-profiles/{soil_profile_id}
* DELETE /api/v1/soil-profiles/{soil_profile_id}

Weather Records

* POST   /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/weather-records/{weather_record_id}
* PATCH  /api/v1/weather-records/{weather_record_id}
* DELETE /api/v1/weather-records/{weather_record_id}

---

## Next Planned Evolution

Phase 6 – Sensor Reading Domain

Future target hierarchy:

Farm
└── Field
├── Crop
├── SoilProfile
├── Weather Records
├── Sensor Readings
└── Future Domains

---

## Phase 6 – AI Readiness Foundation

Status: Completed

### Completed

* AI Data Readiness Assessment
* P1 AI Schema Enhancement
* AI Attribute Expansion Across Core Domains
* Validation & Stabilization Pass
* Router Exception Handling Fixes
* Backward Compatibility Validation

### New AI Attributes

Field
* elevation_m

Crop
* actual_yield_tons_ha
* expected_yield_tons_ha
* seeding_rate_kg_ha
* growth_stage

SoilProfile
* soil_depth_cm
* cation_exchange_capacity_meq

WeatherRecord
* solar_radiation_wm2
* temperature_min_c
* temperature_max_c

### Outcome

Phase 6 formally closed after successful validation and stabilization.

### Architecture Decisions

* All P1 AI attributes are nullable `ADD COLUMN` operations — no server defaults, no backfill required.
* PostgreSQL 11+ handles nullable column additions as metadata-only operations with no table rewrite.
* Business validation for new attributes was added to existing service methods, not new services.
* AI inference write-back fields (e.g. `disease_risk_score`) are reserved for future AI inference services, not the current API layer.

### Lessons Learned

* A formal data readiness assessment before any AI work eliminates speculative schema design and focuses engineering on the highest-value attributes first.
* Additive schema changes (nullable `ADD COLUMN`) are far safer than modifying existing columns in production systems with existing consumers.
* The gap between 18% yield prediction coverage and 82% after just 10 additional attributes demonstrates the leverage of careful attribute selection.
* Router exception handling must be explicitly validated across all domains after any schema change that could alter exception propagation paths.

### References

* Full AI attribute gap analysis: `docs/AI_DATA_READINESS_ASSESSMENT.md`
* Validation report across all layers: `docs/PHASE6_STEP3_VALIDATION_REPORT.md`

---

## Phase 7 – SensorReading Domain

Status: Completed

### Completed

* SensorType shared enum module (`app/core/enums.py`)
* SensorReading ORM Model (`app/db/models/sensor_reading.py`)
* Farm ↔ Field ↔ SensorReading relationship with `cascade="all, delete-orphan"`
* Alembic migration 006: `sensor_readings` table, `sensor_type` PostgreSQL enum, 5 indexes
* SensorReading Pydantic schemas — `SensorReadingCreate` and `SensorReadingResponse` (no Update schema)
* SensorReadingRepository with `create`, `get_by_id`, `list_by_field`, `delete`, `exists`
* SensorReadingService with field existence validation, timezone-aware timestamp validation, future timestamp rejection
* SensorReading API Router with POST, GET (list), GET (single), DELETE endpoints
* `SensorReadingServiceDep` registered in `app/api/deps.py`
* Router registered in `app/api/router.py`

### Domain Hierarchy Established

```
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord
     └── SensorReading   ← Phase 7
```

### Database Changes

* Added `sensor_type` PostgreSQL ENUM type with 11 values:
  `SOIL_MOISTURE`, `SOIL_TEMPERATURE`, `AIR_TEMPERATURE`, `AIR_HUMIDITY`,
  `LIGHT_INTENSITY`, `LEAF_WETNESS`, `ELECTRICAL_CONDUCTIVITY`,
  `SOIL_SALINITY`, `WATER_LEVEL`, `BATTERY_STATUS`, `DEVICE_HEALTH`

* Added `sensor_readings` table with columns:

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `field_id` | `UUID` (FK) | References `fields.id` ON DELETE CASCADE |
| `sensor_type` | `sensor_type` ENUM | Discriminator for physical quantity |
| `sensor_value` | `DOUBLE PRECISION` | IEEE 754 64-bit for sensor ADC precision |
| `unit` | `VARCHAR(50)` | SI or industry-standard unit label |
| `recorded_at` | `TIMESTAMPTZ NOT NULL` | Timezone-aware observation timestamp |
| `notes` | `TEXT` | Nullable free-text annotation |
| `created_at` | `TIMESTAMPTZ` | Audit — row creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | Audit — row last-updated timestamp |

* Added 5 indexes — 3 individual, 2 compound:

| Index | Columns | Purpose |
|---|---|---|
| `ix_sensor_readings_field_id` | `field_id` | Field-level reading lookups |
| `ix_sensor_readings_sensor_type` | `sensor_type` | Cross-field type queries |
| `ix_sensor_readings_recorded_at` | `recorded_at` | Time-range queries |
| `ix_sensor_readings_field_id_recorded_at` | `(field_id, recorded_at)` | Primary telemetry access pattern |
| `ix_sensor_readings_sensor_type_recorded_at` | `(sensor_type, recorded_at)` | Type-scoped time queries |

* `ON DELETE CASCADE` on `field_id` FK — field deletion atomically removes all its sensor readings.

### API Endpoints Added

```http
POST   /api/v1/fields/{field_id}/sensor-readings     201 Created
GET    /api/v1/fields/{field_id}/sensor-readings     200 OK  (recorded_at DESC)
GET    /api/v1/sensor-readings/{sensor_reading_id}   200 OK
DELETE /api/v1/sensor-readings/{sensor_reading_id}  204 No Content
```

No `PATCH` endpoint. No `PUT` endpoint. SensorReading is immutable by design.

### Business Rules Implemented

* Field must exist before sensor reading creation (raises `FieldNotFoundError` → 404)
* `recorded_at` must be timezone-aware; naive datetimes are rejected (raises `InvalidSensorTimestampError` → 422)
* `recorded_at` must not be in the future; future timestamps are rejected (raises `InvalidSensorTimestampError` → 422)
* No sensor value range validation — reserved for future ingestion and SensorDevice domains
* Telemetry list responses ordered by `recorded_at DESC` (most recent first)
* Administrative deletion supported; mutation forbidden

### Architecture Evolution

**Shared Enum Module established:**
`app/core/enums.py` was created as the first file in the shared core layer. `SensorType` was placed here rather than in the ORM model file because it will be reused by future domains: `SensorDevice`, `SensorAlert`, Digital Twin topology, and the AI Recommendation Engine. This is now the standard location for cross-domain enumerations.

**Telemetry Immutability Pattern:**
`SensorReading` is the first domain in AGRIFLOW-AI with an explicit immutability contract. No `SensorReadingUpdate` schema exists. No `update_sensor_reading()` service method exists. No PATCH or PUT endpoint exists. Corrections to historical readings are expressed as new readings.

**Compound Index Strategy:**
Phase 7 introduced the first compound indexes in the project (`field_id, recorded_at`) and (`sensor_type, recorded_at`). These cover the two primary telemetry access patterns efficiently.

**DOUBLE PRECISION for Sensor Values:**
`DOUBLE PRECISION` (IEEE 754 64-bit) was selected over `NUMERIC(p,s)` because sensor ADC outputs and physical measurements require floating-point semantics. `NUMERIC` with fixed scale would silently truncate high-resolution readings from precision sensors.

**Service Extension Point Architecture:**
`SensorReadingService.create_sensor_reading()` contains a documented extension point comment block marking the future boundary for: Redpanda event publishing, Digital Twin state updates, CQRS projections, and Temporal workflow triggers. No integration is implemented; the boundary is reserved.

### Repository Decisions

| ADR | Decision |
|---|---|
| ADR-007-17 | Repository owns persistence, not intelligence |
| ADR-007-18 | Telemetry queries return latest readings first (`ORDER BY recorded_at DESC`) |
| ADR-007-19 | SensorReading supports DELETE but not UPDATE |
| ADR-007-20 | Repository is event-agnostic — no Redpanda publishing from repository layer |
| ADR-007-21 | Phase 7 returns all readings for a field without pagination (deferred) |

### Service Decisions

| ADR | Decision |
|---|---|
| ADR-007-22 | Service layer owns telemetry intelligence (timestamp validation) |
| ADR-007-23 | Field must exist before telemetry creation |
| ADR-007-24 | Future timestamps are rejected |
| ADR-007-25 | Timezone-naive datetimes are rejected |
| ADR-007-26 | Service layer is the future event publishing boundary |
| ADR-007-27 | Historical telemetry cannot be mutated |
| ADR-007-28 | Telemetry supports administrative deletion but not modification |

### API Decisions

| ADR | Decision |
|---|---|
| ADR-007-29 | SensorReading API: POST + GET + DELETE only; no PATCH, no PUT |
| ADR-007-30 | Telemetry responses return newest readings first |
| ADR-007-31 | Administrative deletion returns 204 No Content |
| ADR-007-32 | SensorReading is immutable; no update verb exposed |
| ADR-007-33 | Domain exceptions translated to HTTP in routers; service layer raises typed exceptions |

### Notable Technical Challenges

**SensorType Enum Relocation:**

The `SensorType` enum was initially defined in `app/db/models/sensor_reading.py` (following the `CropStatus` and `SoilType` precedent). A dedicated refactor step relocated it to `app/core/enums.py` because future domains (SensorDevice, SensorAlert) would need to import it — and importing from an ORM model creates problematic circular import chains. The refactor was purely structural; no schema or behavior changed.

**Explicit Alembic Enum Lifecycle Management:**

Unlike `CropStatus` (where SQLAlchemy managed the enum creation implicitly), Phase 7 used `op.execute(sa.text("CREATE TYPE sensor_type AS ENUM (...)"))` explicitly in the upgrade function and `op.execute(sa.text("DROP TYPE sensor_type"))` in the downgrade function. This pattern gives full lifecycle control and avoids the implicit enum creation race conditions encountered in Phase 3.

**DOUBLE PRECISION vs NUMERIC Decision:**

All prior numeric columns in AGRIFLOW-AI use `NUMERIC(p,s)` with fixed precision (e.g. `NUMERIC(5,2)` for temperature). The `sensor_value` column is the first to use `DOUBLE PRECISION`. This decision required explicit architectural justification: sensor ADC outputs operate in floating-point space and fixed-scale types would introduce silent truncation for high-resolution transducers.

### Lessons Learned

* Shared enums must live in a neutral module (`app/core/enums.py`) rather than ORM model files as soon as they are expected to be used across more than one domain.
* Explicit enum DDL in Alembic migrations provides full lifecycle control and avoids implicit creation issues discovered in earlier phases.
* The two-phase timestamp validation order matters: timezone-awareness must be checked before future-timestamp comparison, because a naive datetime cannot be safely compared to a UTC-aware datetime.
* `DOUBLE PRECISION` vs `NUMERIC` is a domain-specific choice. Both are correct in their contexts; the selection must be documented with physical rationale to prevent future refactoring based on incorrect assumptions.
* Documenting the service extension point as a comment block (not TODO) creates a stable contract boundary that survives future code reviewers and AI-assisted development.

### Future Considerations

* **TimescaleDB:** `sensor_readings` was designed to be TimescaleDB-compatible. `recorded_at TIMESTAMPTZ NOT NULL` is the partition key. A `create_hypertable('sensor_readings', 'recorded_at')` call is the only schema operation needed; no application code changes are required.
* **Cassandra:** High-scale deployments (millions of readings/day) will migrate to Cassandra with `(field_id, recorded_at)` as the partition/clustering key — matching the compound index already established.
* **CQRS:** The write path (`create` / `delete`) and read path (`list_by_field` / `get_by_id`) will be split into separate repository implementations backed by different storage engines.
* **Redpanda:** A `SensorReadingCreated` domain event will be published at the service layer extension point, enabling downstream consumers (Digital Twin, AI pipeline, alert engine) to react without coupling to the write path.
* **Temporal Workflows:** Alert evaluation workflows (e.g. sustained low soil moisture → irrigation recommendation) will be triggered from the service layer extension point.
* **Digital Twin:** Each new sensor reading will update the field-level Digital Twin state, providing a continuously current virtual model of every field.
* **Pagination:** `list_by_field` returns all readings in Phase 7. Pagination (`LIMIT` / `OFFSET` or cursor-based) will be added in a future phase when response sizes require it.

---

### Current Platform Status (Post Phase 7)

#### Domain Hierarchy

```text
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord
     └── SensorReading
```

#### Current Database Tables

* alembic_version
* farms
* fields
* crops
* soil_profiles
* weather_records
* sensor_readings

#### Current Architecture

```
Model → Schema → Repository → Service → API
```

#### Current API Coverage

Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

Version

* GET /api/v1/version

Fields, Crops, Soil Profiles, Weather Records

* (unchanged — see Phase 2–5 entries)

Sensor Readings

* POST   /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/sensor-readings/{sensor_reading_id}
* DELETE /api/v1/sensor-readings/{sensor_reading_id}

---

## Phase 8 – Irrigation Management Domain

Status: ✅ Complete

### What Was Built

**Core domain components:**

* `IrrigationMethod` and `WaterSource` enums added to `app/core/enums.py`
* `IrrigationEvent` ORM model (`backend/app/db/models/irrigation_event.py`)
* Alembic migration `235a51cdf901_create_irrigation_events_table`
* `IrrigationEventCreate`, `IrrigationEventUpdate`, `IrrigationEventResponse` Pydantic schemas
* `IrrigationEventRepository` with `create`, `get_by_id`, `list_by_field` (paginated, `started_at DESC`), `update`, `delete`, `exists`
* `IrrigationEventService` with field existence validation, service-level timestamp validation, sparse PATCH ordering guard
* `IrrigationEventNotFoundError` and `InvalidIrrigationTimestampError` domain exception types
* IrrigationEvent API router with 5 endpoints (POST, GET list, GET single, PATCH, DELETE)
* `get_irrigation_event_service()` factory and `IrrigationEventServiceDep` alias in `app/api/deps.py`
* Router registered in `app/api/router.py`
* Swagger documentation validated end-to-end

**Database schema:**

Table: `irrigation_events`  
Enums: `irrigation_method` (8 values), `water_source` (5 values)  
Indexes: `ix_irrigation_events_field_id`, `ix_irrigation_events_started_at`, `ix_irrigation_events_field_id_started_at` (compound)

### Architecture Decisions

| ADR | Decision |
|---|---|
| ADR-008-01 | Use `postgresql.ENUM` with `create_type=False` + explicit `.create()` / `.drop()` calls for all future ENUM types |
| ADR-008-02 | IrrigationEvent is mutable — PATCH is permitted to allow operator correction of logged events |
| ADR-008-03 | `started_at TIMESTAMPTZ NOT NULL` is the TimescaleDB hypertable partition key candidate |
| ADR-008-04 | Sparse PATCH ordering guard: service merges payload with persisted `started_at` before `ended_at >= started_at` check |
| ADR-008-05 | `IrrigationMethod` and `WaterSource` placed in `app/core/enums.py` for future Digital Twin and AI model reuse |

### Migration Issue Encountered — PostgreSQL ENUM Lifecycle Bug

**Problem:** `DuplicateObjectError: type "irrigation_method" already exists` on fresh database installations.

**Root cause:** In SQLAlchemy 2.0.x, `sa.Enum._copy()` — invoked internally by `op.create_table()` when it clones the table definition — does not forward `create_type=False`. On databases where the ENUM type had already been created by the explicit `CREATE TYPE` call in the migration, `op.create_table()` attempted to create it again, resulting in `DuplicateObjectError`.

**Resolution:** Replace `sa.Enum(...)` column definitions with `postgresql.ENUM(name=..., create_type=False)` from `sqlalchemy.dialects.postgresql`. This prevents `op.create_table()` from emitting any `CREATE TYPE` DDL. The enum type lifecycle is owned entirely by:
- `upgrade()`: `irrigation_method_enum.create(op.get_bind(), checkfirst=True)`
- `downgrade()`: `irrigation_method_enum.drop(op.get_bind(), checkfirst=False)`

This is now the authoritative pattern for all future ENUM migrations in AGRIFLOW-AI.

### Enum Lifecycle Fix

Phase 8 is the first migration to use the `postgresql.ENUM` with `create_type=False` pattern. This supersedes the `sa.Enum` pattern used in migrations `003` and `13aabbe35d51`. Those prior migrations work correctly on databases created sequentially but may exhibit `DuplicateObjectError` in certain edge cases on fresh installations when running `alembic upgrade head`. Phase 8 establishes the correct pattern to prevent this in all future phases.

### Lessons Learned

* **`postgresql.ENUM` vs `sa.Enum` for Alembic migrations**: `sa.Enum._copy()` in SQLAlchemy 2.0.x does not forward `create_type=False`. Always use `postgresql.ENUM` with explicit `.create()` / `.drop()` calls for any new PostgreSQL ENUM types.
* **Mutable vs Immutable events**: Not all event domains should be immutable. IoT telemetry (`SensorReading`) is immutable because it records physical sensor state — corrections are new readings. Operational management events (`IrrigationEvent`) are mutable because operators legitimately correct records after logging them.
* **Sparse PATCH cross-field validation**: When only one timestamp is provided in a PATCH payload, the service must retrieve the existing record and merge values before performing cross-field ordering checks. Pydantic alone cannot guard against `ended_at < started_at` when `started_at` is omitted from the update payload.
* **Shared enum module growth**: `app/core/enums.py` now holds three shared enum types (`SensorType`, `IrrigationMethod`, `WaterSource`). This confirms the pattern is working correctly and establishes the module as the neutral import point for all future cross-domain enumerations.
* **TimescaleDB readiness is bidirectional**: Both `sensor_readings.recorded_at` and `irrigation_events.started_at` are hypertable-ready. Future TimescaleDB activation requires no application code changes for either table.

### Swagger Validation

All Phase 8 endpoints were validated through the Swagger UI (`/docs`) after full stack startup:
* `POST /api/v1/fields/{field_id}/irrigation-events` — verified 201 Created
* `GET /api/v1/fields/{field_id}/irrigation-events` — verified 200 OK with pagination
* `GET /api/v1/irrigation-events/{event_id}` — verified 200 OK and 404
* `PATCH /api/v1/irrigation-events/{event_id}` — verified 200 OK, 404, and 400 for invalid timestamps
* `DELETE /api/v1/irrigation-events/{event_id}` — verified 204 No Content

### Current Platform Status (Post Phase 8)

#### Domain Hierarchy

```text
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading   ← Phase 7 (append-only telemetry)
     └── IrrigationEvent ← Phase 8 (mutable operational events)
```

#### Current Database Tables

* alembic_version
* farms
* fields
* crops
* soil_profiles
* weather_records
* sensor_readings
* irrigation_events

#### Current Migration Head

`235a51cdf901_create_irrigation_events_table`

#### Current API Coverage

Fields, Crops, Soil Profiles, Weather Records, Sensor Readings: (unchanged — see Phase 2–7 entries)

Irrigation Events (Phase 8):

* POST   /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/irrigation-events/{event_id}
* PATCH  /api/v1/irrigation-events/{event_id}
* DELETE /api/v1/irrigation-events/{event_id}

---

### Next Planned Evolution

Phase 10 – Disease Observation Domain

---

## Phase 9 – Yield Domain

### What Was Built

Phase 9 introduced `YieldRecord` — the first grandchild domain in AGRIFLOW-AI — establishing a dedicated time-series observation log for crop yield measurements.

**New Files (7):**

| File | Purpose |
|---|---|
| `backend/app/db/models/yield_record.py` | ORM model |
| `backend/app/schemas/yield_record.py` | Pydantic schemas (Base, Create, Update, Response) |
| `backend/app/db/repositories/yield_record.py` | Repository |
| `backend/app/services/yield_record.py` | Service + domain exceptions + helpers |
| `backend/app/api/yield_records/__init__.py` | Package marker |
| `backend/app/api/yield_records/router.py` | API router (5 endpoints) |
| `backend/app/db/migrations/versions/b7e2a9f4c8d3_create_yield_records_table.py` | Alembic migration |

**Modified Files (7):**

| File | Change |
|---|---|
| `backend/app/core/enums.py` | Added `YieldMeasurementMethod` (7 values) |
| `backend/app/db/models/crop.py` | Added `yield_records` relationship |
| `backend/app/db/models/field.py` | Added `yield_records` relationship |
| `backend/app/db/repositories/__init__.py` | Exported `YieldRecordRepository` |
| `backend/app/services/__init__.py` | Exported `YieldRecordService`, `YieldRecordNotFoundError`, `InvalidYieldRecordError` |
| `backend/app/api/deps.py` | Added `get_yield_record_service` factory + `YieldRecordServiceDep` |
| `backend/app/api/router.py` | Included `yield_records_router` |

### Architecture Decisions

**ADR-009-01 — Crop-Anchored FK**

`YieldRecord` anchors to `crop_id` as its primary FK, not `field_id` alone. Yield is a per-crop-cycle measurement. This establishes the first grandchild domain in AGRIFLOW-AI:

```
Farm → Field → Crop → YieldRecord
```

**ADR-009-02 — Denormalized `field_id`**

`field_id` is stored directly on `yield_records` to enable `GET /fields/{field_id}/yield-records`-style queries without a JOIN through `crops`. Both FKs are `NOT NULL` with `ON DELETE CASCADE`. The service resolves `field_id` from the crop record at creation time, guaranteeing consistency.

**ADR-009-03 — `recorded_at TIMESTAMPTZ` as Primary Time Key**

`recorded_at` is the TimescaleDB partition key candidate. Compound index `(crop_id, recorded_at)` is the primary AI feature pipeline access pattern for Phase 12 Yield Prediction Engine.

**ADR-009-04 — Mutable Domain**

`YieldRecord` is mutable (PATCH is permitted). Operators legitimately correct measurement values after logging (recalibrated moisture, corrected area). Contrasts with `SensorReading` (append-only).

**ADR-009-05 — Immutable `crop_id`**

`crop_id` cannot be changed after creation. Changing the crop association of a yield measurement is not a valid correction; the record should be deleted and re-created. `YieldRecordUpdate` schema excludes `crop_id`.

**ADR-009-06 — `area_harvested_ha > 0` Service Guard**

Pydantic schema allows `area_harvested_ha >= 0` (`ge=0`). The service layer tightens this to `> 0`: a zero-area harvest observation is agronomically invalid. Same reasoning applies to `test_weight_kg_hl`.

**ADR-009-07 — `YieldMeasurementMethod` in `app/core/enums.py`**

The new `YieldMeasurementMethod` enum (7 values: MANUAL_SCALE, COMBINE_MONITOR, YIELD_MAP, REMOTE_SENSING, CROP_CUT, LABORATORY_ANALYSIS, ESTIMATED) is placed in the shared `app/core/enums.py` module for reuse by the Phase 12 Yield Prediction Engine, GaaS YieldAdvisor, and Digital Twin field productivity state.

**ADR-009-08 — Shared `CropNotFoundError`**

`CropNotFoundError` is imported from `app.services.crop` rather than re-declared in the yield service. Follows the `FieldNotFoundError` reuse pattern established in `IrrigationEventService`.

**ADR-009-11 — PostgreSQL ENUM Lifecycle**

`postgresql.ENUM` with `create_type=False` + explicit `.create(checkfirst=True)` / `.drop(checkfirst=False)` is applied — mandatory ADR-008-01 pattern for all new ENUM types.

### Service Layer Validation Strategy

Two-layer validation matching the established project pattern:

| Layer | Guard |
|---|---|
| Pydantic schema | `recorded_at` timezone awareness, `yield_value_tons_ha >= 0`, `moisture_content_percent` in [0, 100], `area/test_weight >= 0`, `quality_grade max_length=50` |
| Service layer | `recorded_at` not in future (UTC comparison), `area_harvested_ha > 0` when supplied, `test_weight_kg_hl > 0` when supplied, crop exists check |

Three independently-testable module-level helper functions: `_validate_not_future`, `_validate_area`, `_validate_test_weight`.

### Index Strategy

Four indexes established in migration `b7e2a9f4c8d3`:

| Index | Columns | Purpose |
|---|---|---|
| `ix_yield_records_crop_id` | `(crop_id)` | All records for a crop cycle |
| `ix_yield_records_field_id` | `(field_id)` | All records for a field (direct path) |
| `ix_yield_records_recorded_at` | `(recorded_at)` | Time-range queries |
| `ix_yield_records_crop_id_recorded_at` | `(crop_id, recorded_at)` | Compound — primary AI feature pipeline path |

### Delivered APIs

```
POST   /api/v1/crops/{crop_id}/yield-records   — 201 Created
GET    /api/v1/crops/{crop_id}/yield-records   — 200 OK (paginated, recorded_at DESC)
GET    /api/v1/yield-records/{id}              — 200 OK
PATCH  /api/v1/yield-records/{id}             — 200 OK
DELETE /api/v1/yield-records/{id}             — 204 No Content
```

### Current Platform Status (Post Phase 9)

#### Domain Hierarchy

```text
Farm
└── Field
     ├── Crop
     │    └── YieldRecord  ← Phase 9 (grandchild, mutable)
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading    ← Phase 7 (append-only telemetry)
     └── IrrigationEvent  ← Phase 8 (mutable operational events)
```

#### Current Database Tables

* alembic_version
* farms
* fields
* crops
* soil_profiles
* weather_records
* sensor_readings
* irrigation_events
* yield_records

#### Current Migration Head

`b7e2a9f4c8d3_create_yield_records_table`

#### Current API Coverage

Fields, Crops, Soil Profiles, Weather Records, Sensor Readings, Irrigation Events: (unchanged — see Phase 2–8 entries)

Yield Records (Phase 9):

* POST   /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/yield-records/{yield_record_id}
* PATCH  /api/v1/yield-records/{yield_record_id}
* DELETE /api/v1/yield-records/{yield_record_id}

---

### Next Planned Evolution

Phase 10 – Disease Observation Domain

---

## Phase 10 – Disease Observation Domain

Status: ✅ Complete

### Completed

* `DiseaseSeverity` enum added to `app/core/enums.py` (LOW, MEDIUM, HIGH, CRITICAL)
* `DiagnosisMethod` enum added to `app/core/enums.py` (VISUAL_INSPECTION, LAB_ANALYSIS, IMAGE_AI, AGRONOMIST, SENSOR_DETECTED)
* DiseaseObservation ORM Model (`backend/app/db/models/disease_observation.py`)
* Alembic migration `d3e7b2a9f1c4_create_disease_observations_table`
* DiseaseObservation Pydantic Schemas (`CreateDiseaseObservationRequest`, `UpdateDiseaseObservationRequest`, `DiseaseObservationResponse`)
* `DiseaseObservationRepository` with `create`, `get_by_id`, `get_by_crop`, `get_by_field`, `update`, `delete`
* `DiseaseObservationService` with crop existence validation, server-side `field_id` resolution, future `observed_at` rejection
* `DiseaseObservationNotFoundError` and `InvalidDiseaseObservationError` domain exception types
* DiseaseObservation API router with 6 endpoints (POST, GET list by crop, GET list by field, GET single, PATCH, DELETE)
* `get_disease_observation_service()` factory and `DiseaseObservationServiceDep` alias in `app/api/deps.py`
* Router registered in `app/api/router.py`
* Swagger validation for `DiseaseSeverity` and `DiagnosisMethod` enum exposure

### Database Changes

* Added `disease_severity` PostgreSQL ENUM type (LOW, MEDIUM, HIGH, CRITICAL)
* Added `diagnosis_method` PostgreSQL ENUM type (VISUAL_INSPECTION, LAB_ANALYSIS, IMAGE_AI, AGRONOMIST, SENSOR_DETECTED)
* Added `disease_observations` table with columns:

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID` | Primary key |
| `crop_id` | `UUID` (FK) | References `crops.id` ON DELETE CASCADE |
| `field_id` | `UUID` (FK) | Denormalized; references `fields.id` ON DELETE CASCADE |
| `observed_at` | `TIMESTAMPTZ NOT NULL` | Primary time key |
| `disease_name` | `VARCHAR(255)` | Free-text disease identifier |
| `severity` | `disease_severity` ENUM | Severity classification |
| `affected_area_percent` | `NUMERIC(5,2)` | Nullable; percentage affected [0, 100] |
| `diagnosis_method` | `diagnosis_method` ENUM | Identification method |
| `treatment_applied` | `TEXT` | Nullable treatment notes |
| `notes` | `TEXT` | Nullable operator annotations |
| `created_at` | `TIMESTAMPTZ` | Audit timestamp |
| `updated_at` | `TIMESTAMPTZ` | Audit timestamp |

* Added 6 indexes — 5 individual, 1 compound:

| Index | Columns | Purpose |
|---|---|---|
| `ix_disease_observations_crop_id` | `crop_id` | All observations for a crop cycle |
| `ix_disease_observations_field_id` | `field_id` | All observations for a field (direct path) |
| `ix_disease_observations_observed_at` | `observed_at` | Time-range queries |
| `ix_disease_observations_disease_name` | `disease_name` | Filter by disease name |
| `ix_disease_observations_severity` | `severity` | Filter by severity |
| `ix_disease_observations_crop_id_observed_at` | `(crop_id, observed_at)` | Primary AI feature pipeline path |

### Domain Hierarchy Established

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

### API Endpoints Added

```http
POST   /api/v1/crops/{crop_id}/disease-observations              201 Created
GET    /api/v1/crops/{crop_id}/disease-observations              200 OK  (observed_at DESC, paginated)
GET    /api/v1/fields/{field_id}/disease-observations            200 OK  (observed_at DESC, paginated)
GET    /api/v1/disease-observations/{observation_id}             200 OK
PATCH  /api/v1/disease-observations/{observation_id}             200 OK
DELETE /api/v1/disease-observations/{observation_id}            204 No Content
```

### Business Rules Implemented

* Crop must exist before DiseaseObservation creation (raises `CropNotFoundError` → 404)
* `crop_id` supplied through route path — not in request body
* `field_id` resolved server-side from crop record — not supplied by caller
* `observed_at` must be timezone-aware and not in the future (raises `InvalidDiseaseObservationError` → 400)
* `affected_area_percent`, when supplied, must be within [0, 100] (Pydantic schema validation)
* `crop_id` and `field_id` immutable after creation — excluded from update schema
* PATCH is permitted — DiseaseObservation is a mutable observation record
* List responses ordered by `observed_at DESC` (most recent observation first)

### Architecture Decisions

| ADR | Decision |
|---|---|
| ADR-010-01 | `DiseaseObservation` anchors to `crop_id` — disease pressure is per crop cycle |
| ADR-010-02 | `field_id` denormalized on `disease_observations` for direct field-scoped queries without JOIN |
| ADR-010-03 | `observed_at TIMESTAMPTZ NOT NULL` is the primary time key and TimescaleDB partition key candidate |
| ADR-010-04 | `DiseaseObservation` is mutable — PATCH permitted for operator corrections |
| ADR-010-05 | `crop_id` immutable after creation — excluded from `UpdateDiseaseObservationRequest` |
| ADR-010-06 | `DiseaseSeverity` and `DiagnosisMethod` placed in `app/core/enums.py` for cross-domain reuse |

### Lessons Learned

* The grandchild domain pattern established in Phase 9 (YieldRecord) transferred cleanly to DiseaseObservation — crop anchoring, denormalized `field_id`, and mutable PATCH semantics required no architectural invention.
* Field-scoped list endpoints (`GET /fields/{field_id}/disease-observations`) validate the denormalized FK design — direct queries without JOIN through `crops` are the intended access pattern.
* Reusing `CropNotFoundError` from `app.services.crop` maintains consistency with YieldRecord and avoids exception proliferation in the services package.
* `postgresql.ENUM` with `create_type=False` is now routine — Phase 10 migration applied the ADR-008-01 pattern without incident.

### Future Considerations

* **TimescaleDB:** `disease_observations.observed_at TIMESTAMPTZ NOT NULL` is hypertable-ready; `create_hypertable('disease_observations', 'observed_at')` requires no application code changes.
* **Disease Risk Scoring Engine (Phase 13):** `DiseaseObservation` severity labels and `observed_at` time-series are the primary training label source.
* **Redpanda:** `DiseaseObservationService.create_observation()` contains a documented extension point for `DiseaseObservationCreated` domain events.
* **GaaS PlantHealthAdvisor:** Disease observation list endpoints provide context for natural language crop health queries.

### Current Platform Status (Post Phase 10)

#### Domain Hierarchy

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

#### Current Database Tables

* alembic_version
* farms
* fields
* crops
* soil_profiles
* weather_records
* sensor_readings
* irrigation_events
* yield_records
* disease_observations

#### Current Migration Head

`d3e7b2a9f1c4_create_disease_observations_table`

#### Current Architecture

```
Model → Schema → Repository → Service → API
```

#### Current API Coverage

Health, Version, Fields, Crops, Soil Profiles, Weather Records, Sensor Readings, Irrigation Events, Yield Records: (unchanged — see Phase 1–9 entries)

Disease Observations (Phase 10):

* POST   /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/fields/{field_id}/disease-observations
* GET    /api/v1/disease-observations/{observation_id}
* PATCH  /api/v1/disease-observations/{observation_id}
* DELETE /api/v1/disease-observations/{observation_id}

---

### Next Planned Evolution

Phase 11 – Satellite Observation Domain
