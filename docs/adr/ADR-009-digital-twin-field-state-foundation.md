# ADR-009 — Digital Twin Field State Foundation (Phase 15)

**Status:** Accepted  
**Date:** 2026-10-11  
**Phase:** 15 — Enterprise Intelligence Platform (slice 3)

---

## Context

AGRIFLOW-AI authoritative data lives in normalized domain tables and TimescaleDB hypertables. Copilot, dashboards, and autonomous workflows need a **single field-scoped state document** describing current operational context without multi-endpoint fan-out.

Phase 15 slice 2 delivered CQRS dashboard read models. Slice 3 composes those projections with latest telemetry and crop context into a versioned Digital Twin snapshot.

---

## Decision

1. **Field state document** — JSONB `state_document` on `field_digital_twin_states` with stable schema version `twin-v1`.
2. **Synchronize API** — `POST /api/v1/digital-twin/fields/{field_id}/synchronize` rebuilds state from write models + read models (not a second source of truth).
3. **Read API** — `GET /api/v1/digital-twin/fields/{field_id}/state` returns the persisted document and metadata.
4. **Catalog** — `GET /api/v1/digital-twin/catalog` documents sections for integrators.
5. **Future** — Phase 14 domain-event consumers will call the same synchronize service; Redis cache deferred to Phase 16.

---

## Consequences

**Positive**

- Farm Copilot and MCP tools can target one grounded state payload per field.
- Clear separation: domains own truth; twin is a materialized projection.

**Negative**

- State lags reality until synchronize runs (mitigated by auto-sync on read in development).

---

## References

- ADR-008 dashboard read models
- ADR-007 Feature Store snapshots (embedded in twin `features` section)
