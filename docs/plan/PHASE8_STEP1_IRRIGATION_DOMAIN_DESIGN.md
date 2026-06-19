# Phase 8 – Step 1: Irrigation Domain Design

**Document:** Phase 8 – Step 1  
**Date:** June 2026  
**Author:** AGRIFLOW-AI Architecture Team  
**Scope:** IrrigationEvent domain — entity design, validation rules, API surface, and architecture decisions  
**Status:** Design Refined — Ready for Implementation (Step 2+)

---

## 1. Business Problem

The platform currently tracks what crop exists, what soil properties exist, what weather occurred, and what sensors reported — but has no record of agricultural interventions. Specifically, there is no way to record:

- When irrigation occurred on a field
- How much water was applied
- How long irrigation lasted
- Which irrigation method was used
- What water source was drawn from

Without this, the AI Data Readiness Assessment identifies Irrigation Optimization coverage at only **25%** after Phase 5. Phase 8 introduces `IrrigationEvent` as the first agricultural intervention domain, raising coverage to approximately **72%** (on the path to 92% with P3 soil attribute additions).

Rain-fed cultivation is **not** modeled as an irrigation event. Fields that receive no artificial irrigation are represented by the absence of `IrrigationEvent` records combined with `WeatherRecord.precipitation_mm` — not by a synthetic "rainfed" intervention entry.

---

## 2. Use Cases

- Record an irrigation event when a farm operator activates irrigation on a field
- Record the irrigation method (drip, sprinkler, flood, furrow, center pivot, subsurface, manual, smart)
- Track total water volume applied per event
- Track duration of each irrigation event
- Optionally record the water source drawn from (groundwater, surface water, rainwater, municipal, recycled)
- Retrieve irrigation history for a field ordered by most recent first
- Support FAO-56 water balance model training (volume + duration + method + timing)
- Enable future Digital Twin field water balance state updates (extension point only in Phase 8)
- Provide irrigation history as a feature vector for yield prediction models

---

## 3. Domain Decisions

### 3.1 Field → IrrigationEvent Relationship

`IrrigationEvent` is a **1:N** child of `Field`, identical in cardinality to `WeatherRecord` and `SensorReading`. A field accumulates unlimited irrigation events over its operational life. `field_id` is a non-nullable foreign key.

### 3.2 Editability Decision

`IrrigationEvent` is **mutable** (supports PATCH), unlike `SensorReading` (append-only immutable). Rationale:

- `SensorReading` is machine-generated telemetry — the factual record of what a device reported at a moment in time. Corrections must never alter historical sensor readings.
- `IrrigationEvent` is a **human-logged management action**. A farm operator may need to correct water volume, duration, or method after the fact (e.g., the log was entered from memory; the meter reading was misread). This mirrors the editability model of `WeatherRecord`.
- The AI value of irrigation history depends on accuracy. Permitting corrections increases data quality for model training.

This decision is documented as **ADR-008-01**.

### 3.3 Time-Series Considerations

`IrrigationEvent` is a time-anchored event with a start time and optional end time. The primary time key is `started_at TIMESTAMPTZ NOT NULL`. This column is:

- The partition key for future TimescaleDB hypertable promotion
- The primary ordering key for all list queries (`started_at DESC`)
- The anchor for FAO-56 growing-period irrigation totals

### 3.4 Duration and End Time Strategy

Both `duration_minutes NUMERIC` and `ended_at TIMESTAMPTZ` are **nullable and independent**. A user may supply either, both, or neither:

- Supply only `ended_at`: service calculates a derived display duration
- Supply only `duration_minutes`: service derives an approximate `ended_at` if needed
- Supply both: service validates `ended_at - started_at` is consistent with `duration_minutes` (within tolerance)
- Supply neither: event is recorded as a point event — valid for systems without metered logging

This avoids forcing users to provide data they do not have while maintaining validation coverage when data is provided. Documented as **ADR-008-03**.

### 3.5 Water Volume Strategy

`water_volume_liters NUMERIC(10,3)` is nullable. Some irrigation systems are not metered; some operators estimate rather than measure. Recording the event without volume is preferable to not recording the event. Volume contributes to FAO-56 water balance models when present. Documented as **ADR-008-06**.

### 3.6 Irrigation Method Strategy

`irrigation_method` is a **PostgreSQL ENUM** (`IrrigationMethod`), placed in `app/core/enums.py` following the `SensorType` pattern established in Phase 7. The enum belongs in the shared core module because it will be consumed by the Digital Twin state model, GaaS advisors, and future AI feature engineering.

Proposed values: `DRIP`, `SPRINKLER`, `FLOOD`, `FURROW`, `CENTER_PIVOT`, `SUBSURFACE`, `MANUAL`, `SMART`

**`RAINFED` is explicitly excluded.** Rainfed cultivation is the absence of artificial irrigation, not an irrigation delivery method. Recording a "rainfed" irrigation event would conflate natural precipitation (captured in `WeatherRecord`) with human-initiated water application, polluting FAO-56 water balance calculations and irrigation optimization training data.

Documented as **ADR-008-05**.

### 3.7 Water Source Strategy

`water_source` is a **PostgreSQL ENUM** (`WaterSource`), placed in `app/core/enums.py` alongside `IrrigationMethod`. It replaces the original `VARCHAR(50)` free-text design.

Proposed values: `GROUNDWATER`, `SURFACE_WATER`, `RAINWATER`, `MUNICIPAL`, `RECYCLED_WATER`

**Why normalized enum values over free text:**

- **AI feature engineering:** Water cost models, stress indices, and sustainability scoring require stable categorical inputs. Free-text values (`"well"`, `"Well #3"`, `"ground water"`) fragment into unusable sparse categories.
- **Cross-domain consistency:** Digital Twin resource allocation, GaaS advisor responses, and aggregation queries (`GROUP BY water_source`) depend on a closed value set — identical to the `SensorType` and `IrrigationMethod` pattern.
- **Database integrity:** PostgreSQL ENUM enforcement prevents invalid values at the persistence boundary, matching `CropStatus` and `SensorType` conventions.
- **Internationalization:** Display labels can vary by locale; stored values remain canonical.

`water_source` is **nullable** — operators may not know or track the source for every event. Documented as **ADR-008-09**.

### 3.8 IrrigationEventStatus — Architecture Assessment

**Evaluated values:** `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`

**Decision: Defer to a future Smart Irrigation phase (Option B).**

| Factor | Assessment |
|---|---|
| Phase 8 use cases | Record irrigation that **already occurred** — retrospective operator logging |
| `PLANNED` / `IN_PROGRESS` | Require scheduling workflows, future `started_at`, and controller integration — outside Phase 8 scope |
| `CANCELLED` | Implies a prior scheduling lifecycle that does not exist in Phase 8 |
| Implicit status | Every Phase 8 event represents a completed (or point-in-time) intervention; no status column is required |
| Validation impact | Status introduces state-transition rules, conflicting timestamp validation (`PLANNED` events may legitimately have future `started_at`), and PATCH semantics complexity |
| Future migration path | A nullable `status` column can be added later with `DEFAULT 'COMPLETED'` and backfilled for all existing rows — zero data loss |

Phase 8 establishes the **intervention record**. A future Smart Irrigation phase (post–Phase 14) will introduce `IrrigationEventStatus`, Temporal schedule workflows, and controller-driven `IN_PROGRESS` → `COMPLETED` transitions. Documented as **ADR-008-10**.

### 3.9 source_system — Architecture Assessment

**Evaluated values:** `MANUAL_ENTRY`, `MOBILE_APP`, `IRRIGATION_CONTROLLER`, `SENSOR_AUTOMATION`

**Decision: Defer to a future integration phase (Option B).**

| Factor | Assessment |
|---|---|
| Phase 8 entry path | Single REST API — all events are functionally manual entry |
| Immediate business value | None — without mobile app or controller integrations, every value would be `MANUAL_ENTRY` |
| Phase 7 precedent | `SensorReading` did not introduce `source_system`; provenance deferred until ingestion gateway exists |
| AI provenance | Training data quality scoring benefits from source attribution, but only when multiple ingestion paths exist |
| Future migration path | Column can be added with `DEFAULT 'MANUAL_ENTRY'`; controller integrations populate `IRRIGATION_CONTROLLER` or `SENSOR_AUTOMATION` at ingestion time |

Provenance for Phase 8 is sufficient via `created_at`, `updated_at`, and optional `notes`. Documented as **ADR-008-11**.

---

## 4. Architecture Decisions

The five-layer architecture (`Model → Schema → Repository → Service → Router`) is applied unchanged. Every convention from Phases 2–7 applies:

- `AuditableModel` mixin: UUID v4 PK, `created_at`, `updated_at`
- `Annotated[IrrigationEventService, Depends(get_irrigation_event_service)]` DI alias in `deps.py`
- Domain exceptions declared in the service module (`IrrigationEventNotFoundError`, `InvalidIrrigationTimestampError`, `InvalidIrrigationDurationError`)
- Routers translate domain exceptions to HTTP status codes
- Repositories `flush()` — never `commit()`
- `field_id` excluded from Create schema — resolved from the URL path parameter

---

## 5. Proposed Entity Attributes

| Attribute | PostgreSQL Type | Nullable | Purpose | AI Value | Digital Twin Value |
|---|---|---|---|---|---|
| `id` | UUID | No | Primary key (UUID v4, AuditableModel) | — | Idempotency key for event streaming |
| `field_id` | UUID FK | No | Parent field reference | Feature grouping key | Twin update routing key |
| `started_at` | TIMESTAMPTZ | No | Irrigation start time — primary time key, partition key | FAO-56 period start; GDD + season calendar | Triggers water balance state update in twin |
| `ended_at` | TIMESTAMPTZ | Yes | Irrigation end time — optional, validates against `started_at` | Season-level irrigation schedule reconstruction | Marks end of active irrigation state |
| `duration_minutes` | NUMERIC(8,2) | Yes | Duration in minutes — independent of `ended_at` | Daily/weekly irrigation volume sums; ET₀ offset | Irrigation event duration in twin state |
| `water_volume_liters` | NUMERIC(10,3) | Yes | Total water applied in liters | FAO-56 water balance; irrigation efficiency metric | Field water balance state increment |
| `irrigation_method` | ENUM(IrrigationMethod) | No | Irrigation delivery type | Method-specific efficiency coefficients in irrigation models | Delivery-type classification in twin |
| `water_source` | ENUM(WaterSource) | Yes | Canonical water origin | Water stress, cost, and sustainability modeling | Resource allocation tracking |
| `notes` | TEXT | Yes | Operator free-text annotation | Training data provenance | — |
| `created_at` | TIMESTAMPTZ | No | Audit timestamp (AuditableModel) | Record creation date for data freshness scoring | — |
| `updated_at` | TIMESTAMPTZ | No | Audit timestamp (AuditableModel) | Last-correction date | — |

**`IrrigationMethod` enum values:**

| Value | Description | Typical FAO-56 Efficiency |
|---|---|---|
| `DRIP` | Sub-surface or surface drip/trickle emitters | ~90% |
| `SPRINKLER` | Overhead rotating or fixed sprinklers | ~75% |
| `FLOOD` | Basin or border flood irrigation | ~60% |
| `FURROW` | Row-level furrow / surface irrigation | ~65% |
| `CENTER_PIVOT` | Mechanized center-pivot lateral systems | ~80% |
| `SUBSURFACE` | Subsurface drip or tile drainage reuse | ~90% |
| `MANUAL` | Hand watering, bucket, or hose application | ~50% |
| `SMART` | Sensor-driven or AI-scheduled automated systems | Variable (model-derived) |

**`WaterSource` enum values:**

| Value | Description |
|---|---|
| `GROUNDWATER` | Wells, boreholes, aquifer extraction |
| `SURFACE_WATER` | Rivers, canals, ponds, reservoirs |
| `RAINWATER` | Rainwater harvesting tanks or catchment systems |
| `MUNICIPAL` | Public water supply / treated municipal water |
| `RECYCLED_WATER` | Treated wastewater, drainage reuse, greywater |

---

## 6. Validation Rules

### Schema-Level (Pydantic)

- `started_at`: required, datetime
- `irrigation_method`: required, must be a valid `IrrigationMethod` enum value
- `water_source`: optional, must be a valid `WaterSource` enum value if provided
- `water_volume_liters`: optional, `ge=0` if provided
- `duration_minutes`: optional, `gt=0` if provided

### Service-Level (Business Rules)

| Rule | Error | HTTP |
|---|---|---|
| Field must exist before creation | `FieldNotFoundError` | 404 |
| `started_at` must be timezone-aware | `InvalidIrrigationTimestampError` | 422 |
| `started_at` must not be in the future | `InvalidIrrigationTimestampError` | 422 |
| `ended_at`, if provided, must be timezone-aware | `InvalidIrrigationTimestampError` | 422 |
| `ended_at`, if provided, must be after `started_at` | `InvalidIrrigationDurationError` | 422 |
| `duration_minutes`, if provided, must be `> 0` | `InvalidIrrigationDurationError` | 422 |
| IrrigationEvent must exist before update | `IrrigationEventNotFoundError` | 404 |
| IrrigationEvent must exist before delete | `IrrigationEventNotFoundError` | 404 |

**Validation order for timestamps (mirroring Phase 7 ADR-007-25):** timezone-awareness is validated before future-timestamp comparison. A timezone-naive datetime cannot be safely compared to a UTC-aware datetime.

**Phase 8 default semantics:** All created events represent completed interventions. No status field; no future-dated `started_at` for scheduling purposes.

---

## 7. Repository Query Requirements

### Phase 8 (Required)

| Method | Signature | Purpose |
|---|---|---|
| `create` | `create(data: dict) → IrrigationEvent` | Persist new event |
| `get_by_id` | `get_by_id(id: UUID) → IrrigationEvent \| None` | Single-event lookup |
| `list_by_field` | `list_by_field(field_id: UUID, limit: int, offset: int) → list[IrrigationEvent]` | Paginated field history, `started_at DESC` |
| `update` | `update(id: UUID, data: dict) → IrrigationEvent` | Partial update (PATCH) |
| `delete` | `delete(id: UUID) → bool` | Administrative removal |
| `exists` | `exists(id: UUID) → bool` | Lightweight existence probe |

**Pagination:** `list_by_field` accepts `limit` and `offset` from Phase 8. This follows the `WeatherRecordRepository` pattern and differs from `SensorReadingRepository` (which deferred pagination in Phase 7).

### Future Phase Additions

| Method | Purpose | Phase |
|---|---|---|
| `list_by_field_date_range(field_id, start, end)` | Season-scoped irrigation history for AI model feature windows | Phase 12+ |
| `total_volume_by_field_and_period(field_id, start, end)` | Aggregated water volume for FAO-56 balance calculation | Phase 12+ |
| `count_events_by_method(field_id)` | Method distribution for irrigation optimization model | Phase 14+ |
| `list_by_field_and_status(field_id, status)` | Filter scheduled vs completed events | Smart Irrigation phase |
| `list_by_water_source(field_id, source)` | Resource allocation and sustainability reporting | Phase 12+ |

---

## 8. API Surface Proposal

Following Pattern A (same as `WeatherRecord`) — nested create/list, flat get/update/delete:

| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/api/v1/fields/{field_id}/irrigation-events` | 201 Created | Create a new irrigation event |
| `GET` | `/api/v1/fields/{field_id}/irrigation-events` | 200 OK | List all events for field (`started_at DESC`, paginated) |
| `GET` | `/api/v1/irrigation-events/{irrigation_event_id}` | 200 OK | Retrieve single event |
| `PATCH` | `/api/v1/irrigation-events/{irrigation_event_id}` | 200 OK | Partial update |
| `DELETE` | `/api/v1/irrigation-events/{irrigation_event_id}` | 204 No Content | Administrative removal |

**No `PUT`.** Consistent with all other mutable domains in AGRIFLOW-AI.

**Exception → HTTP mapping:**

| Exception | HTTP Status |
|---|---|
| `FieldNotFoundError` | 404 |
| `IrrigationEventNotFoundError` | 404 |
| `InvalidIrrigationTimestampError` | 422 |
| `InvalidIrrigationDurationError` | 422 |

**URL token:** `irrigation-events` (plural kebab-case, consistent with `weather-records` and `sensor-readings`).

---

## 9. AI Readiness Impact

### Irrigation Optimization Coverage

| Stage | Coverage |
|---|---|
| After Phase 7 | 25% |
| After Phase 8 (IrrigationEvent only) | ~72% |
| After Phase 8 + P3 soil attributes | ~92% |

### Impact by AI Use Case

**Irrigation Optimization (primary, Phase 14 target):**
- `water_volume_liters` + `duration_minutes` provide the historical intervention record required by reinforcement learning and schedule optimization models
- `irrigation_method` provides the efficiency coefficient input for FAO-56 calculations (`DRIP` ≈ 90%, `CENTER_PIVOT` ≈ 80%, `FLOOD` ≈ 60%, `SMART` uses model-derived coefficients)
- `water_source` enables cost-aware optimization (`MUNICIPAL` vs `GROUNDWATER` cost differentials) and sustainability constraints (`RECYCLED_WATER` quotas)
- `started_at` enables season-aggregate irrigation volume computation (ETc vs actual applied water)
- Combined with `SensorReading.SOIL_MOISTURE` time-series, enables pre/post-irrigation soil moisture delta calculation — the core training signal for irrigation optimization models

**Yield Prediction (Phase 12 target):**
- Irrigation timing relative to `Crop.growth_stage` produces crop water stress indicators
- Total seasonal water volume is a direct input to yield response functions (Doorenbos-Kassam FAO-33)
- Irrigation method determines the spatial uniformity of water distribution — a yield variance signal (`CENTER_PIVOT` and `SPRINKLER` have distinct uniformity profiles)

**Disease Prediction (Phase 13 target):**
- `FLOOD` and high-volume irrigation events combined with `SensorReading.LEAF_WETNESS` create the root disease and fungal infection risk signal
- Irrigation-induced waterlogging periods (event volume vs. soil drainage rate) inform anaerobic root zone risk
- `water_source` = `SURFACE_WATER` combined with high-volume events may indicate pathogen introduction risk in certain crop systems

**Digital Twin Water Balance (future — extension point in Phase 8):**
- Each persisted `IrrigationEvent` will eventually trigger a Digital Twin field water balance update: `Θ_after = Θ_before + (volume / (area × depth))`
- The twin's `irrigation_recommendation` field will be updated by the AI inference layer after each event — not in Phase 8

**Precision Agriculture:**
- Normalized `IrrigationMethod` and `WaterSource` enums produce stable one-hot feature vectors without text normalization preprocessing
- `SMART` method events, once controller integrations exist, will correlate with `SensorReading` automation patterns for efficiency benchmarking

---

## 10. Future Extensibility

### TimescaleDB

`irrigation_events.started_at` is `TIMESTAMPTZ NOT NULL` — satisfies TimescaleDB's only structural requirement for hypertable promotion. `create_hypertable('irrigation_events', 'started_at')` converts the table in-place with zero application code changes. Continuous aggregates for weekly/monthly water volume totals — segmented by `irrigation_method` and `water_source` — will serve the AI feature engineering layer.

### Redpanda

The `IrrigationEventService.create_irrigation_event()` method will contain the same documented extension point pattern established in Phase 7 (ADR-007-26). An `IrrigationEventCreated` domain event will be published to topic `irrigation.events.created` after successful persistence. The event payload will include normalized `irrigation_method` and `water_source` enum values for schema-stable downstream consumption. Downstream consumers: Digital Twin water balance updater, AI feature pipeline, CQRS read-model projector.

**Phase 8:** Extension point comment block only — no publisher wired.

### CQRS

Write path: `create`, `update`, `delete` backed by PostgreSQL. Read path: `list_by_field`, aggregation queries backed by TimescaleDB continuous aggregates or Cassandra. The split follows the same incremental migration path documented for `SensorReading` in `docs/08-phase-architecture-handbook.md` Section 14.

Enum-typed dimensions (`irrigation_method`, `water_source`) map cleanly to CQRS read-model materialized views without text normalization at projection time.

**Phase 8:** Single PostgreSQL write/read path only.

### Cassandra

Access pattern maps directly to Cassandra's data model: `PARTITION KEY (field_id)`, `CLUSTERING ORDER BY (started_at DESC)`. A `TimeWindowCompactionStrategy` with 30-day windows is appropriate (irrigation events are lower frequency than sensor readings — monthly rather than hourly windows). Enum columns serialize as text in Cassandra with identical canonical values as PostgreSQL.

**Phase 8:** No Cassandra projection.

### Digital Twin

`IrrigationEvent` attributes map to future `FieldDigitalTwin` state properties:

- `last_irrigation_at` ← `IrrigationEvent.started_at` (most recent)
- `last_irrigation_volume_liters` ← `IrrigationEvent.water_volume_liters`
- `last_irrigation_method` ← `IrrigationEvent.irrigation_method`
- `last_irrigation_water_source` ← `IrrigationEvent.water_source`
- `cumulative_irrigation_liters_season` ← aggregate via Redpanda consumer

When `IrrigationEventStatus` is introduced in the Smart Irrigation phase, the twin's `active_irrigation_state` property will track `IN_PROGRESS` events separately from historical records.

**Phase 8:** No twin state updates — schema only.

### GaaS

The GaaS `IrrigationAdvisor` agent tool `get_irrigation_history(field_id, limit)` will call `GET /api/v1/fields/{field_id}/irrigation-events`. The structured JSON response — with canonical enum values for method and source — is consumed directly by the LLM to answer queries such as: "How much groundwater has Field 5 received this month?" or "What irrigation method am I using on my wheat fields?"

Enum normalization eliminates ambiguous LLM interpretation of free-text water source values.

**Phase 8:** API data layer only — no GaaS agent implementation.

### Smart Irrigation Phase (Deferred Attributes)

The following attributes are reserved for a future Smart Irrigation / integration phase:

| Attribute | Purpose | Trigger Phase |
|---|---|---|
| `status` (`IrrigationEventStatus`) | Schedule lifecycle: PLANNED → IN_PROGRESS → COMPLETED / CANCELLED | Smart Irrigation (post–Phase 14) |
| `source_system` | Ingestion provenance: MANUAL_ENTRY, MOBILE_APP, IRRIGATION_CONTROLLER, SENSOR_AUTOMATION | Integration phase |

Both can be added via Alembic migration with safe defaults and zero breaking changes to the Phase 8 API contract.

---

## 11. Architecture Decision Register

| ADR | Decision |
|---|---|
| **ADR-008-01** | `IrrigationEvent` is mutable — PATCH is permitted because irrigation events are human-logged management actions, not immutable machine telemetry |
| **ADR-008-02** | `started_at TIMESTAMPTZ NOT NULL` is the primary time key — timezone-aware, non-nullable, ordered `DESC` in all list queries |
| **ADR-008-03** | `ended_at` and `duration_minutes` are both nullable and independently optional — either, both, or neither may be supplied; service validates consistency when both are present |
| **ADR-008-04** | `started_at` must be timezone-aware; naive datetimes are rejected with 422 — mirroring ADR-007-25 for all time-series domains |
| **ADR-008-05** | `IrrigationMethod` enum is declared in `app/core/enums.py` — follows the `SensorType` pattern; values are `DRIP`, `SPRINKLER`, `FLOOD`, `FURROW`, `CENTER_PIVOT`, `SUBSURFACE`, `MANUAL`, `SMART`; `RAINFED` is excluded because rainfed is the absence of irrigation, not a delivery method |
| **ADR-008-06** | `water_volume_liters` is nullable — recording an irrigation event without metered volume is preferable to not recording the event |
| **ADR-008-07** | `IrrigationEventService.create_irrigation_event()` contains the future Redpanda / Digital Twin / Temporal extension point — consistent with ADR-007-26; Phase 8 wires comment block only, no publisher |
| **ADR-008-08** | Compound index `(field_id, started_at)` is the primary access index — mirrors the `sensor_readings` compound index strategy for time-series field queries |
| **ADR-008-09** | `water_source` is a nullable `WaterSource` PostgreSQL ENUM in `app/core/enums.py` — normalized values preferred over VARCHAR free text for AI feature stability, aggregation, and cross-domain reuse |
| **ADR-008-10** | `IrrigationEventStatus` is deferred to Smart Irrigation phase — Phase 8 records completed interventions only; status lifecycle requires scheduling workflows not in scope |
| **ADR-008-11** | `source_system` is deferred to integration phase — Phase 8 has a single REST entry path; provenance via audit timestamps is sufficient until controller/mobile integrations exist |

### ADR Alignment Review (Phase 7 and Future Roadmap)

| Concern | Alignment | Notes |
|---|---|---|
| Phase 7 SensorReading patterns | ✅ Aligned | Shared enum in `core/enums.py`, service-layer timestamp validation (ADR-007-25), service as event boundary (ADR-007-26), repository flush-only |
| SensorReading immutability contrast | ✅ Aligned | ADR-008-01 explicitly distinguishes human-logged mutable events from append-only telemetry (ADR-007-27) |
| TimescaleDB | ✅ Aligned | `started_at TIMESTAMPTZ NOT NULL` satisfies hypertable requirement; enum dimensions support continuous aggregate grouping |
| Cassandra | ✅ Aligned | `(field_id, started_at DESC)` partition/clustering key; enum values serialize as stable text |
| Digital Twin | ✅ Aligned | Attribute mapping documented; extension point in service; no twin wiring in Phase 8 |
| GaaS | ✅ Aligned | API returns canonical enums for LLM consumption; agent deferred |
| CQRS / Redpanda | ✅ Aligned | Incremental migration path matches SensorReading; enum payload schema-stable for event streaming |

No existing ADR-008 entries were removed. ADR-008-05 was expanded; ADR-008-09 through ADR-008-11 were added.

---

## 12. Phase 8 Scope Control

Phase 8 delivers the **IrrigationEvent domain data layer only** — persistence, validation, and REST API. The following capabilities are explicitly **out of scope** and remain future roadmap items:

| Capability | Status in Phase 8 | Future Phase |
|---|---|---|
| AI inference / recommendation engine | Not implemented | Phase 14+ |
| Irrigation schedule optimization | Not implemented | Phase 14+ |
| Digital Twin water balance updates | Extension point comment only | Post–Phase 8 twin phase |
| Redpanda event publishing | Extension point comment only | Event infrastructure phase |
| CQRS read-model projection | Not implemented | CQRS migration phase |
| Cassandra time-series projection | Not implemented | Scale-out phase |
| GaaS `IrrigationAdvisor` agent | Not implemented | GaaS phase |
| `IrrigationEventStatus` lifecycle | Not implemented | Smart Irrigation phase |
| `source_system` provenance | Not implemented | Integration phase |
| Irrigation controller / mobile app ingestion | Not implemented | Integration phase |
| TimescaleDB hypertable promotion | Not implemented | Infrastructure phase |

**Phase 8 delivers:**
- `IrrigationEvent` ORM model with `IrrigationMethod` and `WaterSource` enums
- Alembic migration with compound index `(field_id, started_at)`
- Pydantic schemas, repository, service, and REST router
- Full CRUD + paginated field history API
- Service-layer validation and documented Redpanda extension point

**Phase 8 does not deliver:**
- Any runtime integration with external systems
- Any AI model training or inference
- Any event streaming or async downstream processing
- Any read-path optimization beyond PostgreSQL

This scope boundary ensures Step 2 implementation remains focused and testable without premature infrastructure complexity.

---

## Files to Create (Implementation Step 2+)

- `backend/app/core/enums.py` — add `IrrigationMethod` and `WaterSource` enums
- `backend/app/db/models/irrigation_event.py` — ORM model
- `backend/app/db/migrations/versions/007_create_irrigation_events_table.py` — Alembic migration
- `backend/app/schemas/irrigation_event.py` — `IrrigationEventCreate`, `IrrigationEventUpdate`, `IrrigationEventResponse`
- `backend/app/db/repositories/irrigation_event.py` — repository
- `backend/app/services/irrigation_event.py` — service
- `backend/app/api/irrigation_events/router.py` — FastAPI router
- `backend/app/api/deps.py` — add `IrrigationEventServiceDep`
- `backend/app/api/router.py` — register irrigation_events router

---

## Domain Hierarchy After Phase 8

```
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord
     ├── SensorReading
     └── IrrigationEvent    ← Phase 8
```
