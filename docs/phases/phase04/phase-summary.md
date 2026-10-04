# Phase 4 — Soil Intelligence Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `13aabbe35d51`  
**Revises:** `5c2d8e3f7a19` (Phase 3 — crops table)

---

## What This Phase Achieved

Phase 4 introduced the SoilProfile domain — a one-to-one extension of a Field that captures the physical and chemical characteristics of the soil. It established the **one-to-one domain pattern** (unique index enforcing one SoilProfile per Field at the database level) and introduced the `SoilType` enum as a typed soil classification.

SoilProfile is a reference/master entity, not a time-series — it describes a Field's persistent soil characteristics rather than a stream of observations. This contrasts with WeatherRecord (Phase 5) and SensorReading (Phase 7).

---

## Domain Hierarchy After Phase 4

```
Farm
└── Field
     ├── Crop
     └── SoilProfile   ← introduced (one-to-one with Field)
```

---

## Database Changes

**Table created:** `soil_profiles`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID (PK) | NOT NULL | UUID v4 primary key |
| `field_id` | UUID (FK → fields.id) | NOT NULL | Parent field — enforced unique (one-to-one) |
| `soil_type` | ENUM `soil_type` | NOT NULL | Dominant soil texture classification |
| `ph` | NUMERIC(4,2) | NULL | Soil pH on the 0–14 scale; 7.0 = neutral |
| `organic_matter` | NUMERIC(6,3) | NULL | Organic matter content as % by weight |
| `nitrogen` | NUMERIC(8,4) | NULL | Total nitrogen concentration in mg/kg (ppm) |
| `phosphorus` | NUMERIC(8,4) | NULL | Available phosphorus concentration in mg/kg (ppm) |
| `potassium` | NUMERIC(8,4) | NULL | Available potassium concentration in mg/kg (ppm) |
| `notes` | TEXT | NULL | Free-text agronomist observations or lab report references |
| `created_at` | TIMESTAMPTZ | NOT NULL | Server-side row creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Server-side last-updated timestamp |

**PostgreSQL ENUM type created:** `soil_type`

| Value | Description |
|-------|-------------|
| `SANDY` | High sand content, low water retention |
| `CLAY` | High clay content, high water retention |
| `LOAM` | Balanced mixture — ideal for most crops |
| `SILT` | Fine particles, moderate fertility |
| `PEAT` | High organic content, acidic |
| `CHALK` | Alkaline, free-draining |

**Constraints and indexes:**

| Name | Type | Columns | Note |
|------|------|---------|------|
| FK on `field_id` | FOREIGN KEY → `fields.id` | `field_id` | |
| `ix_soil_profiles_field_id` | B-tree **UNIQUE** | `field_id` | Enforces one-to-one at DB level |

---

## AI Readiness Columns Added (Phase 6 — added to this table)

Phase 6 (`005_add_p1_ai_readiness_columns.py`, revision `f3a8c1d9e047`) added:

| Column | Type | Purpose |
|--------|------|---------|
| `soil_depth_cm` | NUMERIC(6,2) | Effective rooting zone depth — root zone constraint for FAO-56 water balance |
| `cation_exchange_capacity_meq` | NUMERIC(8,4) | Nutrient retention capacity — soil fertility AI feature |

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fields/{field_id}/soil-profile` | Create the soil profile for a field |
| GET | `/api/v1/fields/{field_id}/soil-profile` | Get the soil profile for a field |
| PATCH | `/api/v1/soil-profiles/{soil_profile_id}` | Partial update |
| DELETE | `/api/v1/soil-profiles/{soil_profile_id}` | Delete the soil profile |

Note: No `GET /api/v1/fields/{field_id}/soil-profiles` list endpoint — the one-to-one relationship means there is at most one profile per field.

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Field must exist before SoilProfile creation | `SoilProfileService.create_soil_profile` |
| Only one SoilProfile allowed per Field | `SoilProfileService` → check existing + unique index `ix_soil_profiles_field_id` |
| SoilProfile must exist before update or delete | `SoilProfileService` |

---

## Architecture Established

**One-to-one domain pattern** — both a service-level guard (`get_by_field_id` check before `create`) and a database-level `UNIQUE` index on `field_id`. Both layers are required: the service check gives a clean 409 error; the index is a safety net for concurrent requests.

**Nullable scientific columns** — all soil chemistry columns (`ph`, `organic_matter`, `nitrogen`, `phosphorus`, `potassium`) are nullable, reflecting real-world partial data: operators record what they have measured, not all fields. This partial-data pattern recurs across all observational domains.

---

## Business Value

- Soil nutrient tracking per field (N, P, K) — foundation for fertiliser optimisation
- pH monitoring — early soil degradation detection
- `soil_depth_cm` (Phase 6) feeds the FAO-56 water balance model for irrigation optimisation
- Foundation for soil health scoring and nutrient recommendation engine

---

## What Was Deferred

- Soil sampling history (time-series of soil measurements)
- Soil trend analysis
- Fertility scoring engine
- Nutrient recommendation engine
- Automated API tests
