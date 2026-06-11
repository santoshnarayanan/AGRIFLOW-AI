# API Design

## Existing Endpoints

- GET /api/v1/health/live
- GET /api/v1/health/ready
- GET /api/v1/version

## Farm Domain Endpoints

- POST /api/v1/farms/{farm_id}/fields
- GET /api/v1/farms/{farm_id}/fields

## Field Domain Endpoints
- GET /api/v1/fields/{field_id}
- PATCH /api/v1/fields/{field_id}
- DELETE /api/v1/fields/{field_id}

## Request Flow

API -> Schema -> Service -> Repository -> PostgreSQL
