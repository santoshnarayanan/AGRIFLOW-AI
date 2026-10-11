# Phase 15 — Enterprise Intelligence Platform implementation reference

**Status:** Complete (slices 1–5)  
**ADR:** [ADR-007](../../../adr/ADR-007-ai-feature-store.md), [ADR-008](../../../adr/ADR-008-cqrs-dashboard-read-models.md), [ADR-009](../../../adr/ADR-009-digital-twin-field-state-foundation.md), [ADR-010](../../../adr/ADR-010-platform-jwt-rbac.md)  
**Migrations:** `k5l6m7n8o9p0`, `l6m7n8o9p0q1`, `m7n8o9p0q1r2`, `n8o9p0q1r2s3` (`platform_users`)

## Primary objective

Optimized operational intelligence for dashboards, AI, and Digital Twin — governed ML features, CQRS read models, twin state, event-driven refresh, and platform operator auth.

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

## Delivered (slice 3 — Digital Twin foundation)

| Component | Location |
|-----------|----------|
| State document builder | `backend/app/digital_twin/document.py` |
| Twin state ORM | `backend/app/db/models/field_digital_twin_state.py` |
| Synchronize service | `backend/app/services/digital_twin.py` |
| REST API | `GET /api/v1/digital-twin/catalog`, field `state` + `synchronize` |
| Latest telemetry query | `SensorReadingRepository.latest_per_sensor_type` |

## Delivered (slice 4 — Event-driven projection + Feature Store UI)

| Component | Location |
|-----------|----------|
| Intelligence projection handler | `backend/app/events/handlers/intelligence_projection.py` |
| Consumer dispatch wiring | `backend/app/events/handlers/dispatch.py` |
| Config flag | `INTELLIGENCE_EVENT_PROJECTION_ENABLED` |
| Feature Store UI | `frontend/src/pages/FeatureStore.tsx`, `frontend/src/api/features.ts` |
| Tests | `backend/app/tests/test_intelligence_projection.py` |

On field-scoped domain events: materialise feature snapshot → refresh field dashboard read model → synchronise digital twin.

## Delivered (slice 5 — JWT / RBAC)

| Component | Location |
|-----------|----------|
| Platform users ORM + migration | `platform_user.py`, `n8o9p0q1r2s3` |
| JWT + password utilities | `app/core/security/jwt_tokens.py`, `passwords.py` |
| Operator dependency | `app/core/security/platform_auth.py` |
| Auth API | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Protected operator routes | features materialize, read-model refresh, digital-twin sync, events outbox ops |
| Frontend login + bearer header | `frontend/src/stores/authStore.ts`, `frontend/src/api/auth.ts`, `api/client.ts` |
| Tests | `test_platform_auth.py`, `test_jwt_tokens.py` |

Bootstrap admin (after migration): `admin@agriflow.local` / `changeme-admin` — rotate in production.

## Configuration

See `backend/.env.example` — Feature Store, read models, digital twin, `INTELLIGENCE_EVENT_PROJECTION_ENABLED`, `AUTH_REQUIRED`, `ACCESS_TOKEN_EXPIRE_MINUTES`, optional `EVENTS_OPS_API_KEY`.

## Phase 16 handoff

- Farm Copilot / GaaS over feature snapshots and read models
- Temporal training pipelines replacing deterministic engine logic
