# Database Design

## Current Schema

### farms
Primary agricultural entity.

| Column | Type |
|---|---|
| id | UUID |
| name | VARCHAR |
| latitude | NUMERIC |
| longitude | NUMERIC |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

### fields
Represents a field belonging to a farm.

| Column | Type |
|---|---|
| id | UUID |
| farm_id | UUID (FK -> farms.id) |
| name | VARCHAR(255) |
| area_hectares | NUMERIC(10,2) |
| soil_type | VARCHAR(50) |
| latitude | NUMERIC(10,6) |
| longitude | NUMERIC(10,6) |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

### crops
Represents a crop cycle belonging to a field.

| Column | Type |
|---|---|
| id | UUID |
| field_id | UUID (FK -> fields.id) |
| crop_name | VARCHAR(255) |
| crop_variety | VARCHAR(255) |
| planting_date | DATE |
| expected_harvest_date | DATE |
| actual_harvest_date | DATE |
| status | ENUM(crop_status) |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |

### soil_profiles

Represents the soil intelligence profile for a field.

| Column         | Type                           |
| -------------- | ------------------------------ |
| id             | UUID                           |
| field_id       | UUID (FK -> fields.id, UNIQUE) |
| soil_type      | ENUM(soil_type)                |
| ph             | NUMERIC(4,2)                   |
| organic_matter | NUMERIC(5,2)                   |
| nitrogen       | NUMERIC(10,2)                  |
| phosphorus     | NUMERIC(10,2)                  |
| potassium      | NUMERIC(10,2)                  |
| notes          | TEXT                           |
| created_at     | TIMESTAMP                      |
| updated_at     | TIMESTAMP                      |



### weather_records

Represents historical weather observations for a field.

| Column | Type |
|---|---|
| id | UUID |
| field_id | UUID (FK -> fields.id) |
| recorded_at | TIMESTAMP |
| temperature_c | NUMERIC(5,2) |
| humidity_percent | NUMERIC(5,2) |
| rainfall_mm | NUMERIC(8,2) |
| wind_speed_kmh | NUMERIC(8,2) |
| data_source | VARCHAR(100) |
| created_at | TIMESTAMP |
| updated_at | TIMESTAMP |


## sensor_readings

Represents IoT sensor telemetry observations for a field. Append-only — no updates permitted.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | `UUID` | No | Primary key |
| `field_id` | `UUID` (FK → fields.id) | No | ON DELETE CASCADE |
| `sensor_type` | `ENUM(sensor_type)` | No | See sensor_type enum below |
| `sensor_value` | `DOUBLE PRECISION` | No | IEEE 754 64-bit; not NUMERIC |
| `unit` | `VARCHAR(50)` | No | SI or industry-standard unit |
| `recorded_at` | `TIMESTAMPTZ` | No | Timezone-aware observation timestamp |
| `notes` | `TEXT` | Yes | Free-text annotation |
| `created_at` | `TIMESTAMPTZ` | No | Audit timestamp |
| `updated_at` | `TIMESTAMPTZ` | No | Audit timestamp |

### sensor_type Enum

```sql
CREATE TYPE sensor_type AS ENUM (
    'SOIL_MOISTURE',
    'SOIL_TEMPERATURE',
    'AIR_TEMPERATURE',
    'AIR_HUMIDITY',
    'LIGHT_INTENSITY',
    'LEAF_WETNESS',
    'ELECTRICAL_CONDUCTIVITY',
    'SOIL_SALINITY',
    'WATER_LEVEL',
    'BATTERY_STATUS',
    'DEVICE_HEALTH'
);
```

### sensor_readings Indexes

| Index | Columns | Type | Purpose |
|---|---|---|---|
| `ix_sensor_readings_field_id` | `field_id` | Single | Field-level reading lookups |
| `ix_sensor_readings_sensor_type` | `sensor_type` | Single | Cross-field type queries |
| `ix_sensor_readings_recorded_at` | `recorded_at` | Single | Time-range queries |
| `ix_sensor_readings_field_id_recorded_at` | `(field_id, recorded_at)` | Compound | Primary telemetry access pattern |
| `ix_sensor_readings_sensor_type_recorded_at` | `(sensor_type, recorded_at)` | Compound | Type-scoped time queries |

Compound indexes are a Phase 7 introduction — all prior tables use single-column indexes only.

### Design Decisions

**DOUBLE PRECISION vs NUMERIC:**
All prior columns use `NUMERIC(p,s)`. `sensor_value` uses `DOUBLE PRECISION` because sensor ADC outputs are floating-point quantities. Fixed-scale `NUMERIC` would silently truncate high-resolution sensor readings.

**ON DELETE CASCADE:**
`field_id` FK uses `ON DELETE CASCADE`. A field deletion atomically removes all its sensor readings at the database level, consistent with the SQLAlchemy `cascade="all, delete-orphan"` relationship.

**Explicit enum lifecycle:**
Migration 006 uses explicit `CREATE TYPE sensor_type AS ENUM (...)` in the upgrade function and `DROP TYPE sensor_type` in downgrade. This gives full lifecycle control and avoids implicit creation issues seen with earlier enums.

---

## Relationships

Farm (1) -> (N) Fields

Field (1) -> (N) Crops

Field (1) -> (1) SoilProfile

Field (1) -> (N) WeatherRecords

Field (1) -> (N) SensorReadings  ← Phase 7 (ON DELETE CASCADE)


## Current Domain Hierarchy

```
Farm
└── Field
     ├── Crop
     ├── SoilProfile
     ├── WeatherRecord
     └── SensorReading   ← Phase 7
```


## Implemented Migrations

| Migration | Description |
|---|---|
| `001_create_farms_table` | farms table |
| `002_create_fields_table` | fields table |
| `003_create_crops_table` | crops table + `crop_status` enum |
| `13aabbe35d51_add_soil_profiles_table` | soil_profiles table + `soil_type` enum |
| `004_create_weather_records_table` | weather_records table |
| `005_add_p1_ai_readiness_columns` | P1 AI attributes across 4 tables |
| `006_create_sensor_readings_table` | sensor_readings table + `sensor_type` enum + 5 indexes |

## Crop Status Lifecycle

- PLANNED
- PLANTED
- GROWING
- HARVESTED

## Current API Coverage

### Field APIs

- POST   /api/v1/farms/{farm_id}/fields
- GET    /api/v1/farms/{farm_id}/fields
- GET    /api/v1/fields/{field_id}
- PATCH  /api/v1/fields/{field_id}
- DELETE /api/v1/fields/{field_id}

### Crop APIs

- POST   /api/v1/fields/{field_id}/crops
- GET    /api/v1/fields/{field_id}/crops
- GET    /api/v1/crops/{crop_id}
- PATCH  /api/v1/crops/{crop_id}
- DELETE /api/v1/crops/{crop_id}

### Soil Profile APIs

* POST   /api/v1/fields/{field_id}/soil-profile
* GET    /api/v1/fields/{field_id}/soil-profile
* PATCH  /api/v1/soil-profiles/{soil_profile_id}
* DELETE /api/v1/soil-profiles/{soil_profile_id}

### Weather Record APIs

* POST   /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/weather-records/{weather_record_id}
* PATCH  /api/v1/weather-records/{weather_record_id}
* DELETE /api/v1/weather-records/{weather_record_id}

### Sensor Reading APIs (Phase 7)

* POST   /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/sensor-readings/{sensor_reading_id}
* DELETE /api/v1/sensor-readings/{sensor_reading_id}

No PATCH. No PUT. SensorReading is immutable telemetry.


## Future Database Evolution

- Irrigation Management (`irrigation_events` table)
- Yield Tracking (`yield_records` table)
- Disease Observation (`disease_observations` table)
- Satellite Imagery (`satellite_observations` table)
- GIS / PostGIS Support (field boundary polygons)
- AI Recommendation Engine (inference output tables)

### TimescaleDB Hypertable Promotion

`sensor_readings` is designed for zero-friction TimescaleDB conversion. The partition key (`recorded_at TIMESTAMPTZ NOT NULL`) already satisfies the hypertable requirement.

Activation DDL (no application code changes required):

```sql
SELECT create_hypertable(
    'sensor_readings',
    'recorded_at',
    chunk_time_interval => INTERVAL '1 week',
    migrate_data => TRUE
);
```

Capabilities gained:
* Automatic time-based chunk partitioning
* Chunk exclusion for time-range queries
* Continuous aggregates (hourly/daily rollups per field per sensor type)
* Columnar compression for cold chunks (20–100× storage reduction)
* Automatic data retention policies (TTL-based chunk expiry)

### Cassandra Migration Path

For deployments exceeding PostgreSQL vertical scaling limits, `sensor_readings` can be migrated to Cassandra using the CQRS pattern:

Primary table partition: `field_id` (partition key) + `recorded_at DESC` (clustering key) — matching the existing compound index `ix_sensor_readings_field_id_recorded_at`.

Migration requires no changes to the application service layer.


## Phase 6 AI Readiness Foundation (Completed)

Added AI-ready attributes across Field, Crop, SoilProfile, and WeatherRecord domains to support future prediction and recommendation engines.

### New AI Attributes

Field
- elevation_m

Crop
- actual_yield_tons_ha
- expected_yield_tons_ha
- seeding_rate_kg_ha
- growth_stage

SoilProfile
- soil_depth_cm
- cation_exchange_capacity_meq

WeatherRecord
- solar_radiation_wm2
- temperature_min_c
- temperature_max_c
