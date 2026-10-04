# Phase 1 — Foundation

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `8f3a1c2d9e04`  
**Chain position:** First migration — no predecessor

---

## What This Phase Achieved

Phase 1 established the entire technical foundation of AGRIFLOW-AI. There were no business domain capabilities before this phase. By the end of Phase 1 the platform had a running FastAPI backend, a connected PostgreSQL database, a working Alembic migration pipeline, the first domain table (`farms`), and two operational APIs (health + version).

Everything built in Phases 2–16 stands on the patterns and conventions established here.

---

## Domain Hierarchy After Phase 1

```
Farm   ← introduced (model + table only; full API completed Phase 13)
```

---

## Database Changes

**Table created:** `farms`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID (PK) | NOT NULL | UUID v4 primary key |
| `farm_code` | VARCHAR(50) | NOT NULL | Short human-readable identifier (e.g. `FARM-001`) |
| `farm_name` | VARCHAR(255) | NOT NULL | Display name |
| `owner_name` | VARCHAR(255) | NOT NULL | Farm owner or managing entity |
| `country` | VARCHAR(100) | NOT NULL | Country |
| `state` | VARCHAR(100) | NOT NULL | State or province |
| `city` | VARCHAR(100) | NOT NULL | Nearest city or municipality |
| `latitude` | NUMERIC(9,6) | NOT NULL | WGS-84 latitude [-90, 90] |
| `longitude` | NUMERIC(10,6) | NOT NULL | WGS-84 longitude [-180, 180] |
| `total_area_hectares` | NUMERIC(12,4) | NOT NULL | Total farm area (4 d.p. ≈ 1 m² resolution) |
| `is_active` | BOOLEAN | NOT NULL | Soft-delete flag; default `true` |
| `created_at` | TIMESTAMPTZ | NOT NULL | Server-side row creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Server-side last-updated timestamp |

**Constraints and indexes:**

| Name | Type | Columns |
|------|------|---------|
| `uq_farms_farm_code` | UNIQUE | `farm_code` |
| `ix_farms_farm_code` | B-tree | `farm_code` |

**Architectural decisions established by this schema:**
- UUID v4 primary keys (not sequential integers) — globally unique across distributed deployments
- `created_at` / `updated_at` server-side audit timestamps on every table (`AuditableModel` pattern)
- Soft-delete via `is_active` — historical data preserved for audit and AI training
- `farm_code` as a human-readable business key alongside the UUID surrogate key

---

## APIs Delivered

### Infrastructure APIs (Phase 1)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/health/live` | Liveness probe |
| GET | `/api/v1/health/ready` | Readiness probe (database check) |
| GET | `/api/v1/version` | Platform version and environment |

> **Note:** Farm CRUD endpoints (POST, GET, PATCH, DELETE `/api/v1/farms`) were completed in **Phase 13** — the Farm model and table existed from Phase 1 but the full service + schema + router layer was deferred.

---

## Architecture Established

All subsequent phases replicate the patterns introduced here:

| Layer | What was established |
|-------|---------------------|
| **Application** | FastAPI with `APIRouter`, versioned under `/api/v1/` |
| **ORM** | SQLAlchemy 2.0 with `Mapped` / `mapped_column` typed declarations |
| **Database** | PostgreSQL via `asyncpg` driver (`postgresql+asyncpg://`) |
| **Migrations** | Alembic with explicit `upgrade()` / `downgrade()` — no autogenerate in production |
| **Configuration** | Pydantic `BaseSettings` — environment variables, `.env` file support |
| **Logging** | Structured logging (`structlog`) with console / JSON format switching |
| **Container** | Docker Compose with `db` (PostgreSQL) and `backend` (FastAPI) services |

**Clean architecture layer order established (enforced in all future phases):**

```
Router (API) → Schema (Pydantic) → Service (business logic)
    → Repository (data access) → ORM Model → PostgreSQL
```

---

## Business Value

- Platform skeleton ready for domain model development
- Migration-driven schema evolution — no ad-hoc DDL ever
- Farm entity as the root of the entire agricultural domain hierarchy

---

## What Was Deferred

- Farm CRUD API (completed Phase 13)
- Authentication and authorization
- Frontend integration
- Automated API tests
- Docker runtime validation (confirmed working at Phase 4)
