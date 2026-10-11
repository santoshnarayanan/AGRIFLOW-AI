# Phase 15 — Enterprise Intelligence Platform implementation reference

**Status:** In progress — slice 3 (Digital Twin foundation) delivered  
**ADR:** [ADR-007](../../../adr/ADR-007-ai-feature-store.md), [ADR-008](../../../adr/ADR-008-cqrs-dashboard-read-models.md), [ADR-009](../../../adr/ADR-009-digital-twin-field-state-foundation.md)  
**Migrations:** `k5l6m7n8o9p0`, `l6m7n8o9p0q1`, `m7n8o9p0q1r2` (`field_digital_twin_states`)

## Primary objective

Optimized operational intelligence for dashboards, AI, and Digital Twin — starting with governed ML feature materialisation.

## Delivered (slice 1 — Feature Store foundation)

| Component | Location |
|-----------|----------|
| Feature registry (CDD v1.0.0) | `backend/app/features/catalog.py`, `types.py` |
| CA / raw extraction SQL | `backend/app/db/repositories/feature_extraction.py` |
| Snapshot ORM | `backend/app/db/models/field_feature_snapshot.py` |
| Snapshot repository | `backend/app/db/repositories/field_feature_snapshot.py` |
| Feature Store service | `backend/app/services/feature_store.py` |
| REST API | `GET /api/v1/features/catalog`, materialize + snapshot reads under `/features/fields/...` |
| ML engine consumption | `MLEngineService` + engine stubs use latest snapshot when available |
| Contract tests | `backend/app/tests/test_feature_store_catalog.py` |

## Delivered (slice 2 — CQRS dashboard read models)

| Component | Location |
|-----------|----------|
| Field dashboard read model ORM | `backend/app/db/models/field_dashboard_read_model.py` |
| Projection metrics SQL | `backend/app/db/repositories/read_model_metrics.py` |
| Projection service | `backend/app/services/read_model_projection.py` |
| KPI highlights from Feature Store | `backend/app/read_models/kpi.py` |
| REST API | `GET/POST /api/v1/read-models/dashboard`, farm/field dashboard + refresh |
| Dashboard UI (KPI cards) | `frontend/src/pages/Dashboard.tsx` via `usePlatformDashboard` |

## Configuration

See `backend/.env.example` — Feature Store and `READ_MODEL_PROJECTION_VERSION`, `READ_MODEL_AUTO_REFRESH_ON_READ`.

## Delivered (slice 3 — Digital Twin foundation)

| Component | Location |
|-----------|----------|
| State document builder | `backend/app/digital_twin/document.py` |
| Twin state ORM | `backend/app/db/models/field_digital_twin_state.py` |
| Synchronize service | `backend/app/services/digital_twin.py` |
| REST API | `GET /api/v1/digital-twin/catalog`, field `state` + `synchronize` |
| Latest telemetry query | `SensorReadingRepository.latest_per_sensor_type` |

## Upcoming slices

| Slice | Focus |
|-------|--------|
| 4 | Event-driven snapshot refresh + frontend Feature Store UI |
| 5 | Full JWT/RBAC (replace ops-only patterns where applicable) |

## Phase 16 handoff

- Farm Copilot / GaaS over feature snapshots and read models
- Temporal training pipelines replacing deterministic engine logic
