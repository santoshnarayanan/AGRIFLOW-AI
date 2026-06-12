# API Design

## Existing Endpoints

### Health

- GET /api/v1/health/live
- GET /api/v1/health/ready

### Version

- GET /api/v1/version

---

## Field Domain Endpoints

### Create Field

- POST /api/v1/farms/{farm_id}/fields

### List Fields

- GET /api/v1/farms/{farm_id}/fields

### Get Field

- GET /api/v1/fields/{field_id}

### Update Field

- PATCH /api/v1/fields/{field_id}

### Delete Field

- DELETE /api/v1/fields/{field_id}

---

## Crop Domain Endpoints

### Create Crop

- POST /api/v1/fields/{field_id}/crops

### List Crops for Field

- GET /api/v1/fields/{field_id}/crops

### Get Crop

- GET /api/v1/crops/{crop_id}

### Update Crop

- PATCH /api/v1/crops/{crop_id}

### Delete Crop

- DELETE /api/v1/crops/{crop_id}

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

---

## HTTP Status Code Conventions

### Success

- 200 OK
- 201 Created
- 204 No Content

### Client Errors

- 400 Bad Request
- 404 Not Found

---

## Current API Coverage

### Health APIs

- Service Health
- Readiness Check

### Version APIs

- Application Version

### Field APIs

- Create Field
- List Fields
- Get Field
- Update Field
- Delete Field

### Crop APIs

- Create Crop
- List Crops
- Get Crop
- Update Crop
- Delete Crop

---

## Future API Evolution

- Soil Profile APIs
- Weather APIs
- Irrigation APIs
- Sensor APIs
- Yield Analytics APIs
- AI Recommendation APIs
- Satellite Imagery APIs
