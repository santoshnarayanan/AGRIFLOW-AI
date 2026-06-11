# Database Design

## Current Schema

### farms
Primary agricultural entity.

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

## Relationships

Farm (1) -> (N) Fields

## Future Database Evolution

- Crop Domain
- Weather Data
- Soil Sensors
- Satellite Imagery
- GIS / PostGIS Support
- Field Boundary Polygons
