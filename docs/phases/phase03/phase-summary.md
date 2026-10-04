# Phase 3 — Crop Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `5c2d8e3f7a19`  
**Revises:** `3b7e9f1a2c85` (Phase 2 — fields table)

---

## What This Phase Achieved

Phase 3 completed the core agricultural hierarchy: Farm → Field → Crop. A Crop represents one crop cycle planted on a field — from planting date through harvest. It introduced the first PostgreSQL ENUM type (`crop_status`) and established the lifecycle state machine pattern used by Recommendation and Alert domains in Phase 13.

---

## Domain Hierarchy After Phase 3

```
Farm
└── Field
     └── Crop   ← introduced (full CRUD)
```

---

## Database Changes

**Table created:** `crops`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID (PK) | NOT NULL | UUID v4 primary key |
| `field_id` | UUID (FK → fields.id) | NOT NULL | Parent field |
| `crop_name` | VARCHAR(255) | NOT NULL | Common or scientific name (e.g. `Maize`, `Solanum lycopersicum`) |
| `crop_variety` | VARCHAR(255) | NULL | Cultivar or hybrid designation (e.g. `DKC 6870`) |
| `planting_date` | DATE | NOT NULL | Planting or planned planting date |
| `expected_harvest_date` | DATE | NULL | Agronomically projected harvest date |
| `actual_harvest_date` | DATE | NULL | Actual harvest completion date — set only when `status = HARVESTED` |
| `status` | ENUM `crop_status` | NOT NULL | Lifecycle state; default `PLANNED` |
| `created_at` | TIMESTAMPTZ | NOT NULL | Server-side row creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Server-side last-updated timestamp |

**PostgreSQL ENUM type created:** `crop_status`

| Value | Meaning |
|-------|---------|
| `PLANNED` | Crop cycle planned, not yet planted (default) |
| `PLANTED` | Seeds or seedlings in ground |
| `GROWING` | Active growth phase |
| `HARVESTED` | Harvest complete; `actual_harvest_date` should be set |

**Constraints and indexes:**

| Name | Type | Columns |
|------|------|---------|
| FK on `field_id` | FOREIGN KEY → `fields.id` | `field_id` |
| `ix_crops_field_id` | B-tree | `field_id` |

**Note on enum migration pattern:** Phase 3 encountered a `DuplicateObjectError` when `sa.Enum` attempted to create the type twice. This was the first encounter of the PostgreSQL ENUM lifecycle problem later formally resolved in Phase 7 (via `postgresql.ENUM` + `create_type=False`) and documented as **ADR-008-01**.

---

## AI Readiness Columns Added (Phase 6 — added to this table)

Phase 6 (`005_add_p1_ai_readiness_columns.py`, revision `f3a8c1d9e047`) added these columns to `crops`:

| Column | Type | Purpose |
|--------|------|---------|
| `actual_yield_tons_ha` | NUMERIC(10,4) | Harvest yield — primary AI training label |
| `expected_yield_tons_ha` | NUMERIC(10,4) | Agronomist yield benchmark |
| `seeding_rate_kg_ha` | NUMERIC(8,3) | Planting density — AI feature input |
| `growth_stage` | VARCHAR(20) | BBCH phenological stage code (e.g. `BBCH-59`) |

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fields/{field_id}/crops` | Create a crop cycle under a field |
| GET | `/api/v1/fields/{field_id}/crops` | List all crop cycles for a field |
| GET | `/api/v1/crops/{crop_id}` | Get a single crop by ID |
| PATCH | `/api/v1/crops/{crop_id}` | Partial update of a crop cycle |
| DELETE | `/api/v1/crops/{crop_id}` | Delete a crop cycle |

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Field must exist before crop creation | `CropService.create_crop` |
| `actual_harvest_date` only valid when `status = HARVESTED` | `CropService` validation |
| `expected_harvest_date` must be after `planting_date` | Schema-level validator |
| Crop must exist before update or delete | `CropService` |

---

## Architecture Established

**Grandchild domain pattern** — Crop is the third level of the hierarchy. `CropService` coordinates `CropRepository` + `FieldRepository`. This grandchild pattern is reused by `YieldRecord` (Phase 9) and `DiseaseObservation` (Phase 10).

**PostgreSQL ENUM precedent** — first use of a named PostgreSQL ENUM in the project. The enum lifecycle issue encountered here motivated the authoritative pattern documented in ADR-008-01 (Phase 7): always use `postgresql.ENUM` with explicit `.create()` / `.drop()` and `create_type=False` on the column.

---

## Business Value

- Complete Farm → Field → Crop hierarchy enables crop season tracking
- Lifecycle state machine (`PLANNED → PLANTED → GROWING → HARVESTED`) supports crop cycle management
- Foundation for yield tracking (Phase 9), disease observation (Phase 10), and AI yield prediction (Phase 13+)

---

## What Was Deferred

- Multi-cropping support (overlapping crop cycles)
- Crop rotation history
- Automated API tests
