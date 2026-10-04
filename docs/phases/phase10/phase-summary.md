# Phase 10 — Disease Observation Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `d3e7b2a9f1c4`  
**Revises:** `b7e2a9f4c8d3` (Phase 9 — yield_records)

---

## What This Phase Achieved

Phase 10 introduced the DiseaseObservation domain — the first domain that captures **biological risk events** in the field. A DiseaseObservation records that a specific disease or pest condition was observed on a crop: what was found, how severe it was, how much of the crop was affected, and how the diagnosis was made.

DiseaseObservation provides the **primary ground-truth training data** for the Phase 13 alert engine's disease risk models. Without recorded observations of actual disease events, the AI cannot learn to predict or detect disease patterns from sensor and satellite signals.

Two architectural decisions were established here:

1. **Crop-anchored with denormalized `field_id`** — following the same pattern as YieldRecord (Phase 9). Disease events are anchored to the crop cycle in which they were observed, but `field_id` is denormalized to enable field-level queries without joining through crops.
2. **Dual list endpoints (by crop AND by field)** — uniquely, DiseaseObservation supports listing both by crop cycle and by field across all crop cycles. Disease history across seasons is a key agronomic intelligence input that must not require knowledge of individual crop cycle IDs.

---

## Domain Hierarchy After Phase 10

```
Farm
└── Field
     ├── Crop
     │    ├── YieldRecord         (Phase 9)
     │    └── DiseaseObservation  ← introduced (mutable, crop-cycle event)
     ├── SoilProfile              (Phase 4)
     ├── WeatherRecord            (Phase 5)
     ├── SensorReading            (Phase 7)
     └── IrrigationEvent          (Phase 8)
```

---

## Database Changes

**PostgreSQL ENUM type created:** `disease_severity`

| Value | Meaning |
|-------|---------|
| `LOW` | Minor presence, no significant crop impact |
| `MEDIUM` | Moderate spread, manageable with treatment |
| `HIGH` | Significant spread, yield at risk |
| `CRITICAL` | Severe outbreak, immediate intervention required |

**PostgreSQL ENUM type created:** `diagnosis_method`

| Value | Description |
|-------|-------------|
| `VISUAL_INSPECTION` | Field scout assessment |
| `LAB_ANALYSIS` | Pathogen identification via laboratory |
| `IMAGE_AI` | AI-powered image classification (e.g., drone imagery) |
| `AGRONOMIST` | Expert agronomist assessment |
| `SENSOR_DETECTED` | IoT sensor-triggered detection |

**Table created:** `disease_observations`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID (PK) | NOT NULL | — | UUID v4 primary key |
| `crop_id` | UUID (FK → crops.id, CASCADE) | NOT NULL | — | Primary domain anchor — crop cycle FK |
| `field_id` | UUID (FK → fields.id, CASCADE) | NOT NULL | — | Denormalized FK (ADR-009-02) |
| `observed_at` | TIMESTAMPTZ | NOT NULL | — | Observation timestamp — primary time key; composite PK component |
| `disease_name` | VARCHAR(255) | NOT NULL | — | Free-text disease/pest identifier, e.g. `Fusarium Wilt`, `Aphid Infestation` |
| `severity` | ENUM `disease_severity` | NOT NULL | — | Impact level — drives Phase 13 alert severity |
| `affected_area_percent` | NUMERIC(5,2) | NULL | — | % of crop affected; valid range [0, 100] |
| `diagnosis_method` | ENUM `diagnosis_method` | NOT NULL | — | How the observation was made |
| `treatment_applied` | TEXT | NULL | — | Treatment applied in response, if any |
| `notes` | TEXT | NULL | — | Operator annotations |
| `created_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-set |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `now()` | Server-set |

**Constraints and indexes (6 total):**

| Name | Type | Columns | Purpose |
|------|------|---------|---------|
| `fk_disease_observations_crop_id` | FK → `crops.id` ON DELETE CASCADE | `crop_id` | Cascade delete |
| `fk_disease_observations_field_id` | FK → `fields.id` ON DELETE CASCADE | `field_id` | Cascade delete |
| `pk_disease_observations` | PRIMARY KEY | `id` | Explicit named PK |
| `ix_disease_observations_crop_id` | B-tree | `crop_id` | "All observations for a crop cycle" |
| `ix_disease_observations_field_id` | B-tree | `field_id` | "All observations for a field across crops" |
| `ix_disease_observations_observed_at` | B-tree | `observed_at` | Time-range queries; TimescaleDB partition key |
| `ix_disease_observations_disease_name` | B-tree | `disease_name` | "All observations of a specific disease across the platform" |
| `ix_disease_observations_severity` | B-tree | `severity` | "Filter HIGH/CRITICAL severity across all crops" |
| `ix_disease_observations_crop_id_observed_at` | Compound B-tree | `(crop_id, observed_at)` | **Primary access pattern** — disease history for a crop over time |

---

## Phase 12 Upgrade (TimescaleDB)

`disease_observations` was promoted to a **TimescaleDB hypertable** in Phase 12, partitioned by `observed_at`. The continuous aggregate `ca_disease_weekly` computes weekly disease event counts and average severity per field, used by the Phase 13 alert engine as a smoothed risk signal. Retention policy: 7 years (regulatory requirement for crop health records).

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/crops/{crop_id}/disease-observations` | Log a disease observation; `field_id` resolved server-side |
| GET | `/api/v1/crops/{crop_id}/disease-observations` | List by crop cycle (paginated) |
| GET | `/api/v1/fields/{field_id}/disease-observations` | List by field across all crop cycles (paginated) |
| GET | `/api/v1/disease-observations/{observation_id}` | Get a single observation |
| PATCH | `/api/v1/disease-observations/{observation_id}` | Partial update (`crop_id` / `field_id` immutable) |
| DELETE | `/api/v1/disease-observations/{observation_id}` | Delete |

**Notable design:** The `/fields/{field_id}/disease-observations` endpoint is unique among crop-anchored domains. This cross-season field view is essential for agronomic intelligence — e.g., "Has this field had Fusarium outbreaks in the past 3 seasons?"

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Crop must exist before DiseaseObservation creation | `DiseaseObservationService` |
| `field_id` auto-resolved from crop | `DiseaseObservationService.create_disease_observation()` |
| `affected_area_percent` must be in [0, 100] if provided | Pydantic schema validator |
| `observed_at` must be timezone-aware | `DiseaseObservationService` |
| `crop_id` is immutable after creation | `DiseaseObservationService` — rejects PATCH targeting `crop_id` |
| Observation must exist before update or delete | `DiseaseObservationService` |

---

## Architecture Established

**Biological risk event pattern** — DiseaseObservation is the first domain that captures non-continuous, threshold-triggered biological events. The `disease_severity` ENUM is the precedent for the Phase 13 `AlertSeverity` ENUM (`INFO / WARNING / HIGH / CRITICAL`), which reuses the same 4-tier escalation model.

**Cross-season field view** — the dual list endpoint (`by crop` + `by field`) pattern was introduced here. It was not needed in earlier domains because weather, sensor, and irrigation data are already field-anchored. For crop-anchored domains where historical cross-season analysis is important, both endpoints are required.

**`disease_name` as free text** — the decision not to enumerate disease names was deliberate. The set of diseases and pests is region- and crop-specific, changes with new pathogen strains, and cannot be meaningfully bounded at schema design time. The `ix_disease_observations_disease_name` index enables efficient text equality filtering despite free-form storage.

---

## Business Value

- Field-level disease history for crop health analytics
- Ground-truth labels for Phase 13 disease risk alert engine (`DISEASE_RISK_HIGH`, `DISEASE_OUTBREAK` alert types)
- `severity` × `affected_area_percent` product = crop loss risk score input for recommendation engine
- Cross-season disease recurrence analysis for rotational disease management decisions
- `ca_disease_weekly` continuous aggregate (Phase 12) feeds the Phase 13 alert engine as a smoothed weekly risk signal

---

## What Was Deferred

- Disease identification from drone imagery (AI image classification pipeline)
- Disease spread modelling
- Integration with plant pathology databases
- Automated API tests
