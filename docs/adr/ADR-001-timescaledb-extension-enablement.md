# ADR-001 — TimescaleDB Extension Enablement via Alembic Migration

**Status:** Accepted  
**Date:** 2026-06-29  
**Phase:** 12 — TimescaleDB Time-Series Foundation  
**Step:** 1D  
**Decision Makers:** Senior Platform Architecture  
**Governance Reference:** `PHASE12_DECISION_REGISTER.md` P12-D004

---

## Context

AGRIFLOW-AI requires TimescaleDB as a time-series database foundation for Phase 12 features including sensor data optimisation, satellite observation analytics, and AI feature extraction pipelines.

At the start of Step 1D, the system state was:

* PostgreSQL 17.10 running inside `timescale/timescaledb:2.28.1-pg17` (introduced in Step 1C)
* TimescaleDB extension binaries present in the image (`default_version = 2.28.1`)
* TimescaleDB extension NOT installed in the `agriflow` database (`installed_version = NULL`)
* Alembic migration history: linear chain ending at `a1b2c3d4e5f6`
* No application-layer awareness of TimescaleDB

The question to be decided: **How should the TimescaleDB extension be activated in the `agriflow` database?**

There were three candidate approaches:

1. Manual SQL (`psql` or admin tool)
2. Forward Alembic migration
3. Container initialisation script (`docker-compose` entrypoint or init SQL)

---

## Decision

**Enable TimescaleDB through a forward Alembic migration** (`f1e2d3c4b5a6`).

Migration DDL:

```sql
-- upgrade
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- downgrade
DROP EXTENSION IF EXISTS timescaledb CASCADE;
```

The migration was executed from the host Python environment using the project's virtual environment connected to the database via `localhost:25432` (the host-mapped port). This is the pre-documented execution path per Step 1C §11.

A prerequisite operational step was also required: `ALTER SYSTEM SET shared_preload_libraries = 'timescaledb'` followed by `docker compose restart db`. This corrected a Step 1C configuration gap (see §Known Issues in this ADR and P12-D006 in the Decision Register).

---

## Alternatives Considered

### Alternative 1 — Manual SQL via psql

Execute `CREATE EXTENSION timescaledb CASCADE` directly through `psql` or a database administration tool, without any migration record.

**Rejected because:**

* Extension state would not be version-controlled — no record in Alembic history
* Fresh deployments would not automatically install the extension
* Inconsistency between development environments (some may have the extension, others may not)
* Violates AGRIFLOW-AI's infrastructure-as-code principle: all database changes are tracked through Alembic
* Approved by P12-D004 to use forward Alembic migration — manual SQL conflicts with the approved strategy

### Alternative 2 — Container Initialisation Script

Add a SQL file to `docker-compose.yml` as a volume-mounted init script, or modify the Dockerfile to include a `CREATE EXTENSION` statement.

**Rejected because:**

* Requires modification to `docker-compose.yml` or `Dockerfile` — both are explicitly prohibited by Step 1D operating constraints
* Init scripts in the TimescaleDB image only run on a fresh data directory; the existing volume would not be affected
* Extension state would not appear in Alembic history
* Violates Step 1A §8 approved sequence which specifies Alembic migration for extension enablement

### Alternative 3 — Alembic Autogenerate

Use `alembic revision --autogenerate` to generate the migration automatically.

**Not applicable** because `autogenerate` detects SQLAlchemy model changes, not raw SQL DDL like `CREATE EXTENSION`. The migration was authored manually (with `alembic revision --rev-id f1e2d3c4b5a6 -m "enable_timescaledb_extension"`) and populated with explicit DDL.

---

## Consequences

### Positive

* Extension state is version-controlled: any fresh deployment running `alembic upgrade head` will install the extension automatically
* Migration history remains linear and auditable
* Alembic downgrade (`alembic downgrade -1`) provides a reversible path in development environments before hypertables exist
* No application code, API, repository, service, schema, Docker Compose, or Dockerfile changes required
* TimescaleDB API is now available for use in subsequent migration steps (hypertable creation in Step 1E)

### Negative / Trade-offs

* The asyncpg driver caused the first `alembic upgrade head` attempt to fail with a connection drop during `CREATE EXTENSION`. This is a known asyncpg / TimescaleDB interaction when `shared_preload_libraries` is not pre-configured. Future deployments on fresh volumes will not encounter this issue because the TimescaleDB image configures `shared_preload_libraries` during volume initialisation.
* `CREATE EXTENSION timescaledb CASCADE` is inherently non-transactional in some PostgreSQL configurations (it modifies shared state). The Alembic transaction wrapper was not an obstacle in the final execution — the migration committed successfully once `shared_preload_libraries` was configured.

### Downgrade Governance

The `downgrade()` function (`DROP EXTENSION IF EXISTS timescaledb CASCADE`) is **governance-restricted**:

| Condition | Permitted |
|---|---|
| Before Step 1E (no hypertables) | ✅ Yes — development rollback only |
| After Step 1E (hypertables exist) | ❌ No — `CASCADE` would drop all hypertable metadata and chunk data |

After Step 1E, the approved rollback path is **Tier 2 pg_dump restore** per P12-D005.

### Hypertable Deferral

This ADR intentionally does **not** address hypertable creation, which is deferred to Step 1E pending an Architecture Decision Review for primary key strategy. The extension enablement migration is a necessary precondition for hypertable creation but is otherwise a zero-impact change to the application layer.

---

## Known Issues at Time of Decision

### asyncpg Connection Drop During CREATE EXTENSION

When `alembic upgrade head` was first executed, the asyncpg driver raised:

```text
asyncpg.exceptions.ConnectionDoesNotExistError: connection was closed in the middle of operation
```

This occurred because `shared_preload_libraries` was empty — the TimescaleDB server hook attempted to initialise without being loaded as a preload library, causing the PostgreSQL backend to terminate.

**Resolution:** Applied `ALTER SYSTEM SET shared_preload_libraries = 'timescaledb'` (database configuration operation, not Docker infrastructure modification) and restarted the db container. Migration then succeeded on the second attempt.

**Future deployments:** Fresh Docker volumes initialised by `timescale/timescaledb:2.28.1-pg17` will include `shared_preload_libraries = 'timescaledb'` automatically — this issue will not recur on clean installations.

### Backend Health Ready Degradation (Pre-Existing)

`GET /api/v1/health/ready` returns `database: unreachable` inside the Compose network. This is pre-existing (Step 1C §9.1) and unrelated to this decision.

---

## Related Decisions

| ID | Title | Relationship |
|---|---|---|
| P12-D004 | TimescaleDB Extension Enablement Strategy | This ADR implements P12-D004 |
| P12-D003 | Pre-Migration Backup Strategy | Pre-migration backup taken before this decision was implemented |
| P12-D005 | Infrastructure Rollback Strategy | Tier 3 rollback applies until Step 1E |
| P12-D006 | shared_preload_libraries Configuration Gap Resolution | Prerequisite resolved during this step |

---

## References

* `PHASE12_DECISION_REGISTER.md` v1.2 — P12-D004, P12-D006
* `PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md` v1.3 — §2.3, §8
* `PHASE12_STEP1B_TIMESCALEDB_INFRASTRUCTURE_PLAN.md` v1.1 — §7.1.1
* `PHASE12_STEP1C_IMPLEMENTATION_REPORT.md` v1.0 — §8, §9, §11
* `PHASE12_STEP1D_EXTENSION_ENABLEMENT_REPORT.md` v1.0
* [TimescaleDB Extension Documentation](https://docs.timescale.com/self-hosted/latest/install/installation-docker/)

---

*ADR-001 — Accepted: 2026-06-29 — Phase 12 Step 1D*
