# API Design

## Existing Endpoints

### Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

### Version

* GET /api/v1/version

---

## Field Domain Endpoints

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


## API Architecture

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
└── Crops

### Soil Profile Domain

Field
└── SoilProfile

### Weather Record Domain

Field
└── WeatherRecords

### Sensor Reading Domain (Phase 7)

Field
└── SensorReadings (append-only telemetry)

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

### Sensor Reading Domain (Phase 7)

* Field must exist before sensor reading creation (→ 404 Not Found)
* `recorded_at` must be timezone-aware; naive datetimes are rejected (→ 422 Unprocessable Entity)
* `recorded_at` must not be in the future; future timestamps are rejected (→ 422 Unprocessable Entity)
* No sensor value range validation (reserved for future ingestion and SensorDevice domains)
* No update operation permitted — SensorReading is immutable (no PATCH, no PUT)
* Telemetry list responses are ordered by `recorded_at DESC` (most recent first)
* Administrative deletion is supported; modification is forbidden

---

## Current API Inventory

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

### Sensor Readings (Phase 7)

* POST   /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/fields/{field_id}/sensor-readings
* GET    /api/v1/sensor-readings/{sensor_reading_id}
* DELETE /api/v1/sensor-readings/{sensor_reading_id}

---

## Future API Evolution

* Irrigation APIs (Phase 8)
* Yield Analytics APIs (Phase 9)
* Disease Observation APIs (Phase 10)
* Satellite Imagery APIs (Phase 11)
* AI Recommendation APIs (Phase 12+)
* Sensor Aggregation APIs (TimescaleDB continuous aggregates)
* Digital Twin State API
* GaaS / Farm Copilot API


---

## Phase 6 Validation Status

Phase 6 AI Readiness Foundation has been completed.

Validation completed across:
- ORM Models
- Schemas
- Services
- Routers
- OpenAPI Documentation
- Backward Compatibility

Critical router exception handling issues were identified and fixed during stabilization.

---

## Sensor Reading Domain Endpoints (Phase 7)

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
