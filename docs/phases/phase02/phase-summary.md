# Phase 2 — Field Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `3b7e9f1a2c85`  
**Revises:** `8f3a1c2d9e04` (Phase 1 — farms table)

---

## What This Phase Achieved

Phase 2 delivered the first complete domain vertical slice: model → schema → repository → service → API. It also established the clean architecture pattern (BaseRepository, DI via `deps.py`, service-layer domain exceptions) that every subsequent phase follows without deviation.

The Field domain introduced the Farm → Field parent-child relationship, the foundational unit of precision agriculture: a geospatially-located parcel of land that belongs to one farm and carries all subsequent agronomic observations.

---

## Domain Hierarchy After Phase 2

```
Farm
└── Field   ← introduced (full CRUD)
```

---

## Database Changes

**Table created:** `fields`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID (PK) | NOT NULL | UUID v4 primary key |
| `farm_id` | UUID (FK → farms.id) | NOT NULL | Parent farm |
| `name` | VARCHAR(255) | NOT NULL | Display name of the field |
| `area_hectares` | NUMERIC(10,2) | NULL | Field area in hectares |
| `soil_type` | VARCHAR(50) | NULL | Dominant soil classification (free text at Phase 2; replaced by SoilProfile in Phase 4) |
| `latitude` | NUMERIC(10,6) | NULL | WGS-84 latitude [-90, 90] |
| `longitude` | NUMERIC(10,6) | NULL | WGS-84 longitude [-180, 180] |
| `created_at` | TIMESTAMPTZ | NOT NULL | Server-side row creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Server-side last-updated timestamp |

**Constraints and indexes:**

| Name | Type | Columns |
|------|------|---------|
| FK on `farm_id` | FOREIGN KEY → `farms.id` | `farm_id` |
| `ix_fields_farm_id` | B-tree | `farm_id` |

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/farms/{farm_id}/fields` | Create a field under a farm |
| GET | `/api/v1/farms/{farm_id}/fields` | List all fields for a farm |
| GET | `/api/v1/fields/{field_id}` | Get a single field by ID |
| PATCH | `/api/v1/fields/{field_id}` | Partial update of a field |
| DELETE | `/api/v1/fields/{field_id}` | Delete a field |

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Farm must exist before field creation | `FieldService.create_field` → `FarmRepository.get_by_id` |
| Field name must be unique within a farm | `FieldService` → `FieldRepository.get_by_farm_and_name` |
| Field must exist before update or delete | `FieldService.update_field` / `delete_field` |

---

## Architecture Established

**BaseRepository pattern** — introduced here and reused unchanged through Phase 13:
- `get_by_id(id) → Model | None`
- `create(data: dict) → Model`
- `update(id, data: dict) → Model | None`
- `delete(id) → bool`

**Dependency injection via `deps.py`** — `FieldServiceDep = Annotated[FieldService, Depends(get_field_service)]` pattern established. Every subsequent domain adds one factory function and one `Annotated` alias.

**Domain exception translation at API boundary:**
- `FarmNotFoundError` → HTTP 404
- `DuplicateFieldNameError` → HTTP 409

**Service layer coordinates multiple repositories** — `FieldService` uses both `FieldRepository` and `FarmRepository`. This multi-repository coordination pattern recurs at every phase.

---

## Business Value

- Farm → Field relationship enables field-level precision agriculture
- Geospatial foundation (latitude, longitude) for all future spatial analytics
- Area tracking for yield-per-hectare calculations
- Domain hierarchy ready for Crop (Phase 3) and SoilProfile (Phase 4)

---

## What Was Deferred

- GIS polygon boundaries (PostGIS)
- Field analytics and reporting
- Automated API tests
- Advanced pagination
