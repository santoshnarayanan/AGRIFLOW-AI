# API Design

## Existing Endpoints

### Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

### Version

* GET /api/v1/version

### Sensor Reading

* POST   /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/sensor-readings/{sensor_reading_id}
* DELETE /api/v1/sensor-readings/{sensor_reading_id}

### Irrigation Event

* POST   /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/irrigation-events/{event_id}
* PATCH  /api/v1/irrigation-events/{event_id}
* DELETE /api/v1/irrigation-events/{event_id}

### Yield Record

* POST   /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/yield-records/{yield_record_id}
* PATCH  /api/v1/yield-records/{yield_record_id}
* DELETE /api/v1/yield-records/{yield_record_id}

### Disease Observation

* POST   /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/fields/{field_id}/disease-observations
* GET    /api/v1/disease-observations/{observation_id}
* PATCH  /api/v1/disease-observations/{observation_id}
* DELETE /api/v1/disease-observations/{observation_id}

---

## Field Domain Endpoints

Cumulative API inventory for all implemented domains through Phase 11.

### Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

### Version

* GET /api/v1/version

### Create Field

* POST /api/v1/farms/{farm_id}/fields

### List Fields

* GET /api/v1/farms/{farm_id}/fields

### Get Field

* GET /api/v1/fields/{field_id}

### Update Field

* PATCH /api/v1/fields/{field_id}

### Delete Field

* DELETE /api/v1/fields/{field_id}

---

## Crop Domain Endpoints

### Create Crop

* POST /api/v1/fields/{field_id}/crops

### List Crops for Field

* GET /api/v1/fields/{field_id}/crops

### Get Crop

* GET /api/v1/crops/{crop_id}

### Update Crop

* PATCH /api/v1/crops/{crop_id}

### Delete Crop

* DELETE /api/v1/crops/{crop_id}

---

## Soil Profile Domain Endpoints

### Create Soil Profile

* POST /api/v1/fields/{field_id}/soil-profile

### Get Soil Profile for Field

* GET /api/v1/fields/{field_id}/soil-profile

### Update Soil Profile

* PATCH /api/v1/soil-profiles/{soil_profile_id}

### Delete Soil Profile

* DELETE /api/v1/soil-profiles/{soil_profile_id}


---

## Weather Record Domain Endpoints

### Create Weather Record

* POST /api/v1/fields/{field_id}/weather-records

### List Weather Records for Field

* GET /api/v1/fields/{field_id}/weather-records

### Get Weather Record

* GET /api/v1/weather-records/{weather_record_id}

### Update Weather Record

* PATCH /api/v1/weather-records/{weather_record_id}

### Delete Weather Record

* DELETE /api/v1/weather-records/{weather_record_id}

---

## Sensor Reading Domain Endpoints

### Create Sensor Reading

* POST /api/v1/fields/{field_id}/sensor-readings

### List Sensor Readings for Field

* GET /api/v1/fields/{field_id}/sensor-readings

### Get Sensor Reading

* GET /api/v1/sensor-readings/{sensor_reading_id}

### Delete Sensor Reading

* DELETE /api/v1/sensor-readings/{sensor_reading_id}

---

## Irrigation Event Domain Endpoints

### Create Irrigation Event

* POST /api/v1/fields/{field_id}/irrigation-events

### List Irrigation Events for Field

* GET /api/v1/fields/{field_id}/irrigation-events

### Get Irrigation Event

* GET /api/v1/irrigation-events/{event_id}

### Update Irrigation Event

* PATCH /api/v1/irrigation-events/{event_id}

### Delete Irrigation Event

* DELETE /api/v1/irrigation-events/{event_id}

---

## Yield Record Domain Endpoints

### Create Yield Record

* POST /api/v1/crops/{crop_id}/yield-records

### List Yield Records for Crop

* GET /api/v1/crops/{crop_id}/yield-records

### Get Yield Record

* GET /api/v1/yield-records/{yield_record_id}

### Update Yield Record

* PATCH /api/v1/yield-records/{yield_record_id}

### Delete Yield Record

* DELETE /api/v1/yield-records/{yield_record_id}

---

## Disease Observation Domain Endpoints

### Create Disease Observation

* POST /api/v1/crops/{crop_id}/disease-observations

### List Disease Observations for Crop

* GET /api/v1/crops/{crop_id}/disease-observations

### List Disease Observations for Field

* GET /api/v1/fields/{field_id}/disease-observations

### Get Disease Observation

* GET /api/v1/disease-observations/{observation_id}

### Update Disease Observation

* PATCH /api/v1/disease-observations/{observation_id}

### Delete Disease Observation

* DELETE /api/v1/disease-observations/{observation_id}

---

## Satellite Observation Domain Endpoints

### Create Satellite Observation

* POST /api/v1/fields/{field_id}/satellite-observations

### List Satellite Observations for Field

* GET /api/v1/fields/{field_id}/satellite-observations

### List Satellite Observations by Date Range

* GET /api/v1/fields/{field_id}/satellite-observations/range

Query parameters: `start`, `end`, `limit`, `offset`

### Get Latest Satellite Observation by Spectral Index

* GET /api/v1/fields/{field_id}/satellite-observations/latest

Query parameter: `spectral_index`

### List Satellite Observations by Provider

* GET /api/v1/satellite-observations/by-provider/{satellite_provider}

### List Satellite Observations by Processing Level

* GET /api/v1/satellite-observations/by-processing-level/{processing_level}

### Get Satellite Observation

* GET /api/v1/satellite-observations/{observation_id}

### Update Satellite Observation

* PATCH /api/v1/satellite-observations/{observation_id}

### Delete Satellite Observation

* DELETE /api/v1/satellite-observations/{observation_id}

---

Request Flow:

API Router
→ Schema Validation
→ Service Layer
→ Repository Layer
→ PostgreSQL

Response Flow:

PostgreSQL
→ Repository Layer
→ Service Layer
→ Schema Serialization
→ API Response

---

## Dependency Injection Flow

FastAPI Router
→ Dependency Provider (deps.py)
→ Service Layer
→ Repository Layer
→ AsyncSession
→ PostgreSQL

---

## Domain Mapping

### Farm Domain

Farm
└── Fields

### Crop Domain

Field
└── Crop
     ├── YieldRecords
     └── DiseaseObservations

### Soil Profile Domain

Field
└── SoilProfile

### Weather Record Domain

Field
└── WeatherRecords

### Sensor Reading Domain

Field
└── SensorReadings (append-only telemetry)

### Irrigation Event Domain

Field
└── IrrigationEvents (mutable operational events)

### Yield Record Domain

Crop
└── YieldRecords (mutable observation records)

### Disease Observation Domain

Crop
└── DiseaseObservations (mutable observation records)

### Satellite Observation Domain

Field
└── SatelliteObservations (mutable Earth observation records)

---

## HTTP Status Code Conventions

### Success

* 200 OK
* 201 Created
* 204 No Content

### Client Errors

* 400 Bad Request
* 404 Not Found
* 409 Conflict
* 422 Unprocessable Entity

---

## Current API Coverage

### Health APIs

* Service Health
* Readiness Check

### Version APIs

* Application Version

### Field APIs

* Create Field
* List Fields
* Get Field
* Update Field
* Delete Field

### Crop APIs

* Create Crop
* List Crops
* Get Crop
* Update Crop
* Delete Crop

### Soil Profile APIs

* Create Soil Profile
* Get Soil Profile
* Update Soil Profile
* Delete Soil Profile

### Weather Record APIs

* Create Weather Record
* List Weather Records
* Get Weather Record
* Update Weather Record
* Delete Weather Record

### Sensor Reading APIs

* Create Sensor Reading
* List Sensor Readings
* Get Sensor Reading
* Delete Sensor Reading (administrative only — no PATCH)

### Irrigation Event APIs

* Create Irrigation Event
* List Irrigation Events
* Get Irrigation Event
* Update Irrigation Event
* Delete Irrigation Event

### Yield Record APIs

* Create Yield Record
* List Yield Records for Crop
* Get Yield Record
* Update Yield Record
* Delete Yield Record

### Disease Observation APIs

* Create Disease Observation
* List Disease Observations for Crop
* List Disease Observations for Field
* Get Disease Observation
* Update Disease Observation
* Delete Disease Observation

### Satellite Observation APIs

* Create Satellite Observation
* List Satellite Observations for Field
* List Satellite Observations by Date Range
* Get Latest Satellite Observation by Spectral Index
* List Satellite Observations by Provider
* List Satellite Observations by Processing Level
* Get Satellite Observation
* Update Satellite Observation
* Delete Satellite Observation

---

## Business Rules Exposed Through APIs

### Field Domain

* Farm must exist before Field creation
* Field names must be unique within a Farm

### Crop Domain

* Field must exist before Crop creation
* Crop lifecycle management
* Harvest date validation

### Soil Profile Domain

* Field must exist before SoilProfile creation
* Only one SoilProfile allowed per Field
* SoilProfile must exist before update
* SoilProfile must exist before delete

### Weather Record Domain

* Field must exist before WeatherRecord creation
* WeatherRecord must exist before update
* WeatherRecord must exist before delete
* Future timestamps are rejected
* Humidity must be between 0 and 100
* Rainfall cannot be negative
* Wind speed cannot be negative

### Sensor Reading Domain

* Field must exist before sensor reading creation (→ 404 Not Found)
* `recorded_at` must be timezone-aware; naive datetimes are rejected (→ 422 Unprocessable Entity)
* `recorded_at` must not be in the future; future timestamps are rejected (→ 422 Unprocessable Entity)
* No sensor value range validation (reserved for future ingestion and SensorDevice domains)
* No update operation permitted — SensorReading is immutable (no PATCH, no PUT)
* Telemetry list responses are ordered by `recorded_at DESC` (most recent first)
* Administrative deletion is supported; modification is forbidden

### Irrigation Event Domain

* Field must exist before IrrigationEvent creation (→ 404 Not Found)
* `started_at` must be timezone-aware and not in the future (→ 400 Bad Request)
* `ended_at`, when supplied, must be timezone-aware and ≥ `started_at`
* Cross-field ordering validated after sparse PATCH (effective values merged before check)
* `duration_minutes` must be non-negative
* `water_volume_liters` must be non-negative
* PATCH is permitted — IrrigationEvent is a mutable operational event
* List responses are ordered by `started_at DESC` (most recent first)

### Yield Record Domain

* Crop must exist before YieldRecord creation (→ 404 Not Found)
* `crop_id` is supplied through the route path — not in the request body
* `field_id` is resolved server-side from the crop record — not supplied by the caller
* `recorded_at` must be timezone-aware and not in the future (→ 400 Bad Request)
* `area_harvested_ha`, when supplied, must be > 0 (→ 400 Bad Request)
* `test_weight_kg_hl`, when supplied, must be > 0 (→ 400 Bad Request)
* `crop_id` is immutable after creation — excluded from update schema
* PATCH is permitted — YieldRecord is a mutable observation record
* List responses are ordered by `recorded_at DESC` (most recent first)

### Disease Observation Domain

* Crop must exist before DiseaseObservation creation (→ 404 Not Found)
* `crop_id` is supplied through the route path — not in the request body
* `field_id` is resolved server-side from the crop record — not supplied by the caller
* `observed_at` must be timezone-aware and not in the future (→ 400 Bad Request)
* `affected_area_percent`, when supplied, must be within [0, 100] (schema validation)
* `crop_id` and `field_id` are immutable after creation — excluded from update schema
* PATCH is permitted — DiseaseObservation is a mutable observation record
* List responses are ordered by `observed_at DESC` (most recent first)

### Satellite Observation Domain

* Field must exist before SatelliteObservation creation (→ 404 Not Found)
* `field_id` is supplied through the route path — not in the request body
* `observed_at` must be timezone-aware and not in the future (→ 400 Bad Request)
* `index_value` validated against contextual range for `spectral_index` (ratio indices in [-1.0, 1.0]; LAI > 0)
* `resolution_m`, when supplied, must be > 0 (→ 400 Bad Request)
* `cloud_cover_percent`, when supplied, must be within [0, 100] (schema + service validation)
* `field_id` is immutable after creation — excluded from update schema
* PATCH is permitted — SatelliteObservation is a mutable Earth observation record
* List responses are ordered by `observed_at DESC` (most recent first)

---

### Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

### Version

* GET /api/v1/version

### Fields

* POST   /api/v1/farms/{farm_id}/fields
* GET    /api/v1/farms/{farm_id}/fields
* GET    /api/v1/fields/{field_id}
* PATCH  /api/v1/fields/{field_id}
* DELETE /api/v1/fields/{field_id}

### Crops

* POST   /api/v1/fields/{field_id}/crops
* GET    /api/v1/fields/{field_id}/crops
* GET    /api/v1/crops/{crop_id}
* PATCH  /api/v1/crops/{crop_id}
* DELETE /api/v1/crops/{crop_id}

### Soil Profiles

* POST   /api/v1/fields/{field_id}/soil-profile
* GET    /api/v1/fields/{field_id}/soil-profile
* PATCH  /api/v1/soil-profiles/{soil_profile_id}
* DELETE /api/v1/soil-profiles/{soil_profile_id}

### Weather Records

* POST   /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/weather-records/{weather_record_id}
* PATCH  /api/v1/weather-records/{weather_record_id}
* DELETE /api/v1/weather-records/{weather_record_id}

### Sensor Readings

* POST   /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/sensor-readings/{sensor_reading_id}
* DELETE /api/v1/sensor-readings/{sensor_reading_id}

### Irrigation Events

* POST   /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/fields/{field_id}/irrigation-events
* GET    /api/v1/irrigation-events/{event_id}
* PATCH  /api/v1/irrigation-events/{event_id}
* DELETE /api/v1/irrigation-events/{event_id}

### Yield Records

* POST   /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/crops/{crop_id}/yield-records
* GET    /api/v1/yield-records/{yield_record_id}
* PATCH  /api/v1/yield-records/{yield_record_id}
* DELETE /api/v1/yield-records/{yield_record_id}

### Disease Observations

* POST   /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/crops/{crop_id}/disease-observations
* GET    /api/v1/fields/{field_id}/disease-observations
* GET    /api/v1/disease-observations/{observation_id}
* PATCH  /api/v1/disease-observations/{observation_id}
* DELETE /api/v1/disease-observations/{observation_id}

### Satellite Observations

* POST   /api/v1/fields/{field_id}/satellite-observations
* GET    /api/v1/fields/{field_id}/satellite-observations
* GET    /api/v1/fields/{field_id}/satellite-observations/range
* GET    /api/v1/fields/{field_id}/satellite-observations/latest
* GET    /api/v1/satellite-observations/by-provider/{satellite_provider}
* GET    /api/v1/satellite-observations/by-processing-level/{processing_level}
* GET    /api/v1/satellite-observations/{observation_id}
* PATCH  /api/v1/satellite-observations/{observation_id}
* DELETE /api/v1/satellite-observations/{observation_id}

---

## Future API Evolution

* AI Recommendation APIs (Phase 12+)
* Sensor Aggregation APIs (TimescaleDB continuous aggregates)
* Digital Twin State API
* GaaS / Farm Copilot API


---

## Sensor Reading Domain Endpoints

### Create Sensor Reading

```
POST /api/v1/fields/{field_id}/sensor-readings
```

**Status:** 201 Created

**Request Model:** `SensorReadingCreate`

```json
{
  "sensor_type": "SOIL_MOISTURE",
  "sensor_value": 34.7,
  "unit": "%VWC",
  "recorded_at": "2026-06-18T20:00:00Z",
  "notes": "Optional annotation"
}
```

**Response Model:** `SensorReadingResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `FieldNotFoundError` | 404 Not Found | Parent field UUID does not exist |
| `InvalidSensorTimestampError` | 422 Unprocessable Entity | `recorded_at` is timezone-naive or in the future |

**Design note:** `recorded_at` must include a UTC offset (e.g. `2026-06-18T20:00:00Z` or `2026-06-18T22:00:00+02:00`). `datetime.now()` without timezone is invalid.

---

### List Sensor Readings for Field

```
GET /api/v1/fields/{field_id}/sensor-readings
```

**Status:** 200 OK

**Response Model:** `list[SensorReadingResponse]`

**Ordering:** `recorded_at DESC` — most recent reading first. Ordering is applied at the repository layer.

**Pagination:** None in Phase 7. All readings for the field are returned. Pagination deferred to a future phase.

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `FieldNotFoundError` | 404 Not Found | Parent field UUID does not exist |

---

### Get Sensor Reading

```
GET /api/v1/sensor-readings/{sensor_reading_id}
```

**Status:** 200 OK

**Response Model:** `SensorReadingResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `SensorReadingNotFoundError` | 404 Not Found | Reading UUID does not exist |

---

### Delete Sensor Reading

```
DELETE /api/v1/sensor-readings/{sensor_reading_id}
```

**Status:** 204 No Content

**Response body:** None

**Purpose:** Administrative cleanup of invalid or corrupted telemetry. Not a business operation.

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `SensorReadingNotFoundError` | 404 Not Found | Reading UUID does not exist |

---

## Telemetry API Architectural Decisions

### No PATCH / No PUT (ADR-007-29, ADR-007-32)

SensorReading endpoints deliberately omit `PATCH` and `PUT`. Telemetry is a factual record of what a sensor reported. Mutations to historical telemetry would corrupt the time-series integrity of AI training datasets and Digital Twin state.

Corrections to sensor readings are represented by submitting a new reading.

### 422 for Invalid Timestamps (ADR-007-33)

`InvalidSensorTimestampError` maps to HTTP 422 (Unprocessable Entity), not 400 (Bad Request).

Rationale: A timezone-naive or future-dated timestamp is syntactically valid JSON but semantically unprocessable given the telemetry domain contract. This distinction follows RFC 9110 semantics.

### Ordering Semantics (ADR-007-30)

`GET /fields/{field_id}/sensor-readings` returns readings ordered by `recorded_at DESC`. This ordering is enforced at the repository layer (`SensorReadingRepository.list_by_field`) and must not be reordered at the service or API layer.

### Deletion Semantics (ADR-007-31)

`DELETE /sensor-readings/{id}` returns `204 No Content` with an empty body. This is consistent with all other DELETE endpoints in AGRIFLOW-AI.

### HTTP Status Code Reference for Sensor Reading Domain

| Code | Meaning | When Used |
|---|---|---|
| 201 Created | Reading persisted | Successful POST |
| 200 OK | Reading(s) returned | Successful GET |
| 204 No Content | Reading deleted | Successful DELETE |
| 404 Not Found | Resource absent | Field or reading UUID not found |
| 422 Unprocessable Entity | Invalid timestamp | Timezone-naive or future `recorded_at` |

---

## Irrigation Event Domain Endpoints

### Create Irrigation Event

```
POST /api/v1/fields/{field_id}/irrigation-events
```

**Status:** 201 Created

**Request Model:** `IrrigationEventCreate`

```json
{
  "started_at": "2026-06-19T06:00:00Z",
  "ended_at": "2026-06-19T07:30:00Z",
  "duration_minutes": 90.0,
  "water_volume_liters": 2400.0,
  "irrigation_method": "DRIP",
  "water_source": "GROUNDWATER",
  "notes": "Morning drip cycle for Field A"
}
```

**Response Model:** `IrrigationEventResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `FieldNotFoundError` | 404 Not Found | Parent field UUID does not exist |
| `InvalidIrrigationTimestampError` | 400 Bad Request | `started_at` is in the future or `ended_at` < `started_at` |

---

### List Irrigation Events for Field

```
GET /api/v1/fields/{field_id}/irrigation-events?limit=100&offset=0
```

**Status:** 200 OK

**Query Parameters:** `limit` (default 100), `offset` (default 0)

**Response Model:** `PaginatedResponse[IrrigationEventResponse]`

**Ordering:** `started_at DESC` — most recent event first.

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `FieldNotFoundError` | 404 Not Found | Parent field UUID does not exist |

---

### Get Irrigation Event

```
GET /api/v1/irrigation-events/{event_id}
```

**Status:** 200 OK

**Response Model:** `IrrigationEventResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `IrrigationEventNotFoundError` | 404 Not Found | Event UUID does not exist |

---

### Update Irrigation Event

```
PATCH /api/v1/irrigation-events/{event_id}
```

**Status:** 200 OK

**Request Model:** `IrrigationEventUpdate` (all fields optional)

```json
{
  "ended_at": "2026-06-19T08:00:00Z",
  "water_volume_liters": 2600.0,
  "notes": "Corrected volume after meter check"
}
```

**Response Model:** `IrrigationEventResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `IrrigationEventNotFoundError` | 404 Not Found | Event UUID does not exist |
| `InvalidIrrigationTimestampError` | 400 Bad Request | Updated `ended_at` < effective `started_at` |

**Sparse PATCH guard:** When only `ended_at` is provided, the service merges it with the persisted `started_at` before performing the ordering check. This prevents silent violations where a partial update makes `ended_at` precede `started_at`.

---

### Delete Irrigation Event

```
DELETE /api/v1/irrigation-events/{event_id}
```

**Status:** 204 No Content

**Response body:** None

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `IrrigationEventNotFoundError` | 404 Not Found | Event UUID does not exist |

---

---

# Yield Record API

## Endpoints

### Create Yield Record

```
POST /api/v1/crops/{crop_id}/yield-records
```

**Status:** 201 Created

**Request Body:** `YieldRecordCreate`

```json
{
  "recorded_at": "2026-06-23T08:00:00+02:00",
  "yield_value_tons_ha": "7.4250",
  "measurement_method": "COMBINE_MONITOR",
  "area_harvested_ha": "4.5000",
  "moisture_content_percent": "14.30",
  "test_weight_kg_hl": "76.500",
  "quality_grade": "Grade 1",
  "notes": "North section harvested first"
}
```

**Note:** `crop_id` is taken from the URL path. `field_id` is resolved server-side from the crop record — it must not be supplied.

**Response Model:** `YieldRecordResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `CropNotFoundError` | 404 Not Found | Crop UUID does not exist |
| `InvalidYieldRecordError` | 400 Bad Request | `recorded_at` in future, `area_harvested_ha <= 0`, or `test_weight_kg_hl <= 0` |

---

### List Yield Records for a Crop Cycle

```
GET /api/v1/crops/{crop_id}/yield-records?limit=100&offset=0
```

**Status:** 200 OK

**Query Parameters:**

| Parameter | Default | Range | Description |
|---|---|---|---|
| `limit` | 100 | 1–500 | Maximum records to return |
| `offset` | 0 | ≥ 0 | Records to skip |

**Response Model:** `PaginatedResponse[YieldRecordResponse]`

```json
{
  "items": [...],
  "total": 3,
  "limit": 100,
  "offset": 0
}
```

Ordered by `recorded_at DESC` (most recent measurement first).

---

### Get Yield Record

```
GET /api/v1/yield-records/{yield_record_id}
```

**Status:** 200 OK

**Response Model:** `YieldRecordResponse`

```json
{
  "id": "a1b2c3d4-...",
  "crop_id": "e5f6a7b8-...",
  "field_id": "c9d0e1f2-...",
  "recorded_at": "2026-06-23T08:00:00+02:00",
  "yield_value_tons_ha": "7.4250",
  "measurement_method": "COMBINE_MONITOR",
  "area_harvested_ha": "4.5000",
  "moisture_content_percent": "14.30",
  "test_weight_kg_hl": "76.500",
  "quality_grade": "Grade 1",
  "notes": "North section harvested first",
  "created_at": "2026-06-23T06:05:00Z",
  "updated_at": "2026-06-23T06:05:00Z"
}
```

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `None` return from service | 404 Not Found | Yield record UUID does not exist |

---

### Update Yield Record

```
PATCH /api/v1/yield-records/{yield_record_id}
```

**Status:** 200 OK

**Request Body:** `YieldRecordUpdate` (all fields optional — sparse PATCH)

```json
{
  "moisture_content_percent": "13.80",
  "notes": "Updated after lab confirmation"
}
```

**Note:** `crop_id` and `field_id` are immutable and cannot be supplied.

**Response Model:** `YieldRecordResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `YieldRecordNotFoundError` | 404 Not Found | Yield record UUID does not exist |
| `InvalidYieldRecordError` | 400 Bad Request | Updated `recorded_at` in future, or `area_harvested_ha`/`test_weight_kg_hl` <= 0 |

---

### Delete Yield Record

```
DELETE /api/v1/yield-records/{yield_record_id}
```

**Status:** 204 No Content

**Response body:** None

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `YieldRecordNotFoundError` | 404 Not Found | Yield record UUID does not exist |

---

## Yield Record API Architectural Decisions

### POST anchors to `/crops/{crop_id}` (ADR-009-01)

The creation endpoint uses `/crops/{crop_id}/yield-records` rather than `/fields/{field_id}/yield-records`. Yield is a per-crop-cycle measurement. Anchoring to the field would require the client to supply both `crop_id` and `field_id`, introducing a redundant constraint that the server can resolve itself. The server resolves `field_id` from the crop record.

### 400 for Invalid Measurement Values (ADR-009-09)

`InvalidYieldRecordError` maps to HTTP 400 (Bad Request). Violations such as future `recorded_at`, zero harvested area, or zero test weight represent correctable client logic errors — not schema errors (which return 422) or missing resources (which return 404).

### `crop_id` Immutability at API Level (ADR-009-05)

`YieldRecordUpdate` excludes `crop_id`. If a record was logged against the wrong crop, it must be deleted and re-created. Allowing `crop_id` mutation would break the audit trail and invalidate any AI feature vectors already computed from this record.

### HTTP Status Code Reference for Yield Record Domain

| Code | Meaning | When Used |
|---|---|---|
| 201 Created | Record persisted | Successful POST |
| 200 OK | Record(s) returned | Successful GET or PATCH |
| 204 No Content | Record deleted | Successful DELETE |
| 400 Bad Request | Invalid measurement | Future `recorded_at`, `area <= 0`, or `test_weight <= 0` |
| 404 Not Found | Resource absent | Crop or yield record UUID not found |

---

# Disease Observation API (Phase 10)

## Endpoints

### Create Disease Observation

```
POST /api/v1/crops/{crop_id}/disease-observations
```

**Status:** 201 Created

**Request Model:** `CreateDiseaseObservationRequest`

```json
{
  "observed_at": "2026-06-23T08:00:00+02:00",
  "disease_name": "Late Blight",
  "severity": "HIGH",
  "diagnosis_method": "VISUAL_INSPECTION",
  "affected_area_percent": "12.50",
  "treatment_applied": "Copper fungicide applied",
  "notes": "North section showing early symptoms"
}
```

**Note:** `crop_id` is taken from the URL path. `field_id` is resolved server-side from the crop record — it must not be supplied.

**Response Model:** `DiseaseObservationResponse`

**Business Rules:**

* Crop must exist before creation
* `field_id` resolved server-side from crop
* `observed_at` must not be in the future

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `CropNotFoundError` | 404 Not Found | Crop UUID does not exist |
| `InvalidDiseaseObservationError` | 400 Bad Request | `observed_at` is in the future |

---

### List Disease Observations for Crop

```
GET /api/v1/crops/{crop_id}/disease-observations?limit=100&offset=0
```

**Status:** 200 OK

**Query Parameters:**

| Parameter | Default | Range | Description |
|---|---|---|---|
| `limit` | 100 | 1–500 | Maximum records to return |
| `offset` | 0 | ≥ 0 | Records to skip |

**Response Model:** `DiseaseObservationListResponse`

**Ordering:** `observed_at DESC` — most recent observation first.

---

### List Disease Observations for Field

```
GET /api/v1/fields/{field_id}/disease-observations?limit=100&offset=0
```

**Status:** 200 OK

**Query Parameters:**

| Parameter | Default | Range | Description |
|---|---|---|---|
| `limit` | 100 | 1–500 | Maximum records to return |
| `offset` | 0 | ≥ 0 | Records to skip |

**Response Model:** `DiseaseObservationListResponse`

**Ordering:** `observed_at DESC` — most recent observation first.

---

### Get Disease Observation

```
GET /api/v1/disease-observations/{observation_id}
```

**Status:** 200 OK

**Response Model:** `DiseaseObservationResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `DiseaseObservationNotFoundError` | 404 Not Found | Observation UUID does not exist |

---

### Update Disease Observation

```
PATCH /api/v1/disease-observations/{observation_id}
```

**Status:** 200 OK

**Request Model:** `UpdateDiseaseObservationRequest` (all fields optional — sparse PATCH)

```json
{
  "severity": "CRITICAL",
  "notes": "Escalated after follow-up inspection"
}
```

**Note:** `crop_id` and `field_id` are immutable and cannot be supplied.

**Response Model:** `DiseaseObservationResponse`

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `DiseaseObservationNotFoundError` | 404 Not Found | Observation UUID does not exist |
| `InvalidDiseaseObservationError` | 400 Bad Request | Updated `observed_at` is in the future |

---

### Delete Disease Observation

```
DELETE /api/v1/disease-observations/{observation_id}
```

**Status:** 204 No Content

**Response body:** None

**Exception Mapping:**

| Exception | HTTP Status | Condition |
|---|---|---|
| `DiseaseObservationNotFoundError` | 404 Not Found | Observation UUID does not exist |

---

## Disease Observation API Architectural Decisions

### POST anchors to `/crops/{crop_id}` (ADR-010-01)

Disease pressure is a per-crop-cycle measurement. The creation endpoint uses `/crops/{crop_id}/disease-observations`. The server resolves `field_id` from the crop record.

### `field_id` Denormalization (ADR-010-02)

`DiseaseObservationResponse` exposes both `crop_id` and `field_id`. `field_id` is resolved server-side at creation and stored denormalized for direct field-scoped list queries.

### `crop_id` Immutability at API Level (ADR-010-05)

`UpdateDiseaseObservationRequest` excludes `crop_id` and `field_id`. If a record was logged against the wrong crop, it must be deleted and re-created.

### Shared Enum Strategy (ADR-010-06)

`DiseaseSeverity` and `DiagnosisMethod` are defined in `app/core/enums.py` and exposed through OpenAPI schema definitions for Swagger consumers.

### HTTP Status Code Reference for Disease Observation Domain

| Code | Meaning | When Used |
|---|---|---|
| 201 Created | Observation persisted | Successful POST |
| 200 OK | Observation(s) returned | Successful GET or PATCH |
| 204 No Content | Observation deleted | Successful DELETE |
| 400 Bad Request | Invalid observation | Future `observed_at` |
| 404 Not Found | Resource absent | Crop or observation UUID not found |

---

## Irrigation Event API Architectural Decisions

### PATCH is permitted (ADR-008-02)

Unlike `SensorReading` (immutable telemetry), `IrrigationEvent` supports PATCH. Irrigation events are human-logged management actions. Operators may need to correct volume, duration, or end time after the event. Mutability is the correct model for operational management data.

### 400 for Invalid Timestamps (ADR-008-03)

`InvalidIrrigationTimestampError` maps to HTTP 400 (Bad Request), not 422 (Unprocessable Entity).

Rationale: `started_at` in the future or `ended_at` < `started_at` represent semantically incorrect requests from the client's perspective — a logical contradiction in the request payload rather than an unprocessable semantic. HTTP 400 is the appropriate signal for correctable client logic errors.

### HTTP Status Code Reference for Irrigation Event Domain

| Code | Meaning | When Used |
|---|---|---|
| 201 Created | Event persisted | Successful POST |
| 200 OK | Event(s) returned | Successful GET or PATCH |
| 204 No Content | Event deleted | Successful DELETE |
| 400 Bad Request | Invalid timestamp | Future `started_at` or `ended_at` < `started_at` |
| 404 Not Found | Resource absent | Field or event UUID not found |
