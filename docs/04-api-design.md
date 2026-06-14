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

---

## Future API Evolution

* Weather APIs
* Irrigation APIs
* Sensor APIs
* Yield Analytics APIs
* AI Recommendation APIs
* Satellite Imagery APIs
