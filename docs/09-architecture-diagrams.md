# AGRIFLOW-AI Architecture Diagrams

**Document:** Architecture Diagrams Reference  
**Version:** 1.1  
**Date:** June 2026  
**Scope:** Current State (Phase 11) and Target State (Phase 15) — visual architecture reference  
**Status:** Living Document  
**Author:** AGRIFLOW-AI Principal Enterprise Architecture

---

## Table of Contents

1. [AGRIFLOW Platform Evolution](#1-agriflow-platform-evolution)
2. [Current Domain Architecture](#2-current-domain-architecture)
3. [Current Clean Architecture](#3-current-clean-architecture)
4. [Current Request Flow](#4-current-request-flow)
5. [Current Database Architecture](#5-current-database-architecture)
6. [Current Sensor Telemetry Architecture](#6-current-sensor-telemetry-architecture)
7. [AI Readiness Architecture](#7-ai-readiness-architecture)
8. [Future Precision Agriculture Architecture](#8-future-precision-agriculture-architecture)
9. [Future Event-Driven Architecture](#9-future-event-driven-architecture)
10. [Future CQRS Architecture](#10-future-cqrs-architecture)
11. [Future TimescaleDB Architecture](#11-future-timescaledb-architecture)
12. [Future Cassandra Architecture](#12-future-cassandra-architecture)
13. [Future Temporal Workflow Architecture](#13-future-temporal-workflow-architecture)
14. [Future Digital Twin Architecture](#14-future-digital-twin-architecture)
15. [Future GaaS Architecture](#15-future-gaas-architecture)
16. [AGRIFLOW Target State Architecture — Phase 15 Vision](#16-agriflow-target-state-architecture--phase-15-vision)

---

## 1. AGRIFLOW Platform Evolution

### Title
AGRIFLOW-AI Platform Evolution — Phase 1 through Phase 11

### Purpose
Illustrate how each completed phase expanded the AGRIFLOW-AI platform from an empty backend foundation into a multi-domain, AI-ready agricultural intelligence system. This diagram captures the strategic trajectory: each phase added a new domain, new infrastructure, or a critical capability layer that unlocked the next phase.

### Explanation
The platform began with zero capability in Phase 1. By Phase 11, it operates a fully layered Clean Architecture with ten domain models, eleven database migrations, an AI readiness attribute set, append-only IoT telemetry, mutable operational event domains, two grandchild crop-cycle observation domains, and one field-anchored Earth observation domain (`SatelliteObservation`). Each vertical column in the diagram represents a phase boundary. Capabilities are cumulative — nothing is removed; each phase builds on all prior phases.

```mermaid
timeline
    title AGRIFLOW-AI Platform Evolution — Phase 1 to Phase 11
    Phase 1 : FastAPI Foundation
            : PostgreSQL Integration
            : Alembic Migration Framework
            : Docker Foundation
            : Farm Domain Model
            : Health + Version APIs
    Phase 2 : Field Domain
            : Farm → Field Relationship
            : BaseRepository Pattern
            : Dependency Injection Framework
            : Service Layer Architecture
    Phase 3 : Crop Domain
            : CropStatus Enum (PLANNED→HARVESTED)
            : Crop Lifecycle Management
            : Status-Filtered Queries
    Phase 4 : Soil Intelligence Domain
            : SoilProfile (1-to-1 per Field)
            : NPK + pH + Organic Matter
            : Two-Layer Uniqueness Enforcement
    Phase 5 : Weather Intelligence Domain
            : Time-Series Weather Records
            : TIMESTAMPTZ Telemetry Pattern
            : Physical Constraint Validation
    Phase 6 : AI Readiness Foundation
            : P1 AI Attribute Expansion (10 columns)
            : Yield Prediction Coverage 18%→82%
            : Backward-Compatible Schema Evolution
    Phase 7 : Sensor Telemetry Domain
            : Append-Only Immutable Telemetry
            : SensorType Shared Enum (11 types)
            : Compound Index Strategy
            : Future Event Boundary Marked
    Phase 8 : Irrigation Management Domain
            : Mutable Operational Event Pattern
            : IrrigationMethod Enum (8 methods)
            : WaterSource Enum (5 sources)
            : TimescaleDB Partition Key (started_at)
            : ENUM Lifecycle Fix (postgresql.ENUM)
    Phase 9 : Yield Record Domain
            : YieldMeasurementMethod Enum
            : Field-Level Yield Analytics
            : Time-Series Yield Tracking
            : First Grandchild Domain (Crop → YieldRecord)
    Phase 10 : Disease Observation Domain
            : DiseaseSeverity Enum
            : DiagnosisMethod Enum
            : Crop Health Intelligence
            : Disease Monitoring Foundation
            : Second Grandchild Domain (Crop → DiseaseObservation)
    Phase 11 : Satellite Observation Domain
            : SatelliteProvider Enum
            : SpectralIndex Enum
            : ProcessingLevel Enum
            : Field-Anchored Earth Observation
            : NDVI / EVI / LAI Index Storage
            : Mutable Reprocessing Corrections (PATCH)
```

### Key Architectural Observations

- **Phase 1** established the non-negotiable cross-cutting concerns: `AuditableModel`, UUID PKs, Alembic, async SQLAlchemy. Every subsequent phase reuses these without modification.
- **Phase 2** created the five-layer architecture pattern (`Model → Schema → Repository → Service → Router`) that became the immutable template for all future domain additions.
- **Phase 6** was the only phase that did not add a new domain — instead it performed a systematic AI data gap analysis and backfilled the minimum P1 attribute set. This was the most strategically important phase for future AI model training.
- **Phase 7** introduced the first qualitatively different domain: append-only telemetry. The decision to make `SensorReading` immutable and to mark the service layer as the future Redpanda/Digital Twin/Temporal boundary was the platform's first explicit forward-architecture design.
- **Phase 8** introduced the first mutable operational event domain (`IrrigationEvent`) and the authoritative PostgreSQL ENUM lifecycle pattern (`postgresql.ENUM` with `create_type=False`). Both `sensor_readings` and `irrigation_events` are now TimescaleDB-ready.
- **Phase 9** introduced the first grandchild domain (`YieldRecord`), establishing crop-cycle anchoring with denormalized `field_id` for direct field-scoped analytics and time-series yield tracking.
- **Phase 10** extended the grandchild pattern to crop health (`DiseaseObservation`), adding structured disease severity labels and diagnosis method provenance — the primary training label source for the future Disease Risk Scoring Engine.
- **Phase 11** introduced the first field-anchored Earth observation domain (`SatelliteObservation`), storing spectral index values (`SpectralIndex`), satellite provider provenance (`SatelliteProvider`), and processing level metadata (`ProcessingLevel`). Unlike grandchild domains, `SatelliteObservation` anchors directly on `Field` — enabling geospatial analytics without crop-cycle coupling. PATCH is permitted for reprocessing corrections; `field_id` is immutable after creation.

---

## 2. Current Domain Architecture

### Title
AGRIFLOW-AI Current Domain Architecture — Post Phase 11

### Purpose
Show the complete domain model as it exists after Phase 11, including all entities, their relationships, cardinalities, and key attributes. This is the authoritative domain map for current state.

### Explanation
`Farm` is the root aggregate. All domain entities trace their ancestry to a `Farm` via the `Field` pivot. `SoilProfile` has a strict 1:1 cardinality with `Field`. `Crop`, `WeatherRecord`, `SensorReading`, `IrrigationEvent`, and `SatelliteObservation` are 1:N collections per `Field`. `YieldRecord` and `DiseaseObservation` are grandchild domains — they anchor to `Crop` (primary FK) and carry a denormalized `field_id` for direct field-scoped queries. `SensorReading` is the only domain with an explicit immutability contract. `IrrigationEvent`, `YieldRecord`, `DiseaseObservation`, and `SatelliteObservation` are mutable operational observation domains.

```mermaid
graph TD
    Farm["🏚 Farm\n──────────────\nid: UUID PK\nfarm_code: VARCHAR\nfarm_name: VARCHAR\nowner_name: VARCHAR\ncountry / state / city\nlatitude / longitude\ntotal_area_hectares\nis_active: BOOL\ncreated_at / updated_at"]

    Field["🌾 Field\n──────────────\nid: UUID PK\nfarm_id: UUID FK\nname: VARCHAR\narea_hectares: NUMERIC\nsoil_type: VARCHAR\nlatitude / longitude\nelevation_m: NUMERIC\ncreated_at / updated_at"]

    Crop["🌱 Crop\n──────────────\nid: UUID PK\nfield_id: UUID FK\ncrop_name / crop_variety\nplanting_date: DATE\nexpected_harvest_date: DATE\nactual_harvest_date: DATE\nstatus: CropStatus ENUM\nactual_yield_tons_ha\nexpected_yield_tons_ha\nseeding_rate_kg_ha\ngrowth_stage: VARCHAR\ncreated_at / updated_at"]

    SoilProfile["🪨 SoilProfile\n──────────────\nid: UUID PK\nfield_id: UUID FK UNIQUE\nsoil_type: SoilType ENUM\nph / organic_matter\nnitrogen / phosphorus / potassium\nsoil_depth_cm\ncation_exchange_capacity_meq\nnotes: TEXT\ncreated_at / updated_at"]

    WeatherRecord["🌦 WeatherRecord\n──────────────\nid: UUID PK\nfield_id: UUID FK\nrecorded_at: TIMESTAMPTZ\ntemperature_c\nhumidity_percent\nrainfall_mm\nwind_speed_kmh\ndata_source: VARCHAR\nsolar_radiation_wm2\ntemperature_min_c\ntemperature_max_c\ncreated_at / updated_at"]

    SensorReading["📡 SensorReading\n──────────────\nid: UUID PK\nfield_id: UUID FK\nsensor_type: SensorType ENUM\nsensor_value: DOUBLE PRECISION\nunit: VARCHAR\nrecorded_at: TIMESTAMPTZ\nnotes: TEXT\ncreated_at / updated_at\n⚠ APPEND-ONLY — No UPDATE"]

    IrrigationEvent["💧 IrrigationEvent\n──────────────\nid: UUID PK\nfield_id: UUID FK\nstarted_at: TIMESTAMPTZ\nended_at: TIMESTAMPTZ (opt)\nduration_minutes: NUMERIC\nwater_volume_liters: NUMERIC\nirrigation_method: ENUM\nwater_source: ENUM\nnotes: TEXT\ncreated_at / updated_at\n✓ MUTABLE — PATCH supported"]

    YieldRecord["🌾 YieldRecord\n──────────────\nid: UUID PK\ncrop_id: UUID FK ← primary anchor\nfield_id: UUID FK (denormalized)\nrecorded_at: TIMESTAMPTZ\nyield_value_tons_ha: NUMERIC\nmeasurement_method: ENUM\narea_harvested_ha: NUMERIC (opt)\nmoisture_content_percent: NUMERIC (opt)\ntest_weight_kg_hl: NUMERIC (opt)\nquality_grade: VARCHAR (opt)\nnotes: TEXT\ncreated_at / updated_at\n✓ MUTABLE — PATCH supported"]

    DiseaseObservation["🦠 DiseaseObservation\n──────────────\nid: UUID PK\ncrop_id: UUID FK ← primary anchor\nfield_id: UUID FK (denormalized)\nobserved_at: TIMESTAMPTZ\ndisease_name: VARCHAR\nseverity: DiseaseSeverity ENUM\ndiagnosis_method: DiagnosisMethod ENUM\naffected_area_percent: NUMERIC (opt)\ntreatment_applied: TEXT (opt)\nnotes: TEXT\ncreated_at / updated_at\n✓ MUTABLE — PATCH supported"]

    SatelliteObservation["🛰 SatelliteObservation\n──────────────\nid: UUID PK\nfield_id: UUID FK ← primary anchor\nobserved_at: TIMESTAMPTZ\nsatellite_provider: SatelliteProvider ENUM\nspectral_index: SpectralIndex ENUM\nindex_value: NUMERIC\nprocessing_level: ProcessingLevel ENUM\nresolution_m: NUMERIC (opt)\ncloud_cover_percent: NUMERIC (opt)\nscene_id: VARCHAR (opt)\nnotes: TEXT\ncreated_at / updated_at\n✓ MUTABLE — PATCH supported"]

    Farm -->|"1 : N\nhas fields"| Field
    Field -->|"1 : N\ngrows crops"| Crop
    Field -->|"1 : 1\nhas profile"| SoilProfile
    Field -->|"1 : N\nrecords weather"| WeatherRecord
    Field -->|"1 : N\ngenerates telemetry"| SensorReading
    Field -->|"1 : N\nreceives irrigation"| IrrigationEvent
    Field -.->|"1 : N\ndenormalized FK"| YieldRecord
    Field -.->|"1 : N\ndenormalized FK"| DiseaseObservation
    Field -->|"1 : N\nrecords satellite"| SatelliteObservation
    Crop -->|"1 : N\nmeasures yield"| YieldRecord
    Crop -->|"1 : N\nobserves disease"| DiseaseObservation
```

### Key Architectural Observations

- `Farm → Field → {Crop, SoilProfile, WeatherRecord, SensorReading, IrrigationEvent, SatelliteObservation}` is the stable aggregate hierarchy. `YieldRecord` and `DiseaseObservation` introduce grandchild paths: `Farm → Field → Crop → {YieldRecord, DiseaseObservation}`.
- `SoilProfile` is the only 1:1 entity. Its uniqueness is enforced at two levels: `UNIQUE` constraint in PostgreSQL and `DuplicateSoilProfileError` at the service layer.
- `WeatherRecord`, `SensorReading`, `IrrigationEvent`, `YieldRecord`, `DiseaseObservation`, and `SatelliteObservation` are all time-keyed domains with `TIMESTAMPTZ`. All six are TimescaleDB hypertable candidates.
- `SensorReading` is immutable (no PATCH, no UPDATE); `IrrigationEvent`, `YieldRecord`, `DiseaseObservation`, and `SatelliteObservation` are mutable (full CRUD). This contrast reflects the fundamental difference between sensor telemetry (immutable physical fact) and operational management records (correctible human actions or reprocessed observations).
- `YieldRecord` and `DiseaseObservation` are the first entities to carry two parent FKs (`crop_id` primary anchor, `field_id` denormalized). `SatelliteObservation` is field-anchored only — no crop FK — enabling Earth observation analytics independent of crop lifecycle state.
- All ten domain tables carry `created_at` and `updated_at` via `AuditableModel`.

---

## 3. Current Clean Architecture

### Title
AGRIFLOW-AI Current Clean Architecture — Layer Boundaries and Dependency Direction

### Purpose
Illustrate the strict five-layer Clean Architecture that governs every domain in AGRIFLOW-AI. Show the dependency rule: dependencies point inward only — outer layers depend on inner layers, never the reverse.

### Explanation
FastAPI routes are the outermost layer. They accept HTTP requests, validate via Pydantic schemas, and delegate to services. Services own business rules and domain invariants but have no knowledge of SQL. Repositories encapsulate all database access. ORM models define table structures. PostgreSQL is the persistence engine. `deps.py` is the wiring hub — it opens sessions, creates repositories, creates services, and injects them into routes.

```mermaid
graph TB
    subgraph "External Boundary"
        Client["HTTP Client\nBrowser / IoT Device / API Consumer"]
    end

    subgraph "API Layer  [app/api/]"
        Router["FastAPI Router\nrouter.py per domain\n• HTTP method + route path\n• Request body reception\n• Exception → HTTP status mapping\n• Structured request logging"]
        Schema["Pydantic Schemas\nschemas/{domain}.py\n• CreateSchema / UpdateSchema\n• ResponseSchema\n• ConfigDict(from_attributes=True)"]
        Deps["deps.py\n• AsyncSession lifecycle\n• Repository factory\n• Service factory\n• Annotated type aliases"]
    end

    subgraph "Service Layer  [app/services/]"
        Service["Domain Service\nservices/{domain}.py\n• Business rules\n• Domain invariants\n• Cross-domain orchestration\n• Domain exception declaration\n• Future event publishing boundary"]
    end

    subgraph "Repository Layer  [app/db/repositories/]"
        BaseRepo["BaseRepository[T]\n• get_by_id()\n• get_all()\n• create()\n• update()\n• delete()"]
        ConcreteRepo["Domain Repository\nrepositories/{domain}.py\n• list_by_field()\n• exists_for_field()\n• Domain-specific queries\n• flush() — not commit()"]
    end

    subgraph "Model Layer  [app/db/models/]"
        ORM["SQLAlchemy ORM Model\nmodels/{domain}.py\n• Table definition\n• Column types + constraints\n• Relationships\n• Inherits AuditableModel"]
        AuditMixin["AuditableModel Mixin\n• id: UUID PK\n• created_at: TIMESTAMPTZ\n• updated_at: TIMESTAMPTZ"]
        CoreEnums["app/core/enums.py\n• SensorType (Phase 7)\n• IrrigationMethod (Phase 8)\n• WaterSource (Phase 8)\n• YieldMeasurementMethod (Phase 9)\n• DiseaseSeverity (Phase 10)\n• DiagnosisMethod (Phase 10)\n• SatelliteProvider (Phase 11)\n• SpectralIndex (Phase 11)\n• ProcessingLevel (Phase 11)"]
    end

    subgraph "Database Layer"
        PG[("PostgreSQL 17\n• farms\n• fields\n• crops\n• soil_profiles\n• weather_records\n• sensor_readings\n• irrigation_events\n• yield_records\n• disease_observations\n• satellite_observations\n• alembic_version")]
        Alembic["Alembic\nMigration Engine\n001 → a1b2c3d4e5f6\n(current head)"]
    end

    Client -->|"HTTP Request"| Router
    Router -->|"Inject via Depends()"| Deps
    Deps -->|"Instantiate"| Service
    Service -->|"Delegate persistence"| ConcreteRepo
    ConcreteRepo -->|"Inherits"| BaseRepo
    ConcreteRepo -->|"Queries via"| ORM
    ORM -->|"Inherits"| AuditMixin
    ORM -->|"Uses enums from"| CoreEnums
    ORM -->|"Maps to"| PG
    Alembic -->|"Manages schema of"| PG
    Router -->|"Validates with"| Schema
    Router -.->|"Returns JSON"| Client
```

### Key Architectural Observations

- **Dependency inversion is absolute.** `Service` never imports from `Router`. `Repository` never imports from `Service`. This boundary is enforced by convention and code review.
- **`deps.py` is the composition root.** All object construction and wiring happens there. Routes and services are unaware of each other's construction details.
- **`BaseRepository` provides the CRUD contract.** Concrete repositories re-declare inherited methods with typed signatures for IDE and mypy support, but add no new CRUD logic.
- **`AuditableModel` is the universal base.** Adding any new table without inheriting `AuditableModel` is an architectural violation.
- **`app/core/enums.py` is the shared vocabulary layer.** `SensorType` (Phase 7), `IrrigationMethod` / `WaterSource` (Phase 8), `YieldMeasurementMethod` (Phase 9), `DiseaseSeverity` / `DiagnosisMethod` (Phase 10), and `SatelliteProvider` / `SpectralIndex` / `ProcessingLevel` (Phase 11) are placed there to enable reuse by Digital Twin, AI Engine, and GaaS components in future phases.
- **Phase 11 added `SatelliteObservation` across all five layers:** `models/satellite_observation.py` (ORM), `repositories/satellite_observation.py` (`SatelliteObservationRepository`), `services/satellite_observation.py` (`SatelliteObservationService`), `schemas/satellite_observation.py`, and `api/satellite_observations/router.py` — following the identical template established in Phase 2.
- **Phase 10 added `DiseaseObservation` across all five layers:** `models/disease_observation.py` (ORM), `repositories/disease_observation.py` (`DiseaseObservationRepository`), `services/disease_observation.py` (`DiseaseObservationService`), `schemas/disease_observation.py`, and `api/disease_observations/router.py` — following the identical template established in Phase 2.

---

## 4. Current Request Flow

### Title
AGRIFLOW-AI Current Request Flow — Full Lifecycle Sequence

### Purpose
Trace the complete lifecycle of an HTTP request from the moment a client sends it to the moment a JSON response is returned. Show every layer touched, every responsibility exercised, and the transaction boundary.

### Explanation
The sequence diagram uses `POST /api/v1/fields/{field_id}/sensor-readings` as the canonical example — it exercises the most validation steps. The transaction is opened by `deps.py` and committed only on success. If any layer raises an exception, the session context manager performs automatic rollback.

```mermaid
sequenceDiagram
    autonumber
    participant Client as HTTP Client
    participant Router as FastAPI Router
    participant Deps as deps.py
    participant Schema as Pydantic Schema
    participant Svc as SensorReadingService
    participant Repo as SensorReadingRepository
    participant FRepo as FieldRepository
    participant DB as PostgreSQL

    Client->>Router: POST /fields/{field_id}/sensor-readings\n{sensor_type, sensor_value, unit, recorded_at}
    Router->>Schema: Validate request body (SensorReadingCreate)
    Schema-->>Router: Validated payload or 422 Unprocessable Entity

    Router->>Deps: Inject AsyncSession + SensorReadingService
    Deps->>Deps: Open AsyncSession\nBegin transaction

    Router->>Svc: create_sensor_reading(field_id, payload)

    Svc->>FRepo: get_by_id(field_id)
    FRepo->>DB: SELECT * FROM fields WHERE id = ?
    DB-->>FRepo: Field ORM instance
    FRepo-->>Svc: Field or None

    alt Field not found
        Svc-->>Router: raise FieldNotFoundError
        Router-->>Client: 404 Not Found
    end

    Svc->>Svc: Validate recorded_at is timezone-aware
    alt Naive datetime
        Svc-->>Router: raise InvalidSensorTimestampError
        Router-->>Client: 422 Unprocessable Entity
    end

    Svc->>Svc: Validate recorded_at is not in the future
    alt Future timestamp
        Svc-->>Router: raise InvalidSensorTimestampError
        Router-->>Client: 422 Unprocessable Entity
    end

    Svc->>Repo: create(SensorReading ORM instance)
    Repo->>DB: INSERT INTO sensor_readings (...)
    DB-->>Repo: Persisted ORM instance
    Repo->>Repo: session.flush()
    Repo-->>Svc: SensorReading ORM instance

    Note over Svc: Future extension point (ADR-007-26):\nRedpanda publish / Digital Twin update\n/ Temporal workflow trigger

    Svc-->>Router: SensorReading ORM instance
    Router->>Schema: model_validate(orm) → SensorReadingResponse
    Deps->>Deps: session.commit()
    Router-->>Client: 201 Created\n{SensorReadingResponse JSON}
```

### Key Architectural Observations

- **The transaction is opened and closed exclusively by `deps.py`.** No service or repository calls `commit()` — this is the contract enforced by ADR-002-02.
- **Validation is layered.** Pydantic handles schema-level validation (field presence, type coercion). The service layer re-validates domain invariants (timezone-awareness, future timestamps). Both layers are necessary — Pydantic cannot reject a valid-format datetime that happens to be in the future.
- **The extension point at step 14 is architectural.** It is the intended insertion point for Redpanda publishing, Digital Twin updates, and Temporal workflow triggers. It requires no modification to any business logic above it.
- **Error translation belongs in the router.** Services raise typed domain exceptions. Routers translate them to HTTP status codes via `try/except`. This keeps services ignorant of HTTP semantics.

### Satellite Observation Request Flow (Phase 11 — Mutable Field-Anchored Pattern)

The sequence below uses `POST /api/v1/fields/{field_id}/satellite-observations` as the canonical Phase 11 example. Unlike append-only `SensorReading`, `SatelliteObservation` supports PATCH for reprocessing corrections. `field_id` is resolved at creation and is immutable thereafter.

```mermaid
sequenceDiagram
    autonumber
    participant Client as HTTP Client
    participant Router as FastAPI Router
    participant Deps as deps.py
    participant Schema as Pydantic Schema
    participant Svc as SatelliteObservationService
    participant Repo as SatelliteObservationRepository
    participant FRepo as FieldRepository
    participant DB as PostgreSQL

    Client->>Router: POST /fields/{field_id}/satellite-observations\n{observed_at, satellite_provider, spectral_index, index_value, ...}
    Router->>Schema: Validate request body (SatelliteObservationCreate)
    Schema-->>Router: Validated payload or 422 Unprocessable Entity

    Router->>Deps: Inject AsyncSession + SatelliteObservationService
    Deps->>Deps: Open AsyncSession\nBegin transaction

    Router->>Svc: create_satellite_observation(field_id, payload)

    Svc->>FRepo: get_by_id(field_id)
    FRepo->>DB: SELECT * FROM fields WHERE id = ?
    DB-->>FRepo: Field ORM instance
    FRepo-->>Svc: Field or None

    alt Field not found
        Svc-->>Router: raise FieldNotFoundError
        Router-->>Client: 404 Not Found
    end

    Svc->>Svc: Validate observed_at is timezone-aware and not in the future
    Svc->>Svc: Validate index_value bounds for spectral_index (ratio -1 to 1, LAI positive)
    Svc->>Svc: Validate cloud_cover_percent 0 to 100 when supplied

    Svc->>Repo: create(SatelliteObservation ORM instance)
    Repo->>DB: INSERT INTO satellite_observations (...)
    DB-->>Repo: Persisted ORM instance
    Repo->>Repo: session.flush()
    Repo-->>Svc: SatelliteObservation ORM instance

    Svc-->>Router: SatelliteObservation ORM instance
    Router->>Schema: model_validate(orm) to SatelliteObservationResponse
    Deps->>Deps: session.commit()
    Router-->>Client: 201 Created\n{SatelliteObservationResponse JSON}
```

**Phase 11 status:** Implementation ✅ | Validation ⏳ Deferred | Testing ⏳ Deferred (Phase 16)

---

## 5. Current Database Architecture

### Title
AGRIFLOW-AI Current Database Architecture — Tables, Relationships, and Migration Strategy

### Purpose
Show the complete current database schema including all ten domain tables, their foreign key relationships, primary index strategy, and the Alembic migration chain that produced them. This diagram is the DBA reference view of the platform.

### Explanation
All tables use UUID v4 primary keys generated server-side. Foreign keys establish the `Farm → Field → {Crop, SoilProfile, WeatherRecord, SensorReading, IrrigationEvent, SatelliteObservation}` hierarchy, with grandchild domains `YieldRecord` and `DiseaseObservation` anchoring on `Crop` and carrying denormalized `field_id`. PostgreSQL ENUM types are created in separate calls before their owning tables to enable independent lifecycle management. Starting from Phase 8, `postgresql.ENUM` with `create_type=False` is the authoritative enum lifecycle pattern. Alembic migrations are linear and sequential.

```mermaid
erDiagram
    farms {
        UUID id PK
        VARCHAR farm_code
        VARCHAR farm_name
        VARCHAR owner_name
        VARCHAR country
        VARCHAR state
        VARCHAR city
        NUMERIC latitude
        NUMERIC longitude
        NUMERIC total_area_hectares
        BOOL is_active
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    fields {
        UUID id PK
        UUID farm_id FK
        VARCHAR name
        NUMERIC area_hectares
        VARCHAR soil_type
        NUMERIC latitude
        NUMERIC longitude
        NUMERIC elevation_m
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    crops {
        UUID id PK
        UUID field_id FK
        VARCHAR crop_name
        VARCHAR crop_variety
        DATE planting_date
        DATE expected_harvest_date
        DATE actual_harvest_date
        crop_status status
        NUMERIC actual_yield_tons_ha
        NUMERIC expected_yield_tons_ha
        NUMERIC seeding_rate_kg_ha
        VARCHAR growth_stage
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    soil_profiles {
        UUID id PK
        UUID field_id FK_UNIQUE
        soil_type soil_type
        NUMERIC ph
        NUMERIC organic_matter
        NUMERIC nitrogen
        NUMERIC phosphorus
        NUMERIC potassium
        NUMERIC soil_depth_cm
        NUMERIC cation_exchange_capacity_meq
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    weather_records {
        UUID id PK
        UUID field_id FK
        TIMESTAMPTZ recorded_at
        NUMERIC temperature_c
        NUMERIC humidity_percent
        NUMERIC rainfall_mm
        NUMERIC wind_speed_kmh
        VARCHAR data_source
        NUMERIC solar_radiation_wm2
        NUMERIC temperature_min_c
        NUMERIC temperature_max_c
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    sensor_readings {
        UUID id PK
        UUID field_id FK
        sensor_type sensor_type
        DOUBLE_PRECISION sensor_value
        VARCHAR unit
        TIMESTAMPTZ recorded_at
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    irrigation_events {
        UUID id PK
        UUID field_id FK
        TIMESTAMPTZ started_at
        TIMESTAMPTZ ended_at
        NUMERIC duration_minutes
        NUMERIC water_volume_liters
        irrigation_method irrigation_method
        water_source water_source
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    yield_records {
        UUID id PK
        UUID crop_id FK
        UUID field_id FK
        TIMESTAMPTZ recorded_at
        NUMERIC yield_value_tons_ha
        yield_measurement_method measurement_method
        NUMERIC area_harvested_ha
        NUMERIC moisture_content_percent
        NUMERIC test_weight_kg_hl
        VARCHAR quality_grade
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    disease_observations {
        UUID id PK
        UUID crop_id FK
        UUID field_id FK
        TIMESTAMPTZ observed_at
        VARCHAR disease_name
        disease_severity severity
        diagnosis_method diagnosis_method
        NUMERIC affected_area_percent
        TEXT treatment_applied
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    satellite_observations {
        UUID id PK
        UUID field_id FK
        TIMESTAMPTZ observed_at
        satellite_provider satellite_provider
        spectral_index spectral_index
        NUMERIC index_value
        processing_level processing_level
        NUMERIC resolution_m
        NUMERIC cloud_cover_percent
        VARCHAR scene_id
        TEXT notes
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    farms ||--o{ fields : "has"
    fields ||--o{ crops : "grows"
    fields ||--o| soil_profiles : "has profile"
    fields ||--o{ weather_records : "records"
    fields ||--o{ sensor_readings : "generates"
    fields ||--o{ irrigation_events : "receives"
    fields ||--o{ yield_records : "yields (denormalized)"
    fields ||--o{ disease_observations : "disease history (denormalized)"
    fields ||--o{ satellite_observations : "observes"
    crops ||--o{ yield_records : "measures"
    crops ||--o{ disease_observations : "observes"
```

### Migration Chain

```mermaid
graph LR
    M1["001\ncreate_farms_table\nFarm table\nUUID PK strategy"]
    M2["002\ncreate_fields_table\nField table\nfarm_id FK\nix_fields_farm_id"]
    M3["003\ncreate_crops_table\ncrop_status ENUM\nCrop table\nix_crops_field_id"]
    M4["13aabbe35d51\nadd_soil_profiles_table\nsoil_type ENUM\nsoil_profiles UNIQUE field_id"]
    M5["004\ncreate_weather_records_table\nWeatherRecord table\nix_recorded_at"]
    M6["005\nadd_p1_ai_readiness_columns\nADD COLUMN x10\n4 tables extended"]
    M7["006\ncreate_sensor_readings_table\nsensor_type ENUM\n5 indexes incl. compound"]
    M8["235a51cdf901\ncreate_irrigation_events_table\nirrigation_method ENUM\nwater_source ENUM\n3 indexes incl. compound"]
    M9["b7e2a9f4c8d3\ncreate_yield_records_table\nyield_measurement_method ENUM\n4 indexes incl. compound"]
    M10["d3e7b2a9f1c4\ncreate_disease_observations_table\ndisease_severity ENUM\ndiagnosis_method ENUM\n6 indexes incl. compound"]
    M11["a1b2c3d4e5f6\ncreate_satellite_observations_table\nsatellite_provider ENUM\nspectral_index ENUM\nprocessing_level ENUM\n7 indexes incl. compound"]

    M1 --> M2 --> M3 --> M4 --> M5 --> M6 --> M7 --> M8 --> M9 --> M10 --> M11
    M11 --> HEAD["HEAD\na1b2c3d4e5f6\n(current)"]
```

### Key Architectural Observations

- **All time-series tables index their primary time key.** `weather_records`, `sensor_readings`, `irrigation_events`, `yield_records`, `disease_observations`, and `satellite_observations` each have individual time indexes. `sensor_readings`, `irrigation_events`, `yield_records`, `disease_observations`, and `satellite_observations` add compound `(parent_id, time_key)` or `(spectral_index, observed_at)` indexes — the primary AI feature pipeline access pattern.
- **`soil_profiles.field_id` carries a `UNIQUE` constraint**, not a `UNIQUE INDEX`. The `UNIQUE` constraint is supplemented by a `UNIQUE INDEX` for explicit index naming.
- **Migration 005 used `ADD COLUMN` with no server defaults.** Adding nullable columns to existing tables with large row counts is instantaneous on PostgreSQL 11+ (metadata-only operation). This is the only safe strategy for live production schema evolution.
- **All Field children use `ON DELETE CASCADE`.** Deleting a `Field` atomically removes all its children at the database level.
- **Phase 8 established `postgresql.ENUM` as the authoritative enum migration pattern.** All future migrations must use `postgresql.ENUM` with `create_type=False` + explicit `.create()` / `.drop()` calls.

---

## 6. Current Sensor Telemetry Architecture

### Title
AGRIFLOW-AI Sensor Telemetry Architecture — Phase 7 IoT Data Ingestion Pipeline

### Purpose
Show how sensor data flows from IoT field devices through the ingestion API into immutable PostgreSQL storage, and illustrate the extension points where future event-driven components will be wired.

### Explanation
Phase 7 introduced the first real-time telemetry capability. IoT gateways submit sensor readings via REST. The API layer validates, the service layer enforces immutability rules (timezone-awareness, no future timestamps), and the repository persists to `sensor_readings`. The service contains a documented extension point (ADR-007-26) marking where Redpanda publishing, Digital Twin updates, and Temporal triggers will connect in future phases — without modifying the current business logic.

```mermaid
graph TB
    subgraph "IoT Edge Layer"
        S1["Soil Moisture\nSensor"]
        S2["Air Temperature\nSensor"]
        S3["Leaf Wetness\nSensor"]
        S4["EC / Salinity\nSensor"]
        GW["Field IoT\nGateway\n(aggregates + forwards)"]
        S1 & S2 & S3 & S4 -->|"MQTT / HTTP"| GW
    end

    subgraph "API Ingestion Layer"
        EP["POST /api/v1/fields/{field_id}/sensor-readings"]
        VAL["Pydantic Validation\n• SensorReadingCreate schema\n• sensor_type enum validation\n• recorded_at: datetime required"]
    end

    subgraph "Service Layer (Business Rules)"
        SVC["SensorReadingService\n• Field existence check\n• Timezone-aware timestamp check\n• Future timestamp rejection\n• Persistence delegation"]
        EXT["⬛ Extension Point (ADR-007-26)\n[NOT YET IMPLEMENTED]\n• Redpanda event publish\n• Digital Twin state update\n• CQRS read-model projection\n• Temporal workflow trigger"]
    end

    subgraph "Repository Layer"
        REPO["SensorReadingRepository\n• create()\n• list_by_field() → ORDER BY recorded_at DESC\n• get_by_id()\n• delete()\n⚠ NO update() exposed"]
    end

    subgraph "Storage Layer"
        PG[("PostgreSQL 17\nsensor_readings\n• DOUBLE PRECISION sensor_value\n• TIMESTAMPTZ recorded_at\n• ON DELETE CASCADE\n• 5 indexes")]
        IDX["Indexes:\n• ix_field_id\n• ix_sensor_type\n• ix_recorded_at\n• ix_(field_id, recorded_at)\n• ix_(sensor_type, recorded_at)"]
    end

    subgraph "Future Storage Upgrade"
        TS[("TimescaleDB\nHypertable\n(zero code changes)")]
        COMP["Weekly Chunks\n+ Columnar Compression\n+ Continuous Aggregates"]
    end

    GW -->|"HTTP POST\nJSON payload"| EP
    EP --> VAL
    VAL -->|"Validated payload"| SVC
    SVC -->|"After persistence"| EXT
    SVC --> REPO
    REPO -->|"INSERT"| PG
    PG --- IDX
    PG -.->|"Future: create_hypertable()"| TS
    TS --- COMP
```

### Key Architectural Observations

- **Immutability is the defining characteristic of `SensorReading`.** No `PATCH` or `PUT` endpoint exists. The API router module docstring explicitly references ADR-007-32. Corrections to erroneous readings are expressed as new readings, not modifications.
- **`DOUBLE PRECISION` was chosen deliberately over `NUMERIC`.** Sensor ADC outputs and physical unit measurements (mV, µS/cm, lux) require IEEE 754 64-bit floating-point precision. Fixed-scale `NUMERIC` would silently truncate high-resolution readings.
- **The extension point is a zero-cost future capability.** Adding Redpanda publishing requires no changes to validation logic, field existence checks, or timestamp validation. The extension point is below all business logic.
- **TimescaleDB promotion requires zero application changes.** The `sensor_readings` table satisfies TimescaleDB's only structural requirement: a `NOT NULL TIMESTAMPTZ` partition column (`recorded_at`). `create_hypertable()` is a single SQL call.

---

## 7. AI Readiness Architecture

### Title
AGRIFLOW-AI AI Readiness Architecture — Data Feeds and Model Coverage

### Purpose
Show how the current data domains combine to feed four target AI use cases, and visualize the AI data coverage achieved after Phase 11 completion.

### Explanation
Phase 6 conducted a systematic gap analysis across every planned AI use case. The result was a prioritized attribute roadmap. 10 P1 attributes were added across 4 domains, raising yield prediction coverage from 18% to 82%. Phases 8–11 subsequently added `IrrigationEvent`, `YieldRecord`, `DiseaseObservation`, and `SatelliteObservation` domains, closing the major structural gaps for irrigation optimisation, yield prediction, disease monitoring, and remote sensing feature pipelines. The diagram shows the data-to-AI mapping and the current coverage state.

```mermaid
graph TB
    subgraph "Current Data Domains"
        FARM["🏚 Farm\n• GPS coordinates\n• total_area_hectares\n• country / climate zone"]
        FIELD["🌾 Field\n• latitude / longitude\n• elevation_m\n• area_hectares\n• soil_type"]
        CROP["🌱 Crop\n• crop_name / variety\n• planting_date\n• actual_harvest_date\n• actual_yield_tons_ha ✦\n• expected_yield_tons_ha ✦\n• seeding_rate_kg_ha ✦\n• growth_stage ✦"]
        SOIL["🪨 SoilProfile\n• NPK levels\n• pH / organic_matter\n• soil_depth_cm ✦\n• CEC meq ✦"]
        WEATHER["🌦 WeatherRecord\n• temperature_c / min / max ✦\n• humidity_percent\n• rainfall_mm\n• solar_radiation_wm2 ✦\n• wind_speed_kmh"]
        SENSOR["📡 SensorReading\n• SOIL_MOISTURE\n• SOIL_TEMPERATURE\n• AIR_TEMPERATURE\n• LEAF_WETNESS\n• ELECTRICAL_CONDUCTIVITY\n• LIGHT_INTENSITY\n• BATTERY_STATUS"]
        IRR["💧 IrrigationEvent ✅\n• started_at / ended_at\n• water_volume_liters\n• irrigation_method\n• water_source"]
        YIELD_D["🌾 YieldRecord ✅\n• yield_value_tons_ha\n• measurement_method\n• moisture_content_percent\n• quality_grade"]
        DISEASE_D["🦠 DiseaseObservation ✅\n• disease_name\n• severity (DiseaseSeverity)\n• diagnosis_method\n• affected_area_percent\n• observed_at"]
        SAT_D["🛰 SatelliteObservation ✅\n• spectral_index (NDVI/EVI/LAI)\n• index_value\n• satellite_provider\n• cloud_cover_percent\n• observed_at"]
    end

    subgraph "AI Use Cases — Current Coverage"
        YIELD["🌾 Yield Prediction\nCoverage: 100% ✅\n(was 18% pre-Phase 6)\nKey features: yield history,\nGDD inputs, seeding rate,\nsoil profile, weather,\ngranular YieldRecord labels,\nsatellite NDVI/EVI"]
        DISEASE["🦠 Disease Prediction\nCoverage: 90% 🟡\nKey gaps: multi-point LEAF_WETNESS\ntime-series depth"]
        IRRIGATION["💧 Irrigation Optimization\nCoverage: 85% 🟡\nKey gaps: ET₀ calc,\nfield capacity model"]
        WEATHER_AI["⛅ Weather Intelligence\nCoverage: 65% 🟡\nKey gaps: vapor pressure\ndeficit, atmospheric pressure,\nforecast integration"]
    end

    subgraph "Phase 11 — Remote Sensing (Implemented)"
        SAT["SatelliteObservation ✅\n• ndvi / evi / lai\n• cloud_cover\n• observed_at"]
    end

    FARM & FIELD & CROP --> YIELD
    SOIL & WEATHER & SENSOR --> YIELD
    YIELD_D --> YIELD
    SAT_D --> YIELD
    CROP & WEATHER & SENSOR --> DISEASE
    DISEASE_D --> DISEASE
    SAT_D --> DISEASE
    SOIL & SENSOR & IRR --> IRRIGATION
    WEATHER & SENSOR --> WEATHER_AI

    SAT -.->|"NDVI trend vectors"| DISEASE
    SAT -.->|"Remote sensing yield maps"| YIELD
```

> ✦ = P1 AI attribute added in Phase 6 migration 005

### Key Architectural Observations

- **Yield Prediction reached 100% structural coverage** after Phase 9 and was strengthened by Phase 11. `YieldRecord` provides granular time-series yield labels with measurement method provenance — the primary training label source for the Phase 12 Yield Prediction Engine. `SatelliteObservation` adds NDVI/EVI/LAI remote sensing features.
- **Disease Prediction improved from 40% to 90%** after Phases 10–11. `DiseaseObservation` supplies structured severity labels (`DiseaseSeverity`), diagnosis method provenance (`DiagnosisMethod`), and time-keyed observation history. `SatelliteObservation` closes the satellite NDVI structural gap. The remaining 10% gap is primarily multi-point `LEAF_WETNESS` time-series depth.
- **Irrigation Optimization reached 85%** after Phases 7–9. `IrrigationEvent` water volume combined with `SensorReading.SOIL_MOISTURE` and `YieldRecord` enables water-use efficiency calculations. Remaining gaps are ET₀ calculation inputs and field capacity modelling.
- **`SensorReading.SOIL_MOISTURE` remains the single most valuable telemetry attribute** for Irrigation Optimization — it provides the missing state variable (current soil water content) that no other domain supplies.
- **`SatelliteObservation` (Phase 11) is implemented** with field-anchored spectral index storage. API validation and automated testing are deferred to Phase 16.
- **The AI layer does not write back to these domains directly** (ADR-006-03). Future inference services will write to designated `_score` and `_prediction` columns, not to the core domain attributes.

---

## 8. Future Precision Agriculture Architecture

### Title
AGRIFLOW-AI Future Precision Agriculture Architecture — Multi-Source Intelligence Platform

### Purpose
Show the complete precision agriculture data integration vision where IoT sensors, weather intelligence, satellite imagery, soil science, and crop data converge into an AI analytics platform that produces actionable field-level recommendations.

### Explanation
Precision Agriculture is the application of observational technology to optimize agricultural inputs at the sub-field level. AGRIFLOW-AI's architecture assembles the four required data streams — geospatial (satellite), environmental (weather), physical (soil/sensor), and biological (crop) — and routes them through an AI analytics layer to produce prescriptions for irrigation, fertilization, disease management, and harvest scheduling.

```mermaid
graph TB
    subgraph "Data Collection Layer"
        IOT["IoT Field Sensors\n• Soil moisture probes\n• Temperature / humidity arrays\n• Leaf wetness sensors\n• EC conductivity probes\n• Light intensity sensors"]
        SAT_SRC["Satellite Systems\n• Sentinel-2 (10m resolution)\n• Landsat 8 / 9\n• Planet Labs\n• Azure Maps / Bing Imagery"]
        WEATHER_SRC["Weather Services\n• Historical station data\n• Open-Meteo / Tomorrow.io\n• Automated weather stations\n• Forecast feeds (7-day)"]
        LAB["Laboratory Services\n• NPK analysis reports\n• pH / organic matter\n• CEC / bulk density\n• Micronutrient panels"]
        OPERATOR["Farm Operator\n• Manual observations\n• Disease sightings\n• Equipment logs\n• Harvest records"]
    end

    subgraph "AGRIFLOW-AI Data Platform"
        INGEST["Data Ingestion Gateway\n• REST APIs (FastAPI)\n• Batch import endpoints\n• Satellite imagery processor\n• IoT gateway adapter"]
        DOMAINS["Domain Storage (PostgreSQL)\n• SensorReading (IoT)\n• WeatherRecord\n• SoilProfile\n• Crop\n• IrrigationEvent (Ph.8) ✅\n• YieldRecord (Ph.9) ✅\n• DiseaseObservation (Ph.10) ✅\n• SatelliteObservation (Ph.11) ✅"]
        TIMESERIES["Time-Series Store\n(TimescaleDB)\n• Sensor hypertables\n• Hourly aggregates\n• 90-day rolling windows"]
    end

    subgraph "AI Analytics Layer"
        FE["Feature Engineering\n• Growing Degree Days (GDD)\n• Vapor Pressure Deficit\n• Evapotranspiration (ET₀)\n• NDVI trend vectors\n• Soil Water Balance"]
        MODELS["ML Model Registry\n• Yield Prediction (XGBoost)\n• Disease Risk Scoring (RF)\n• Irrigation Schedule (LSTM)\n• Anomaly Detection"]
        INFERENCE["Real-Time Inference\n• FastAPI + ONNX Runtime\n• Sub-100ms recommendations\n• Confidence scoring\n• Model versioning"]
    end

    subgraph "Recommendation Engine"
        RECS["Prescription Output\n• Variable-rate irrigation maps\n• Fertilization prescriptions\n• Disease intervention alerts\n• Harvest window predictions\n• Yield forecasts"]
    end

    subgraph "Delivery Layer"
        DASH["Farm Dashboard\n(React + TypeScript)"]
        MOBILE["Farm Mobile App"]
        GAAS["Farm Copilot\n(GaaS / LLM)"]
        EQUIP["Precision Equipment\n• Variable-rate spreaders\n• Automated irrigation\n• Drone dispatch"]
    end

    IOT -->|"HTTPS POST\nsensor readings"| INGEST
    SAT_SRC -->|"Imagery + indices"| INGEST
    WEATHER_SRC -->|"Observations + forecasts"| INGEST
    LAB -->|"Soil reports"| INGEST
    OPERATOR -->|"Manual entries"| INGEST

    INGEST --> DOMAINS
    INGEST --> TIMESERIES

    DOMAINS --> FE
    TIMESERIES --> FE
    FE --> MODELS
    MODELS --> INFERENCE
    INFERENCE --> RECS

    RECS --> DASH
    RECS --> MOBILE
    RECS --> GAAS
    RECS --> EQUIP
```

### Key Architectural Observations

- **The four data collection streams are orthogonal and independently valuable.** IoT provides high-frequency field-level telemetry. Satellite provides field-boundary-scale vegetation indices. Weather provides the environmental context. Soil profiles provide the slowly-changing substrate properties. No single stream can replace the others.
- **TimescaleDB is the bridge between raw telemetry and AI feature engineering.** Continuous aggregates (hourly, daily) reduce raw high-frequency data into the time-window features that ML models consume.
- **ONNX Runtime enables polyglot model serving.** Models trained in scikit-learn, XGBoost, or PyTorch can be exported to ONNX format and served by the existing FastAPI backend — no separate Python model-serving framework required.
- **Variable-rate prescriptions require sub-field spatial resolution.** The PostGIS `GEOMETRY` column (planned for `fields` in Phase 8+) enables field boundary-aware spatial join of satellite imagery and IoT sensor zones.

---

## 9. Future Event-Driven Architecture

### Title
AGRIFLOW-AI Future Event-Driven Architecture — Redpanda Streaming Platform

### Purpose
Illustrate how AGRIFLOW-AI will evolve from a synchronous REST-only platform to an event-driven architecture where IoT sensor events flow through Redpanda to multiple downstream consumers simultaneously, with zero coupling between producers and consumers.

### Explanation
The trigger for event-driven architecture is the `SensorReadingService` extension point documented in ADR-007-26. When Phase 8 introduces Redpanda, the existing service requires a single constructor injection to publish `SensorReadingCreated` events. All downstream consumers — Digital Twin updater, anomaly detector, CQRS projector, alert engine — subscribe independently. The write path remains fast and synchronous; downstream processing is asynchronous and isolated.

```mermaid
graph TB
    subgraph "IoT Device Layer"
        DEVICES["Field IoT Devices\n• Soil moisture probes\n• Temperature sensors\n• Leaf wetness sensors\n• Weather stations\n• Irrigation controllers"]
    end

    subgraph "Ingestion Layer"
        API["AGRIFLOW-AI REST API\nPOST /sensor-readings\nPOST /weather-records\nPOST /irrigation-events"]
        SVC["Domain Services\n• SensorReadingService\n• WeatherRecordService\n(future: IrrigationService)"]
        PG_WRITE[("PostgreSQL\nWrite Store\n(source of truth)")]
    end

    subgraph "Event Bus — Redpanda"
        BROKER["Redpanda Cluster\n(Kafka-compatible)\nTopic: sensor.readings.created\nTopic: weather.records.created\nTopic: irrigation.events.created\nTopic: crop.status.updated\nTopic: ai.inference.completed"]
    end

    subgraph "Consumer Services"
        DT_CONSUMER["Digital Twin Consumer\n• Subscribes: sensor.readings.created\n• Updates: FieldDigitalTwin state\n• Store: Redis / Cassandra"]
        ANOMALY["Anomaly Detection Consumer\n• Subscribes: sensor.readings.created\n• Evaluates: threshold rules\n• Publishes: anomaly.detected"]
        AI_PIPELINE["AI Feature Pipeline Consumer\n• Subscribes: sensor.readings.created\n• Maintains: rolling feature windows\n• Feeds: inference engine"]
        CQRS_PROJ["CQRS Read Projector\n• Subscribes: all domain events\n• Updates: read models\n• Store: TimescaleDB / Cassandra"]
        ALERT["Alert Engine Consumer\n• Subscribes: anomaly.detected\n• Triggers: Temporal workflow\n• Notifies: farm operator"]
    end

    subgraph "AI Inference Layer"
        INFERENCE["Inference Engine\n• Yield prediction\n• Disease risk scoring\n• Irrigation recommendation"]
        AI_TOPIC["Publishes:\nai.inference.completed"]
    end

    DEVICES -->|"HTTPS POST"| API
    API --> SVC
    SVC -->|"1. Persist"| PG_WRITE
    SVC -->|"2. Publish event\n(async, after commit)"| BROKER

    BROKER -->|"Consumer group:\ndigital-twin"| DT_CONSUMER
    BROKER -->|"Consumer group:\nanomaly-detection"| ANOMALY
    BROKER -->|"Consumer group:\nai-features"| AI_PIPELINE
    BROKER -->|"Consumer group:\ncqrs-projector"| CQRS_PROJ
    BROKER -->|"Consumer group:\nalert-engine"| ALERT

    AI_PIPELINE --> INFERENCE
    INFERENCE -->|"Publish result"| AI_TOPIC
    AI_TOPIC -->|"Subscribed by DT Consumer"| BROKER
```

### Key Architectural Observations

- **Producer-consumer decoupling is the central value.** `SensorReadingService` publishes one event and its responsibility ends. Whether 3 or 30 consumers process that event has zero impact on write latency.
- **Redpanda was chosen over Apache Kafka** for lower operational overhead (no ZooKeeper, no JVM, single-binary deployment) and Kafka-protocol compatibility — all existing Kafka client libraries work with Redpanda unchanged.
- **Event ordering is guaranteed within a partition.** By partitioning `sensor.readings.created` on `field_id`, all readings from the same field arrive in `recorded_at` order at every consumer.
- **At-least-once delivery with idempotent consumers.** `SensorReading` has a UUID `id` that consumers use as an idempotency key to prevent duplicate processing on consumer restarts.
- **The current architecture is already publish-ready.** The `SensorReadingService` constructor accepts injected dependencies. Adding an `event_publisher: Optional[EventPublisher] = None` parameter requires changing one line in `deps.py`.

---

## 10. Future CQRS Architecture

### Title
AGRIFLOW-AI Future CQRS Architecture — Read/Write Separation for Sensor Telemetry

### Purpose
Show how AGRIFLOW-AI will split the `SensorReadingRepository` into separate Write and Read implementations backed by different storage engines, enabling independent scaling of ingestion throughput and query performance.

### Explanation
CQRS (Command Query Responsibility Segregation) is motivated by the structural divergence of write and read patterns. Writes are single-reading, low-latency, transactional. Reads range from single-record lookups to hour-aggregated feature vectors consumed by ML models. Serving both from the same `SensorReadingRepository` with PostgreSQL creates unnecessary coupling. The CQRS split preserves the service layer interface while routing commands and queries to optimal storage engines.

```mermaid
graph TB
    subgraph "Command Side — Write Path"
        WRITE_API["POST /sensor-readings\n(IoT Ingestion)"]
        WRITE_SVC["SensorReadingWriteService\n• Field existence check\n• Timestamp validation\n• Business rules"]
        WRITE_REPO["SensorReadingWriteRepository\n(PostgreSQL)\n• create()\n• delete()"]
        WRITE_DB[("PostgreSQL\nWrite Store\nTransactional\nNormalized")]
        EVENT_PUB["EventPublisher\nRedpanda\nsensor.readings.created"]
    end

    subgraph "Event Propagation"
        REDPANDA["Redpanda\nTopic:\nsensor.readings.created"]
        PROJECTOR["CQRS Projector\n(Consumer Service)\n• Subscribes to events\n• Transforms to read models\n• Writes to read stores"]
    end

    subgraph "Query Side — Read Path"
        READ_API_DASH["GET /fields/{id}/sensor-readings\n(Dashboard)"]
        READ_API_AI["GET /fields/{id}/sensor-features\n(AI Feature Service)"]
        READ_API_DT["GET /fields/{id}/digital-twin\n(Digital Twin)"]
        READ_SVC["SensorReadingQueryService\n(read-only)\n• No state mutation\n• Aggregation support\n• Latest-per-type queries"]
        READ_REPO_TS["SensorReadingAggregateRepository\n(TimescaleDB)\n• hourly_avg_by_field()\n• latest_by_type()\n• rolling_window()"]
        READ_REPO_CASS["SensorReadingCassandraRepository\n(Cassandra)\n• list_by_field() — massive scale\n• get_by_id()\n• latest_by_type()"]
        TS_DB[("TimescaleDB\nContinuous Aggregates\nsensor_readings_hourly\nCold data compressed")]
        CASS_DB[("Apache Cassandra\nHot read store\nPartitioned by field_id\nClustered by recorded_at DESC")]
    end

    WRITE_API --> WRITE_SVC
    WRITE_SVC --> WRITE_REPO
    WRITE_REPO --> WRITE_DB
    WRITE_SVC --> EVENT_PUB
    EVENT_PUB --> REDPANDA
    REDPANDA --> PROJECTOR
    PROJECTOR --> TS_DB
    PROJECTOR --> CASS_DB

    READ_API_DASH --> READ_SVC
    READ_API_AI --> READ_SVC
    READ_API_DT --> READ_SVC
    READ_SVC --> READ_REPO_TS
    READ_SVC --> READ_REPO_CASS
    READ_REPO_TS --> TS_DB
    READ_REPO_CASS --> CASS_DB
```

### Key Architectural Observations

- **The service layer contract is unchanged.** CQRS is a repository-layer concern. Service method signatures remain identical. The split is transparent to routers and to any consumer of the service interface.
- **Write consistency is PostgreSQL-level transactional.** The command path uses synchronous PostgreSQL writes. The eventual consistency is only in the read path — read models may lag writes by milliseconds.
- **Incremental migration is safe.** The CQRS split can be introduced one step at a time: (1) add event publishing, (2) add read repositories, (3) route read consumers to read repositories, (4) deprecate read operations from `SensorReadingWriteRepository`.
- **Query-side storage choice is access-pattern-driven.** TimescaleDB serves time-aggregated analytical queries (hourly averages, rolling windows). Cassandra serves high-throughput, low-latency latest-value lookups across millions of fields.

---

## 11. Future TimescaleDB Architecture

### Title
AGRIFLOW-AI Future TimescaleDB Architecture — High-Frequency Sensor Time-Series Storage

### Purpose
Show how the existing `sensor_readings` PostgreSQL table will be promoted to a TimescaleDB hypertable, enabling automatic time-partitioned storage, continuous aggregates, and columnar compression — with zero application code changes.

### Explanation
TimescaleDB is a PostgreSQL extension that transparently partitions tables by time into "chunks." Each chunk maps to a time interval (e.g. one week). Queries with time-range predicates skip irrelevant chunks entirely. Continuous aggregates are materialised views that auto-update as new data arrives. Columnar compression reduces cold chunk storage by 20–100×. The AGRIFLOW-AI `sensor_readings` table was designed from day one to satisfy TimescaleDB's only structural requirement: a `NOT NULL TIMESTAMPTZ` partition key.

```mermaid
graph TB
    subgraph "Application Layer (Unchanged)"
        APP["AGRIFLOW-AI FastAPI\nSensorReadingRepository\nSensorReadingService\n(Zero code changes required)"]
    end

    subgraph "TimescaleDB Hypertable Layer"
        HT["sensor_readings\n(Hypertable)\nPartition key: recorded_at\nChunk interval: 1 week"]

        subgraph "Active Chunks (Hot Data)"
            C1["Chunk: 2026-W25\n(current week)\nB-tree indexed\nFull write throughput"]
            C2["Chunk: 2026-W24\n(last week)\nB-tree indexed\nRead-optimized"]
        end

        subgraph "Warm Chunks (Recent Data)"
            C3["Chunk: 2026-W20\n(1 month ago)\nB-tree indexed"]
            C4["Chunk: 2026-W16\n(2 months ago)\nB-tree indexed"]
        end

        subgraph "Cold Chunks (Historical Data)"
            C5["Chunk: 2025-W52\nColumnar compressed\n20–100× storage reduction"]
            CN["Chunk: 2025-WN\nColumnar compressed\nAuto-retained per policy"]
        end
    end

    subgraph "Continuous Aggregates Layer"
        CA_HOURLY["sensor_readings_hourly\n(Continuous Aggregate)\n• time_bucket('1 hour', recorded_at)\n• AVG / MIN / MAX / COUNT\n• Per field_id + sensor_type\n• Auto-refreshed on new data"]
        CA_DAILY["sensor_readings_daily\n(Continuous Aggregate)\n• time_bucket('1 day', recorded_at)\n• AVG / MIN / MAX / COUNT\n• GDD accumulation inputs\n• ET₀ calculation inputs"]
    end

    subgraph "Analytics & AI Layer"
        AGG_REPO["SensorAggregationRepository\n• hourly_avg_by_field()\n• daily_stats_by_type()\n• rolling_30d_window()"]
        AI_FE["AI Feature Engineering\n• GDD calculation\n• Vapor Pressure Deficit\n• Soil Water Balance\n• Rolling anomaly windows"]
        DASHBOARD["Dashboard Analytics\n• Sensor trend charts\n• Aggregated time-series\n• Field comparison views"]
    end

    subgraph "Data Retention"
        POLICY["Retention Policy\n• Hot: 90 days full resolution\n• Warm: 1 year compressed\n• Archive: Azure Blob / S3"]
    end

    APP --> HT
    HT --- C1 & C2
    HT --- C3 & C4
    HT --- C5 & CN
    HT -->|"Auto-populates"| CA_HOURLY
    HT -->|"Auto-populates"| CA_DAILY
    CA_HOURLY --> AGG_REPO
    CA_DAILY --> AGG_REPO
    AGG_REPO --> AI_FE
    AGG_REPO --> DASHBOARD
    CN --- POLICY
```

### Key Architectural Observations

- **Chunk exclusion is the performance multiplier.** A query for "last 7 days of soil moisture for field X" touches only 1–2 chunks out of potentially hundreds. Without TimescaleDB, the same query must scan the entire `sensor_readings` table.
- **Continuous aggregates eliminate repeated full-scan analytics.** Instead of computing "average hourly soil moisture" from raw data on every dashboard request, the continuous aggregate materialises the result incrementally.
- **Migration is non-destructive.** `create_hypertable('sensor_readings', 'recorded_at', migrate_data => TRUE)` converts the existing table in-place. Existing data is distributed across initial chunks. No export/re-import cycle is required.
- **Columnar compression is segment-aware.** TimescaleDB's native columnar compression is especially effective for sensor data because readings from the same field and sensor type have high temporal correlation — ideal for run-length and delta encoding.

---

## 12. Future Cassandra Architecture

### Title
AGRIFLOW-AI Future Cassandra Architecture — Distributed IoT Telemetry at Agricultural Scale

### Purpose
Show how Apache Cassandra will provide horizontally scalable, linearly-growing write throughput for AGRIFLOW-AI's sensor telemetry when farm deployments reach thousands of farms and billions of annual sensor readings — beyond what a single PostgreSQL instance can serve.

### Explanation
Cassandra's data model is designed for the access patterns AGRIFLOW-AI already uses. The primary access pattern — "all readings for a field, newest first" — maps exactly to Cassandra's partition + clustering key model: `PARTITION KEY (field_id)` with `CLUSTERING ORDER BY (recorded_at DESC)`. A secondary table enables "all readings of a given sensor type across all fields" — a cross-field analytics access pattern.

```mermaid
graph TB
    subgraph "Application Layer"
        WRITE_SVC["SensorReadingWriteService\n(unchanged)"]
        READ_SVC["SensorReadingQueryService\n(unchanged)"]
    end

    subgraph "Repository Layer (Injected via deps.py)"
        PG_REPO["SensorReadingWriteRepository\n(PostgreSQL — write source of truth)"]
        CASS_REPO["SensorReadingCassandraRepository\n(Cassandra — read replica)\n• list_by_field(field_id)\n• latest_by_type(field_id, sensor_type)\n• get_by_id(reading_id)"]
    end

    subgraph "Redpanda — Migration Bridge"
        EVENT["sensor.readings.created\nevent stream"]
        PROJECTOR["Cassandra Projector\n• Subscribes to Redpanda\n• Dual-writes to both tables\n• Idempotent on reading_id"]
    end

    subgraph "Cassandra Cluster (3-Node Minimum)"
        subgraph "Data Center: Primary"
            N1["Node 1\nToken range: 0–33%"]
            N2["Node 2\nToken range: 33–66%"]
            N3["Node 3\nToken range: 66–100%"]
        end
        subgraph "Data Center: Replica (DR)"
            N4["Node 4 (Replica)"]
            N5["Node 5 (Replica)"]
            N6["Node 6 (Replica)"]
        end

        TABLE1["sensor_readings_by_field\nPARTITION KEY: (field_id)\nCLUSTERING: recorded_at DESC\nCompaction: TWCS 7-day windows"]
        TABLE2["sensor_readings_by_type\nPARTITION KEY: (sensor_type)\nCLUSTERING: recorded_at DESC, field_id\nFor: cross-field analytics"]
    end

    subgraph "Scaling Characteristics"
        SCALE["Linear Horizontal Scaling\n• Add node → capacity increases linearly\n• No single point of failure\n• Multi-datacenter replication\n• Tunable consistency (QUORUM)"]
    end

    WRITE_SVC --> PG_REPO
    PG_REPO -->|"INSERT (source of truth)"| EVENT
    EVENT --> PROJECTOR
    PROJECTOR -->|"INSERT (async)"| TABLE1
    PROJECTOR -->|"INSERT (async)"| TABLE2

    READ_SVC --> CASS_REPO
    CASS_REPO --> TABLE1
    CASS_REPO --> TABLE2

    N1 & N2 & N3 --- TABLE1
    N1 & N2 & N3 --- TABLE2
    N4 & N5 & N6 -.->|"Replication Factor: 3"| N1 & N2 & N3

    TABLE1 & TABLE2 --- SCALE
```

### Key Architectural Observations

- **Cassandra's partition model maps directly to existing access patterns.** The compound index `(field_id, recorded_at)` on PostgreSQL's `sensor_readings` table was architecturally equivalent to Cassandra's `PARTITION KEY (field_id) CLUSTERING recorded_at DESC`. No access-pattern redesign is required.
- **TimeWindowCompactionStrategy (TWCS) is the correct compaction for time-series.** TWCS groups SSTables into time windows (7 days default) and compacts within windows only. This prevents old data from being recompacted when new data arrives — essential for append-heavy workloads.
- **PostgreSQL remains the write source of truth.** Cassandra is introduced as an async read replica via Redpanda projections. This ensures no data loss if Cassandra is unavailable during a write burst — reads degrade gracefully to the PostgreSQL write store.
- **Service and API layers are completely isolated from this change.** The only modification required at integration time is swapping the repository injection in `deps.py`.

---

## 13. Future Temporal Workflow Architecture

### Title
AGRIFLOW-AI Future Temporal Workflow Architecture — Durable Agricultural Process Orchestration

### Purpose
Show how Temporal will orchestrate complex, long-running, stateful agricultural processes that span minutes to days — including soil moisture alert evaluation, yield prediction pipelines, irrigation scheduling, and satellite imagery processing — with guaranteed durability and exactly-once execution semantics.

### Explanation
Temporal is a workflow orchestration engine that persists workflow state durably. If a workflow's worker dies mid-execution, Temporal replays the workflow history to reconstruct state and continues from where it left off. This is the correct solution for agricultural processes that involve: waiting (soil moisture deficit persists for 15 minutes before alerting), retrying (external weather API may be temporarily unavailable), and coordinating (irrigation recommendation requires yield prediction + soil moisture + weather forecast).

```mermaid
graph TB
    subgraph "Trigger Layer"
        SENSOR_EVENT["SensorReadingCreated Event\n(Redpanda)"]
        SCHEDULED["Scheduled Triggers\n• Daily yield forecast\n• Weekly disease risk\n• Monthly soil health"]
        MANUAL["Manual Triggers\n• Operator request\n• API trigger endpoint"]
    end

    subgraph "Temporal Server"
        TS["Temporal Service\n• Workflow execution history\n• Durable state persistence\n• Timer service\n• Task queue management"]
        subgraph "Task Queues"
            Q1["alerts\ntask queue"]
            Q2["yield-prediction\ntask queue"]
            Q3["irrigation\ntask queue"]
            Q4["satellite\ntask queue"]
        end
    end

    subgraph "Workflow Definitions"
        W1["SoilMoistureAlertWorkflow\n1. Receive low moisture reading\n2. sleep(15 minutes)\n3. Check if condition persists\n4. If persists: create irrigation rec\n5. Notify operator\n6. Wait for acknowledgement\n7. Auto-escalate after 2h TTL"]

        W2["YieldPredictionWorkflow\n1. Collect crop features\n2. Collect soil features\n3. Collect 30d weather window\n4. Collect 30d sensor window\n5. Call inference service\n6. Write prediction to CropRecord\n7. Notify via GaaS"]

        W3["IrrigationScheduleWorkflow\n1. Compute soil water balance\n2. Retrieve weather forecast\n3. Compute ET₀ projection\n4. Determine irrigation volume\n5. Schedule irrigation event\n6. Monitor execution\n7. Record IrrigationEvent"]

        W4["SatelliteProcessingWorkflow\n1. Poll satellite API for new imagery\n2. Download scene for field boundary\n3. Compute NDVI / EVI\n4. Detect vegetation anomalies\n5. Update SatelliteObservation\n6. Trigger disease risk assessment"]
    end

    subgraph "Activity Workers"
        ACT["Temporal Activity Functions\n• get_latest_soil_moisture()\n• create_irrigation_recommendation()\n• call_inference_service()\n• send_operator_notification()\n• fetch_weather_forecast()\n• download_satellite_imagery()\n• compute_ndvi()"]
    end

    subgraph "AGRIFLOW-AI Services"
        AGRIFLOW["AGRIFLOW-AI Domain APIs\n• SensorReadingService\n• WeatherRecordService\n• CropService\n• IrrigationEventService (Phase 8)\n• YieldRecordService (Phase 9)\n• DiseaseObservationService (Phase 10)\n• SatelliteObservationService (Phase 11) ✅"]
    end

    SENSOR_EVENT -->|"SOIL_MOISTURE below threshold"| Q1
    SCHEDULED -->|"Daily"| Q2
    SCHEDULED -->|"Daily"| Q3
    MANUAL -->|"On demand"| Q4

    Q1 --> W1
    Q2 --> W2
    Q3 --> W3
    Q4 --> W4

    W1 & W2 & W3 & W4 -->|"Execute activities"| ACT
    ACT -->|"Call domain APIs"| AGRIFLOW
    TS -->|"Coordinates"| Q1 & Q2 & Q3 & Q4
```

### Key Architectural Observations

- **Temporal solves the "orchestration without orchestrator" problem.** Without Temporal, `SensorReadingService` would need to implement timers, retries, and state persistence manually — a distributed systems problem that dwarfs the agricultural domain logic.
- **Workflows are pure business logic.** `SoilMoistureAlertWorkflow.run()` reads exactly like the agricultural decision process it models: wait, check, recommend, notify, escalate. The durability mechanism is invisible to the workflow author.
- **`SensorReadingService` is the only integration point.** The Temporal client is injected optionally into `SensorReadingService`. The extension point comment in Phase 7 (`# Temporal workflow initiation`) identifies the exact line where this integration wires in.
- **Long-running agricultural timescales are natural.** `YieldPredictionWorkflow` may take hours to complete if external data services are slow. `SatelliteProcessingWorkflow` may wait days for cloud-free imagery. Temporal handles these timescales natively; HTTP request timeouts cannot.

---

## 14. Future Digital Twin Architecture

### Title
AGRIFLOW-AI Future Digital Twin Architecture — Virtual Farm Intelligence Platform

### Purpose
Create a comprehensive architecture showing the complete Digital Twin stack for AGRIFLOW-AI: from physical farm sensors and satellite imagery through a continuously updated virtual model to AI simulation, prediction, and autonomous decision layers.

### Explanation
A Digital Twin is a live, continuously updated virtual representation of a physical entity. In agriculture, a Digital Twin of a field mirrors the field's current state: soil moisture, crop growth stage, disease risk, nutrient levels, weather conditions — updated in real-time as new sensor readings and satellite observations arrive. The AI layer runs against the twin's state to generate predictions and recommendations without needing to query the raw time-series data each time.

```mermaid
graph TB
    subgraph "Physical World — Real Farm"
        FARM_PHYS["🏚 Physical Farm\n• Soil composition\n• Topography\n• Infrastructure"]
        FIELD_PHYS["🌾 Physical Fields\n• Growing crops\n• Soil moisture gradients\n• Pest/disease vectors"]
        SENSORS_PHYS["📡 IoT Sensors (in-field)\n• Soil moisture probes\n• Air/soil temperature\n• Leaf wetness\n• EC conductivity"]
        SATELLITE_PHYS["🛰 Satellites\n• Sentinel-2 (optical)\n• SAR (all-weather)\n• Planet Labs (daily)"]
        WEATHER_PHYS["🌦 Weather Stations\n• Automated field stations\n• Nearby meteorological\n• Global NWP models"]
    end

    subgraph "Data Synchronization Layer"
        IOT_INGEST["IoT Ingestion\n• REST API gateway\n• Redpanda: sensor.readings.created"]
        SAT_INGEST["Satellite Processor\n• Scene download\n• NDVI / EVI computation\n• Cloud mask filtering"]
        WEATHER_INGEST["Weather Sync\n• Historical records\n• Forecast integration\n• NWP downscaling"]
    end

    subgraph "Digital Twin Core — Farm Twin"
        FARM_TWIN["🔷 Farm Digital Twin\n• Farm-level aggregate state\n• Cross-field risk summary\n• Resource allocation view\n• Financial performance model"]

        subgraph "Field Twins"
            FIELD_TWIN["🔷 Field Digital Twin\n• field_id: UUID\n• farm_id: UUID\n• last_updated: TIMESTAMPTZ\n────────────────────\nSensor State:\n• soil_moisture: float\n• soil_temperature: float\n• air_temperature: float\n• air_humidity: float\n• leaf_wetness: float\n• electrical_conductivity: float\n────────────────────\nAI Inference State:\n• yield_prediction_tons_ha: float\n• disease_risk_score: float\n• irrigation_recommendation: str\n────────────────────\nOperational State:\n• active_crop: str\n• growth_stage: str\n• days_to_harvest: int"]

            CROP_TWIN["🌱 Crop Twin\n• Current growth stage\n• GDD accumulated\n• Predicted harvest date\n• Stress indicators"]

            SOIL_TWIN["🪨 Soil Twin\n• Current NPK state\n• pH trend\n• Moisture balance\n• Salinity monitoring"]

            WEATHER_TWIN["🌦 Weather Twin\n• Current conditions\n• 7-day forecast\n• ET₀ calculation\n• Accumulated GDD"]

            SENSOR_TWIN["📡 Sensor Twin\n• Latest per-type readings\n• Sensor health status\n• Battery monitoring\n• Calibration state"]

            SAT_TWIN["🛰 Satellite Twin\n• Latest NDVI\n• EVI trend\n• Anomaly zones\n• Vegetation stress map"]
        end
    end

    subgraph "Twin State Store"
        REDIS["Redis\n• Hot field twin state\n• Sub-millisecond read\n• TTL-managed freshness"]
        CASSANDRA_DT["Cassandra\n• Twin state history\n• Point-in-time queries\n• Trend reconstruction"]
    end

    subgraph "AI Layer — Twin Consumers"
        SIMULATION["Simulation Engine\n• 'What if' scenarios\n• Irrigation impact model\n• Fertilization response\n• Climate stress testing"]
        PREDICTION["Prediction Engine\n• 30-day yield forecast\n• Disease outbreak probability\n• Soil degradation trajectory\n• Optimal harvest window"]
        DECISION["Autonomous Decision Layer\n• Irrigation auto-scheduling\n• Pest intervention triggers\n• Yield optimization actions\n• Alert escalation rules"]
    end

    subgraph "Delivery Interfaces"
        DASH_DT["Farm Twin Dashboard\n• Real-time field state view\n• Stress heatmaps\n• Prediction overlays"]
        GAAS_DT["GaaS Farm Copilot\n• 'What is the current\n  state of Field 5?'\n• Natural language interface"]
        AUTO["Autonomous Systems\n• Variable-rate irrigation\n• Drone dispatch\n• Equipment scheduling"]
    end

    SENSORS_PHYS -->|"HTTPS POST"| IOT_INGEST
    SATELLITE_PHYS -->|"Imagery API"| SAT_INGEST
    WEATHER_PHYS -->|"Station data"| WEATHER_INGEST

    IOT_INGEST -->|"SensorReadingCreated event"| SENSOR_TWIN
    SAT_INGEST --> SAT_TWIN
    WEATHER_INGEST --> WEATHER_TWIN

    SENSOR_TWIN & CROP_TWIN & SOIL_TWIN & WEATHER_TWIN & SAT_TWIN --> FIELD_TWIN
    FIELD_TWIN --> FARM_TWIN

    FIELD_TWIN -->|"Write state"| REDIS
    FIELD_TWIN -->|"Append history"| CASSANDRA_DT

    REDIS & CASSANDRA_DT --> SIMULATION
    REDIS & CASSANDRA_DT --> PREDICTION
    PREDICTION --> DECISION

    SIMULATION & PREDICTION & DECISION --> DASH_DT
    SIMULATION & PREDICTION & DECISION --> GAAS_DT
    DECISION --> AUTO

    FARM_PHYS -.->|"mirrors"| FARM_TWIN
    FIELD_PHYS -.->|"mirrors"| FIELD_TWIN
```

### Key Architectural Observations

- **The Digital Twin is a read model, not a new source of truth.** The source of truth remains the AGRIFLOW-AI domain databases (PostgreSQL for operational data, TimescaleDB for sensor time-series). The twin is a materialized projection optimized for instant state queries.
- **Redis serves the hot path.** Any query for "current field state" hits Redis with sub-millisecond latency. This enables the AI inference layer, dashboard, and GaaS to read field state without touching the database.
- **`SensorType` enum alignment was strategic.** The 11 values in `app/core/enums.py` (`SOIL_MOISTURE`, `SOIL_TEMPERATURE`, `AIR_TEMPERATURE`, etc.) map directly to `FieldDigitalTwin` state properties. This alignment was intentional in Phase 7 and requires no refactoring at Digital Twin integration time.
- **The Simulation Layer enables prescriptive agriculture.** "What happens to yield prediction if we irrigate Field 5 today with 30mm?" can be answered by running the prediction engine against a modified twin state — without touching real data.
- **Autonomous Decision Layer completes the autonomy stack.** At Phase 15+, the system can initiate irrigation, dispatch drones, and adjust equipment schedules without operator intervention — based on the digital twin's current state and the prediction engine's output.

---

## 15. Future GaaS Architecture

### Title
AGRIFLOW-AI Future GaaS Architecture — Generative-As-A-Service Agricultural Intelligence

### Purpose
Show the complete Generative-As-A-Service layer that transforms AGRIFLOW-AI from a data platform into a conversational agricultural intelligence system, where farmers and agronomists can ask natural language questions and receive contextual, data-grounded recommendations.

### Explanation
GaaS (Generative-As-A-Service) is AGRIFLOW-AI's LLM-powered intelligence interface. A Farm Copilot agent receives natural language queries, decomposes them into tool calls against the AGRIFLOW-AI API surface (already fully structured and documented via FastAPI's OpenAPI spec), retrieves current context from the Digital Twin, queries agricultural knowledge from a vector store, and synthesises a recommendation using an LLM. The result is a data-grounded, explainable recommendation — not hallucination.

```mermaid
graph TB
    subgraph "User Interaction Layer"
        FARMER["👩‍🌾 Farm Operator\n'Should I irrigate Field 5 today?'"]
        AGRO["🧑‍🔬 Agronomist\n'Analyze disease risk for my\nwheat crop in Field 3'"]
        MANAGER["👔 Farm Manager\n'Forecast this season yield\nacross all my fields'"]
        MOBILE_APP["Farm Mobile App"]
        WEB_DASH["Web Dashboard\nCopilot Chat Panel"]
    end

    subgraph "GaaS Orchestration Layer"
        COPILOT["🤖 Farm Copilot Agent\n(LangChain / LangGraph)\n• Query intent classification\n• Multi-step tool planning\n• Context window management\n• Response synthesis"]

        subgraph "Advisor Agents"
            YIELD_ADV["🌾 Yield Advisor\n• Harvest predictions\n• Season comparisons\n• Market timing advice"]
            DISEASE_ADV["🦠 Disease Advisor\n• Risk assessment\n• Treatment recommendations\n• Outbreak probability"]
            IRR_ADV["💧 Irrigation Advisor\n• Water budget analysis\n• Schedule optimization\n• Deficit irrigation strategies"]
            SOIL_ADV["🪨 Soil Advisor\n• Nutrient recommendations\n• pH management\n• Amendment schedules"]
        end
    end

    subgraph "Tool Layer — AGRIFLOW-AI APIs"
        T1["get_field_sensor_readings()\n→ GET /fields/{id}/sensor-readings"]
        T2["get_field_digital_twin()\n→ Digital Twin State (Redis)"]
        T3["get_yield_prediction()\n→ AI Inference Service"]
        T4["get_weather_records()\n→ GET /fields/{id}/weather-records"]
        T5["get_soil_profile()\n→ GET /fields/{id}/soil-profile"]
        T6["get_crop_status()\n→ GET /fields/{id}/crops"]
        T7["get_disease_risk()\n→ AI Disease Risk Score"]
        T8["get_satellite_observations()\n→ GET /fields/{id}/satellite"]
    end

    subgraph "Knowledge Layer"
        VECTOR["Vector Knowledge Base\n(Azure AI Search / Pinecone)\n• Agronomic best practices\n• Crop disease database\n• Irrigation manuals\n• Regional climate guides\n• Pesticide regulations"]
        RAG["RAG Pipeline\n• Semantic similarity search\n• Context retrieval\n• Source attribution\n• Confidence scoring"]
    end

    subgraph "LLM Layer"
        LLM["LLM Provider\n• GPT-4o (OpenAI)\n• Claude 3.5 Sonnet (Anthropic)\n• Azure OpenAI Service\n• Model router by task type"]
        GUARDRAILS["Safety Guardrails\n• Agri domain validation\n• Hallucination detection\n• Source verification\n• Regulatory compliance check"]
    end

    subgraph "AGRIFLOW-AI Data Platform"
        API_LAYER["AGRIFLOW-AI FastAPI\nAll domain APIs"]
        DT_STORE["Digital Twin Store\n(Redis / Cassandra)"]
        AI_MODELS["AI Model Registry\n• Yield prediction\n• Disease risk\n• Irrigation optimizer"]
    end

    FARMER & AGRO & MANAGER --> MOBILE_APP & WEB_DASH
    MOBILE_APP & WEB_DASH --> COPILOT

    COPILOT --> YIELD_ADV & DISEASE_ADV & IRR_ADV & SOIL_ADV

    COPILOT -->|"Tool calls"| T1 & T2 & T3 & T4 & T5 & T6 & T7 & T8

    T1 & T4 & T5 & T6 & T8 --> API_LAYER
    T2 --> DT_STORE
    T3 & T7 --> AI_MODELS

    COPILOT -->|"Semantic search"| RAG
    RAG --> VECTOR

    COPILOT -->|"Synthesis prompt"| LLM
    LLM --> GUARDRAILS
    GUARDRAILS -->|"Grounded recommendation"| COPILOT

    COPILOT -->|"Natural language response\n+ data citations"| MOBILE_APP & WEB_DASH
```

### Key Architectural Observations

- **The AGRIFLOW-AI REST API is already GaaS-ready.** FastAPI's auto-generated OpenAPI specification (`/docs`) is immediately consumable as an LLM tool manifest. No separate API wrapper layer is required.
- **RAG prevents hallucination in the agricultural domain.** An LLM without retrieval augmentation may invent pesticide dosages or irrigation thresholds. RAG grounds every recommendation in the vector knowledge base (which contains verified agronomic publications).
- **Specialized advisor agents are preferable to a single generalist agent.** The `YieldAdvisor`, `DiseaseAdvisor`, and `IrrigationAdvisor` agents carry domain-specific system prompts and tool subsets, reducing token cost and improving focus.
- **Source attribution is a trust requirement.** Farm operators acting on AI recommendations need to know whether a recommendation is based on sensor data from today, agronomic research from 2023, or AI inference. The GaaS layer must surface citations in every response.
- **Azure OpenAI Service is the preferred LLM deployment** for enterprise and cooperative customers with data sovereignty requirements. Data does not leave the Azure tenancy when using Azure OpenAI.

---

## 16. AGRIFLOW Target State Architecture — Phase 15 Vision

### Title
AGRIFLOW-AI Phase 15 Enterprise Target State — Complete Autonomous Agricultural Intelligence Platform

### Purpose
Present the final strategic vision for AGRIFLOW-AI as a complete enterprise-grade autonomous agricultural intelligence platform. This diagram is the "north star" architecture that every phase decision points toward.

### Explanation
Phase 15 represents the completion of AGRIFLOW-AI's evolutionary arc from Reactive Farming through Data-Driven, Predictive, and Intelligent Farming to Autonomous Agriculture. Every component in this diagram traces directly to an architectural decision made in Phases 1–7 or documented in the roadmap. The architecture integrates operational data management, real-time telemetry, event-driven intelligence, Digital Twin modeling, AI prediction, and Generative AI into a single coherent enterprise platform.

```mermaid
graph TB
    subgraph "Users & Clients"
        FARMERS["👩‍🌾 Farm Operators"]
        AGROS["🧑‍🔬 Agronomists"]
        COOPS["🏢 Agricultural Cooperatives"]
        ANALYSTS["📊 Data Analysts"]
        MACHINES["🤖 Autonomous Machines"]
    end

    subgraph "Frontend Layer"
        REACT["React + TypeScript\nFarm Management Dashboard\n• Field map view\n• Crop lifecycle tracking\n• Sensor telemetry charts\n• Recommendation feed"]
        MOBILE["Mobile App\n• Farm Copilot chat\n• Push alerts\n• Field inspection logs"]
        COPILOT_UI["Farm Copilot\nConversational AI Interface\nGaaS Layer"]
    end

    subgraph "API Gateway Layer"
        GATEWAY["API Gateway\n(Azure API Management)\n• Rate limiting\n• JWT authentication\n• API versioning\n• Request routing"]
    end

    subgraph "Domain API Services (FastAPI)"
        CORE_APIS["Core Domain APIs\n• Farm API\n• Field API\n• Crop API\n• Soil Profile API\n• Weather Record API\n• Sensor Reading API"]
        EXT_APIS["Extended Domain APIs\n• Irrigation API (Ph.8)\n• Yield Record API (Ph.9)\n• Disease Observation API (Ph.10)\n• Satellite Observation API (Ph.11) ✅"]
        AI_APIS["AI Service APIs\n• Yield Prediction API\n• Disease Risk API\n• Irrigation Recommendation API\n• Digital Twin State API"]
        GAAS_API["GaaS API\n• Farm Copilot endpoint\n• Advisor agent endpoints\n• RAG query endpoint"]
    end

    subgraph "Workflow Orchestration"
        TEMPORAL["Temporal\n• SoilMoistureAlertWorkflow\n• YieldPredictionWorkflow\n• IrrigationScheduleWorkflow\n• SatelliteProcessingWorkflow\n• DiseaseRiskWorkflow"]
    end

    subgraph "Event Streaming Layer"
        REDPANDA["Redpanda Cluster\nTopics:\n• sensor.readings.created\n• weather.records.created\n• crop.status.updated\n• ai.inference.completed\n• satellite.scene.processed\n• irrigation.event.executed\n• anomaly.detected\n• alert.escalated"]
    end

    subgraph "AI & ML Platform"
        INFERENCE["Inference Engine\n(FastAPI + ONNX)\n• Yield prediction model\n• Disease risk model\n• Irrigation optimizer\n• Anomaly detector"]
        MLOPS["MLOps Platform\n(MLflow / Azure ML)\n• Model registry\n• Experiment tracking\n• A/B model testing\n• Drift monitoring"]
        FEATURE_STORE["Feature Store\n• GDD accumulation\n• ET₀ vectors\n• Rolling sensor windows\n• NDVI trend features"]
        LLM_LAYER["LLM Platform\n(Azure OpenAI)\n• GPT-4o\n• Embedding models\n• Moderation API"]
    end

    subgraph "Digital Twin Platform"
        DT_ENGINE["Digital Twin Engine\n• FieldDigitalTwin state machine\n• Real-time sensor state updates\n• AI inference write-back\n• Simulation runner"]
        REDIS_DT["Redis\nHot Twin State\n(sub-ms reads)"]
    end

    subgraph "Knowledge Platform"
        VECTOR_DB["Vector Database\n(Azure AI Search)\n• Agronomic publications\n• Disease encyclopaedia\n• Crop management guides\n• Regulatory documents"]
        RAG_ENGINE["RAG Engine\n• Semantic retrieval\n• Context assembly\n• Citation tracking"]
    end

    subgraph "Primary Storage Layer"
        PG["PostgreSQL 17\n(Operational Store)\n• farms / fields / crops\n• soil_profiles\n• weather_records\n• domain entities"]
        TSDB["TimescaleDB\n(Time-Series Store)\n• sensor_readings hypertable\n• Continuous aggregates\n• Columnar compression"]
        CASSANDRA["Apache Cassandra\n(Scale-Out Store)\n• Billions of sensor readings\n• Partition: field_id\n• Clustering: recorded_at DESC"]
    end

    subgraph "External Data Sources"
        SATELLITE["🛰 Satellite Systems\n• Sentinel-2 / Landsat\n• Planet Labs\n• Copernicus Services"]
        IOT_DEVICES["📡 IoT Device Network\n• In-field sensor arrays\n• Weather stations\n• Irrigation controllers\n• Drone telemetry"]
        WEATHER_EXT["🌦 External Weather\n• Open-Meteo\n• Tomorrow.io\n• National Met Services"]
    end

    subgraph "Infrastructure Platform"
        DOCKER["Docker / Kubernetes\n(Azure AKS)\nContainer orchestration"]
        MONITORING["Observability\n• Azure Monitor\n• Datadog\n• Structlog → ELK"]
        BLOB["Azure Blob Storage\n• Satellite imagery\n• ML model artifacts\n• Data lake archives"]
    end

    FARMERS & AGROS & COOPS --> REACT
    ANALYSTS --> REACT
    FARMERS & AGROS --> MOBILE
    FARMERS & AGROS & COOPS --> COPILOT_UI
    MACHINES --> GATEWAY

    REACT & MOBILE & COPILOT_UI --> GATEWAY

    GATEWAY --> CORE_APIS & EXT_APIS & AI_APIS & GAAS_API

    CORE_APIS & EXT_APIS -->|"Writes"| PG
    CORE_APIS -->|"Sensor writes"| TSDB
    CORE_APIS -->|"Publish events"| REDPANDA

    REDPANDA -->|"Triggers workflows"| TEMPORAL
    REDPANDA -->|"Updates twin"| DT_ENGINE
    REDPANDA -->|"Projects reads"| CASSANDRA
    REDPANDA -->|"Feeds features"| FEATURE_STORE

    DT_ENGINE --> REDIS_DT
    AI_APIS --> INFERENCE
    INFERENCE --> FEATURE_STORE
    INFERENCE --> MLOPS

    GAAS_API --> LLM_LAYER
    GAAS_API --> RAG_ENGINE
    RAG_ENGINE --> VECTOR_DB
    GAAS_API --> REDIS_DT

    AI_APIS --> REDIS_DT

    TSDB & CASSANDRA & PG --> FEATURE_STORE

    IOT_DEVICES -->|"HTTPS POST"| GATEWAY
    SATELLITE --> EXT_APIS
    WEATHER_EXT --> CORE_APIS

    CORE_APIS & EXT_APIS & AI_APIS --> DOCKER
    DOCKER --> MONITORING
    MLOPS --> BLOB
    SATELLITE -.->|"imagery stored in"| BLOB
```

### Platform Capability Summary at Phase 15

```mermaid
graph LR
    subgraph "Evolution Arc"
        P1["Phase 1–2\nReactive Farming\n• Farm & Field records\n• Manual data entry\n• Basic CRUD APIs"]
        P2["Phase 3–5\nData-Driven Farming\n• Crop lifecycle tracking\n• Soil intelligence\n• Weather observation"]
        P3["Phase 6–7\nPredictive Foundation\n• AI-ready attributes\n• IoT telemetry\n• Immutable sensor data"]
        P4["Phase 8–11\nPredictive Farming\n• Irrigation tracking ✅\n• Yield records ✅\n• Disease observation ✅\n• Satellite observation ✅"]
        P5["Phase 12–14\nIntelligent Farming\n• AI yield prediction\n• Disease risk scoring\n• Irrigation optimization\n• Digital Twin v1"]
        P6["Phase 15+\nAutonomous Agriculture\n• Full Digital Twin\n• GaaS Farm Copilot\n• Event-driven platform\n• Autonomous actions"]
    end

    P1 --> P2 --> P3 --> P4 --> P5 --> P6
```

### Key Architectural Observations

- **Every component traces to a Phase 1–10 architectural decision.** The UUID primary key strategy enables Digital Twin state keys. The `AuditableModel` timestamps enable time-series analytics. The `app/core/enums.py` shared enum module enables Digital Twin sensor state mapping and disease severity classification. No foundational refactoring is required at Phase 15.
- **Redpanda is the central integration fabric.** Every major platform capability — Digital Twin, AI Feature Store, CQRS, Temporal, Alert Engine — connects to the platform via Redpanda topics. This ensures the core domain APIs remain stable as new consumers are added.
- **The five-layer Clean Architecture scales to Phase 15 without modification.** Completed domains (Irrigation ✅, Yield ✅, Disease Observation ✅, Satellite Observation ✅) follow the same `Model → Schema → Repository → Service → Router` pattern established in Phase 2. The only additions are Redpanda publishing in the service layer and Temporal workflow triggering at the extension point.
- **Azure is the preferred infrastructure platform** for enterprise and cooperative deployments due to Azure OpenAI Service data sovereignty, Azure Kubernetes Service (AKS) orchestration, Azure API Management gateway, and Azure AI Search vector capabilities — all available within a single Azure tenancy.
- **GaaS is the ultimate user interface.** The Phase 15 Farm Copilot makes the entire platform accessible to farm operators who have no interest in dashboards, APIs, or ML model outputs — they simply ask what they need to know and receive a grounded, cited, actionable recommendation.

---

## Document Notes

**Diagram Rendering:** All diagrams in this document are authored in Mermaid syntax and render natively in GitHub Markdown, GitLab Markdown, Notion, and any Mermaid-compatible viewer.

**Architecture Alignment:** Every diagram in this document is grounded in the decisions documented in:
- `docs/08-phase-architecture-handbook.md` — primary source of architectural decisions
- `docs/06-roadmap.md` — phase sequencing and domain roadmap
- `docs/AI_DATA_READINESS_ASSESSMENT.md` — AI coverage assessment and gap analysis

**Living Document:** This document should be updated at the completion of each phase to reflect new domain additions, architectural decisions, and technology adoptions.

**Last Updated:** Phase 11 completion — June 2026

---

*AGRIFLOW-AI Architecture Diagrams — Produced by AGRIFLOW-AI Principal Enterprise Architecture*  
*For implementation history, see `docs/08-phase-architecture-handbook.md`*  
*For phase roadmap, see `docs/06-roadmap.md`*
