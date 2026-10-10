# Phase 13 — Decision Intelligence Implementation Reference

**Status:** Complete  
**Delivery:** October 2026  
**Alembic HEAD (at Phase 13):** `h2i3j4k5l6m7`  
**Migrations added:** `g1h2i3j4k5l6` (recommendations), `h2i3j4k5l6m7` (alerts)

---

## 1. Purpose

Phase 13 added the **decision layer** on top of Phases 1–12 (data collection + TimescaleDB analytics):

1. **Farm CRUD API** — completed the Farm vertical slice deferred since Phase 1  
2. **Recommendation domain** — structured, lifecycle-managed agronomic decisions per field  
3. **Alert domain** — operational alerts with severity, acknowledgement, and optional link to a recommendation  

Records are **standard PostgreSQL tables** (not hypertables): low volume, mutable, with explicit validity and status semantics.

---

## 2. Implementation map

### 2.1 Farm API (Phase 1 model, Phase 13 API)

| Layer | Path |
|-------|------|
| Router | `backend/app/api/farms/router.py` |
| Service | `backend/app/services/farm.py` |
| Repository | `backend/app/db/repositories/farm.py` |
| Schemas | `backend/app/schemas/farm.py` |
| Model | `backend/app/db/models/farm.py` (existing) |
| DI | `FarmServiceDep` in `backend/app/api/deps.py` |

**Business rules:** `farm_code` uniqueness (`DuplicateFarmCodeError`); soft delete via `is_active = false` on DELETE.

### 2.2 Recommendation domain

| Layer | Path |
|-------|------|
| Router | `backend/app/api/recommendations/router.py` |
| Service | `backend/app/services/recommendation.py` |
| Repository | `backend/app/db/repositories/recommendation.py` |
| Schemas | `backend/app/schemas/recommendation.py` |
| Model | `backend/app/db/models/recommendation.py` |
| Migration | `backend/app/db/migrations/versions/g1h2i3j4k5l6_create_recommendations_table.py` |
| DI | `RecommendationServiceDep` in `backend/app/api/deps.py` |

**ORM relationships:** `Field.recommendations`, `Crop.recommendations` (back-refs; cascade delete-orphan on field side).

### 2.3 Alert domain

| Layer | Path |
|-------|------|
| Router | `backend/app/api/alerts/router.py` |
| Service | `backend/app/services/alert.py` |
| Repository | `backend/app/db/repositories/alert.py` |
| Schemas | `backend/app/schemas/alert.py` |
| Model | `backend/app/db/models/alert.py` |
| Migration | `backend/app/db/migrations/versions/h2i3j4k5l6m7_create_alerts_table.py` |
| DI | `AlertServiceDep` in `backend/app/api/deps.py` |

**ORM relationships:** `Field.alerts`; optional `recommendation_id` FK to `recommendations` (SET NULL on delete).

### 2.4 Registration

- `backend/app/db/models/__init__.py` — exports `Recommendation`, `Alert` for Alembic  
- `backend/app/services/__init__.py` — exports services and domain exceptions  
- `backend/app/api/router.py` — includes `farms_router`, `recommendations_router`, `alerts_router`  

### 2.5 Shared vocabulary

Five enum classes appended to `backend/app/core/enums.py`:

| Enum | Values (count) |
|------|----------------|
| `RecommendationType` | 6 |
| `RecommendationStatus` | 6 |
| `RecommendationPriority` | 4 |
| `AlertType` | 10 |
| `AlertSeverity` | 4 |

PostgreSQL ENUM types are created in the Phase 13 migrations using the same explicit lifecycle pattern as Phases 7–11 (ADR-008-01).

---

## 3. REST API surface

Base path: `/api/v1`. **16 new endpoints** (51 → 66 total). Prior phase endpoints unchanged.

### 3.1 Farms

| Method | Path | Status |
|--------|------|--------|
| POST | `/farms` | 201 |
| GET | `/farms` | 200 (paginated list) |
| GET | `/farms/{farm_id}` | 200 |
| PATCH | `/farms/{farm_id}` | 200 |
| DELETE | `/farms/{farm_id}` | 204 (soft delete) |

### 3.2 Recommendations

| Method | Path | Status |
|--------|------|--------|
| POST | `/fields/{field_id}/recommendations` | 201 |
| GET | `/fields/{field_id}/recommendations` | 200 (`limit` ≤ 500, `offset`) |
| GET | `/recommendations/{recommendation_id}` | 200 |
| PATCH | `/recommendations/{recommendation_id}` | 200 |
| DELETE | `/recommendations/{recommendation_id}` | 204 |

### 3.3 Alerts

| Method | Path | Status |
|--------|------|--------|
| POST | `/fields/{field_id}/alerts` | 201 |
| GET | `/fields/{field_id}/alerts` | 200 |
| GET | `/fields/{field_id}/alerts/active` | 200 (unacknowledged only) |
| GET | `/alerts/{alert_id}` | 200 |
| PATCH | `/alerts/{alert_id}` | 200 |
| DELETE | `/alerts/{alert_id}` | 204 |

Full request/response field lists: [04-api-design.md](../04-api-design.md).  
**Note:** `04-api-design.md` lists five Alert routes; the **`/alerts/active`** route was added in implementation and should be treated as part of the contract.

Interactive exploration: `http://localhost:8000/docs` when the API is running.

---

## 4. Business rules (service layer)

### 4.1 Recommendation

| Rule | Enforcement |
|------|-------------|
| Field must exist | `RecommendationService` → `FieldNotFoundError` (404) |
| `crop_id`, if set, must belong to `field_id` | `CropFieldMismatchError` (422) |
| `confidence_score` ∈ [0, 1] when provided | Schema + service |
| `valid_until` > `valid_from` when both set | `InvalidRecommendationError` (422) |
| Status → `ACKNOWLEDGED` sets `acknowledged_at` | Service auto-set |

### 4.2 Alert

| Rule | Enforcement |
|------|-------------|
| Field must exist | `AlertService` |
| `crop_id` / `recommendation_id`, if set, must match field | Mismatch errors (422) |
| `triggered_at` required, timezone-aware | Schema; event time ≠ `created_at` |
| `expires_at` > `triggered_at` when set | Service validation |
| `is_acknowledged` true sets `acknowledged_at` | Service auto-set |

### 4.3 Storage pattern

- **Decision layer tables** = relational PostgreSQL, not TimescaleDB hypertables.  
- **`crop_id`**: nullable, `ON DELETE SET NULL` — field-level decisions survive crop cycle end.  
- **`alerts.recommendation_id`**: nullable, `ON DELETE SET NULL` — alerts persist if recommendation is deleted.

---

## 5. Architecture decisions (ADR-013)

| ID | Decision |
|----|----------|
| ADR-013-01 | Recommendations anchor on `field_id`; optional `crop_id` |
| ADR-013-02 | Same nullable `crop_id` pattern on Alert |
| ADR-013-03 | `triggered_at` mandatory on Alert (detection time) |
| ADR-013-04 | `confidence_score` as `NUMERIC(4,3)` |
| ADR-013-05 | `engine_version` on Recommendation for ML lineage |

Narrative and diagrams: [../../phases/phase13/phase-summary.md](../../phases/phase13/phase-summary.md).

---

## 6. Database objects

| Object | Migration |
|--------|-----------|
| Table `recommendations` + enums `recommendation_type`, `recommendation_status`, `recommendation_priority` | `g1h2i3j4k5l6` |
| Table `alerts` + enums `alert_type`, `alert_severity` | `h2i3j4k5l6m7` |

Column-level reference: [03-database.md](../03-database.md) (recommendations, alerts sections).

Apply migrations:

```bash
cd backend
alembic upgrade head
```

Expected HEAD after Phase 13: `h2i3j4k5l6m7`.

---

## 7. Phase 14 extension points

Service `create_*` methods include comments marking where **domain event publishing** (Redpanda) is intended:

| Service method | Intended event (Phase 14) |
|----------------|---------------------------|
| `RecommendationService.create_recommendation` | `RecommendationCreated` |
| `AlertService.create_alert` | `AlertTriggered` |
| (Phases 7–11 services) | e.g. `SensorReadingCreated`, `YieldRecordCreated`, … |

No event infrastructure is implemented in Phase 13; APIs and persistence are the contract for Phase 14 ML engines and streaming.

**Explicitly deferred from Phase 13:** automated API tests; alert deduplication; websocket push; automated ML pipelines writing recommendations.

---

## 8. Verification checklist

Use after deploy or local `alembic upgrade head`:

1. `GET /api/v1/health/ready` → database connected  
2. `POST /api/v1/farms` with valid `farm_code` → 201  
3. `POST /api/v1/fields/{field_id}/recommendations` with timezone-aware `valid_from` → 201  
4. `PATCH /api/v1/recommendations/{id}` with `status: ACKNOWLEDGED` → `acknowledged_at` populated  
5. `POST /api/v1/fields/{field_id}/alerts` with `triggered_at` → 201  
6. `GET /api/v1/fields/{field_id}/alerts/active` → only `is_acknowledged = false`  

---

## 9. Related documentation

| Topic | Location |
|-------|----------|
| Phase 13 narrative + Mermaid | [../../phases/phase13/phase-summary.md](../../phases/phase13/phase-summary.md) |
| Roadmap / capability framing | [../06-roadmap.md](../06-roadmap.md) |
| Phase history entry | [../07-phase-history.md](../07-phase-history.md) § Phase 13 |
| Implementation archaeology | [../architecture-implementation-history.md](../architecture-implementation-history.md) |
| Future phases (10–12 implementation refs) | [./README.md](./README.md) |
