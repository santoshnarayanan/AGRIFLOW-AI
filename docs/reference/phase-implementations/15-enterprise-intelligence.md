# Phase 15 — Enterprise Intelligence Platform implementation reference

**Status:** In progress — slice 1 (Feature Store foundation) delivered  
**ADR:** [ADR-007](../../../adr/ADR-007-ai-feature-store.md)  
**Migration:** `k5l6m7n8o9p0` (`field_feature_snapshots`)

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

## Configuration

See `backend/.env.example` — `FEATURE_STORE_REGISTRY_VERSION`, `FEATURE_STORE_GDD_BASE_C`.

## Upcoming slices

| Slice | Focus |
|-------|--------|
| 2 | CQRS read models + dashboard projections |
| 3 | Digital Twin foundation (field state document) |
| 4 | Event-driven snapshot refresh + frontend Feature Store UI |
| 5 | Full JWT/RBAC (replace ops-only patterns where applicable) |

## Phase 16 handoff

- Farm Copilot / GaaS over feature snapshots and read models
- Temporal training pipelines replacing deterministic engine logic
