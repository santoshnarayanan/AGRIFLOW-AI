# Phase 8 — Irrigation Event Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `235a51cdf901`  
**Revises:** `a8f3d1b6e924` (Phase 7 — sensor_readings)

---

## What This Phase Achieved

Phase 8 introduced the IrrigationEvent domain — AGRIFLOW-AI's first **operational event** domain. An IrrigationEvent captures a discrete irrigation action applied to a field: when it started, how long it ran, how much water was used, what method was applied, and where the water came from.

Three architectural decisions were established here:

1. **Field-anchored, not crop-anchored.** Irrigation is a field-level operation — you irrigate a field, not a specific crop. This mirrors SensorReading (Phase 7) and WeatherRecord (Phase 5), all of which anchor on Field.
2. **Mutable (PATCH permitted).** Unlike the append-only SensorReading, irrigation events are operator-entered records that may need correction. Operators can update volume, duration, or method after the event is logged.
3. **Composite primary key for TimescaleDB compatibility.** The ORM model uses `(id, started_at)` as a composite PK (ADR-002 Strategy A), making the table ready for hypertable promotion without schema changes.

---

## Domain Hierarchy After Phase 8

```
Farm
└── Field
     ├── Crop
     │    ├── YieldRecord       (Phase 9)
     │    └── DiseaseObservation (Phase 10)
     ├── SoilProfile            (Phase 4 — one-to-one)
     ├── WeatherRecord          (Phase 5 — time-series)
     ├── SensorReading          (Phase 7 — append-only)
     └── IrrigationEvent        ← introduced (mutable, operational event)
```

---

## Database Changes

**PostgreSQL ENUM type created:** `irrigation_method`

| Value | Description |
|-------|-------------|
| `DRIP` | Slow, targeted emitter delivery — highest efficiency |
| `SPRINKLER` | Overhead spray system |
| `FLOOD` | Basin or border flooding |
| `FURROW` | Channel-guided surface flow |
| `CENTER_PIVOT` | Rotating pivot arm sprinkler |
| `SUBSURFACE` | Below-soil drip tape |
| `MANUAL` | Hand-applied, bucket, or hose |
| `AUTOMATED` | Automated system (method unspecified) |

**PostgreSQL ENUM type created:** `water_source`

| Value |
|-------|
| `GROUNDWATER` |
| `SURFACE_WATER` |
| `RAINWATER` |
| `MUNICIPAL` |
| `RECYCLED_WATER` |

**Table created:** `irrigation_events`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID (PK) | NOT NULL | — | UUID v4 primary key |
| `field_id` | UUID (FK → fields.id, CASCADE) | NOT NULL | — | Parent field |
| `started_at` | TIMESTAMPTZ | NOT NULL | — | Event start — primary time key; part of composite PK for TimescaleDB |
| `ended_at` | TIMESTAMPTZ | NULL | — | Optional end timestamp |
| `duration_minutes` | NUMERIC(8,2) | NULL | — | Independent of `ended_at` — for non-metered system estimates |
| `water_volume_liters` | NUMERIC(10,3) | NULL | — | Nullable for non-metered systems |
| `irrigation_method` | ENUM `irrigation_method` | NOT NULL | — | Drives FAO-56 efficiency coefficients in Phase 12/13 models |
| `water_source` | ENUM `water_source` | NULL | — | Optional provenance |
| `notes` | TEXT | NULL | — | Operator annotations |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-side row creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-side last-updated timestamp |

**Note on `duration_minutes` vs `ended_at`:** These are stored independently because non-metered systems may record a duration without knowing the precise end time, and automated systems may compute duration independently of system clock timestamps.

**Constraints and indexes (3 total):**

| Name | Type | Columns |
|------|------|---------|
| `fk_irrigation_events_field_id` | FK → `fields.id` ON DELETE CASCADE | `field_id` |
| `pk_irrigation_events` | PRIMARY KEY | `id` |
| `ix_irrigation_events_field_id` | B-tree | `field_id` |
| `ix_irrigation_events_started_at` | B-tree | `started_at` |
| `ix_irrigation_events_field_id_started_at` | Compound B-tree | `(field_id, started_at)` |

---

## Phase 12 Upgrade (TimescaleDB)

`irrigation_events` was promoted to a **TimescaleDB hypertable** in Phase 12, partitioned by `started_at`. The composite PK `(id, started_at)` established in this phase was specifically designed to satisfy TimescaleDB's requirement that the partition key column be part of the primary key constraint. Zero schema changes were required at Phase 12.

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fields/{field_id}/irrigation-events` | Log an irrigation event |
| GET | `/api/v1/fields/{field_id}/irrigation-events` | List all events for a field (paginated, max 500) |
| GET | `/api/v1/irrigation-events/{event_id}` | Get a single event |
| PATCH | `/api/v1/irrigation-events/{event_id}` | Partial update |
| DELETE | `/api/v1/irrigation-events/{event_id}` | Delete |

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Field must exist before IrrigationEvent creation | `IrrigationEventService` |
| `started_at` must be timezone-aware | `IrrigationEventService` — `_validate_timezone_aware()` |
| `ended_at`, if provided, must be after `started_at` | `IrrigationEventService` |

---

## Architecture Established

**Operational event pattern** — IrrigationEvent is the first domain that models a discrete operational action (as opposed to a continuous sensor observation). This pattern recurs in any future domain tracking discrete agronomic interventions (fertilizer application, spraying events, etc.).

**FAO-56 ready** — `irrigation_method` values map directly to FAO-56 field application efficiency coefficients used in the Phase 13 irrigation recommendation engine. Without this column, the water balance model cannot apply method-specific efficiency corrections.

**`water_source` nullable** — Not all systems can identify water origin. Null is semantically meaningful: "source unrecorded", not "no water was used."

---

## Business Value

- Complete irrigation history per field for water audit and compliance
- `water_volume_liters` × `irrigation_method` efficiency → actual soil water input for FAO-56 models
- Foundation for Phase 13 irrigation over/under-application alert engine
- Phase 14 `IrrigationEventLogged` domain event insertion point identified in service layer

---

## What Was Deferred

- Real-time irrigation scheduling (Phase 14)
- Soil water balance calculation (Phase 13 Recommendation engine)
- Integration with smart irrigation controller APIs
- Automated API tests
