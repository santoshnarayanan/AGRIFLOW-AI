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


## Relationships

Farm (1) -> (N) Fields

Field (1) -> (N) Crops

Field (1) -> (1) SoilProfile


## Current Domain Hierarchy

Farm
└── Field
├── Crop
└── SoilProfile


## Implemented Migrations

- 001_create_farms_table
- 002_create_fields_table
- 003_create_crops_table
- 004_create_soil_profiles_table

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


## Future Database Evolution

- Weather Data
- Soil Sensors
- Satellite Imagery
- GIS / PostGIS Support
- Field Boundary Polygons
- Irrigation Management
- Yield Tracking
- AI Recommendation Engine
