# ADR-010 — Platform JWT authentication and RBAC (Phase 15)

**Status:** Accepted  
**Date:** 2026-10-11  
**Phase:** 15 — Enterprise Intelligence Platform  

---

## Context

Phase 14 introduced an optional `X-Events-Ops-Key` for outbox operator APIs. Phase 15 adds intelligence operator endpoints (feature materialisation, read-model refresh, digital-twin sync) that need a consistent authentication model for staging and production without scattering ad-hoc secrets.

---

## Decision

1. **`platform_users` table** — Email/password accounts with `platform_role` enum (`VIEWER`, `OPERATOR`, `ADMIN`). Migration seeds `admin@agriflow.local` (password documented in `.env.example`).
2. **JWT access tokens** — `POST /api/v1/auth/login` issues HS256 bearer tokens (`sub`, `email`, `role`, `exp`) signed with `SECRET_KEY`.
3. **`PlatformOperatorDep`** — Operator routes accept **Bearer JWT** (OPERATOR/ADMIN) or legacy **`X-Events-Ops-Key`** when `EVENTS_OPS_API_KEY` is set. When `AUTH_REQUIRED=false` (default in development), unauthenticated calls receive a synthetic development principal.
4. **Protected operations** — Materialise features, refresh read models, synchronise digital twin, and Phase 14 outbox ops require `PlatformOperatorDep`. Read/catalog endpoints remain open for dashboards and ML consumers.
5. **Event-driven projection** — Field-scoped domain events trigger feature snapshot materialisation, read-model refresh, and twin sync when `INTELLIGENCE_EVENT_PROJECTION_ENABLED=true` (slice 4).

---

## Consequences

**Positive**

- One dependency for operator APIs; JWT scales to UI login and future Farm Copilot admin tools.
- Ops key remains for automation during migration.

**Negative**

- Bootstrap admin credentials must be rotated after first deploy.
- Projection handler failures surface as consumer errors; monitor inbox/outbox metrics.

---

## References

- Phase 15 implementation: `docs/reference/phase-implementations/15-enterprise-intelligence.md`
- Code: `app/core/security/platform_auth.py`, `app/api/auth/router.py`, `app/events/handlers/intelligence_projection.py`
