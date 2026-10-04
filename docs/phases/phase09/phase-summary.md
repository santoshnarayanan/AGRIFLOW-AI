# Phase 9 — Yield Record Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `b7e2a9f4c8d3`  
**Revises:** `235a51cdf901` (Phase 8 — irrigation_events)

---

## What This Phase Achieved

Phase 9 introduced the YieldRecord domain — AGRIFLOW-AI's first **crop-cycle outcome** domain. A YieldRecord captures the measured harvest output of a crop cycle: how many tonnes per hectare were produced, by what measurement method, with what grain quality.

YieldRecord is the **primary AI training label** for the yield prediction engine. Its `yield_value_tons_ha` column is the dependent variable in all supervised learning models. Without accurately measured yield records, the AI platform cannot train or validate any prediction models.

Three architectural decisions were established here:

1. **Crop-anchored with denormalized `field_id` (ADR-009-02).** Yield is inherently a crop-cycle outcome — a YieldRecord belongs to a specific crop cycle, not just a field. However, `field_id` is also stored as a denormalized FK to avoid a join through the `crops` table in every field-level query.
2. **`crop_id` is immutable after creation (ADR-009-05).** Moving a yield record to a different crop cycle would corrupt the training data history. The service layer rejects any PATCH that changes `crop_id`.
3. **Composite PK `(id, recorded_at)` for TimescaleDB compatibility (ADR-002 Strategy A).** Ready for hypertable promotion without schema changes.

---

## Domain Hierarchy After Phase 9

```
Farm
└── Field
     ├── Crop
     │    ├── YieldRecord        ← introduced (mutable, crop-cycle outcome)
     │    └── DiseaseObservation (Phase 10)
     ├── SoilProfile             (Phase 4)
     ├── WeatherRecord           (Phase 5)
     ├── SensorReading           (Phase 7)
     └── IrrigationEvent         (Phase 8)
```

---

## Database Changes

**PostgreSQL ENUM type created:** `yield_measurement_method`

| Value | Description |
|-------|-------------|
| `MANUAL_SCALE` | Physical weighing by operator |
| `COMBINE_MONITOR` | Integrated yield monitor in harvesting machinery |
| `YIELD_MAP` | GPS-tagged yield map from combine |
| `REMOTE_SENSING` | Estimated from satellite spectral indices |
| `CROP_CUT` | Standard FAO crop-cut experiment |
| `LABORATORY_ANALYSIS` | Post-harvest sample analysis |
| `ESTIMATED` | Agronomist estimate — lowest confidence weight |

**Table created:** `yield_records`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID (PK) | NOT NULL | — | UUID v4 primary key |
| `crop_id` | UUID (FK → crops.id, CASCADE) | NOT NULL | — | Primary domain anchor — crop cycle FK |
| `field_id` | UUID (FK → fields.id, CASCADE) | NOT NULL | — | Denormalized FK (ADR-009-02) — avoids join through crops |
| `recorded_at` | TIMESTAMPTZ | NOT NULL | — | Harvest measurement timestamp — primary time key; composite PK component |
| `yield_value_tons_ha` | NUMERIC(10,4) | NOT NULL | — | **Primary AI training label** — must be ≥ 0 |
| `measurement_method` | ENUM `yield_measurement_method` | NOT NULL | — | Data quality weight in AI feature pipeline |
| `area_harvested_ha` | NUMERIC(10,4) | NULL | — | Harvested area; must be > 0 if supplied |
| `moisture_content_percent` | NUMERIC(5,2) | NULL | — | Grain moisture at time of harvest; valid range [0, 100] |
| `test_weight_kg_hl` | NUMERIC(6,3) | NULL | — | Bulk density — grain quality indicator |
| `quality_grade` | VARCHAR(50) | NULL | — | Free-form grade code, e.g. `Grade 1`, `Feed Grade` |
| `notes` | TEXT | NULL | — | Operator annotations |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-set |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-set |

**Constraints and indexes (4 total):**

| Name | Type | Columns | Purpose |
|------|------|---------|---------|
| `fk_yield_records_crop_id` | FK → `crops.id` ON DELETE CASCADE | `crop_id` | Cascade delete when crop is removed |
| `fk_yield_records_field_id` | FK → `fields.id` ON DELETE CASCADE | `field_id` | Cascade delete when field is removed |
| `pk_yield_records` | PRIMARY KEY | `id` | Explicit named PK |
| `ix_yield_records_crop_id` | B-tree | `crop_id` | "All yield records for a crop cycle" |
| `ix_yield_records_field_id` | B-tree | `field_id` | "All yield records for a field across crops" |
| `ix_yield_records_recorded_at` | B-tree | `recorded_at` | Time-range queries; TimescaleDB partition key |
| `ix_yield_records_crop_id_recorded_at` | Compound B-tree | `(crop_id, recorded_at)` | **Primary access pattern** — yield history for a crop cycle over time |

---

## Phase 12 Upgrade (TimescaleDB)

`yield_records` was promoted to a **TimescaleDB hypertable** in Phase 12, partitioned by `recorded_at`. The composite PK `(id, recorded_at)` established in this phase was specifically designed for this upgrade. Zero schema changes were required at Phase 12.

The continuous aggregate `ca_yield_seasonal` computes seasonal yield statistics per field, but is **exempt** from the standard retention policy — yield history is retained indefinitely as it is the primary AI training label.

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/crops/{crop_id}/yield-records` | Log a yield record; `field_id` resolved server-side from crop |
| GET | `/api/v1/crops/{crop_id}/yield-records` | List all records for a crop cycle (paginated) |
| GET | `/api/v1/yield-records/{yield_record_id}` | Get a single record |
| PATCH | `/api/v1/yield-records/{yield_record_id}` | Partial update (`crop_id` / `field_id` immutable) |
| DELETE | `/api/v1/yield-records/{yield_record_id}` | Delete |

**Notable design:** `field_id` is NOT accepted in the POST body. The API resolves it automatically from the crop's `field_id`. This prevents a caller from passing a `field_id` that doesn't match the crop.

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Crop must exist before YieldRecord creation | `YieldRecordService` |
| `field_id` auto-resolved from crop — not caller-supplied | `YieldRecordService.create_yield_record()` |
| `yield_value_tons_ha` must be ≥ 0 | Pydantic schema validator |
| `area_harvested_ha` must be > 0 if provided | Pydantic schema validator |
| `moisture_content_percent` must be in [0, 100] if provided | Pydantic schema validator |
| `crop_id` is immutable after creation | `YieldRecordService` — rejects any PATCH targeting `crop_id` (ADR-009-05) |
| YieldRecord must exist before update or delete | `YieldRecordService` |

---

## Architecture Established

**Crop-cycle outcome pattern** — YieldRecord is the canonical example of a domain that measures the end result of a crop cycle. `DiseaseObservation` (Phase 10) follows the same crop-anchored + denormalized-`field_id` pattern.

**AI training label design** — `measurement_method` enables the AI feature pipeline to weight training examples by data quality. `COMBINE_MONITOR` and `YIELD_MAP` samples carry higher confidence weights than `ESTIMATED` samples. This column is how measurement uncertainty is made explicit in the training data.

**Denormalized FK rationale (ADR-009-02)** — Querying yield records at the field level (e.g., "all yield records across all crop cycles for Field X") would require joining `yield_records → crops → fields`. The denormalized `field_id` eliminates this join, which matters at query time in the Phase 12 feature extraction pipeline that reads across all fields.

---

## Business Value

- Harvest outcome tracking per crop cycle — foundation for yield analysis
- `yield_value_tons_ha` is the dependent variable (training label) for the Phase 12/13 AI yield prediction model
- `measurement_method` enables confidence-weighted training in Phase 12 model pipelines
- `moisture_content_percent` and `quality_grade` support grain quality analytics and trading decisions

---

## What Was Deferred

- Multi-harvest support within a single crop cycle
- Yield benchmarking against regional averages
- Integration with grain trading and commodity price systems
- Automated API tests
