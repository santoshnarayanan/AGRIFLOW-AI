# AGRIFLOW-AI — Phase 12 Decision Register

**Document Type:** Architecture & Infrastructure Decision Register  
**Version:** 1.1  
**Phase:** 12 — TimescaleDB Time-Series Foundation  
**Status:** Active  
**Governance Reference:** `docs/report/PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md` v1.3

This register records formal decisions made during Phase 12. Decisions affecting API contracts, domain models, repository interfaces, service interfaces, primary key strategy, or database architecture require an **Architecture Decision Review (ADR)** per Step 1A Section 2.4 before implementation.

---

## Decision Index

| ID | Title | Step | Status | Date |
|---|---|---|---|---|
| P12-D001 | TimescaleDB Docker Image Selection | 1B | ✅ Approved for Implementation | June 2026 |
| P12-D002 | TimescaleDB Version Pinning Strategy | 1B | ✅ Approved for Implementation | June 2026 |
| P12-D003 | Pre-Migration Backup Strategy | 1B | ✅ Approved for Implementation | June 2026 |
| P12-D004 | TimescaleDB Extension Enablement Strategy | 1C | ✅ Approved for Implementation | June 2026 |
| P12-D005 | Infrastructure Rollback Strategy | 1B / 1C | ✅ Approved for Implementation | June 2026 |

---

## P12-D001 — TimescaleDB Docker Image Selection

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D001 |
| **Step** | 1B |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §2.1 — PostgreSQL 17; TimescaleDB as PostgreSQL extension; Docker Compose primary dev runtime |
| **Deciders** | Senior Platform Architecture (Step 1B Planning) |

### Context

AGRIFLOW-AI runs PostgreSQL 17 via `postgres:17-alpine` in Docker Compose on macOS Apple Silicon. Phase 12 requires a TimescaleDB-enabled PostgreSQL 17 image without introducing a separate database technology.

### Decision

Adopt the official **`timescale/timescaledb`** Docker image (Alpine-based, lightweight) with a **pinned semver tag** on the PostgreSQL 17 platform.

**Image reference (implementation target):**

```text
timescale/timescaledb:<semver>-pg17
```

**Example at time of planning:** `timescale/timescaledb:2.28.0-pg17` — illustrative only; see P12-D002 for version selection policy.

**Implemented pin:** Record the exact tag selected at Step 1B implementation in P12-D002 § Implemented Pin Record.

### Alternatives Considered

| Alternative | Rejected Because |
|---|---|
| `timescale/timescaledb-ha:pg17` | Ubuntu-based HA image with Patroni, Toolkit, PostGIS — operational overhead not required for local dev; exceeds Step 1B scope |
| `timescale/timescaledb:latest-pg17` | Violates Step 1A pinning requirement; `latest-*` tags can shift TimescaleDB minor versions unexpectedly |
| `postgres:17-alpine` + manual extension install | Not supported in standard Postgres image; extension must ship with database container |
| `timescale/timescaledb:<semver>-pg17-oss` | Valid fallback for OSS-only licensing; full image selected for complete TimescaleDB feature set needed in Phase 12E |

### Rationale

1. Official Timescale-maintained image based on the [official PostgreSQL Docker image](https://hub.docker.com/_/postgres) — same environment variables, data directory layout, and `pg_isready` health check semantics.
2. PostgreSQL 17 platform tag aligns with approved Step 1A baseline.
3. Multi-architecture builds (amd64 + arm64) support macOS Apple Silicon via Docker Desktop.
4. TimescaleDB ships as a pre-installed extension binary — no Python dependency changes required.

### Consequences

* Only `docker-compose.yml` `db.image` (and optional header comment) changes in Step 1B.
* Backend Dockerfile and `requirements.txt` remain unchanged.
* Existing `postgres_data` volume remains mounted at `/var/lib/postgresql/data`.

### Compliance

✅ Compliant with Step 1A approved baseline. No conflict identified.

---

## P12-D002 — TimescaleDB Version Pinning Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D002 |
| **Step** | 1B |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §12 Recommendation #1 — pin image tag; do not use `latest` |

### Context

TimescaleDB intentionally omits a bare `latest` tag to prevent unexpected PostgreSQL major version upgrades. AGRIFLOW-AI requires reproducible dev environments and controlled upgrade paths.

### Decision

Pin the Docker image to an **exact semver tag** encoding both TimescaleDB and PostgreSQL platform versions:

```text
<timescaledb-version>-pg17
```

### Version Selection Policy

| Rule | Detail |
|---|---|
| Selection criterion | Latest stable TimescaleDB release for PostgreSQL 17 available at implementation time |
| Prohibited tags | `latest`, `latest-pg17` |
| Pin requirement | Always commit an explicit semantic version — never a rolling tag |
| Verification gate | Confirm selected tag exists on [Docker Hub — timescale/timescaledb tags](https://hub.docker.com/r/timescale/timescaledb/tags) before Step 1B image swap; re-verify before Step 1C |
| Record keeping | Record the exact implemented pin in § Implemented Pin Record below |

### Implemented Pin Record

| Field | Value |
|---|---|
| **Implemented pin** | *To be recorded at Step 1B implementation* |
| **Implementation date** | *To be recorded* |
| **Verified on Docker Hub** | *To be recorded* |
| **Example (planning reference only)** | `2.28.0-pg17` |

### Upgrade Policy

| Environment | Policy |
|---|---|
| Local development | Update pin deliberately; document in this register with new decision entry |
| Shared / staging | Requires backup + smoke test before pin bump |
| Production (future) | Requires change window, pg_dump, and rollback plan |

### Consequences

* Image upgrades are explicit, reviewable diffs in `docker-compose.yml`.
* Team must record pin changes as new register entries or amendments to P12-D002.

### Compliance

✅ Compliant with Step 1A approved baseline.

---

## P12-D003 — Pre-Migration Backup Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D003 |
| **Step** | 1B (before image swap); repeated before Step 1C |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §6.6, §12 Recommendation #2 — pg_dump before image switch |

### Context

Step 1B replaces the database container image while retaining the `postgres_data` Docker volume. Although TimescaleDB images are PostgreSQL-compatible, a point-in-time logical backup is mandatory before any infrastructure change.

### Decision

Execute a **custom-format pg_dump** from the host before Step 1B image swap and before Step 1C extension migration.

**Standard backup command:**

```bash
docker compose exec db pg_dump \
  -U agriflow \
  -d agriflow \
  -F c \
  -f /tmp/pre_phase12_step1b_$(date +%Y%m%d_%H%M%S).dump

docker compose cp db:/tmp/pre_phase12_step1b_*.dump ./backups/
```

**Host-native alternative (current port mapping):**

```bash
pg_dump -h localhost -p 25432 -U agriflow -d agriflow \
  -F c -f "./backups/pre_phase12_step1b_$(date +%Y%m%d_%H%M%S).dump"
```

### Backup Storage

| Requirement | Detail |
|---|---|
| Location | `./backups/` (gitignored) or operator secure storage |
| Retention | Retain until Step 1C validated; minimum 30 days for shared environments |
| Naming | `pre_phase12_step1b_YYYYMMDD_HHMMSS.dump`, `pre_phase12_step1c_YYYYMMDD_HHMMSS.dump` |
| Verification | `pg_restore --list <dumpfile>` confirms readable archive |

### Consequences

* Backup is a **mandatory gate** before Step 1B and Step 1C execution — not optional.
* Empty/dev environments should still practice the backup workflow to validate runbook.

### Compliance

✅ Compliant with Step 1A approved baseline.

---

## P12-D004 — TimescaleDB Extension Enablement Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D004 |
| **Step** | 1C |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §2.3 Step 1C Approved; §8 Step 1C actions; immutable Alembic history |

### Context

TimescaleDB must be activated as a PostgreSQL extension in the `agriflow` database. Step 1A approves extension enablement via forward Alembic migration without application-layer changes.

### Decision

Enable TimescaleDB through a **new forward-only Alembic migration** executed after Step 1B image validation:

**Upgrade DDL:**

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

**Downgrade DDL (Alembic completeness — governance restricted):**

```sql
DROP EXTENSION IF EXISTS timescaledb CASCADE;
```

**Downgrade governance (see Step 1B plan §7.1.1):**

| Rule | Detail |
|---|---|
| Purpose | Satisfies Alembic migration reversibility — not a production rollback procedure |
| Permitted use | Development environments **before any hypertables exist** (pre-Step 1D) |
| After Step 1D | Extension removal is **not** a normal rollback strategy |
| Post-Step 1D rollback | Restore from pg_dump backup (P12-D003 / P12-D005 Tier 2) |

**Verification queries:**

```sql
-- Extension installed in AGRIFLOW database
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Extension binaries available in database image
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name = 'timescaledb';
```

Both queries should be executed — `pg_available_extensions` confirms binaries in the image; `pg_extension` confirms installation in `agriflow`.

### Constraints

| Constraint | Detail |
|---|---|
| No historical migration edits | Migrations `001` through `a1b2c3d4e5f6` remain immutable |
| No schema changes beyond extension | Existing tables, indexes, enums unchanged in Step 1C |
| No application code changes | API, Service, Repository, Schema layers unchanged |
| Privilege requirement | `POSTGRES_USER` (`agriflow`) must have `CREATE` privilege on database — default superuser in dev Compose |

### Note on Image Auto-Enablement

The `timescale/timescaledb` image may pre-enable the extension in the default `postgres` database. The `agriflow` database (set via `POSTGRES_DB`) requires explicit `CREATE EXTENSION` — the Alembic migration ensures extension state is version-controlled and reproducible across environments.

### Consequences

* Step 1C is fully specified — no additional architectural decisions required for extension enablement.
* Hypertable conversion (Step 1D) remains deferred pending Architecture Approval for primary key strategy.

### Compliance

✅ Compliant with Step 1A approved baseline. Does not implement deferred Step 1D/1E items.

---

## P12-D005 — Infrastructure Rollback Strategy

| Attribute | Value |
|---|---|
| **Decision ID** | P12-D005 |
| **Step** | 1B / 1C |
| **Status** | ✅ Approved for Implementation |
| **Date** | June 2026 |
| **Baseline Reference** | Step 1A §6.6 Rollback Risks; §12 Recommendation #8 |

### Context

Infrastructure changes must be reversible without data loss. Rollback procedures must be defined before execution.

### Decision

Adopt a **three-tier rollback model**:

#### Tier 1 — Image Revert (Step 1B failure)

1. `docker compose down`
2. Revert `docker-compose.yml` `db.image` to `postgres:17-alpine`
3. `docker compose up -d`
4. Validate: health check passes, APIs respond, data intact

**Data impact:** None — same volume, compatible PostgreSQL 17.

#### Tier 2 — Logical Restore (data corruption or migration failure)

1. `docker compose down`
2. Remove volume: `docker volume rm agriflow-ai_postgres_data` (destructive)
3. Restore: `docker compose up -d db` then `pg_restore` from P12-D003 backup
4. Revert compose image if needed
5. Validate schema and row counts

#### Tier 3 — Extension Rollback (Step 1C failure — pre-Step 1D only)

1. `alembic downgrade -1` (runs `DROP EXTENSION IF EXISTS timescaledb CASCADE`)
2. Validate: extension absent; existing tables operational
3. If downgrade fails: Tier 2 logical restore

**Governance:** Tier 3 is valid only **before Step 1D introduces hypertables**. After hypertables exist, rollback uses Tier 2 backup restore — not extension removal.

### Rollback Decision Matrix

| Failure Scenario | Rollback Tier | Estimated Recovery |
|---|---|---|
| TimescaleDB image fails to start | Tier 1 | < 5 minutes |
| Data present but APIs fail | Tier 1 + logs review | < 15 minutes |
| Volume corruption | Tier 2 | 15–60 minutes |
| Extension migration fails | Tier 3 → Tier 2 if needed | 15–60 minutes |

### Consequences

* Rollback runbook must be executed in practice during Step 1B validation on a disposable copy before shared-environment changes.
* `DROP EXTENSION ... CASCADE` via Alembic downgrade is a **dev-only, pre-Step 1D** rollback path — not applicable after hypertables exist (Step 1D deferred).

### Compliance

✅ Compliant with Step 1A approved baseline.

---

## Deferred Decisions (Not in This Register)

The following remain **deferred pending Architecture Decision Review** per Step 1A §2.2. They must **not** be implemented based on Step 1B planning alone:

| Topic | Register Status |
|---|---|
| Composite Primary Key migration | ⏳ Awaiting ADR |
| UUID Primary Key migration strategy | ⏳ Awaiting ADR |
| Hypertable primary key strategy | ⏳ Awaiting ADR — investigation scoped to Step 1D |
| Repository-level analytics methods | ⏳ Awaiting ADR |
| `time_bucket()` repository implementations | ⏳ Awaiting ADR |
| Primary key / `create_hypertable()` compatibility investigation | ⏳ Deferred to Step 1D — not in Step 1B scope |

---

**Version 1.1**

**Revision Summary:**

* Generalized version pinning policy (P12-D001, P12-D002).
* Added Implemented Pin Record to P12-D002.
* Clarified Alembic downgrade governance (P12-D004, P12-D005).
* Strengthened extension validation queries (P12-D004).
* Explicitly deferred PK / hypertable investigation to Step 1D.

No architectural decisions were changed.

---

*Decision Register v1.1 — Architecture review refinements incorporated: June 2026*
