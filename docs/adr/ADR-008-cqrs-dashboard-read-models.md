# ADR-008 — CQRS Dashboard Read Models (Phase 15)

**Status:** Accepted  
**Date:** 2026-10-11  
**Phase:** 15 — Enterprise Intelligence Platform (slice 2)

---

## Context

Dashboard and operator views currently fan out across many REST calls (per-field alerts and recommendations). Phase 14 domain events enable asynchronous projection, but operators need **query-optimised read models** immediately for KPI cards and farm/field summaries.

---

## Decision

1. **Field-scoped read model** — `field_dashboard_read_models` stores denormalised KPIs per field (alert counts, active recommendations, latest Feature Store highlights).
2. **Synchronous projection (slice 2)** — `POST .../refresh` rebuilds read models from write-side tables and latest feature snapshots. Event-driven projectors defer to slice 4.
3. **Read API** — `GET /api/v1/read-models/dashboard` aggregates stored field projections; farm and field routes return scoped views.
4. **Write path unchanged** — Commands continue through existing services; projections are a separate read path (CQRS).

---

## Consequences

**Positive**

- Dashboard KPIs become O(1) API calls after refresh.
- Clear extension point for Redpanda consumers to call the same projection service.

**Negative**

- Projections are eventually consistent until refresh (or future event consumers run).

---

## References

- ADR-007 AI Feature Store (KPI highlights sourced from latest snapshot)
- Phase 14 domain events (future async projection trigger)
