# ADR-006 — Domain Events and Transactional Outbox (Phase 14)

**Status:** Accepted  
**Date:** 2026-10-11  
**Phase:** 14 — Event-Driven Enterprise Platform  

---

## Context

Phases 1–13 delivered synchronous REST APIs and a decision layer (recommendations, alerts). Downstream capabilities — ML engine triggers, CQRS projections (Phase 15), Digital Twin updates — require **asynchronous propagation** of business-significant state changes without coupling write paths to Redpanda consumers.

Service modules already document extension points (e.g. ADR-007-26 on `SensorReadingService`) but no event infrastructure existed.

---

## Decision

1. **Transactional outbox** — Domain events are inserted into `domain_event_outbox` in the **same database transaction** as the aggregate mutation (same `AsyncSession` / request transaction).
2. **Relay process** — A separate worker (`python -m app.events.relay`) polls unpublished outbox rows and publishes to Redpanda (Kafka protocol). On success, `published_at` is set.
3. **Event contracts** — Typed event names (`DomainEventType`), versioned topic names (`agriflow.domain.<kebab>.v1`), and Pydantic payload schemas under `app/events/schemas.py`.
4. **Catalog API** — `GET /api/v1/events/catalog` exposes registered event types for operators and integrators (no secrets).
5. **Feature flags** — `EVENTS_ENABLED` and `REDPANDA_ENABLED` allow local development without a broker; outbox rows still accumulate when events are enabled so the relay can be tested independently.

---

## Consequences

**Positive**

- No dual-write: aggregate and outbox commit or roll back together.
- REST API contracts unchanged; events are a side effect.
- Phase 15 projection services can subscribe to stable topic names.

**Negative**

- End-to-end latency includes relay poll interval (default 2s).
- Requires operating the relay alongside the API in production.

---

## References

- Phase 14 handbook: `docs/reference/08-architecture-handbook.md` § Phase 14
- First wired producer: `SensorReadingCreated` in `SensorReadingService`
