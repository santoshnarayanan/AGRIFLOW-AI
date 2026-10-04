# AGRIFLOW-AI — Phase 12 Step 1B

## TimescaleDB Infrastructure Design & Implementation Plan

**Document Type:** Infrastructure Design & Implementation Plan (Planning Only)  
**Version:** 1.1  
**Date:** June 2026  
**Scope:** Phase 12 Step 1B — TimescaleDB Docker Infrastructure Design; Step 1C Implementation Readiness  
**Status:** Planning Complete — No Implementation Performed  
**Author:** Senior Platform Architecture  
**Governance Reference:** `docs/report/PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md` v1.3 — Approved Architecture Baseline

---

## 1. Reference Architecture & Compliance

This plan **SHALL** follow the approved architecture documented in:

| Reference | Version | Status |
|---|---|---|
| `docs/report/PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md` | 1.3 | ✅ Approved Architecture Baseline |
| `docs/report/PHASE12_DECISION_REGISTER.md` | Initial | ✅ Decisions P12-D001 through P12-D005 |

**Compliance statement:** No architectural decisions from Step 1A are overridden by this plan. All recommendations align with Step 1A §2.1 approved decisions and respect §2.2 deferred decisions.

| Step 1A Approved Constraint | This Plan Compliance |
|---|---|
| PostgreSQL 17 | ✅ Image platform `*-pg17` |
| Docker Compose primary dev runtime | ✅ Single `db.image` change only |
| TimescaleDB as PostgreSQL extension | ✅ Extension via Step 1C migration; not separate DB |
| API / Service / Repository / Schema unchanged | ✅ No application-layer modifications |
| Immutable Alembic history | ✅ Forward migration only in Step 1C |
| Backend Dockerfile unchanged | ✅ No backend container changes |
| Python dependencies unchanged | ✅ No requirements changes |

**Conflict protocol (Step 1A §2.4):** If any implementation activity conflicts with the approved baseline, **pause implementation** and document the conflict. Do not assume or override.

---

## 2. Objective

Design the infrastructure implementation required to introduce TimescaleDB into AGRIFLOW-AI while preserving **complete backward compatibility**.

| Activity | Included in This Plan | Executed Now |
|---|---|---|
| TimescaleDB Docker image evaluation & selection | ✅ | ❌ |
| Docker Compose impact analysis | ✅ | ❌ |
| Data preservation & rollback design | ✅ | ❌ |
| Step 1C extension enablement design | ✅ | ❌ |
| Compatibility verification | ✅ | ❌ |
| Risk review | ✅ | ❌ |
| Step 1B + 1C implementation sequence | ✅ | ❌ |
| Decision register entries | ✅ | ❌ |
| Docker / migration / code modifications | ❌ | ❌ |

This step **prepares** implementation. It does **not** execute Docker or database modifications.

---

## 3. Current Environment

| Component | Current State | Source |
|---|---|---|
| Operating System | macOS Apple Silicon (M1) | Project dev standard |
| Container Runtime | Docker Desktop | Step 1A §3.6 |
| Orchestration | Docker Compose | `docker-compose.yml` |
| Database Image | `postgres:17-alpine` | `docker-compose.yml` line 20 |
| Database Name | `agriflow` | `POSTGRES_DB` |
| Database User | `agriflow` | `POSTGRES_USER` |
| Host Port | `25432:5432` | pgAdmin / host tools |
| Persistence | Named volume `postgres_data` | `/var/lib/postgresql/data` |
| Backend | FastAPI on Python 3.12 | `backend/Dockerfile` |
| ORM | SQLAlchemy 2.0.36 (async) | `requirements.txt` |
| Driver | asyncpg 0.30.0 | `requirements.txt` |
| Migrations | Alembic 1.14.0 (async runner) | `app/db/migrations/env.py` |
| Migration Head | `a1b2c3d4e5f6_create_satellite_observations_table` | Step 1A §3.5 |
| Domain Tables | 10 (+ `alembic_version`) | Step 1A |
| REST Endpoints | 51+ | Step 1A |

**Known documentation drift:** Compose header comment (line 5) references "PostgreSQL 18" but runtime image is PostgreSQL 17. Correct during Step 1B implementation as optional hygiene (Step 1A §12 #6).

---

## 4. TimescaleDB Docker Image Evaluation

### 4.1 Research Summary

| Criterion | Finding |
|---|---|
| Official image | `timescale/timescaledb` on Docker Hub — maintained by Timescale |
| Source repository | [timescale/timescaledb-docker](https://github.com/timescale/timescaledb-docker) |
| Base image | Official PostgreSQL Docker image (same env vars, data directory, tooling) |
| PostgreSQL 17 support | Tags: `<semver>-pg17` (e.g. `2.28.0-pg17`); `latest-pg17` rolling — not for committed config |
| ARM64 / Apple Silicon | Multi-architecture manifest (amd64 + arm64) on official `timescale/timescaledb` |
| `latest` tag policy | **No bare `latest` tag** — Timescale intentionally omits it to prevent unexpected PG major upgrades |
| Alternative HA image | `timescale/timescaledb-ha:pg17` — Ubuntu, Patroni, Toolkit; not required for dev |

### 4.2 Image Comparison

| Image | Base | PG 17 | ARM64 | Size Profile | Recommendation |
|---|---|---|---|---|---|
| `timescale/timescaledb:<semver>-pg17` | Alpine / Postgres official | ✅ | ✅ | Lightweight | **✅ Selected** |
| `timescale/timescaledb:<semver>-pg17-oss` | Alpine | ✅ | ✅ | Lightweight | Fallback if OSS-only licensing required |
| `timescale/timescaledb:latest-pg17` | Alpine | ✅ | ✅ | Lightweight | ❌ Rolling tag — dev discovery only |
| `timescale/timescaledb-ha:pg17` | Ubuntu | ✅ | ✅ | Heavy | ❌ Over-engineered for local Compose dev |
| `postgres:17-alpine` (current) | Alpine | ✅ | ✅ | Minimal | ❌ No TimescaleDB extension binaries |

### 4.3 Recommended Image

**Decision:** P12-D001 — `timescale/timescaledb:<semver>-pg17` (exact semver pinned at implementation time)

```yaml
# Target state (Step 1B implementation — NOT applied in this planning step)
# Use latest stable *-pg17 semver available at implementation time (see P12-D002)
image: timescale/timescaledb:<semver>-pg17   # e.g. timescale/timescaledb:2.28.0-pg17
```

### 4.4 Why This Image Is Preferred

1. **Official and maintained** — Timescale publishes semver tags with explicit PostgreSQL platform (`-pg17`), matching Step 1A PostgreSQL 17 approval.
2. **PostgreSQL compatibility** — Built on the official Postgres Docker image; existing volume data directory, `POSTGRES_*` environment variables, and `pg_isready` health checks behave identically.
3. **Apple Silicon support** — Multi-arch builds run natively on M1 via Docker Desktop without Rosetta emulation.
4. **Extension pre-installed** — TimescaleDB binaries ship in the image; activation is a `CREATE EXTENSION` operation (Step 1C), not a separate database product.
5. **Minimal infrastructure diff** — Single-line `docker-compose.yml` change; backend Dockerfile and Python stack unchanged per approved baseline.
6. **Version pinning** — Explicit semver tag `<version>-pg17` satisfies Step 1A requirement to avoid `latest`; the exact patch version is selected at implementation time and recorded in the Decision Register (P12-D002).
7. **Long-term maintenance** — Timescale publishes regular semver releases per PG platform; upgrade path is pin bump + backup + smoke test, not image family migration.

### 4.5 Version Pinning Strategy

**Decision:** P12-D002

| Rule | Detail |
|---|---|
| Committed tag format | `<timescaledb-semver>-pg17` |
| Version selection | Latest stable TimescaleDB release for PostgreSQL 17 available at implementation time |
| Prohibited | `latest`, `latest-pg17` in committed `docker-compose.yml` |
| Verification before Step 1C | Confirm selected tag exists on Docker Hub; record exact version in Decision Register (P12-D002) |
| Pin change process | Update compose file + record implemented pin in Decision Register |

---

## 5. Docker Compose Impact Analysis

**File reviewed:** `docker-compose.yml` (project root)

### 5.1 Lines Requiring Modification (Step 1B Implementation)

| Line(s) | Current | Target | Required |
|---|---|---|---|
| **20** | `image: postgres:17-alpine` | `image: timescale/timescaledb:<semver>-pg17` | **Yes — primary change** |
| **5** (comment) | `PostgreSQL 18 with persistent volume` | `PostgreSQL 17 + TimescaleDB with persistent volume` | Optional hygiene |

**Total required code changes:** 1 line (`db.image`).

### 5.2 Services Remaining Unchanged

| Service / Resource | Lines | Status |
|---|---|---|
| `db.restart` | 21 | Unchanged |
| `db.environment` | 22–25 | Unchanged |
| `db.volumes` | 26–27 | Unchanged |
| `db.ports` | 28–29 | Unchanged |
| `db.healthcheck` | 30–35 | Unchanged |
| `backend` (entire service) | 37–64 | Unchanged |
| `volumes.postgres_data` | 66–68 | Unchanged |
| Network (default bridge) | implicit | Unchanged |

### 5.3 Compatibility Assessment

| Aspect | Current | After Step 1B | Compatible |
|---|---|---|---|
| **Volume** | `postgres_data` → `/var/lib/postgresql/data` | Same mount path | ✅ Yes — PG17 → PG17 data directory |
| **Network** | Default Compose bridge; backend → `db:5432` | Same | ✅ Yes |
| **Health check** | `pg_isready -U agriflow -d agriflow` | Same command | ✅ Yes — TimescaleDB image includes `pg_isready` |
| **Environment variables** | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Same | ✅ Yes — official Postgres env contract |
| **Port mapping** | `25432:5432` | Same | ✅ Yes — pgAdmin / Postman unchanged |
| **Backend dependency** | `depends_on: db: condition: service_healthy` | Same | ✅ Yes |
| **Backend env override** | `POSTGRES_HOST: db` | Same | ✅ Yes |
| **Connection URL** | `postgresql+asyncpg://agriflow:...@db:5432/agriflow` | Same scheme and path | ✅ Yes |

### 5.4 Volume Compatibility Notes

Switching from `postgres:17-alpine` to `timescale/timescaledb:<semver>-pg17` retains the existing Docker volume without re-initialization because:

* Both images target **PostgreSQL 17** with the same data directory format.
* The TimescaleDB image is a superset — it adds extension shared libraries without altering the core PostgreSQL catalog layout.
* **Mandatory safeguard:** P12-D003 pg_dump backup before first start on the new image.

**Risk:** If the volume was initialized on a materially different PostgreSQL minor build, automatic recovery may still succeed, but backup-first is non-negotiable per Step 1A governance.

---

## 6. Existing Data Preservation Strategy

**Decision references:** P12-D003 (backup), P12-D005 (rollback)

### 6.1 Preservation Objectives

| Asset | Preservation Method |
|---|---|
| Existing database (`agriflow`) | Retain `postgres_data` volume + pg_dump backup |
| Docker volume | Same volume name and mount — no volume recreation |
| Existing schema (10 domain tables) | No DDL in Step 1B; Step 1C adds extension only |
| Alembic history (11 migrations) | Immutable; forward migration in Step 1C only |
| Existing row data | Volume retention + backup verification |

### 6.2 Backup Strategy

**When:** Immediately before Step 1B image swap; again before Step 1C extension migration.

**Command (in-container — recommended):**

```bash
docker compose exec db pg_dump \
  -U agriflow \
  -d agriflow \
  -F c \
  -f /tmp/pre_phase12_backup.dump

docker compose cp db:/tmp/pre_phase12_backup.dump ./backups/
```

**Command (host-native via mapped port):**

```bash
mkdir -p backups
pg_dump -h localhost -p 25432 -U agriflow -d agriflow \
  -F c -f "./backups/pre_phase12_step1b_$(date +%Y%m%d_%H%M%S).dump"
```

**Verification:**

```bash
pg_restore --list ./backups/pre_phase12_step1b_*.dump | head -20
```

### 6.3 Recovery Strategy

| Scenario | Recovery Procedure |
|---|---|
| Image swap succeeds; data intact | No recovery needed — proceed to validation |
| Image swap succeeds; data anomalies | Tier 2: stop stack → pg_restore from backup |
| Volume corrupted | Tier 2: remove volume → recreate → pg_restore |
| Extension migration fails | Tier 3: `alembic downgrade -1` → if fails, Tier 2 restore |

**Full restore command (empty database):**

```bash
docker compose down
docker volume rm agriflow-ai_postgres_data   # destructive — backup must exist
docker compose up -d db
# wait for healthy
pg_restore -h localhost -p 25432 -U agriflow -d agriflow \
  --no-owner --role=agriflow ./backups/pre_phase12_step1b_*.dump
```

### 6.4 Rollback Strategy

See Decision Register **P12-D005** for the three-tier rollback model:

| Tier | Trigger | Action | Data Loss Risk |
|---|---|---|---|
| **1** | Image fails / API regression | Revert `db.image` to `postgres:17-alpine`; `docker compose up -d` | None |
| **2** | Data corruption | Remove volume; restore from pg_dump | None if backup valid |
| **3** | Step 1C extension failure | `alembic downgrade -1`; escalate to Tier 2 if needed | None pre-hypertable |

---

## 7. Extension Enablement Strategy (Step 1C Design)

**Decision reference:** P12-D004

Step 1C is **designed** here but **not executed**. No migration file is created in Step 1B planning.

### 7.1 Approach

| Aspect | Design |
|---|---|
| Mechanism | New forward Alembic migration after Step 1B validation |
| DDL | `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;` |
| Downgrade | `DROP EXTENSION IF EXISTS timescaledb CASCADE;` — see §7.1.1 governance note |
| Execution | `docker compose run --rm backend alembic upgrade head` |
| Schema impact | Extension metadata only — no table DDL |
| Application impact | None — no code, schema, or API changes |

#### 7.1.1 Alembic Downgrade Governance

The Step 1C migration template includes `DROP EXTENSION IF EXISTS timescaledb CASCADE` in `downgrade()` to satisfy Alembic migration completeness. The following governance rules apply:

| Rule | Detail |
|---|---|
| **Purpose of downgrade DDL** | Migration reversibility for development environments only — not a production rollback procedure |
| **Permitted use** | Step 1C validation or local dev rollback **before any hypertables exist** (pre-Step 1D) |
| **After Step 1D** | Once hypertables are introduced, extension removal via `DROP EXTENSION CASCADE` is **no longer a normal rollback strategy** — it would destroy hypertable metadata and dependent objects |
| **Future rollback** | Post-Step 1D rollback procedures focus on **restoring from pg_dump backups** (P12-D003 / P12-D005 Tier 2), not removing the extension |
| **Migration content** | The downgrade SQL itself is unchanged — governance applies to **when and whether** downgrade is invoked |

### 7.2 Extension Verification

**Post-migration SQL — extension installed in AGRIFLOW database:**

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';
```

**Expected result:** One row — `timescaledb` with version matching the pinned image semver.

**Post-migration SQL — extension binaries available in database image:**

```sql
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name = 'timescaledb';
```

**Expected result:** One row — `installed_version` populated and aligned with `pg_extension.extversion`.

**Validation interpretation:**

| Catalog | Confirms |
|---|---|
| `pg_available_extensions` | TimescaleDB extension binaries are **available** in the database image |
| `pg_extension` | TimescaleDB extension has been **installed** in the `agriflow` database |

Both checks together provide stronger validation than either alone.

**Pre-Step 1C baseline (Step 1B):** `pg_available_extensions` should return a row with `installed_version` NULL — confirming binaries present but extension not yet activated in `agriflow`.

**Additional sanity checks:**

```sql
-- Confirm existing domain tables unchanged
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Confirm Alembic head
SELECT version_num FROM alembic_version;
```

### 7.3 Existing Tables Remain Unchanged

Step 1C explicitly does **not**:

* Convert tables to hypertables (Step 1D — requires Architecture Approval)
* Modify primary keys (deferred per Step 1A §2.2)
* Add compression, retention, or continuous aggregates (Step 1E)
* Alter any Phase 1–11 migration files

### 7.4 Image vs Migration Extension State

The `timescale/timescaledb` image may auto-enable TimescaleDB in the default `postgres` database. Because AGRIFLOW-AI uses `POSTGRES_DB=agriflow`, the Alembic migration ensures extension activation in the **application database** and records the change in version control — reproducible across fresh environments.

---

## 8. Compatibility Verification

### 8.1 Component Compatibility Matrix

| Component | Version | TimescaleDB Compatibility | Action Required |
|---|---|---|---|
| **SQLAlchemy** | 2.0.36 (async) | ✅ Full — standard SQL; no TimescaleDB dialect needed for baseline | None |
| **asyncpg** | 0.30.0 | ✅ Full — PostgreSQL wire protocol compatible | None |
| **Alembic** | 1.14.0 (async) | ✅ Full — `op.execute()` for extension DDL | Step 1C migration only |
| **FastAPI** | Current | ✅ No DB engine awareness | None |
| **pgAdmin 4** | External | ✅ Connects via `localhost:25432` — standard PostgreSQL | None |
| **Postman** | External | ✅ REST API unchanged | None |
| **Repositories** | 10 domain repos | ✅ Standard SQLAlchemy queries — unchanged pre-hypertable | None |
| **Services** | Domain services | ✅ Business logic DB-agnostic | None |
| **Pydantic schemas** | All domain schemas | ✅ No storage coupling | None |
| **Backend Dockerfile** | Python 3.12-slim | ✅ Connects via libpq/asyncpg — no TimescaleDB client needed | None |

### 8.2 Step 1B Validation Checklist (Post-Implementation)

| # | Validation | Method | Expected |
|---|---|---|---|
| 1 | Database container starts | `docker compose ps` | `db` healthy |
| 2 | PostgreSQL version | `SELECT version();` | PostgreSQL 17.x |
| 3 | Existing tables present | `\dt` or information_schema query | 10 domain tables + alembic_version |
| 4 | Row count spot-check | `SELECT COUNT(*) FROM farms;` (etc.) | Matches pre-migration counts |
| 5 | Alembic head unchanged | `SELECT version_num FROM alembic_version;` | `a1b2c3d4e5f6` |
| 6 | Backend connects | `docker compose logs backend` | No connection errors |
| 7 | API smoke test | Postman / Swagger `/docs` | 200 responses on sample endpoints |
| 8 | pgAdmin connectivity | Connect `localhost:25432` | Successful auth |
| 9 | Extension available (pre-1C) | `pg_available_extensions` query | Row present; `installed_version` NULL |

### 8.3 Step 1C Validation Checklist (Post-Implementation)

| # | Validation | Method | Expected |
|---|---|---|---|
| 1 | Extension binaries available | `pg_available_extensions` query | `timescaledb` row; `installed_version` populated post-migration |
| 2 | Extension installed | `pg_extension` query | `timescaledb` row present |
| 3 | No new tables | information_schema | Same table list as pre-1C |
| 4 | Existing APIs | Postman regression sample | Unchanged responses |
| 5 | Alembic head advanced | `alembic current` | New revision ID |
| 6 | Downgrade governance documented | Migration file review | `DROP EXTENSION` present with §7.1.1 governance note in comments |

### 8.4 Primary Key Investigation — Deferred to Step 1D

Primary key compatibility investigation — including any `create_hypertable(...)` experimentation — is **explicitly deferred to Step 1D** (Hypertable Conversion). This activity relates to the deferred Architecture Decision Review for primary key strategy (Step 1A §2.2) and is **out of scope for Step 1B**.

| Aspect | Detail |
|---|---|
| **Step 1B focus** | Infrastructure readiness only — Docker image swap, volume compatibility, application connectivity |
| **Step 1D scope** | Primary key strategy evaluation, hypertable PK constraint investigation, ADR input |
| **Governance** | Step 1B must not include guidance to experiment with hypertables or `create_hypertable()` |

The Decision Register continues to list Primary Key Strategy as a deferred architectural decision awaiting ADR.

---

## 9. Risk Review

### 9.1 Infrastructure Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Image swap prevents PostgreSQL start | Medium | Low | P12-D003 backup; Tier 1 rollback to `postgres:17-alpine` |
| Volume incompatible with new image | Medium | Low | PG17 → PG17; backup + Tier 2 restore |
| Stale compose PG 18 comment causes confusion | Low | Medium | Fix comment during Step 1B (optional hygiene) |
| Pin tag unavailable on Docker Hub | Low | Low | Verify tag at pull time; select latest stable `*-pg17` patch |

### 9.2 Migration Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Step 1C `CREATE EXTENSION` fails (privileges) | Low | Low | Dev `POSTGRES_USER` is superuser by default |
| Step 1C applied before Step 1B validated | Medium | Low | Enforce sequence gate: 1B validation complete before 1C |
| Accidental Step 1D hypertable attempt | High | Low | Governance — requires Architecture Approval; not in this plan |

### 9.3 Docker Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| Image pull failure (network/registry) | Low | Low | Pre-pull selected pin: `docker pull timescale/timescaledb:<semver>-pg17` |
| Larger image size vs alpine | Low | Certain | Accept ~200MB increase; monitor disk |
| Compose project name affects volume name | Low | Low | Document actual volume name via `docker volume ls` before Tier 2 rollback |

### 9.4 Apple Silicon Risks

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| ARM64 image unavailable | Low | Very Low | Official multi-arch manifest confirmed |
| Rosetta emulation performance | Low | Very Low | Native arm64 run expected |
| Docker Desktop resource limits | Low | Medium | Ensure ≥ 4GB RAM allocated to Docker Desktop |

### 9.5 Rollback Risks

| Risk | Severity | Mitigation |
|---|---|---|
| No backup taken before change | **High** | P12-D003 mandatory gate — do not proceed without dump |
| Tier 2 volume name mismatch | Medium | Record volume name before first change |
| `DROP EXTENSION CASCADE` after hypertables | High (future) | Not applicable until Step 1D — post-Step 1D rollback uses Tier 2 backup restore (§7.1.1) |

### 9.6 Operational Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Shared dev environment downtime | Medium | Communicate maintenance window; backup first |
| Operator skips validation checklist | Medium | Require sign-off on §8.2 checklist before Step 1C |
| Pin drift between team members | Low | Single pinned tag in committed compose file |

---

## 10. Implementation Sequence

### 10.1 Overview

```text
Phase 12 Step 1B (Infrastructure)
  │
  ├─ 1B.1  Pre-flight & backup
  ├─ 1B.2  Pull pinned TimescaleDB image
  ├─ 1B.3  Update docker-compose.yml (db.image)
  ├─ 1B.4  Restart stack & validate
  └─ 1B.5  Application smoke test
  │
  ▼  Gate: Step 1B validation checklist complete
  │
Phase 12 Step 1C (Extension Enablement)
  │
  ├─ 1C.1  Pre-flight & backup
  ├─ 1C.2  Create Alembic migration (CREATE EXTENSION)
  ├─ 1C.3  Apply migration
  ├─ 1C.4  Verify extension & schema
  └─ 1C.5  Application regression smoke test
```

**Out of scope:** Step 1D (hypertables) and Step 1E (policies/aggregates) — require Architecture Approval per Step 1A §2.2.

---

### 10.2 Step 1B Implementation Activities

#### 1B.1 — Pre-Flight & Backup

| Attribute | Detail |
|---|---|
| **Purpose** | Establish recovery point before any infrastructure change |
| **Files affected** | None (creates `./backups/*.dump`) |
| **Expected outcome** | Verified pg_dump archive of `agriflow` database |
| **Rollback** | N/A — pre-change activity |
| **Validation** | `pg_restore --list` succeeds; record dump filename and timestamp |

#### 1B.2 — Pull Pinned TimescaleDB Image

| Attribute | Detail |
|---|---|
| **Purpose** | Ensure image available locally before stack restart |
| **Files affected** | None |
| **Expected outcome** | Selected pinned image (e.g. `timescale/timescaledb:<semver>-pg17`) present locally |
| **Rollback** | N/A — pull is non-destructive |
| **Validation** | `docker image inspect timescale/timescaledb:<semver>-pg17` returns manifest; record exact tag in Decision Register |

#### 1B.3 — Update Docker Compose Database Image

| Attribute | Detail |
|---|---|
| **Purpose** | Switch database container to TimescaleDB-enabled PostgreSQL 17 |
| **Files affected** | `docker-compose.yml` line 20 (line 5 comment optional) |
| **Expected outcome** | `db.image: timescale/timescaledb:<semver>-pg17` (exact semver per P12-D002) |
| **Rollback** | Tier 1: revert line 20 to `postgres:17-alpine` |
| **Validation** | Git diff shows only intended lines changed |

#### 1B.4 — Restart Stack & Database Validation

| Attribute | Detail |
|---|---|
| **Purpose** | Start TimescaleDB container with existing volume |
| **Files affected** | None (runtime only) |
| **Expected outcome** | `db` service healthy; PostgreSQL 17 accepting connections |
| **Rollback** | Tier 1: revert compose + `docker compose down && docker compose up -d` |
| **Validation** | §8.2 checklist items 1–5, 9 |

**Commands:**

```bash
docker compose down
docker compose up -d
docker compose ps
docker compose exec db psql -U agriflow -d agriflow -c "SELECT version();"
```

#### 1B.5 — Application Smoke Test

| Attribute | Detail |
|---|---|
| **Purpose** | Confirm backend connectivity and API behaviour unchanged |
| **Files affected** | None |
| **Expected outcome** | FastAPI starts; sample endpoints return expected responses |
| **Rollback** | Tier 1 if connection failures persist after logs review |
| **Validation** | §8.2 checklist items 6–8 |

**Commands:**

```bash
docker compose logs backend --tail 50
curl -s http://localhost:8000/docs | head -5
docker compose run --rm backend alembic current
```

---

### 10.3 Step 1C Implementation Activities

#### 1C.1 — Pre-Flight & Backup

| Attribute | Detail |
|---|---|
| **Purpose** | Recovery point before extension DDL |
| **Files affected** | None (creates backup file) |
| **Expected outcome** | pg_dump archive post-Step 1B, pre-Step 1C |
| **Rollback** | N/A |
| **Validation** | `pg_restore --list` succeeds |

#### 1C.2 — Create Alembic Extension Migration

| Attribute | Detail |
|---|---|
| **Purpose** | Version-control TimescaleDB extension activation |
| **Files affected** | New file: `backend/app/db/migrations/versions/<rev>_enable_timescaledb_extension.py` |
| **Expected outcome** | Migration with `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE` upgrade and documented downgrade |
| **Rollback** | Delete migration file if not yet applied |
| **Validation** | Code review: no table DDL; no changes to existing migrations |

**Migration template (for implementer — do not create in Step 1B planning):**

```python
def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")


def downgrade() -> None:
    # WARNING: destructive if hypertables exist (Step 1D+)
    # Governance: see PHASE12_STEP1B plan §7.1.1 — dev-only pre-hypertable rollback
    op.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE;")
```

**Downgrade governance:** See §7.1.1. The downgrade DDL satisfies Alembic completeness; it is not a post-Step 1D rollback strategy.

#### 1C.3 — Apply Extension Migration

| Attribute | Detail |
|---|---|
| **Purpose** | Activate TimescaleDB in `agriflow` database |
| **Files affected** | Database catalog only (`pg_extension`) |
| **Expected outcome** | Alembic head advanced; extension installed |
| **Rollback** | Tier 3: `alembic downgrade -1` — **dev-only, pre-Step 1D** (see §7.1.1) |
| **Validation** | `alembic current` shows new revision |

**Command:**

```bash
docker compose run --rm backend alembic upgrade head
```

#### 1C.4 — Verify Extension & Schema

| Attribute | Detail |
|---|---|
| **Purpose** | Confirm extension active; no unintended schema changes |
| **Files affected** | None |
| **Expected outcome** | `timescaledb` in `pg_extension`; 10 domain tables unchanged |
| **Rollback** | Tier 3 if verification fails |
| **Validation** | §8.3 checklist items 1–3, 5 |

**Commands:**

```bash
docker compose exec db psql -U agriflow -d agriflow \
  -c "SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = 'timescaledb';"

docker compose exec db psql -U agriflow -d agriflow \
  -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';"

docker compose exec db psql -U agriflow -d agriflow \
  -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1;"
```

#### 1C.5 — Application Regression Smoke Test

| Attribute | Detail |
|---|---|
| **Purpose** | Confirm zero application-layer regression after extension |
| **Files affected** | None |
| **Expected outcome** | All sampled APIs operational; no new errors in backend logs |
| **Rollback** | Tier 3 → Tier 2 if persistent failure |
| **Validation** | §8.3 checklist items 4, 6 |

---

## 11. Decision Register Summary

Formal decisions recorded in `docs/report/PHASE12_DECISION_REGISTER.md`:

| ID | Decision | Step |
|---|---|---|
| P12-D001 | Docker image: `timescale/timescaledb:<semver>-pg17` | 1B |
| P12-D002 | Semver pin policy; exact version recorded at implementation | 1B |
| P12-D003 | pg_dump backup before 1B and 1C | 1B / 1C |
| P12-D004 | Alembic `CREATE EXTENSION` for Step 1C | 1C |
| P12-D005 | Three-tier rollback model | 1B / 1C |

---

## 12. Implementation Readiness Assessment

### 12.1 Step 1C Readiness

| Question | Answer |
|---|---|
| Are additional architectural decisions required for Step 1C? | **No** — Step 1C is fully specified by Step 1A §8 and P12-D004 |
| Are application-layer changes required? | **No** |
| Are dependency changes required? | **No** |
| Is the migration DDL defined? | **Yes** — `CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE` |
| Is rollback defined? | **Yes** — P12-D005 Tier 3 |
| Is validation defined? | **Yes** — §8.3 checklist |

**Conclusion:** This plan enables Step 1C implementation without requiring additional architectural decisions, subject to successful Step 1B validation gate.

### 12.2 Explicitly Deferred (Not in Step 1B / 1C Scope)

| Item | Governance Status |
|---|---|
| Hypertable conversion | Requires Architecture Approval (Primary Key Strategy) — Step 1D |
| Primary key / hypertable PK investigation | Deferred to Step 1D — includes `create_hypertable()` compatibility evaluation |
| Composite / UUID PK migration | Awaiting ADR |
| Repository `time_bucket()` analytics | Awaiting ADR |
| Compression / retention / continuous aggregates | Step 1E — after 1D |

---

## 13. Success Criteria

This planning activity is successful when:

| # | Criterion | Status |
|---|---|---|
| 1 | TimescaleDB Docker image evaluated and recommended with PG17 + ARM64 rationale | ✅ |
| 2 | Docker Compose impact documented to exact line level | ✅ |
| 3 | Data preservation, backup, recovery, and rollback strategies defined | ✅ |
| 4 | Step 1C extension enablement fully designed (migration not created) | ✅ |
| 5 | Compatibility verified for SQLAlchemy, asyncpg, Alembic, pgAdmin, Postman, FastAPI, repositories, services | ✅ |
| 6 | Risks identified across infrastructure, migration, Docker, Apple Silicon, rollback, operations | ✅ |
| 7 | Step 1B and 1C implementation sequences defined with purpose, files, outcome, rollback, validation | ✅ |
| 8 | Decision register created with P12-D001 through P12-D005 | ✅ |
| 9 | All recommendations comply with Step 1A v1.3 approved baseline | ✅ |
| 10 | No docker-compose, Dockerfile, Alembic, Python, or migration files modified | ✅ |

---

## 14. Conclusion

Phase 12 Step 1B planning defines a **minimal, governance-compliant infrastructure transition** from `postgres:17-alpine` to `timescale/timescaledb:<semver>-pg17` — a single-line Docker Compose change backed by mandatory backup, tiered rollback, and structured validation. The exact semver is selected and recorded at implementation time per P12-D002.

Step 1C is fully specified and ready for implementation immediately after Step 1B validation, requiring only one forward Alembic migration with no application-layer changes.

Hypertable conversion, primary key investigation, and analytics capabilities remain **deferred pending Architecture Decision Review** per the Step 1A approved baseline. Primary key compatibility investigation is explicitly scoped to Step 1D — not Step 1B. This plan does not address, override, or pre-approve those deferred decisions.

**Recommended next action:** Execute Step 1B implementation activities (§10.2) following P12-D003 backup gate.

---

**Version 1.1**

**Revision Summary:**

* Refined version pinning policy.
* Deferred Primary Key investigation to Step 1D.
* Clarified extension rollback governance.
* Strengthened extension validation guidance.

No architectural decisions were changed. Only implementation planning guidance was improved.

---

*Planning document v1.1 — Phase 12 Step 1B — Design & Implementation Plan*  
*Architecture review refinements incorporated: June 2026*  
*No docker-compose.yml, Dockerfile, Alembic, Python code, SQLAlchemy models, migrations, or dependencies were modified during this planning activity.*
