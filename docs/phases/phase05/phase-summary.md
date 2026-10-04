# Phase 5 — Weather Intelligence Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `7d4f2a9b1e63`  
**Revises:** `13aabbe35d51` (Phase 4 — soil_profiles table)

---

## What This Phase Achieved

Phase 5 introduced the WeatherRecord domain — AGRIFLOW-AI's first time-series domain. WeatherRecord is a one-to-many, append-oriented table: a Field can have an unbounded number of weather observations, each anchored by a `recorded_at` timestamp.

This phase established the **time-series domain pattern** (timestamp-anchored observations, field-scoped, ordered by time) that was later promoted to TimescaleDB hypertables in Phase 12. The deliberate inclusion of `recorded_at` as a dedicated column and the `ix_weather_records_recorded_at` index were the first steps toward the TimescaleDB partition key strategy formalised in Phase 12 ADR-002.

---

## Domain Hierarchy After Phase 5

```
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     └── WeatherRecord   ← introduced (one-to-many, time-series)
```

---

## Database Changes

**Table created:** `weather_records`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID (PK) | NOT NULL | — | UUID v4 primary key |
| `field_id` | UUID (FK → fields.id) | NOT NULL | — | Parent field |
| `recorded_at` | TIMESTAMPTZ | NOT NULL | — | Observation timestamp — TimescaleDB partition key candidate |
| `temperature_c` | NUMERIC(5,2) | NOT NULL | — | Air temperature in °C |
| `humidity_percent` | NUMERIC(5,2) | NOT NULL | — | Relative humidity % |
| `rainfall_mm` | NUMERIC(8,2) | NOT NULL | `0` | Rainfall in mm; defaults to 0 for partial sensor sets |
| `wind_speed_kmh` | NUMERIC(6,2) | NOT NULL | `0` | Wind speed in km/h; defaults to 0 for partial sensor sets |
| `data_source` | VARCHAR(50) | NOT NULL | `'MANUAL'` | Data provenance: `MANUAL`, `IOT_SENSOR`, `WEATHER_API`, etc. |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-side row creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-side last-updated timestamp |

**Constraints and indexes:**

| Name | Type | Columns | Purpose |
|------|------|---------|---------|
| `fk_weather_records_field_id` | FOREIGN KEY → `fields.id` | `field_id` | Referential integrity |
| `pk_weather_records` | PRIMARY KEY | `id` | Explicit named PK |
| `ix_weather_records_field_id` | B-tree | `field_id` | "All records for a field" query |
| `ix_weather_records_recorded_at` | B-tree | `recorded_at` | "Records within a time window" query |

---

## AI Readiness Columns Added (Phase 6 — added to this table)

Phase 6 (`005_add_p1_ai_readiness_columns.py`, revision `f3a8c1d9e047`) added:

| Column | Type | Purpose |
|--------|------|---------|
| `solar_radiation_wm2` | NUMERIC(8,3) | Solar irradiance in W/m² — required for Penman-Monteith ET₀ calculation |
| `temperature_min_c` | NUMERIC(5,2) | Daily minimum °C — Growing Degree Day (GDD) calculation |
| `temperature_max_c` | NUMERIC(5,2) | Daily maximum °C — GDD calculation |

---

## Phase 12 Upgrade (TimescaleDB)

`weather_records` was converted to a **TimescaleDB hypertable** in Phase 12 (migration `c9d8e7f6a5b4`), partitioned by `recorded_at`. This was possible with zero application code changes because the column and index were designed for it in Phase 5.

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fields/{field_id}/weather-records` | Record a weather observation |
| GET | `/api/v1/fields/{field_id}/weather-records` | List all records for a field (paginated) |
| GET | `/api/v1/weather-records/{weather_record_id}` | Get a single record by ID |
| PATCH | `/api/v1/weather-records/{weather_record_id}` | Partial update (operator correction) |
| DELETE | `/api/v1/weather-records/{weather_record_id}` | Delete a record |

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Field must exist before WeatherRecord creation | `WeatherRecordService.create_weather_record` |
| `recorded_at` cannot be in the future | `WeatherRecordService` — `_validate_not_future()` |
| `humidity_percent` must be in [0, 100] | Pydantic schema validator |
| `rainfall_mm` must be ≥ 0 | Pydantic schema validator |
| `wind_speed_kmh` must be ≥ 0 | Pydantic schema validator |
| Record must exist before update or delete | `WeatherRecordService` |

---

## Architecture Established

**Time-series domain pattern** — the conventions established here were adopted unchanged by SensorReading (Phase 7), IrrigationEvent (Phase 8), YieldRecord (Phase 9), DiseaseObservation (Phase 10), and SatelliteObservation (Phase 11):
- Dedicated `recorded_at TIMESTAMPTZ NOT NULL` column as the primary time key
- Separate B-tree index on `recorded_at` for time-range queries
- Separate B-tree index on `field_id` for field-scoped queries
- Future-timestamp rejection at the service layer
- `data_source` column for provenance tracking

**PATCH-permitted (mutable) time-series** — WeatherRecord allows operator correction via PATCH, unlike SensorReading (Phase 7) which is append-only. The distinction: weather records may be manually entered and corrected; IoT sensor telemetry is immutable once ingested.

---

## Business Value

- Field-level historical weather observation — foundation for climate intelligence
- `recorded_at` + `field_id` indexed for efficient time-range queries at scale
- `solar_radiation_wm2` (Phase 6) enables Penman-Monteith ET₀ evapotranspiration — the input to FAO-56 irrigation scheduling
- `temperature_min_c` / `temperature_max_c` (Phase 6) enable Growing Degree Day accumulation — primary phenological forecasting input
- TimescaleDB upgrade path established (zero code changes required at Phase 12)

---

## What Was Deferred

- Weather forecast ingestion (external API integration)
- Climate trend analysis
- Drought monitoring
- Weather anomaly detection
- Automated API tests
