# Phase 7 — SensorReading Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `a8f3d1b6e924`  
**Revises:** `f3a8c1d9e047` (Phase 6 — AI readiness columns)

---

## What This Phase Achieved

Phase 7 introduced the SensorReading domain — AGRIFLOW-AI's first IoT telemetry domain and the first **append-only** (immutable) time-series. SensorReading captures raw readings from physical sensors deployed in the field: soil moisture probes, temperature sensors, EC meters, leaf wetness sensors, and others.

Three major architectural decisions were established here:

1. **Telemetry is append-only.** SensorReadings are immutable once written — no PATCH endpoint exists. This mirrors how real IoT systems work: a sensor reading is a historical fact, not a mutable record.
2. **`DOUBLE PRECISION` for sensor values.** ADC outputs from IoT hardware require 15–17 significant digits — `NUMERIC` is inappropriate. This is documented explicitly in the migration.
3. **`postgresql.ENUM` with `create_type=False` is the correct ENUM migration pattern.** Phase 7's migration file contains the definitive explanation of why `sa.Enum` fails in SQLAlchemy 2.0 (the `_copy()` method does not forward `create_type=False`). This became the authoritative pattern for all subsequent enum-bearing migrations.

---

## Domain Hierarchy After Phase 7

```
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord   (mutable, Phase 5)
     └── SensorReading   ← introduced (append-only, Phase 7)
```

---

## Database Changes

**PostgreSQL ENUM type created:** `sensor_type`

| Value | Sensor measures |
|-------|----------------|
| `SOIL_MOISTURE` | Volumetric water content (%) |
| `SOIL_TEMPERATURE` | Soil temperature (°C) |
| `AIR_TEMPERATURE` | Air temperature (°C) |
| `AIR_HUMIDITY` | Relative humidity (%) |
| `LIGHT_INTENSITY` | Photosynthetically active radiation (lux or µmol) |
| `LEAF_WETNESS` | Leaf surface wetness — key disease risk input |
| `ELECTRICAL_CONDUCTIVITY` | Soil EC in dS/m — salinity indicator |
| `SOIL_SALINITY` | Direct salinity measurement |
| `WATER_LEVEL` | Irrigation reservoir or drainage level |
| `BATTERY_STATUS` | Sensor device battery (V) |
| `DEVICE_HEALTH` | Sensor diagnostic / heartbeat signal |

**Table created:** `sensor_readings`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID (PK) | NOT NULL | UUID v4 primary key |
| `field_id` | UUID (FK → fields.id, CASCADE) | NOT NULL | Parent field; CASCADE delete removes all readings when field is deleted |
| `sensor_type` | ENUM `sensor_type` | NOT NULL | Physical quantity measured |
| `sensor_value` | DOUBLE PRECISION | NOT NULL | Raw numeric value — IEEE 754 64-bit; preserves full ADC resolution |
| `unit` | VARCHAR(50) | NOT NULL | SI or industry-standard unit (e.g. `%`, `°C`, `lux`, `dS/m`, `mm`, `V`) |
| `recorded_at` | TIMESTAMPTZ | NOT NULL | Timezone-aware capture timestamp — TimescaleDB partition key |
| `notes` | TEXT | NULL | Free-text annotations or anomaly flags from the ingestion pipeline |
| `created_at` | TIMESTAMPTZ | NOT NULL | Server-side row creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Server-side last-updated timestamp |

**Constraints and indexes (5 total):**

| Name | Type | Columns | Purpose |
|------|------|---------|---------|
| `fk_sensor_readings_field_id` | FK → `fields.id` ON DELETE CASCADE | `field_id` | Cascade delete |
| `pk_sensor_readings` | PRIMARY KEY | `id` | Explicit named PK |
| `ix_sensor_readings_field_id` | B-tree | `field_id` | "All readings for a field" |
| `ix_sensor_readings_sensor_type` | B-tree | `sensor_type` | "All readings of a type" |
| `ix_sensor_readings_recorded_at` | B-tree | `recorded_at` | "Readings in a time window" |
| `ix_sensor_readings_field_id_recorded_at` | Compound B-tree | `(field_id, recorded_at)` | **Primary telemetry access pattern** — field readings in time range |
| `ix_sensor_readings_sensor_type_recorded_at` | Compound B-tree | `(sensor_type, recorded_at)` | Typed readings in time range — AI feature pipelines |

---

## Phase 12 Upgrade (TimescaleDB)

`sensor_readings` was converted to a **TimescaleDB hypertable** in Phase 12 (migration `c9d8e7f6a5b4`), partitioned by `recorded_at`. A continuous aggregate was also created for hourly and daily rollups per sensor type and field — the primary AI feature engineering input.

Zero application code changes were required at Phase 12 because the compound indexes and `recorded_at` partition key column were established here in Phase 7.

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fields/{field_id}/sensor-readings` | Ingest a sensor reading |
| GET | `/api/v1/fields/{field_id}/sensor-readings` | List all readings for a field (paginated) |
| GET | `/api/v1/sensor-readings/{sensor_reading_id}` | Get a single reading by ID |
| DELETE | `/api/v1/sensor-readings/{sensor_reading_id}` | Delete a reading (admin correction only) |

**No PATCH endpoint.** SensorReading is append-only — see ADR-007 series below.

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Field must exist before SensorReading creation | `SensorReadingService.create_sensor_reading` |
| `recorded_at` must be timezone-aware (not naive) | `SensorReadingService` — `_validate_timezone_aware()` |
| `recorded_at` cannot be in the future | `SensorReadingService` — `_validate_not_future()` |
| No update (PATCH/PUT) permitted on any reading | No `SensorReadingUpdate` schema exists; no PATCH route |

---

## Architectural Decisions (ADR-007 Series)

| Decision | What was established |
|----------|---------------------|
| **ADR-007 — Append-only telemetry** | SensorReading has no PATCH endpoint. A sensor measurement is a historical fact. Corrections are made by ingesting a new reading, not by mutating the existing one. |
| **ADR-007 — Timezone-aware timestamps required** | Naive timestamps (without timezone) are rejected at the service layer. Agricultural data crosses timezones; ambiguous timestamps corrupt time-series queries. |
| **ADR-007 — Future timestamps rejected** | A reading cannot be recorded for a future time. The service enforces this; schema validation is not sufficient. |
| **ADR-007 — `DOUBLE PRECISION` for IoT values** | `NUMERIC(p,s)` is inappropriate for ADC outputs. IoT sensors produce floating-point outputs requiring 15–17 significant digits (IEEE 754 DOUBLE). Using `NUMERIC` would silently lose precision at the sensor hardware resolution. |
| **ADR-007 — `ON DELETE CASCADE` on `field_id`** | Deleting a Field removes all its sensor readings atomically. This matches the SQLAlchemy `cascade="all, delete-orphan"` on the ORM relationship. |
| **ADR-007 — Service layer as future Redpanda boundary** | The `create_sensor_reading` method is the intended insertion point for Phase 14 domain event publishing (`SensorReadingIngested`). No changes to the service interface are needed at Phase 14. |

**PostgreSQL ENUM lifecycle fix (definitive pattern):**

The migration contains the authoritative explanation of why `sa.Enum` fails in SQLAlchemy 2.0:
> `sa.Enum._copy()` — called internally by `op.create_table()` — does not forward `create_type=False`. The copy is constructed with the default `create_type=True`, causing a second `CREATE TYPE` collision.

The fix: always use `postgresql.ENUM` (not `sa.Enum`) in `op.create_table()` column definitions when the type is managed explicitly. This pattern was adopted for all subsequent enum-bearing migrations from Phase 7 onward and is documented as **ADR-008-01**.

---

## Shared Enum Module

Phase 7 created `backend/app/core/enums.py` as the **central module for all PostgreSQL-backed enum types**. `SensorType` (11 values) was the first entry. Subsequent phases added their enums here, making `enums.py` a single-source-of-truth for all domain classification types across the platform.

By Phase 13, `enums.py` contains 14 enum classes covering sensor types, soil types, crop status, irrigation methods, water sources, yield measurement methods, disease severity, diagnosis methods, satellite providers, spectral indices, processing levels, recommendation types, recommendation status, recommendation priority, alert types, and alert severity.

---

## Business Value

- IoT sensor data persistence for precision agriculture at field level
- Soil moisture readings available for irrigation scheduling models
- Leaf wetness + temperature readings available for disease risk scoring (Phase 13 alert engine)
- EC/salinity data for soil health monitoring
- Compound indexes on `(field_id, recorded_at)` and `(sensor_type, recorded_at)` support telemetry dashboards at scale
- TimescaleDB hypertable upgrade path established (zero code changes required at Phase 12)
- Phase 14 Redpanda event publishing insertion point identified in service layer

---

## What Was Deferred

- Real-time streaming / WebSocket endpoint for live sensor data
- Sensor anomaly detection
- Multi-sensor aggregation queries
- Automated API tests
