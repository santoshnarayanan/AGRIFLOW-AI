# ADR-007 — AI Feature Store (Phase 15)

**Status:** Accepted  
**Date:** 2026-10-11  
**Phase:** 15 — Enterprise Intelligence Platform  

---

## Context

Phase 12 delivered eight TimescaleDB continuous aggregates (ADR-004). Phase 14 delivered ML engine stubs that write recommendations but do not read analytical features. Phase 15 must materialise **versioned, field-scoped feature vectors** from continuous aggregates (and selective raw hypertables) so prediction engines, dashboards, and future Digital Twin / Farm Copilot consumers share one governed extraction path.

---

## Decision

1. **In-code feature registry** — CDD-aligned feature definitions live in `app/features/catalog.py` (mirrors Phase 14 event catalog pattern). `GET /api/v1/features/catalog` exposes metadata; no secrets.
2. **Snapshot persistence** — `field_feature_snapshots` stores immutable JSONB feature payloads per `(field_id, registry_version, as_of)` with optional `crop_id` scope.
3. **Extraction layer** — `FeatureExtractionRepository` issues bounded-window SQL against continuous aggregates and approved raw tables only (no application writes to CAs).
4. **Materialisation API** — `POST /api/v1/features/fields/{field_id}/materialize` computes and persists a snapshot; list/get endpoints support ML and operator workflows.
5. **ML consumption** — Phase 14 engines read the latest snapshot when present (higher confidence / evidence text); stubs remain the fallback when no snapshot exists.

---

## Consequences

**Positive**

- Single extraction path for ML, read models, and future Copilot grounding.
- Bounded cardinality per ADR-004 (daily/hourly buckets, not raw scans).
- Versioned snapshots support model audit and replay.

**Negative**

- Snapshots can be stale relative to CA refresh lag (documented in snapshot metadata).
- Irrigation depth (`irrigation_30d_mm`) requires field `area_hectares` for liter→mm conversion.

---

## References

- ADR-004 continuous aggregate catalogue and CDD feature mapping §10
- Phase 14 handoff: `docs/reference/phase-implementations/14-event-platform.md`
