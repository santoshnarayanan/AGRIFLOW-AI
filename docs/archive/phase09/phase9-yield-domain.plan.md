# Phase 9 – Yield Domain Implementation Plan

**Document:** Phase 9 – Full Implementation Plan  
**Date:** June 2026  
**Author:** AGRIFLOW-AI Architecture Team  
**Scope:** YieldRecord domain — entity design, migration, schemas, repository, service, API, ADRs, testing, AI readiness  
**Status:** Planning Complete — Ready for Step-by-Step Implementation

---

## 1. Business Problem

The `Crop` domain captures yield expectations and actuals as simple scalar columns
(`actual_yield_tons_ha`, `expected_yield_tons_ha`). This is inadequate for:

- Multiple measurement passes per harvest (plot sections, replication trials)
- Measurement method provenance (combine monitor vs. crop cut vs. remote sensing)
- Grain quality attributes alongside quantity (moisture content, test weight, grade)
- Granular time-keyed yield observations that feed the Phase 12 Yield Prediction Engine
- TimescaleDB hypertable promotion for historical yield analytics

`YieldRecord` is the dedicated domain for discrete, time-keyed yield observations. It does
not replace the Crop-level yield fields (which remain as quick-access summaries); it provides
the detailed observation log that AI pipelines require.

---

## 2. Use Cases

- Record a yield measurement for a completed crop cycle with measurement method classification
- Record multiple yield observations across sub-field plots within the same crop cycle
- Capture quality attributes (moisture content, test weight, quality grade) alongside quantity
- Retrieve yield history for a crop cycle ordered by measurement date (most recent first)
- Retrieve all yield records for a field across all crop cycles for historical analysis
- Correct a yield record after measurement error (PATCH, mutable domain)
- Delete an erroneous measurement

---

## 3. Domain Model Design

### Entity

`YieldRecord` — a discrete yield observation linked to a crop cycle.

### Key Architectural Decision: Crop-Anchored FK (ADR-009-01)

`YieldRecord` anchors to `crop_id` as its primary FK (not `field_id` alone), because yield
is per crop cycle, not per field point-in-time. This is the first "grandchild" domain in
AGRIFLOW-AI:

```
Farm → Field → Crop → YieldRecord
```

`field_id` is denormalized directly on `yield_records` (ADR-009-02) to:
- Enable direct field-scoped queries (`GET /fields/{field_id}/yield-records`) without
  a JOIN through `crops`
- Match the compound index access pattern used by the AI feature pipeline
- Maintain consistency with all other field-scoped query patterns

Both `crop_id` and `field_id` are `NOT NULL` with `ON DELETE CASCADE`.

### Columns

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | `UUID` | No | PK (AuditableModel) |
| `crop_id` | `UUID` (FK → crops.id) | No | ON DELETE CASCADE; primary domain anchor |
| `field_id` | `UUID` (FK → fields.id) | No | ON DELETE CASCADE; denormalized for direct field queries |
| `recorded_at` | `TIMESTAMPTZ` | No | Measurement timestamp; TimescaleDB partition key candidate |
| `yield_value_tons_ha` | `NUMERIC(10,4)` | No | Primary measurement; must be ≥ 0 |
| `measurement_method` | `ENUM(yield_measurement_method)` | No | Method classification |
| `area_harvested_ha` | `NUMERIC(10,4)` | Yes | Sub-field area; must be > 0 if supplied |
| `moisture_content_percent` | `NUMERIC(5,2)` | Yes | Grain moisture; must be in [0, 100] |
| `test_weight_kg_hl` | `NUMERIC(6,3)` | Yes | Grain density; must be > 0 if supplied |
| `quality_grade` | `VARCHAR(50)` | Yes | Free-form grade string (e.g. "Grade 1") |
| `notes` | `TEXT` | Yes | Operator annotations |
| `created_at` | `TIMESTAMPTZ` | No | AuditableModel |
| `updated_at` | `TIMESTAMPTZ` | No | AuditableModel |

---

## 4. Entity Relationships

```
Farm (1)
  └── Field (N)
        └── Crop (N)
              └── YieldRecord (N)   ← Phase 9
```

`yield_records` also carries a direct `field_id` FK enabling:

```
Field (1) ──────────────────────────────── YieldRecord (N)
              [denormalized path, no JOIN required]
```

`SoilProfile` remains 1:1 with `Field`. All other domain entities remain unchanged.

---

## 5. Business Rules

Rules enforced at the service layer:

| # | Rule | Exception |
|---|---|---|
| 1 | Crop must exist before YieldRecord creation | `CropNotFoundError` (imported from `app.services.crop`) |
| 2 | `recorded_at` must be timezone-aware | Pydantic `@field_validator` → 422 |
| 3 | `recorded_at` must not be in the future | `InvalidYieldRecordError` → 400 |
| 4 | `yield_value_tons_ha` must be ≥ 0 | Pydantic `ge=0` + service defence-in-depth |
| 5 | `moisture_content_percent`, when supplied, must be in [0, 100] | `InvalidYieldRecordError` → 400 |
| 6 | `area_harvested_ha`, when supplied, must be > 0 | `InvalidYieldRecordError` → 400 |
| 7 | `test_weight_kg_hl`, when supplied, must be > 0 | `InvalidYieldRecordError` → 400 |
| 8 | YieldRecord must exist before update | `YieldRecordNotFoundError` → 404 |
| 9 | YieldRecord must exist before delete | `YieldRecordNotFoundError` → 404 |

`crop_id` on `YieldRecord` is immutable — it cannot be changed via PATCH.
The schema's `Update` model excludes it.

---

## 6. Database Design

### New Enum

`yield_measurement_method` — placed in `app/core/enums.py` as
`YieldMeasurementMethod(str, enum.Enum)`:

| Value | Meaning |
|---|---|
| `MANUAL_SCALE` | Weighed with manual scales |
| `COMBINE_MONITOR` | Combine harvester yield monitor |
| `YIELD_MAP` | Precision yield mapping (GPS-referenced) |
| `REMOTE_SENSING` | Satellite or drone biomass estimation |
| `CROP_CUT` | FAO crop cut sampling method |
| `LABORATORY_ANALYSIS` | Lab sample extrapolation |
| `ESTIMATED` | Agronomist visual estimate |

Cross-domain reuse: Yield Prediction Engine (Phase 12), GaaS YieldAdvisor, Digital Twin
field productivity state.

### Migration

New migration: `create_yield_records_table`

- `down_revision`: `235a51cdf901` (Phase 8 head)
- Module-level `postgresql.ENUM("MANUAL_SCALE", ..., name="yield_measurement_method",
  create_type=False)` (ADR-008-01 pattern mandatory)
- `upgrade()`: enum.create(checkfirst=True) → create_table → 4 indexes
- `downgrade()`: drop compound index → individual indexes → table → enum.drop(checkfirst=False)

---

## 7. Index Strategy

| Index | Columns | Type | Primary Use Case |
|---|---|---|---|
| `ix_yield_records_crop_id` | `(crop_id)` | Single | All records for a crop cycle |
| `ix_yield_records_field_id` | `(field_id)` | Single | All records for a field (direct path) |
| `ix_yield_records_recorded_at` | `(recorded_at)` | Single | Time-range queries across all fields |
| `ix_yield_records_crop_id_recorded_at` | `(crop_id, recorded_at)` | Compound | Crop yield history in time order; primary AI feature pipeline access |

The compound index `(crop_id, recorded_at)` is the TimescaleDB query direction after
hypertable promotion on `recorded_at`.

---

## 8. ORM Design

File: `backend/app/db/models/yield_record.py`

- Inherits `AuditableModel`, `Base`
- `__tablename__ = "yield_records"`
- `__table_args__`: `Index("ix_yield_records_crop_id_recorded_at", "crop_id", "recorded_at")`
- `crop_id` FK with `index=True` (creates `ix_yield_records_crop_id`)
- `field_id` FK with `index=True` (creates `ix_yield_records_field_id`)
- `recorded_at` with `index=True` (creates `ix_yield_records_recorded_at`)
- `Enum(YieldMeasurementMethod, name="yield_measurement_method", create_constraint=True)`
  for column type
- `from __future__ import annotations` at top; `TYPE_CHECKING` guard for relationships
- Relationships: `crop: Mapped[Crop]`, `field: Mapped[Field]`
- `__repr__` method

Also modify:
- `backend/app/db/models/crop.py`: add `yield_records: Mapped[list[YieldRecord]] =
  relationship(back_populates="crop", cascade="all, delete-orphan")`
- `backend/app/db/models/field.py`: add `yield_records: Mapped[list[YieldRecord]] =
  relationship(back_populates="field", cascade="all, delete-orphan")`

---

## 9. Schema Design

File: `backend/app/schemas/yield_record.py`

### `YieldRecordBase(BaseModel)`
- `recorded_at: datetime` — `@field_validator` for timezone awareness
- `yield_value_tons_ha: Decimal` — `ge=0, decimal_places=4`
- `measurement_method: YieldMeasurementMethod`
- `area_harvested_ha: Decimal | None` — `ge=0, decimal_places=4`
- `moisture_content_percent: Decimal | None` — `ge=0, le=100, decimal_places=2`
- `test_weight_kg_hl: Decimal | None` — `ge=0, decimal_places=3`
- `quality_grade: str | None` — `max_length=50`
- `notes: str | None`

### `YieldRecordCreate(BaseModel)`
- Same fields as Base (required: `recorded_at`, `yield_value_tons_ha`, `measurement_method`)
- `crop_id` excluded — injected from URL path
- `field_id` excluded — resolved server-side from crop record

### `YieldRecordUpdate(BaseModel)`
- All fields optional (sparse PATCH)
- `crop_id` excluded — immutable after creation
- `recorded_at: datetime | None` — `@field_validator` for timezone awareness

### `YieldRecordResponse(YieldRecordBase)`
- `model_config = ConfigDict(from_attributes=True)`
- `id: uuid.UUID`
- `crop_id: uuid.UUID`
- `field_id: uuid.UUID`
- `created_at: datetime`
- `updated_at: datetime`

---

## 10. Repository Design

File: `backend/app/db/repositories/yield_record.py`

`YieldRecordRepository(BaseRepository[YieldRecord])`:

| Method | Source | Notes |
|---|---|---|
| `get_by_id(record_id)` | Inherited + retyped | |
| `create(data)` | Inherited + retyped | |
| `update(record_id, data)` | Inherited + retyped | |
| `delete(record_id)` | Inherited + retyped | |
| `list_by_crop(crop_id, *, limit, offset)` | Custom | `WHERE crop_id = ? ORDER BY recorded_at DESC` |
| `list_by_field(field_id, *, limit, offset)` | Custom | `WHERE field_id = ? ORDER BY recorded_at DESC` |
| `exists(record_id)` | Custom | `SELECT id WHERE id = ?` PK-only probe |

The compound index `(crop_id, recorded_at)` covers `list_by_crop`.
The `field_id` index covers `list_by_field`.

Also modify `backend/app/db/repositories/__init__.py`:
add `YieldRecordRepository` import and `__all__` entry.

---

## 11. Service Design

File: `backend/app/services/yield_record.py`

### Domain Exceptions

```python
class YieldRecordNotFoundError(ValueError): ...
class InvalidYieldRecordError(ValueError): ...
```

`CropNotFoundError` imported from `app.services.crop` — not re-declared (same pattern as
`FieldNotFoundError` reuse in `IrrigationEventService`).

### `YieldRecordService`

Constructor: `yield_record_repository: YieldRecordRepository`,
`crop_repository: CropRepository`

| Method | Business Rules Applied |
|---|---|
| `create_yield_record(crop_id, payload)` | Rule 1 (crop exists), Rule 3 (not future), Rules 4–7 (measurement validation); extract `field_id` from crop ORM |
| `get_yield_record(record_id)` | Returns `None` if not found (router handles 404) |
| `list_crop_yield_records(crop_id, *, limit, offset)` | No validation at list time |
| `list_field_yield_records(field_id, *, limit, offset)` | No validation at list time |
| `update_yield_record(record_id, payload)` | Rule 8 (exists), Rule 3 if `recorded_at` in payload, Rules 4–7 for changed measurement fields |
| `delete_yield_record(record_id)` | Rule 9 (exists via delete() returning False) |

### Module-Level Helpers (independently testable)

- `_validate_not_future(*, recorded_at: datetime, log: Any) -> None`
  — same pattern as in `irrigation_event.py`
- `_validate_measurement_values(*, yield_value_tons_ha, moisture_content_percent,
  area_harvested_ha, test_weight_kg_hl, log) -> None`

### Future Extension Point (in `create_yield_record`, after persistence)

```
# YieldRecordCreated event → Redpanda / Kafka topic
# Digital Twin field productivity state update
# CQRS read-model projection
# Phase 12 Yield Prediction Engine trigger
# GaaS YieldAdvisor tool layer
```

Also modify `backend/app/services/__init__.py`:
add imports for `YieldRecordService`, `YieldRecordNotFoundError`, `InvalidYieldRecordError`.

---

## 12. API Design

File: `backend/app/api/yield_records/router.py`

`router = APIRouter(tags=["Yield Records"])`

| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/crops/{crop_id}/yield-records` | 201 Created | Log a yield observation for a crop cycle |
| `GET` | `/crops/{crop_id}/yield-records` | 200 OK | List yield records for a crop (paginated, `recorded_at DESC`) |
| `GET` | `/fields/{field_id}/yield-records` | 200 OK | List all yield records for a field (paginated, `recorded_at DESC`) |
| `GET` | `/yield-records/{yield_record_id}` | 200 OK | Fetch a single yield record |
| `PATCH` | `/yield-records/{yield_record_id}` | 200 OK | Partial update |
| `DELETE` | `/yield-records/{yield_record_id}` | 204 No Content | Delete a yield record |

### Exception → HTTP Mapping

| Exception | HTTP Status |
|---|---|
| `CropNotFoundError` | 404 Not Found |
| `YieldRecordNotFoundError` | 404 Not Found |
| `InvalidYieldRecordError` | 400 Bad Request |

### Query Parameters (list endpoints)

- `limit: int = Query(default=100, ge=1, le=500)`
- `offset: int = Query(default=0, ge=0)`

Response type for list endpoints: `PaginatedResponse[YieldRecordResponse]`

---

## 13. Dependency Injection Changes

### `backend/app/api/deps.py`

Add imports:
```python
from app.db.repositories.yield_record import YieldRecordRepository
from app.services.yield_record import YieldRecordService
```

Add factory and alias:
```python
def get_yield_record_service(session: SessionDep) -> YieldRecordService:
    return YieldRecordService(
        yield_record_repository=YieldRecordRepository(session),
        crop_repository=CropRepository(session),
    )

YieldRecordServiceDep = Annotated[YieldRecordService, Depends(get_yield_record_service)]
```

### `backend/app/api/router.py`

Add:
```python
from app.api.yield_records.router import router as yield_records_router
api_router.include_router(yield_records_router)
```

---

## 14. Validation Rules

### Pydantic Schema Layer

| Field | Validation | Error |
|---|---|---|
| `recorded_at` | `@field_validator` — must be timezone-aware | 422 Unprocessable Entity |
| `yield_value_tons_ha` | `ge=0` | 422 |
| `area_harvested_ha` | `ge=0` | 422 |
| `moisture_content_percent` | `ge=0, le=100` | 422 |
| `test_weight_kg_hl` | `ge=0` | 422 |
| `quality_grade` | `max_length=50` | 422 |

### Service Layer

| Rule | Validation | HTTP |
|---|---|---|
| Crop exists | `crop_repository.get_by_id` returns `None` | 404 |
| `recorded_at` not future | UTC comparison | 400 |
| `moisture_content_percent` in [0, 100] | Defence-in-depth beyond `le=100` Pydantic guard | 400 |
| `area_harvested_ha > 0` if supplied | Pydantic allows 0; service tightens to > 0 | 400 |
| `test_weight_kg_hl > 0` if supplied | Same reasoning | 400 |

Note: Pydantic `ge=0` permits exactly zero for `area_harvested_ha`; the service rejects it
because an observation with zero harvested area is agronomically invalid.

---

## 15. ADR-009 Series

| ADR | Decision |
|---|---|
| ADR-009-01 | `YieldRecord` anchors to `crop_id` as primary FK — yield is per crop cycle, not per field point-in-time |
| ADR-009-02 | `field_id` is denormalized directly on `yield_records` to enable field-scoped queries without JOIN through `crops`; both FKs are NOT NULL with ON DELETE CASCADE |
| ADR-009-03 | `recorded_at TIMESTAMPTZ NOT NULL` is the primary time key and TimescaleDB partition key candidate |
| ADR-009-04 | `YieldRecord` is mutable — PATCH is permitted; yield measurement corrections are legitimate operator actions |
| ADR-009-05 | `crop_id` is immutable after creation — `YieldRecordUpdate` excludes it; changing the crop association of a measurement is not a valid correction |
| ADR-009-06 | `area_harvested_ha > 0` (not `>= 0`) when supplied — a zero-area harvest is agronomically invalid; Pydantic `ge=0` is tightened at the service layer |
| ADR-009-07 | `YieldMeasurementMethod` is placed in `app/core/enums.py` for future reuse by Yield Prediction Engine (Phase 12), GaaS YieldAdvisor, and Digital Twin field productivity model |
| ADR-009-08 | `CropNotFoundError` is imported from `app.services.crop` — not re-declared in the yield service, following the `FieldNotFoundError` reuse pattern across child domains |
| ADR-009-09 | `InvalidYieldRecordError` maps to HTTP 400 Bad Request — measurement value violations are client-correctable logic errors, not schema errors |
| ADR-009-10 | `YieldRecordService.create_yield_record` contains a documented extension point for Redpanda publishing, Digital Twin updates, and Phase 12 model triggers |
| ADR-009-11 | `postgresql.ENUM` with `create_type=False` + explicit `.create()` / `.drop()` is used for `yield_measurement_method` — mandatory ADR-008-01 pattern for all new ENUM types |
| ADR-009-12 | List endpoints (`list_by_crop`, `list_by_field`) include pagination (`limit`/`offset`) from Phase 9 onwards — unlike Phase 7 SensorReading which deferred pagination |

---

## 16. Testing Strategy

### Unit Tests

- `test_validate_not_future`: timezone-naive input, future datetime, valid past datetime
- `test_validate_measurement_values`:
  - zero yield (valid), negative yield (invalid)
  - moisture 0 (valid), moisture 100 (valid), moisture 100.01 (invalid)
  - zero area (invalid), positive area (valid)
  - zero test weight (invalid), positive test weight (valid)

### Integration Tests (Repository)

- `test_list_by_crop_returns_ordered_records` — verify `recorded_at DESC` ordering
- `test_list_by_field_returns_all_crop_records` — multiple crops on one field
- `test_exists_returns_false_for_unknown_id`
- `test_pagination_limit_offset`

### API Integration Tests

| Endpoint | Test Cases |
|---|---|
| POST `/crops/{crop_id}/yield-records` | 201 success, 404 crop not found, 400 future timestamp, 400 invalid moisture |
| GET `/crops/{crop_id}/yield-records` | 200 empty list, 200 paginated list, ordering verified |
| GET `/fields/{field_id}/yield-records` | 200 multi-crop list |
| GET `/yield-records/{id}` | 200 found, 404 not found |
| PATCH `/yield-records/{id}` | 200 partial update, 404 not found, 400 invalid measurement |
| DELETE `/yield-records/{id}` | 204 success, 404 not found |

---

## 17. AI Readiness Impact

| AI Capability | Impact |
|---|---|
| Yield Prediction (Phase 12) | Provides the primary training label (`yield_value_tons_ha` per crop cycle, timestamped) — the critical gap in the Phase 6 AI Data Readiness Assessment |
| Irrigation Optimization | Enables water-use efficiency (`water_volume_liters` from IrrigationEvent ÷ `yield_value_tons_ha` = litres per tonne) |
| Digital Twin | Field productivity state (`latest_yield_by_crop_type`) derived from YieldRecord history |
| GaaS YieldAdvisor | `list_by_field` endpoint becomes a GaaS tool for natural language yield history queries |
| Disease-Yield Correlation | Cross-join of YieldRecord with future DiseaseObservation (Phase 10) via shared `crop_id` |

Phase 6 AI Readiness Assessment identified `actual_yield_tons_ha` on the Crop model gave
82% yield prediction coverage. `YieldRecord` provides the remaining 18%: time-series
granularity, measurement method quality signals, and grain quality attributes.

---

## 18. Future Extensibility

- **TimescaleDB (Phase 13+):** `recorded_at TIMESTAMPTZ NOT NULL` satisfies hypertable
  requirement. Activation:
  `SELECT create_hypertable('yield_records', 'recorded_at', chunk_time_interval => INTERVAL '1 season');`
- **Yield Prediction Engine (Phase 12):** `list_by_crop` with date range provides feature
  vector assembly. `measurement_method` acts as data quality weight in the training pipeline.
- **CQRS:** Write side (`create`, `update`, `delete`) and read side (`list_by_crop`,
  `list_by_field`) are already separated at the repository interface boundary.
- **Redpanda (Phase 14+):** `YieldRecordCreated` event on topic `yield.records.created`
  triggers AI ingestion pipeline, Digital Twin, CQRS projector.
- **YieldRecord V2 (P2 attributes):** `dry_matter_percent`, `protein_content_percent`,
  `harvest_loss_percent` — additive nullable `ADD COLUMN` migrations (ADR-006-01 pattern).
- **Phase 10 cross-reference:** `yield_records.crop_id` joins to
  `disease_observations.crop_id` (future) for disease-impact correlation models.

---

## Files Summary

### New Files (7)

| File | Purpose |
|---|---|
| `backend/app/db/models/yield_record.py` | ORM model |
| `backend/app/schemas/yield_record.py` | Pydantic schemas (Base, Create, Update, Response) |
| `backend/app/db/repositories/yield_record.py` | Repository |
| `backend/app/services/yield_record.py` | Service + domain exceptions + helpers |
| `backend/app/api/yield_records/__init__.py` | Package marker |
| `backend/app/api/yield_records/router.py` | API router (6 endpoints) |
| `backend/app/db/migrations/versions/XXXX_create_yield_records_table.py` | Alembic migration |

### Modified Files (7)

| File | Change |
|---|---|
| `backend/app/core/enums.py` | Add `YieldMeasurementMethod` (7 values) |
| `backend/app/db/models/crop.py` | Add `yield_records` relationship |
| `backend/app/db/models/field.py` | Add `yield_records` relationship |
| `backend/app/db/repositories/__init__.py` | Export `YieldRecordRepository` |
| `backend/app/services/__init__.py` | Export `YieldRecordService`, `YieldRecordNotFoundError`, `InvalidYieldRecordError` |
| `backend/app/api/deps.py` | Add `get_yield_record_service` factory + `YieldRecordServiceDep` |
| `backend/app/api/router.py` | Include `yield_records_router` |

---

## Implementation Steps

| Step | Scope |
|---|---|
| Step 1 | Add `YieldMeasurementMethod` enum to `app/core/enums.py` |
| Step 2 | Create `YieldRecord` ORM model; add `yield_records` relationship to `Crop` and `Field` |
| Step 3 | Write Alembic migration: `yield_measurement_method` enum + `yield_records` table + 4 indexes |
| Step 4 | Create Pydantic schemas: `YieldRecordBase`, `YieldRecordCreate`, `YieldRecordUpdate`, `YieldRecordResponse` |
| Step 5 | Create `YieldRecordRepository` with `list_by_crop`, `list_by_field`, `exists`; update `repositories/__init__.py` |
| Step 6 | Create `YieldRecordService` with domain exceptions, validation helpers, extension point; update `services/__init__.py` |
| Step 7 | Create `yield_records` API router (6 endpoints); wire into `deps.py` and `api/router.py` |
