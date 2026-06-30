# Phase 12 — Platform Bootstrap Guide

**Version:** 1.2  
**Status:** Approved  
**Last Updated:** 2026-06-30  
**Scope:** Operational guide — rebuild the complete Phase 12 analytical platform from scratch  
**Architecture Reference:** [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md)  
**CDD Reference:** [backend/app/cdd/README.md](../backend/app/cdd/README.md)

---

## Purpose

This guide enables a developer to **completely rebuild** the AGRIFLOW-AI Phase 12 analytical platform — from an empty machine through a fully validated TimescaleDB deployment with CDD v1.0.0 — without reading implementation reports.

Use this guide for:

- New developer onboarding
- New machine setup
- Database rebuild after volume wipe
- Docker environment recreation
- Disaster recovery (Tier 2 `pg_dump` restore)
- Local development environment recreation

**Expected outcome:** PostgreSQL 17.10 + TimescaleDB 2.28.1, Alembic at `f6a7b8c9d0e1`, 6 hypertables, 6 compression policies, 8 continuous aggregates, 11 retention policies, 27 platform background jobs, and CDD v1.0.0 (458,645 rows) validated.

---

## Platform Bootstrap Philosophy

This guide is an **operational runbook** — it tells you what to run, in what order, and how to verify success. It does not explain *why* the architecture was designed this way. For architectural rationale, use the [Phase 12 Complete Architecture Handbook](12-phase12-complete-architecture-handbook.md).

**Guiding principles:**

1. **Execute sequentially.** Each stage depends on the previous one. Do not run Alembic before Docker is healthy, or seed CDD before migrations complete.
2. **Never skip validation.** Every major step includes verification commands. A passing migration does not guarantee a healthy platform — confirm hypertables, policies, row counts, and API health.
3. **Resolve failures before proceeding.** A failed validation at any stage blocks all downstream steps. Fix the root cause, then re-run validation from that stage forward.
4. **Cross-reference, don't duplicate.** ADRs, handbooks, and validation reports contain the detailed explanations. This guide links to them instead of repeating architectural content.
5. **Treat this as the operational companion** to the Complete Architecture Handbook — architecture explains *what* was built; this guide explains *how to build it again*.

> **Working directory legend:** Commands in this guide are prefixed with a location indicator — **📍 Repository Root**, **📍 `backend/`**, **📍 Host Machine**, **📍 Docker Container**, or **📍 PostgreSQL (psql)** — so you always know where to run them.

---

## Expected Platform State After Successful Bootstrap

When bootstrap completes successfully, the platform matches this end state:

| Category | Component | Expected Value |
|---|---|---|
| **Infrastructure** | PostgreSQL | 17.10 |
| | TimescaleDB | 2.28.1 |
| | Docker services | `db` (healthy) + `backend` (running) |
| | Alembic revision | `f6a7b8c9d0e1` (head) |
| **Database** | Hypertables | 6 |
| | Compression policies | 6 |
| | Continuous aggregates | 8 |
| | Refresh policies | 8 |
| | Retention policies | 11 |
| | Background jobs (platform) | 27 (+ 2 system) |
| **Data** | Canonical Development Dataset | `cdd-v1.0.0` / profile `cdd-dev` / seed `42` |
| | Total rows | 458,645 |
| | Materialised aggregates | 8 CAs with bucket data (post manual refresh) |
| **Application** | API health (`/health/live`) | HTTP 200 — `alive` |
| | API readiness (`/health/ready`) | HTTP 200 — database reachable |
| **Architecture** | Phase 13 ready | ✅ Persistence layer complete — Feature Store may begin |

---

## Estimated Execution Timeline

Approximate durations on a typical development machine (macOS / Windows with Docker Desktop):

| Stage | Estimated Duration |
|---|---|
| Repository setup (clone, venv, dependencies, `.env`) | 5–10 min |
| Docker startup (`docker compose up -d --build`) | 1–3 min |
| Alembic migrations (`alembic upgrade head`) | < 1 min |
| CDD generation (in-memory) | ~5 s |
| Dataset persistence (`execute_cdd_workflow`) | ~28 s |
| Continuous aggregate refresh (manual × 8) | ~30 s |
| Platform validation (SQL + API checks) | ~2 min |
| **Complete rebuild (total)** | **~5–10 min** |

> **Tip:** First-time Docker image pulls add 2–5 minutes. Subsequent rebuilds are faster.

> **⚠️ Common First-Time Mistakes**
>
> - **Forgetting to activate the Python virtual environment** before running Alembic or CDD — commands fail with `ModuleNotFoundError`. See [Section 2](#2-repository-setup).
> - **Using PostgreSQL port `5432` instead of `25432` from the host** — Alembic and CDD cannot connect. Set `POSTGRES_PORT=25432` in `backend/.env`. See [Section 11](#11-troubleshooting).
> - **Running Alembic before Docker is healthy** — connection refused. Wait for `docker compose ps` to show `db` as `healthy`. See [Section 3](#3-docker-environment).
> - **Forgetting the root `.env` file** — `POSTGRES_PASSWORD must be set` on `docker compose up`. Create `.env` at repository root. See [Section 2](#2-repository-setup).
> - **Running CDD persistence twice without cleaning the database** — duplicate primary key errors. Wipe with `docker compose down -v` or truncate tables first. See [Section 6](#6-canonical-development-dataset-cdd).
> - **Forgetting the one-time manual Continuous Aggregate refresh** after initial CDD load — CAs appear empty. Run `refresh_continuous_aggregate(..., NULL, NULL)` for all 8 aggregates. See [Section 6](#6-canonical-development-dataset-cdd) and [Step 3C](report/PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md).

---

## Daily Developer Commands

Quick reference for everyday development. Run all Docker commands from the repository root unless noted.

### Local Developer Startup Workflow

```mermaid
flowchart LR
    VENV["Activate .venv"]
    UP["docker compose up -d"]
    PS["docker compose ps"]
    API["curl health/live"]
    WORK["Develop / validate"]

    VENV --> UP --> PS --> API --> WORK

    style WORK fill:#c8e6c9
```

### Daily Development Cycle

```mermaid
flowchart TD
    START["Start day"]
    UP["docker compose up -d"]
    CODE["Develop / test APIs"]
    MIG{"Schema changed?"}
    ALE["alembic upgrade head"]
    VAL["Quick validation"]
    STOP["docker compose stop"]

    START --> UP --> CODE --> MIG
    MIG -->|Yes| ALE --> CODE
    MIG -->|No| VAL
    CODE --> VAL --> STOP

    style VAL fill:#e3f2fd
```

### Docker

| Command | Purpose | Expected Result |
|---|---|---|
| `docker compose up -d` | Start `db` and `backend` in background | Both containers `Up`; `db` becomes `healthy` |
| `docker compose stop` | Stop containers without removing volumes | Containers stopped; data preserved |
| `docker compose restart` | Restart all services | Containers recycle; connections briefly drop |
| `docker compose ps` | List running containers | `db` healthy, `backend` running |
| `docker compose logs -f backend` | Stream backend logs | Uvicorn startup and request logs |
| `docker compose logs -f db` | Stream database logs | PostgreSQL ready messages |
| `docker compose logs --tail 50 db` | Recent database log lines | Last 50 log entries |
| `docker compose down -v` | Stop and **delete** `postgres_data` volume | Full database wipe — use only for rebuild |

> **📍 Repository Root**

```bash
# Start services
docker compose up -d

# Stop services (data preserved)
docker compose stop

# Restart after config change
docker compose restart

# View running containers
docker compose ps

# View logs (last 50 lines)
docker compose logs --tail 50 backend
docker compose logs --tail 50 db
```

### Python Environment

> **📍 Repository Root** (activate venv) · **📍 `backend/`** (install dependencies)

```bash
# Activate virtual environment (macOS / Linux)
source .venv/bin/activate

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\activate

# Install / update dependencies
cd backend && pip install -r requirements.txt

# Verify Python version
python --version
```

**Expected:** `Python 3.12.x` and `import fastapi, sqlalchemy, alembic` succeeds.

### Alembic

> **📍 `backend/`** (venv active)

```bash
cd backend

# Show current revision
alembic current

# Show migration history
alembic history

# Apply all pending migrations
alembic upgrade head
```

| Command | What it does | Expected output |
|---|---|---|
| `alembic current` | Prints the revision applied to the connected database | `f6a7b8c9d0e1 (head)` on a current platform |
| `alembic history` | Lists all migration revisions in dependency order | 16 revisions ending at `f6a7b8c9d0e1` |
| `alembic upgrade head` | Runs all pending migrations via async SQLAlchemy engine | Sequential `Running upgrade` lines; no errors |

**Verification:** `alembic current` matches `f6a7b8c9d0e1 (head)`.

### PostgreSQL

> **📍 Repository Root** (commands execute inside Docker `db` container via `docker compose exec`)

```bash
# Interactive psql session
docker compose exec db psql -U agriflow -d agriflow

# Verify TimescaleDB extension
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';"

# List databases
docker compose exec -T db psql -U agriflow -d postgres -c "\l"
```

**Expected:** Extension version `2.28.1`; database `agriflow` exists and is owned by user `agriflow`.

### Backup & Restore

> **📍 Repository Root** (output file written to current directory)

```bash
# Create backup (custom format)
docker compose exec -T db pg_dump -U agriflow -d agriflow -F c > agriflow_backup.dump

# Restore backup
docker compose exec -T db pg_restore -U agriflow -d agriflow --clean --if-exists < agriflow_backup.dump
```

**Expected:** Backup file ~40–50 MB with CDD loaded; restore completes without fatal errors. See [Section 9](#9-backup--restore).

### Platform Validation (Quick Checklist)

Run these after schema changes, CDD reload, or container restart:

> **📍 `backend/`** + **📍 Repository Root** (mixed — see comments in block)

```bash
# 1. Alembic head
cd backend && alembic current

# 2. Hypertable count
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT COUNT(*) FROM timescaledb_information.hypertables;"

# 3. Background job summary
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT proc_name, COUNT(*) FROM timescaledb_information.jobs GROUP BY proc_name ORDER BY proc_name;"

# 4. CDD sensor row count
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT COUNT(*) FROM sensor_readings;"

# 5. API health
curl -s http://localhost:8000/api/v1/health/live
curl -s http://localhost:8000/api/v1/health/ready
```

**Expected:** Head `f6a7b8c9d0e1`; 6 hypertables; 27 policy jobs; 438,000 sensor rows; HTTP 200 on both health endpoints.

### Further Reading (Daily Commands)

| Topic | Document |
|---|---|
| Complete architecture | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) |
| Full validation SQL | [Section 8](#8-sql-verification-cheat-sheet) of this guide |
| Troubleshooting | [Section 11](#11-troubleshooting) of this guide |

---

## Table of Contents

- [Platform Bootstrap Philosophy](#platform-bootstrap-philosophy)
- [Expected Platform State After Successful Bootstrap](#expected-platform-state-after-successful-bootstrap)
- [Estimated Execution Timeline](#estimated-execution-timeline)
- [Daily Developer Commands](#daily-developer-commands)
1. [Prerequisites](#1-prerequisites)
2. [Repository Setup](#2-repository-setup)
- [Repository Layout](#repository-layout)
3. [Docker Environment](#3-docker-environment)
4. [Database Initialization](#4-database-initialization)
5. [Schema Creation](#5-schema-creation)
6. [Canonical Development Dataset (CDD)](#6-canonical-development-dataset-cdd)
7. [Platform Validation](#7-platform-validation)
8. [SQL Verification Cheat Sheet](#8-sql-verification-cheat-sheet)
9. [Backup & Restore](#9-backup--restore)
10. [Complete Platform Rebuild](#10-complete-platform-rebuild)
11. [Troubleshooting](#11-troubleshooting)
12. [Platform Health Checklist](#12-platform-health-checklist)
- [Platform Verification Dashboard](#platform-verification-dashboard)
- [Complete Platform Rebuild Checklist](#complete-platform-rebuild-checklist)
- [Platform Lifecycle](#platform-lifecycle)
- [Next Steps](#next-steps)

---

## 1. Prerequisites

### Required Software

| Tool | Version | Purpose |
|---|---|---|
| **Git** | 2.x+ | Clone repository |
| **Python** | **3.12.x** | Backend runtime (see `.python-version`) |
| **Docker Desktop** | 24.x+ | Container runtime |
| **Docker Compose** | 2.x+ | Service orchestration |

> **Python 3.14 is not supported.** Use Python 3.12.x until upstream `pydantic-core` compatibility is confirmed.

### Platform Versions (Phase 12)

| Component | Version | Source |
|---|---|---|
| PostgreSQL | 17.10 | `timescale/timescaledb:2.28.1-pg17` image |
| TimescaleDB | 2.28.1 | Same image |
| FastAPI | 0.115.5 | `backend/requirements.txt` |
| SQLAlchemy | 2.0.36 | `backend/requirements.txt` |
| Alembic | 1.14.0 | `backend/requirements.txt` |
| Alembic head | `f6a7b8c9d0e1` | Phase 12 retention policies |

### Version Compatibility Matrix

Verified platform versions for Phase 12 bootstrap. Do not mix major versions across components.

| Component | Required Version | Notes |
|---|---|---|
| **Python** | 3.12.x | See `.python-version`; 3.14 not supported |
| **Docker** | 24.x+ | Docker Desktop on macOS / Windows |
| **Docker Compose** | 2.x+ | Bundled with Docker Desktop |
| **PostgreSQL** | 17.10 | Via `timescale/timescaledb:2.28.1-pg17` image |
| **TimescaleDB** | 2.28.1 | Extension enabled by migration `f1e2d3c4b5a6` |
| **FastAPI** | 0.115.5 | `backend/requirements.txt` |
| **SQLAlchemy** | 2.0.36 | Async engine; Alembic migrations |
| **Alembic** | 1.14.0 | Head revision `f6a7b8c9d0e1` |
| **CDD Version** | `cdd-v1.0.0` | Profile `cdd-dev`, seed `42` |
| **Alembic Head Revision** | `f6a7b8c9d0e1` | Retention policies — final Phase 12 migration |

### Optional Tools

| Tool | Purpose |
|---|---|
| `pyenv` | Automatic Python 3.12 selection via `.python-version` |
| `pgAdmin` | GUI database inspection (`localhost:25432`) |
| `curl` / `httpie` | API health checks |

### Network & Ports

| Service | Host Port | Container Port |
|---|---|---|
| PostgreSQL | `25432` | `5432` |
| FastAPI | `8000` | `8000` |

### Further Reading

| Topic | Document |
|---|---|
| Local development setup | [05-local-setup.md](05-local-setup.md) |
| Phase 12 architecture | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) |

---

## 2. Repository Setup

### Clone Repository

> **📍 Host Machine**

```bash
git clone <repository-url>
cd AGRIFLOW-AI
```

**Expected outcome:** Repository root contains `docker-compose.yml`, `backend/`, and `docs/`.

### Create Python Virtual Environment

**macOS / Linux:**

> **📍 Repository Root**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**

> **📍 Repository Root**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Expected outcome:** Shell prompt shows `(.venv)` active.

### Install Dependencies

> **📍 `backend/`** (venv active)

```bash
cd backend
pip install -r requirements.txt
```

**Expected outcome:** All packages install without error. Verify with:

> **📍 `backend/`**

```bash
python -c "import fastapi, sqlalchemy, alembic; print('OK')"
```

### Configure Environment Files

Docker Compose requires `POSTGRES_PASSWORD` at the **project root**. The backend reads credentials from `backend/.env`.

**Step 1 — Backend environment:**

> **📍 Repository Root**

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=25432
POSTGRES_DB=agriflow
POSTGRES_USER=agriflow
POSTGRES_PASSWORD=changeme
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
```

> **Important:** When running Alembic or CDD from the **host machine**, use port **25432** (Docker host mapping). When the backend runs **inside Docker**, Compose overrides `POSTGRES_HOST=db` and port `5432` automatically.

**Step 2 — Docker Compose root environment:**

Create a `.env` file at the repository root (same password as `backend/.env`):

> **📍 Repository Root**

```bash
echo "POSTGRES_PASSWORD=changeme" > .env
```

**Expected outcome:** `docker compose config` resolves `POSTGRES_PASSWORD` without error.

---

## Repository Layout

Simplified tree of directories developers interact with during Phase 12 bootstrap:

```text
AGRIFLOW-AI/
├── docs/                          Phase 12 handbooks, ADRs, validation reports
├── docker-compose.yml             Local Docker stack (PostgreSQL + FastAPI)
├── backend/
│   ├── alembic.ini                Alembic configuration and migration entry point
│   ├── requirements.txt           Python dependencies
│   └── app/
│       ├── cdd/                   Canonical Development Dataset generator and persistence
│       ├── db/
│       │   ├── migrations/        Alembic revisions (domain schema + TimescaleDB stack)
│       │   ├── models/            SQLAlchemy ORM models
│       │   └── repositories/    Data access layer (unchanged in Phase 12)
│       ├── api/                   FastAPI routers and health endpoints
│       └── services/              Domain business logic (unchanged in Phase 12)
```

| Directory | Purpose |
|---|---|
| `docs/` | Architecture handbooks, ADRs, bootstrap guide, and validation reports |
| `docker-compose.yml` | Defines `db` (TimescaleDB) and `backend` (FastAPI) services |
| `backend/app/cdd/` | Deterministic dataset generation, validation, and persistence workflow |
| `backend/app/db/migrations/` | All Alembic revisions including Phase 12 TimescaleDB migrations |
| `backend/app/db/models/` | ORM models — six time-series models use composite PKs per ADR-002 |
| `backend/app/db/repositories/` | Repository layer — no Phase 12 changes; queries work against hypertables transparently |
| `backend/app/api/` | REST API including `/api/v1/health/live` and `/ready` validation endpoints |
| `backend/app/services/` | Service layer — unchanged in Phase 12 |

### Further Reading

| Topic | Document |
|---|---|
| Environment configuration | [05-local-setup.md](05-local-setup.md) |
| Decision register (backup protocol) | [PHASE12_DECISION_REGISTER.md](report/PHASE12_DECISION_REGISTER.md) |

---

## 3. Docker Environment

### Bootstrap Workflow Overview

```mermaid
flowchart TD
    CLONE["Clone repository"]
    VENV["Create venv + pip install"]
    ENV["Configure .env files"]
    UP["docker compose up -d"]
    WAIT["Wait for db healthcheck"]
    MIG["alembic upgrade head"]
    CDD["execute_cdd_workflow"]
    CA["Manual CA refresh"]
    VAL["Platform validation"]

    CLONE --> VENV --> ENV --> UP --> WAIT --> MIG --> CDD --> CA --> VAL

    style VAL fill:#c8e6c9
```

### Start Containers

> **📍 Repository Root**

```bash
# From repository root
docker compose up -d --build
```

**Expected outcome:**

```text
✔ Container agriflow-ai-db-1       Started (healthy)
✔ Container agriflow-ai-backend-1  Started
```

#### What this command does

`docker compose up -d --build` pulls or builds the TimescaleDB and FastAPI images, creates the `postgres_data` volume if absent, starts the `db` service, waits for `pg_isready` healthcheck success, then starts `backend` with live-reload mounted source. PostgreSQL initialises on first volume creation; existing data is preserved on subsequent starts.

#### Expected Output

Both containers report `Started`. The `db` container transitions to `healthy` within ~10–30 seconds. Backend binds port `8000` on the host.

#### Verification

> **📍 Repository Root**

```bash
docker compose ps
docker compose exec db pg_isready -U agriflow -d agriflow
curl -s http://localhost:8000/api/v1/health/live
```

#### Troubleshooting

See [Section 11](#11-troubleshooting) — `POSTGRES_PASSWORD must be set`, connection refused, wrong image.

### Verify Services

> **📍 Repository Root**

```bash
docker compose ps
```

| Service | Expected State | Health |
|---|---|---|
| `db` | `Up` | `healthy` |
| `backend` | `Up` | running |

**Database connectivity:**

> **📍 Repository Root** → **📍 Docker Container (`db`)**

```bash
docker compose exec db pg_isready -U agriflow -d agriflow
```

**Expected output:** `agriflow:5432 - accepting connections`

**API liveness:**

> **📍 Host Machine** (Repository Root)

```bash
curl -s http://localhost:8000/api/v1/health/live
```

**Expected output:** `{"status":"alive"}` (HTTP 200)

### Restart Containers

> **📍 Repository Root**

```bash
docker compose restart
```

Use after configuration changes that do not require image rebuild.

### Stop Containers

> **📍 Repository Root**

```bash
docker compose stop
```

### Stop and Remove Volumes (Full Database Wipe)

> **📍 Repository Root**

```bash
docker compose down -v
```

> **Warning:** `-v` deletes the `postgres_data` volume. All database content is lost. Use only for a clean rebuild or when restoring from backup.

### Further Reading

| Topic | Document |
|---|---|
| ADR-001 (TimescaleDB image) | [ADR-001-timescaledb-extension-enablement.md](adr/ADR-001-timescaledb-extension-enablement.md) |
| Foundation handbook | [10-phase12-step1-foundation-handbook.md](10-phase12-step1-foundation-handbook.md) |
| Daily commands | [Daily Developer Commands](#daily-developer-commands) |

---

## 4. Database Initialization

### Database Initialization Flow

```mermaid
flowchart LR
    IMG["timescale/timescaledb<br/>2.28.1-pg17"]
    PG["PostgreSQL 17.10"]
    EXT["TimescaleDB extension<br/>migration f1e2d3c4b5a6"]
    SCHEMA["Domain schema<br/>migrations 001–a1b2"]
    TS["TimescaleDB stack<br/>migrations c9d8–f6a7"]

    IMG --> PG --> EXT --> SCHEMA --> TS

    style TS fill:#e3f2fd
```

### PostgreSQL Startup

PostgreSQL starts automatically with `docker compose up -d`. The `db` service uses:

- **Image:** `timescale/timescaledb:2.28.1-pg17`
- **Volume:** `postgres_data` (persistent)
- **Healthcheck:** `pg_isready` every 10 seconds

Wait for healthy status before running migrations:

> **📍 Repository Root**

```bash
docker compose ps db
```

### TimescaleDB Extension

The extension is **not** active on a fresh PostgreSQL instance until migration `f1e2d3c4b5a6` runs. Verify after migrations (Section 5):

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';"
```

**Expected output:**

```text
   extname   | extversion
-------------+------------
 timescaledb | 2.28.1
```

### Database Verification (Pre-Migration)

On a brand-new volume, only system catalogs exist:

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c "\dt"
```

**Expected output:** No application tables (or only `alembic_version` after first migration attempt).

### Further Reading

| Topic | Document |
|---|---|
| ADR-001 | [ADR-001-timescaledb-extension-enablement.md](adr/ADR-001-timescaledb-extension-enablement.md) |
| Extension enablement report | [PHASE12_STEP1D_EXTENSION_ENABLEMENT_REPORT.md](report/PHASE12_STEP1D_EXTENSION_ENABLEMENT_REPORT.md) |
| Foundation handbook | [10-phase12-step1-foundation-handbook.md](10-phase12-step1-foundation-handbook.md) |

---

## 5. Schema Creation

### Run All Migrations

From the `backend` directory with venv active:

> **📍 `backend/`** (venv active)

```bash
cd backend
alembic upgrade head
```

**Alternative — run inside Docker:**

> **📍 Repository Root**

```bash
docker compose run --rm backend alembic upgrade head
```

**Expected output:** Migrations apply sequentially ending at `f6a7b8c9d0e1`.

#### What this command does

`alembic upgrade head` connects to PostgreSQL using `DATABASE_URL` from `backend/.env`, then executes each pending migration revision in order inside async transactions. Domain migrations (`001`–`a1b2c3d4e5f6`) create relational tables. Phase 12 migrations enable TimescaleDB, convert six tables to hypertables, register compression policies, create continuous aggregates, and register retention policies. The `alembic_version` table records the applied head revision.

#### Expected Output

Sequential `INFO` lines: `Running upgrade <rev> -> <rev>, <description>`. Final revision: `f6a7b8c9d0e1`. No `ERROR` or rollback messages.

#### Verification

> **📍 `backend/`**

```bash
alembic current
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT version_num FROM alembic_version;"
```

Both should show `f6a7b8c9d0e1`.

#### Troubleshooting

Wrong port (`25432` from host), missing extension image, or hypertable migration before domain schema — see [Section 11](#11-troubleshooting) and [ADR-002](adr/ADR-002-hypertable-primary-key-conversion-strategy.md).

**Verify Alembic head:**

> **📍 `backend/`**

```bash
alembic current
```

**Expected output:**

```text
f6a7b8c9d0e1 (head)
```

### Database Migration Lifecycle

```mermaid
flowchart TD
    CONNECT["Alembic connects<br/>via DATABASE_URL"]
    READ["Read alembic_version"]
    PENDING["Identify pending revisions"]
    EXEC["Execute migration DDL"]
    COMMIT["Commit transaction"]
    UPDATE["Update alembic_version"]
    DONE["Head reached"]

    CONNECT --> READ --> PENDING --> EXEC --> COMMIT --> UPDATE
    UPDATE --> PENDING
    UPDATE --> DONE

    style DONE fill:#c8e6c9
```

### Migration Sequence

```mermaid
flowchart TD
  M001["001–006<br/>Domain tables"]
  MA1B["a1b2c3d4e5f6<br/>satellite_observations"]
  MF1E["f1e2d3c4b5a6<br/>ADR-001 Extension"]
  MC9D["c9d8e7f6a5b4<br/>ADR-002 Hypertables"]
  MD4F["d4f5e6a7b8c9<br/>ADR-003 Compression"]
  ME5F["e5f6a7b8c9d0<br/>ADR-004 CAs"]
  MF6A["f6a7b8c9d0e1<br/>ADR-005 Retention"]

  M001 --> MA1B --> MF1E --> MC9D --> MD4F --> ME5F --> MF6A

  style MF1E fill:#e3f2fd
  style MC9D fill:#e3f2fd
  style MD4F fill:#fff9c4
  style ME5F fill:#fff3e0
  style MF6A fill:#eceff1
```

### What Each Phase 12 Migration Introduces

| Revision | ADR | Introduces |
|---|---|---|
| `f1e2d3c4b5a6` | ADR-001 | `CREATE EXTENSION timescaledb` — enables hypertable, compression, CA, and retention APIs |
| `c9d8e7f6a5b4` | ADR-002 | Converts 6 time-series tables to hypertables; composite PKs `(id, time_col)`; chunk intervals per table |
| `d4f5e6a7b8c9` | ADR-003 | Enables columnar compression + 6 `add_compression_policy()` jobs (12-hour schedule) |
| `e5f6a7b8c9d0` | ADR-004 | Creates 8 continuous aggregates `WITH NO DATA` + 8 `add_continuous_aggregate_policy()` jobs (T1–T4) |
| `f6a7b8c9d0e1` | ADR-005 | Registers 11 `add_retention_policy()` jobs (5 raw + 6 CA); exempts `yield_records`, `ca_irrigation_monthly`, `ca_yield_seasonal` |

Prior migrations (`001` through `a1b2c3d4e5f6`) create the standard PostgreSQL domain schema (farms, fields, crops, soil, weather, sensors, irrigation, yield, disease, satellite).

**Detail:** [ADR-001](adr/ADR-001-timescaledb-extension-enablement.md) through [ADR-005](adr/ADR-005-timescaledb-retention-policy-strategy.md).

### Further Reading

| Topic | Document |
|---|---|
| ADR-002 (hypertables) | [ADR-002-hypertable-primary-key-conversion-strategy.md](adr/ADR-002-hypertable-primary-key-conversion-strategy.md) |
| ADR-003 (compression) | [ADR-003-timescaledb-compression-policy-strategy.md](adr/ADR-003-timescaledb-compression-policy-strategy.md) |
| ADR-004 (continuous aggregates) | [ADR-004-timescaledb-continuous-aggregate-strategy.md](adr/ADR-004-timescaledb-continuous-aggregate-strategy.md) |
| ADR-005 (retention) | [ADR-005-timescaledb-retention-policy-strategy.md](adr/ADR-005-timescaledb-retention-policy-strategy.md) |
| Complete architecture | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) |

---

## 6. Canonical Development Dataset (CDD)

### CDD Overview

| Attribute | Value |
|---|---|
| Version | `cdd-v1.0.0` |
| Profile | `cdd-dev` |
| Seed | `42` |
| Temporal window | 2025-06-01 → 2026-05-31 (America/Chicago) |
| Total rows | **458,645** |
| Sensor rows | 438,000 |

CDD provides deterministic, reproducible agricultural data for validation and benchmarking. See [CDD Architecture](report/PHASE12_STEP2CA_CANONICAL_DEVELOPMENT_DATASET_ARCHITECTURE.md).

### Dataset Generation Flow

```mermaid
flowchart TD
    GEN["generate_cdd()<br/>in-memory"]
    VAL["CDDValidator<br/>pre-persistence"]
    PER["persist_cdd_dataset()<br/>bulk_insert_mappings"]
    VER["verify_cdd_persistence()<br/>scoped COUNT queries"]
    STAT["build_statistics()"]

    GEN --> VAL --> PER --> VER --> STAT

    style VAL fill:#fff9c4
    style PER fill:#fff3e0
    style VER fill:#c8e6c9
```

### Canonical Development Dataset Generation (End-to-End)

```mermaid
flowchart TD
    ORC["CDDOrchestrator<br/>profile=cdd-dev seed=42"]
    VAL["CDDValidator<br/>in-memory rules"]
    BULK["bulk_insert_mappings<br/>FK-ordered inserts"]
    CHK["Hypertable chunks<br/>~172 created"]
    CA["Manual CA refresh<br/>8 aggregates"]

    ORC --> VAL --> BULK --> CHK --> CA

    style ORC fill:#e3f2fd
    style CA fill:#fff3e0
```

### Generate and Persist CDD

There is no `make cdd-regenerate` target yet. Run the workflow from Python:

> **📍 `backend/`** (venv active)

```bash
cd backend
python -c "
import asyncio
from app.cdd import execute_cdd_workflow

async def main():
    report = await execute_cdd_workflow(notes='platform bootstrap')
    print(f'success={report.success}')
    if report.statistics:
        s = report.statistics
        print(f'version={s.version} seed={s.seed} rows={s.actual_row_count}')
        print(f'generation_ms={s.generation_duration_ms} persistence_ms={s.persistence_duration_ms}')
    if report.errors:
        for e in report.errors:
            print(f'ERROR: {e}')

asyncio.run(main())
"
```

**Expected outcome:**

```text
success=True
version=cdd-v1.0.0 seed=42 rows=458645
generation_ms=~5000 persistence_ms=~28500
```

#### What this command does

`execute_cdd_workflow` runs the full CDD pipeline: `generate_cdd()` builds 458,645 in-memory records via deterministic UUID v5 and scoped PRNG; `CDDValidator` checks FK integrity and row counts; `persist_cdd_dataset()` writes via `bulk_insert_mappings` in FK order (farms → fields → … → yield) in a single transaction; `verify_cdd_persistence()` compares scoped PostgreSQL counts against generated expectations.

#### Expected Output

`success=True`, `version=cdd-v1.0.0`, `seed=42`, `rows=458645`. Generation ~5 s; persistence ~28 s.

#### Verification

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c "SELECT COUNT(*) FROM sensor_readings;"
```

Expected: `438000`. Full counts in [Section 8](#cdd-row-counts).

#### Troubleshooting

Duplicate key on re-run (wipe DB first), `RETURNING` errors (use `execute_cdd_workflow`, not `add_all`) — see [Step 2C-C](report/PHASE12_STEP2CC_CDD_GENERATION_AND_PERSISTENCE_REPORT.md) and [Section 11](#11-troubleshooting).

| Phase | Duration (measured) | Reference |
|---|---|---|
| Generation | ~5 s | [Step 2C-C](report/PHASE12_STEP2CC_CDD_GENERATION_AND_PERSISTENCE_REPORT.md) |
| Persistence | ~28 s | Step 2C-C |
| Total workflow | ~34 s | Step 2C-C |

**Pre-persistence validation:** 0 errors (1 non-blocking warning on `disease_observations` count 48 vs target 54 is expected).

### Generation Only (No Database Writes)

> **📍 `backend/`** (venv active)

```bash
cd backend
python -c "
from app.cdd import generate_cdd
r = generate_cdd(profile='cdd-dev', seed=42)
print(f'rows={r.dataset.total_row_count} passed={r.validation_report.passed}')
"
```

**Expected output:** `rows=458645 passed=True`

#### What this command does

`generate_cdd()` runs the orchestrator and validator only — no database connection. Use this to confirm determinism and validation rules before persisting, or to inspect row counts without writing data.

#### Expected Output

`rows=458645 passed=True`

#### Verification

Re-run with the same `seed=42`; row count and UUIDs are identical across runs.

#### Troubleshooting

Validation failures block persistence — inspect `report.errors()` output. See [backend/app/cdd/README.md](../backend/app/cdd/README.md).

### Deterministic Regeneration

Identical inputs produce identical UUIDs and values:

- `CDD_VERSION` = `cdd-v1.0.0`
- `CDD_SEED` = `42`
- Profile = `cdd-dev`

Constants are defined in `backend/app/cdd/config.py`. **Always wipe the database** (or truncate all domain tables) before re-seeding to avoid primary-key conflicts.

### Post-CDD: Manual Continuous Aggregate Refresh

CAs are created `WITH NO DATA`. Automatic refresh policies scan only recent windows relative to `now()`. CDD data is predominantly historical — a **one-time full refresh** is required after first seed.

Run each aggregate individually (cannot run inside a transaction):

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
for agg in ca_sensor_hourly ca_sensor_daily ca_weather_daily ca_satellite_daily \
           ca_weather_weekly ca_irrigation_monthly ca_disease_weekly ca_yield_seasonal; do
  echo "CALL refresh_continuous_aggregate('${agg}', NULL, NULL);" | \
    docker compose exec -T db psql -U agriflow -d agriflow
done
```

**Expected outcome:** Each command returns `CALL` with no error. After refresh, all 8 CAs contain materialised buckets.

**Why this is required:** Documented in [Step 3C](report/PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md) — not a defect.

### CDD Verification (SQL)

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT 'sensor_readings' AS tbl, COUNT(*) FROM sensor_readings
   UNION ALL SELECT 'weather_records', COUNT(*) FROM weather_records
   UNION ALL SELECT 'yield_records', COUNT(*) FROM yield_records;"
```

**Expected output:**

| tbl | count |
|---|---|
| sensor_readings | 438000 |
| weather_records | 14600 |
| yield_records | 22 |

Full domain counts: Section 8.

### Further Reading

| Topic | Document |
|---|---|
| CDD generator package | [backend/app/cdd/README.md](../backend/app/cdd/README.md) |
| CDD architecture | [PHASE12_STEP2CA_CANONICAL_DEVELOPMENT_DATASET_ARCHITECTURE.md](report/PHASE12_STEP2CA_CANONICAL_DEVELOPMENT_DATASET_ARCHITECTURE.md) |
| CDD persistence report | [PHASE12_STEP2CC_CDD_GENERATION_AND_PERSISTENCE_REPORT.md](report/PHASE12_STEP2CC_CDD_GENERATION_AND_PERSISTENCE_REPORT.md) |
| CA validation (manual refresh) | [PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md](report/PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md) |

---

## 7. Platform Validation

### Validation Flow

```mermaid
flowchart TD
    A["Alembic head<br/>f6a7b8c9d0e1"]
    H["6 hypertables"]
    C["6 compression policies"]
    CA["8 continuous aggregates"]
    R["11 retention policies"]
    J["27 platform jobs"]
    D["458,645 CDD rows"]
    API["health/live 200"]

    A --> H --> C --> CA --> R --> J
    D --> J
    J --> API

    style API fill:#c8e6c9
```

### Platform Validation Workflow

```mermaid
flowchart TD
    ALE["1. alembic current"]
    HT["2. Hypertables x6"]
    CMP["3. Compression jobs x6"]
    CA["4. CAs x8"]
    RET["5. Retention jobs x11"]
    ROWS["6. CDD row counts"]
    API["7. health/live + ready"]

    ALE --> HT --> CMP --> CA --> RET --> ROWS --> API

    style API fill:#c8e6c9
```

#### What these commands do

Platform validation confirms the full TimescaleDB stack is registered and operational after migrations and CDD load. Queries against `timescaledb_information.*` inspect hypertables, policy jobs, and continuous aggregates. Row-count queries confirm CDD persistence. Health endpoints confirm the FastAPI application can reach PostgreSQL.

#### Expected Output

| Check | Expected |
|---|---|
| Alembic head | `f6a7b8c9d0e1` |
| Hypertables | 6 |
| Compression jobs | 6 |
| Continuous aggregates | 8 |
| Refresh jobs | 8 |
| Retention jobs | 11 |
| Sensor rows | 438,000 |
| API health | HTTP 200 |

#### Verification

Run all commands in this section sequentially. Cross-check with [Section 8](#8-sql-verification-cheat-sheet) for detailed SQL.

#### Troubleshooting

Failed background jobs, empty CAs, wrong counts — see [Section 11](#11-troubleshooting) and runtime validation reports (Steps 2C-D, 3C, 4C).

### Alembic Version

> **📍 `backend/`**

```bash
cd backend && alembic current
```

**Expected:** `f6a7b8c9d0e1 (head)`

### Hypertables (6)

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT hypertable_name, compression_enabled, num_chunks
   FROM timescaledb_information.hypertables
   WHERE hypertable_schema = 'public'
   ORDER BY hypertable_name;"
```

**Expected:** 6 rows; all `compression_enabled = t`; total chunks ≈ **172** after CDD load.

### Compression Policies (6)

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT COUNT(*) FROM timescaledb_information.jobs WHERE proc_name = 'policy_compression';"
```

**Expected:** `6`

### Continuous Aggregates (8)

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT COUNT(*) FROM timescaledb_information.continuous_aggregates;"
```

**Expected:** `8`

### Refresh Policies (8)

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT COUNT(*) FROM timescaledb_information.jobs WHERE proc_name = 'policy_refresh_continuous_aggregate';"
```

**Expected:** `8`

### Retention Policies (11)

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT COUNT(*) FROM timescaledb_information.jobs WHERE proc_name = 'policy_retention';"
```

**Expected:** `11`

**Exemptions verified:**

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT COUNT(*) FROM timescaledb_information.jobs
   WHERE proc_name = 'policy_retention' AND hypertable_name = 'yield_records';"
```

**Expected:** `0`

### Background Jobs (27 platform + 2 system)

> **📍 Repository Root** → **📍 PostgreSQL (psql)**

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT proc_name, COUNT(*) FROM timescaledb_information.jobs GROUP BY proc_name ORDER BY proc_name;"
```

**Expected:**

| proc_name | count |
|---|---|
| policy_compression | 6 |
| policy_job_stat_history_retention | 1 |
| policy_refresh_continuous_aggregate | 8 |
| policy_retention | 11 |
| policy_telemetry | 1 |

**Total:** 27 jobs. All `last_run_status = Success` after first policy cycle (verify via Section 8).

### Application Health

> **📍 Host Machine** (Repository Root — `curl` to localhost)

```bash
curl -s http://localhost:8000/api/v1/health/live
curl -s http://localhost:8000/api/v1/health/ready
```

**Expected:** `alive` (200) and `ready` (200) after DB is reachable.

### Further Reading

| Topic | Document |
|---|---|
| Runtime validation (compression) | [PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md](report/PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md) |
| Runtime validation (CAs) | [PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md](report/PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md) |
| Runtime validation (retention) | [PHASE12_STEP4C_RETENTION_RUNTIME_VALIDATION_REPORT.md](report/PHASE12_STEP4C_RETENTION_RUNTIME_VALIDATION_REPORT.md) |
| Analytical platform handbook | [11-phase12-analytical-platform-handbook.md](11-phase12-analytical-platform-handbook.md) |

---

## 8. SQL Verification Cheat Sheet

Run all queries via:

> **📍 Repository Root** → **📍 PostgreSQL (psql)** (interactive session)

```bash
docker compose exec -T db psql -U agriflow -d agriflow
```

Or pipe single queries with `-c` as shown below.

> **📍 PostgreSQL (psql)** — all `sql` blocks below execute inside the `agriflow` database.

### Infrastructure

```sql
-- TimescaleDB version
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Alembic head
SELECT version_num FROM alembic_version;
```

**Expected:** `2.28.1` and `f6a7b8c9d0e1`

### Hypertables

```sql
SELECT hypertable_name, num_dimensions, compression_enabled,
       primary_dimension, num_chunks
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'public'
ORDER BY hypertable_name;
```

```sql
SELECT hypertable_name, COUNT(*) AS chunk_count
FROM timescaledb_information.chunks
WHERE hypertable_schema = 'public'
GROUP BY hypertable_name
ORDER BY hypertable_name;
```

**Expected:** 6 hypertables; ~172 total chunks after CDD.

### Compression

```sql
SELECT j.job_id, j.hypertable_name, j.scheduled, j.schedule_interval,
       js.last_run_status, js.total_successes
FROM timescaledb_information.jobs j
LEFT JOIN timescaledb_information.job_stats js ON j.job_id = js.job_id
WHERE j.proc_name = 'policy_compression'
ORDER BY j.job_id;
```

```sql
SELECT hypertable_name,
       pg_size_pretty(before_compression_total_bytes) AS before,
       pg_size_pretty(after_compression_total_bytes) AS after,
       round(before_compression_total_bytes::numeric
             / NULLIF(after_compression_total_bytes, 0), 2) AS ratio
FROM timescaledb_information.hypertable_compression_stats
WHERE hypertable_name = 'sensor_readings';
```

**Expected (CDD, post-compression):** sensor ratio ≈ **5.63×**; 79% storage reduction. See [Step 2C-D](report/PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md).

### Continuous Aggregates

```sql
SELECT view_name, materialization_hypertable_name, view_definition IS NOT NULL AS has_def
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;
```

```sql
SELECT 'ca_sensor_hourly' AS agg, COUNT(*), MIN(bucket), MAX(bucket) FROM ca_sensor_hourly
UNION ALL SELECT 'ca_sensor_daily', COUNT(*), MIN(bucket), MAX(bucket) FROM ca_sensor_daily
UNION ALL SELECT 'ca_weather_daily', COUNT(*), MIN(bucket), MAX(bucket) FROM ca_weather_daily
UNION ALL SELECT 'ca_satellite_daily', COUNT(*), MIN(bucket), MAX(bucket) FROM ca_satellite_daily
UNION ALL SELECT 'ca_weather_weekly', COUNT(*), MIN(bucket), MAX(bucket) FROM ca_weather_weekly
UNION ALL SELECT 'ca_irrigation_monthly', COUNT(*), MIN(bucket), MAX(bucket) FROM ca_irrigation_monthly
UNION ALL SELECT 'ca_disease_weekly', COUNT(*), MIN(bucket), MAX(bucket) FROM ca_disease_weekly
UNION ALL SELECT 'ca_yield_seasonal', COUNT(*), MIN(bucket), MAX(bucket) FROM ca_yield_seasonal;
```

**Expected:** All 8 aggregates return rows after manual refresh (Section 6).

### Retention

```sql
SELECT j.job_id, j.hypertable_name, j.config->>'drop_after' AS drop_after,
       j.scheduled, js.last_run_status
FROM timescaledb_information.jobs j
LEFT JOIN timescaledb_information.job_stats js ON j.job_id = js.job_id
WHERE j.proc_name = 'policy_retention'
ORDER BY j.job_id;
```

```sql
-- yield_records exemption
SELECT COUNT(*) FROM timescaledb_information.jobs
WHERE proc_name = 'policy_retention' AND hypertable_name = 'yield_records';
```

**Expected:** 11 retention jobs; 0 for `yield_records`.

### Jobs (All Policies)

```sql
SELECT proc_name, COUNT(*) AS job_count
FROM timescaledb_information.jobs
GROUP BY proc_name
ORDER BY proc_name;
```

```sql
SELECT j.job_id, j.hypertable_name, j.proc_name, js.last_run_status
FROM timescaledb_information.jobs j
LEFT JOIN timescaledb_information.job_stats js ON j.job_id = js.job_id
WHERE j.proc_name IN ('policy_compression', 'policy_refresh_continuous_aggregate', 'policy_retention')
ORDER BY j.proc_name, j.job_id;
```

### Storage

```sql
SELECT hypertable_name,
       pg_size_pretty(hypertable_size(format('%I.%I', hypertable_schema, hypertable_name)::regclass)) AS total_size
FROM timescaledb_information.hypertables
WHERE hypertable_schema = 'public'
ORDER BY hypertable_name;
```

**Expected (CDD, compressed):** Total hypertable storage ≈ **41 MB**.

### CDD Row Counts

```sql
SELECT 'farms' AS domain, COUNT(*) FROM farms
UNION ALL SELECT 'fields', COUNT(*) FROM fields
UNION ALL SELECT 'crops', COUNT(*) FROM crops
UNION ALL SELECT 'weather_records', COUNT(*) FROM weather_records
UNION ALL SELECT 'sensor_readings', COUNT(*) FROM sensor_readings
UNION ALL SELECT 'satellite_observations', COUNT(*) FROM satellite_observations
UNION ALL SELECT 'irrigation_events', COUNT(*) FROM irrigation_events
UNION ALL SELECT 'disease_observations', COUNT(*) FROM disease_observations
UNION ALL SELECT 'yield_records', COUNT(*) FROM yield_records;
```

**Expected totals:**

| Domain | Rows |
|---|---|
| farms | 1 |
| fields | 10 |
| crops | 18 |
| weather_records | 14,600 |
| sensor_readings | 438,000 |
| satellite_observations | 5,840 |
| irrigation_events | 96 |
| disease_observations | 48 |
| yield_records | 22 |
| **Total** | **458,645** |

### Hypertable Time Ranges

```sql
SELECT 'sensor_readings' AS tbl, MIN(recorded_at), MAX(recorded_at), COUNT(*) FROM sensor_readings
UNION ALL SELECT 'weather_records', MIN(recorded_at), MAX(recorded_at), COUNT(*) FROM weather_records
UNION ALL SELECT 'yield_records', MIN(recorded_at), MAX(recorded_at), COUNT(*) FROM yield_records;
```

**Expected:** Data spans 2025-06-01 through 2026-06-01 (UTC-aligned per CDD).

### Further Reading

| Topic | Document |
|---|---|
| Step 2C-D validation SQL | [PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md](report/PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md) |
| Step 4C SQL appendix | [PHASE12_STEP4C_RETENTION_RUNTIME_VALIDATION_REPORT.md](report/PHASE12_STEP4C_RETENTION_RUNTIME_VALIDATION_REPORT.md) |
| Complete architecture | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) |

---

## 9. Backup & Restore

### Operational Lifecycle

```mermaid
flowchart LR
    RUN["Running platform"]
    DUMP["pg_dump backup"]
    STORE["Secure storage<br/>outside repo"]
    WIPE["docker compose down -v"]
    RESTORE["pg_restore"]
    VERIFY["Section 7 validation"]

    RUN --> DUMP --> STORE
    STORE --> RESTORE
    WIPE --> RESTORE --> VERIFY

    style STORE fill:#fff9c4
    style VERIFY fill:#c8e6c9
```

### Backup and Restore Workflow

```mermaid
flowchart TD
    LIVE["Running platform<br/>CDD + policies"]
    DUMP["pg_dump -F c"]
    FILE["agriflow_backup.dump<br/>outside repo"]
    WIPE["docker compose down -v"]
    REST["pg_restore --clean"]
    VAL["Section 7 validation"]

    LIVE --> DUMP --> FILE
    FILE --> REST
    WIPE --> REST --> VAL

    style FILE fill:#fff9c4
    style VAL fill:#c8e6c9
```

### Create Backup

> **📍 Repository Root** (backup file written to current directory) · **📍 Host Machine** (local `pg_dump` variant)

**Custom format (recommended):**

```bash
docker compose exec -T db pg_dump -U agriflow -d agriflow -F c > agriflow_backup.dump
```

**Plain SQL:**

```bash
docker compose exec -T db pg_dump -U agriflow -d agriflow > agriflow_backup.sql
```

**From host (if `pg_dump` installed locally):**

> **📍 Host Machine**

```bash
pg_dump -h localhost -p 25432 -U agriflow -d agriflow -F c -f agriflow_backup.dump
```

**Expected outcome:** Backup file created. Size ≈ 40–50 MB with CDD loaded and compressed.

#### What this command does

`pg_dump` exports a logical snapshot of the `agriflow` database — schema, hypertable metadata, TimescaleDB policies, continuous aggregates, and all row data — into a portable file. Custom format (`-F c`) supports selective restore and compression.

#### Expected Output

File `agriflow_backup.dump` created on disk. No error output from `pg_dump`.

#### Verification

> **📍 Repository Root**

```bash
ls -lh agriflow_backup.dump
```

Non-zero file size (~40–50 MB with CDD).

#### Troubleshooting

Permission denied or connection refused — confirm `db` container is running and credentials match. See [Section 11](#11-troubleshooting).

> **Never commit backup files to Git.** Store outside the repository.

### Restore Backup

**Prerequisite:** Database container running; target database exists (empty or wiped).

> **📍 Repository Root** (stdin redirected into Docker `db` container)

**Custom format restore:**

```bash
docker compose exec -T db pg_restore -U agriflow -d agriflow --clean --if-exists < agriflow_backup.dump
```

**Plain SQL restore:**

```bash
docker compose exec -T db psql -U agriflow -d agriflow < agriflow_backup.sql
```

**Expected outcome:** All tables, hypertables, policies, and data restored.

#### What this command does

`pg_restore` replays the dump into the target database, recreating tables, TimescaleDB extension objects, hypertable chunks, policy jobs, and row data. `--clean --if-exists` drops conflicting objects before restore.

#### Expected Output

Restore completes without `FATAL` errors. Warnings about existing objects may appear with `--clean`.

#### Verification

Run [Verify After Restore](#verify-after-restore) commands below.

#### Troubleshooting

Restore into non-empty database may conflict — prefer wipe (`docker compose down -v`) or use `--clean`. See P12-D003 in [Decision Register](report/PHASE12_DECISION_REGISTER.md).

### Verify After Restore

> **📍 Repository Root** + **📍 Host Machine** (`curl`)

```bash
docker compose exec -T db psql -U agriflow -d agriflow -c "SELECT version_num FROM alembic_version;"
docker compose exec -T db psql -U agriflow -d agriflow -c "SELECT COUNT(*) FROM sensor_readings;"
curl -s http://localhost:8000/api/v1/health/ready
```

**Expected:** Alembic at head; sensor count 438,000; health `ready`.

**Governance:** Pre-migration backups are mandatory per P12-D003. See [Decision Register](report/PHASE12_DECISION_REGISTER.md).

### Further Reading

| Topic | Document |
|---|---|
| Backup protocol | [PHASE12_DECISION_REGISTER.md](report/PHASE12_DECISION_REGISTER.md) — P12-D003 |
| Operational lifecycle | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) §11 |

---

## 10. Complete Platform Rebuild

### Full Rebuild Workflow

Execute these steps in order for a **clean rebuild from empty environment**:

| Step | Command / Action | Expected Outcome |
|---|---|---|
| 1 | Clone repo + create venv + `pip install -r backend/requirements.txt` | Dependencies installed |
| 2 | Configure `backend/.env` and root `.env` | Credentials set; port 25432 on host |
| 3 | `docker compose down -v` | Old volume removed (optional) |
| 4 | `docker compose up -d --build` | `db` healthy, `backend` running |
| 5 | `cd backend && alembic upgrade head` | Head = `f6a7b8c9d0e1` |
| 6 | Run `execute_cdd_workflow` (Section 6) | 458,645 rows persisted |
| 7 | Manual CA refresh loop (Section 6) | 8 CAs materialised |
| 8 | Run Section 7 validation | All counts match |
| 9 | `curl /api/v1/health/live` and `/ready` | HTTP 200 |

```mermaid
flowchart TD
    START(["Empty environment"])
    SETUP["1. Clone + venv + deps"]
    ENV["2. Configure .env"]
    DOWN["3. docker compose down -v"]
    UP["4. docker compose up -d"]
    MIG["5. alembic upgrade head"]
    SEED["6. execute_cdd_workflow"]
    REF["7. refresh_continuous_aggregate x8"]
    VAL["8. SQL + API validation"]
    DONE(["Phase 12 platform ready"])

    START --> SETUP --> ENV --> DOWN --> UP --> MIG --> SEED --> REF --> VAL --> DONE

    style DONE fill:#c8e6c9,stroke:#2e7d32
```

### Complete Platform Bootstrap

```mermaid
flowchart TD
    subgraph setup ["Environment Setup"]
        CLONE["Clone + venv"]
        ENV["Configure .env"]
    end

    subgraph infra ["Infrastructure"]
        DOWN["docker compose down -v"]
        UP["docker compose up -d"]
        MIG["alembic upgrade head"]
    end

    subgraph data ["Data Plane"]
        CDD["execute_cdd_workflow"]
        REF["CA refresh x8"]
    end

    subgraph verify ["Validation"]
        SQL["SQL verification"]
        API["API health checks"]
    end

    CLONE --> ENV --> DOWN --> UP --> MIG --> CDD --> REF --> SQL --> API

    style API fill:#c8e6c9
```

### Estimated Time

| Phase | Duration |
|---|---|
| Docker build + startup | 1–3 min |
| Alembic migrations | < 1 min |
| CDD workflow | ~35 s |
| CA manual refresh | ~30 s |
| Validation | ~2 min |
| **Total** | **~5–10 min** |

### Further Reading

| Topic | Document |
|---|---|
| Complete architecture handbook | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) |
| Bootstrap guide checklist | [Complete Platform Rebuild Checklist](#complete-platform-rebuild-checklist) |

---

## 11. Troubleshooting

This section summarises common Phase 12 issues. Full debugging narratives are in dedicated documents — not duplicated here.

| Symptom | Likely Cause | Resolution | Detail In |
|---|---|---|---|
| `POSTGRES_PASSWORD must be set` on `docker compose up` | Missing root `.env` | Create `.env` at repo root with `POSTGRES_PASSWORD` | Section 2 |
| Alembic connection refused | Wrong port in `backend/.env` | Use `POSTGRES_PORT=25432` from host | Section 2 |
| `extension "timescaledb" does not exist` | Wrong Docker image | Verify `timescale/timescaledb:2.28.1-pg17` in `docker-compose.yml` | [ADR-001](adr/ADR-001-timescaledb-extension-enablement.md) |
| Migration fails on hypertable PK | Pre-Phase-12 schema state | Ensure all domain migrations applied before `c9d8e7f6a5b4` | [ADR-002](adr/ADR-002-hypertable-primary-key-conversion-strategy.md) |
| CDD persistence `RETURNING` error | Composite PK + `add_all()` | Use `execute_cdd_workflow` (uses `bulk_insert_mappings`) | [Step 2C-C](report/PHASE12_STEP2CC_CDD_GENERATION_AND_PERSISTENCE_REPORT.md) |
| CAs empty after migration | `WITH NO DATA` + historical CDD | Run manual `refresh_continuous_aggregate(NULL, NULL)` | [Step 3C](report/PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md) |
| CA refresh policy registration fails | `start_offset` < 2 × bucket width | Fixed in migration v1.3 for `ca_weather_weekly` | [Step 3 Lessons Learned](report/PHASE12_STEP3B_IMPLEMENTATION_LESSONS_LEARNED.md) |
| `COMMENT ON MATERIALIZED VIEW` fails | CAs are `relkind='v'` | Use `COMMENT ON VIEW` in migrations | Step 3 Lessons Learned |
| Compression ratio low at CDD scale | Dev dataset below production volume | Architecture validated; ratio improves at scale | [Step 2C-D](report/PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md) |
| Retention dropped CDD data unexpectedly | Should not happen at CDD age (~395 days) | Verify `drop_after` ≥ 24 months for sensors | [Step 4C](report/PHASE12_STEP4C_RETENTION_RUNTIME_VALIDATION_REPORT.md) |
| Duplicate key on CDD re-run | Existing data in database | Wipe volume or truncate before re-seed | Section 6 |
| `refresh_continuous_aggregate` in transaction error | TimescaleDB restriction | Pipe each `CALL` individually via `psql` | Step 3C |

### Diagnostic Commands

> **📍 Repository Root**

```bash
# Container logs
docker compose logs db --tail 50
docker compose logs backend --tail 50

# Failed background jobs
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT j.job_id, j.proc_name, j.hypertable_name, js.last_run_status, js.last_run_status_detail
   FROM timescaledb_information.jobs j
   JOIN timescaledb_information.job_stats js ON j.job_id = js.job_id
   WHERE js.last_run_status != 'Success';"
```

### Further Reading

| Topic | Document |
|---|---|
| CA implementation lessons | [PHASE12_STEP3B_IMPLEMENTATION_LESSONS_LEARNED.md](report/PHASE12_STEP3B_IMPLEMENTATION_LESSONS_LEARNED.md) |
| ADR-001 (extension) | [ADR-001-timescaledb-extension-enablement.md](adr/ADR-001-timescaledb-extension-enablement.md) |
| ADR-004 (CAs) | [ADR-004-timescaledb-continuous-aggregate-strategy.md](adr/ADR-004-timescaledb-continuous-aggregate-strategy.md) |
| ADR-005 (retention) | [ADR-005-timescaledb-retention-policy-strategy.md](adr/ADR-005-timescaledb-retention-policy-strategy.md) |

---

## Platform Lifecycle

The bootstrap guide supports an iterative engineering workflow. After initial setup, developers repeat subsets of this cycle as the platform evolves.

```mermaid
flowchart TD
    DEV["Developer"]
    CODE["Code Changes"]
    MIG["Database Migration<br/>alembic upgrade head"]
    CDD["CDD Generation<br/>execute_cdd_workflow"]
    REF["CA Refresh<br/>manual or policy"]
    VAL["Platform Validation<br/>SQL + API health"]
    TEST["Testing / Smoke checks"]
    COMMIT["Git Commit"]
    NEXT["Next Phase Development"]

    DEV --> CODE --> MIG
    MIG --> CDD
    MIG --> REF
    CDD --> REF --> VAL --> TEST --> COMMIT --> NEXT
    NEXT --> CODE

    style VAL fill:#e3f2fd
    style NEXT fill:#c8e6c9
```

**How this supports safe iteration:**

- **Migrations first** — schema and TimescaleDB policy changes are version-controlled and reversible in development.
- **CDD re-seed after wipe** — deterministic data restores a known validation corpus without manual test data entry.
- **CA refresh after data changes** — ensures analytical rollups reflect new or regenerated data.
- **Validation before commit** — SQL checks and health endpoints catch policy registration failures, empty aggregates, and connection issues early.
- **Phase 13 builds on this cycle** — Feature Store development adds extraction pipelines atop the validated persistence layer without redesigning storage.

### Further Reading

| Topic | Document |
|---|---|
| Operational lifecycle | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) §11 |
| Complete rebuild checklist | [Complete Platform Rebuild Checklist](#complete-platform-rebuild-checklist) |

---

## 12. Platform Health Checklist

Use this checklist to confirm the platform is fully operational and ready for **Phase 13 — Feature Store**.

### Phase 13 Readiness

```mermaid
flowchart TD
    subgraph infra ["Infrastructure"]
        I1["PostgreSQL 17.10"]
        I2["TimescaleDB 2.28.1"]
        I3["Alembic f6a7b8c9d0e1"]
    end

    subgraph stack ["TimescaleDB Stack"]
        S1["6 hypertables"]
        S2["6 compression policies"]
        S3["8 continuous aggregates"]
        S4["11 retention policies"]
        S5["27 background jobs"]
    end

    subgraph data ["Data Plane"]
        D1["CDD v1.0.0 loaded"]
        D2["458,645 rows"]
        D3["CAs materialised"]
    end

    subgraph app ["Application"]
        A1["API health/live 200"]
        A2["API health/ready 200"]
        A3["0 app-layer changes"]
    end

    infra --> stack --> data --> app --> P13["Phase 13 Feature Store"]

    style P13 fill:#c8e6c9,stroke:#2e7d32
```

### Checklist

| # | Check | Command / Query | Expected |
|---|---|---|---|
| 1 | Docker services healthy | `docker compose ps` | `db` healthy, `backend` up |
| 2 | TimescaleDB active | `SELECT extversion FROM pg_extension WHERE extname='timescaledb'` | `2.28.1` |
| 3 | Alembic at head | `alembic current` | `f6a7b8c9d0e1` |
| 4 | Hypertables | `SELECT COUNT(*) FROM timescaledb_information.hypertables` | `6` |
| 5 | Chunks created | `SELECT SUM(num_chunks) FROM timescaledb_information.hypertables` | `~172` |
| 6 | Compression policies | `jobs WHERE proc_name='policy_compression'` | `6` |
| 7 | Continuous aggregates | `continuous_aggregates` count | `8` |
| 8 | CA refresh policies | `jobs WHERE proc_name='policy_refresh_continuous_aggregate'` | `8` |
| 9 | CAs materialised | `SELECT COUNT(*) FROM ca_sensor_daily` | `> 0` |
| 10 | Retention policies | `jobs WHERE proc_name='policy_retention'` | `11` |
| 11 | `yield_records` exempt | retention jobs on `yield_records` | `0` |
| 12 | Background jobs success | all policy `last_run_status` | `Success` |
| 13 | CDD row count | `SUM` across domains | `458,645` |
| 14 | API liveness | `GET /api/v1/health/live` | `200 alive` |
| 15 | API readiness | `GET /api/v1/health/ready` | `200 ready` |

When all 15 checks pass, the Phase 12 analytical platform is **bootstrap-complete** and ready for Phase 13 development.

### Further Reading

| Topic | Document |
|---|---|
| Complete architecture | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) |
| Phase 13 readiness | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) §12 |

---

## Platform Verification Dashboard

One-page status summary. Replace status indicators after running validation commands.

| Capability | Verification | Expected Status |
|---|---|---|
| Docker | `docker compose ps` — `db` healthy, `backend` up | ✅ Running |
| PostgreSQL | `pg_isready -U agriflow -d agriflow` | ✅ Connected |
| TimescaleDB | `SELECT extversion FROM pg_extension WHERE extname='timescaledb'` | ✅ Extension Loaded (`2.28.1`) |
| Alembic | `alembic current` | ✅ Latest Revision (`f6a7b8c9d0e1`) |
| Hypertables | `SELECT COUNT(*) FROM timescaledb_information.hypertables` | ✅ Present (`6`) |
| Compression | `jobs WHERE proc_name='policy_compression'` | ✅ Enabled (`6` jobs) |
| Continuous Aggregates | `SELECT COUNT(*) FROM timescaledb_information.continuous_aggregates` | ✅ Registered (`8`) |
| Refresh Policies | `jobs WHERE proc_name='policy_refresh_continuous_aggregate'` | ✅ Active (`8` jobs) |
| Retention Policies | `jobs WHERE proc_name='policy_retention'` | ✅ Active (`11` jobs) |
| Canonical Development Dataset | `SELECT COUNT(*) FROM sensor_readings` | ✅ Generated (`438000`) |
| Platform Ready | All checks above + `health/ready` 200 | ✅ Yes |

**Quick verify all:**

> **📍 Repository Root** + **📍 `backend/`**

```bash
docker compose ps && \
cd backend && alembic current && \
docker compose exec -T db psql -U agriflow -d agriflow -c \
  "SELECT (SELECT extversion FROM pg_extension WHERE extname='timescaledb') AS tsdb,
          (SELECT COUNT(*) FROM timescaledb_information.hypertables) AS hypertables,
          (SELECT COUNT(*) FROM timescaledb_information.continuous_aggregates) AS cas,
          (SELECT COUNT(*) FROM sensor_readings) AS sensors;" && \
curl -s http://localhost:8000/api/v1/health/ready
```

---

## Complete Platform Rebuild Checklist

Practical checklist for rebuilding from an empty Docker environment. Check each step before proceeding.

| Step | Action | Status |
|---|---|---|
| Clone repository | `git clone` + `cd AGRIFLOW-AI` | ☐ |
| Create virtual environment | `python3.12 -m venv .venv` + activate | ☐ |
| Install dependencies | `cd backend && pip install -r requirements.txt` | ☐ |
| Configure `backend/.env` | Port `25432`, credentials set | ☐ |
| Configure root `.env` | `POSTGRES_PASSWORD` set | ☐ |
| Start Docker | `docker compose up -d --build` | ☐ |
| Verify PostgreSQL | `pg_isready` returns accepting connections | ☐ |
| Verify TimescaleDB | Extension query returns `2.28.1` (after migrations) | ☐ |
| Run Alembic migrations | `alembic upgrade head` | ☐ |
| Verify Alembic head | `f6a7b8c9d0e1 (head)` | ☐ |
| Generate Canonical Development Dataset | `execute_cdd_workflow` — `success=True` | ☐ |
| Persist dataset | 458,645 rows committed | ☐ |
| Refresh continuous aggregates | Manual `refresh_continuous_aggregate` × 8 | ☐ |
| Verify Hypertables | 6 hypertables, ~172 chunks | ☐ |
| Verify Compression | 6 `policy_compression` jobs | ☐ |
| Verify Continuous Aggregates | 8 CAs with rows | ☐ |
| Verify Retention Policies | 11 `policy_retention` jobs | ☐ |
| Verify Background Jobs | 27 platform jobs, `Success` status | ☐ |
| Execute validation SQL | [Section 8](#8-sql-verification-cheat-sheet) row counts | ☐ |
| Verify API health | `health/live` and `health/ready` → 200 | ☐ |
| Platform ready for Phase 13 | All checks pass | ☐ |

---

## Next Steps

After successfully completing bootstrap and passing the [Platform Health Checklist](#12-platform-health-checklist), proceed as follows.

### Read

| Document | Why |
|---|---|
| [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) | Definitive Phase 12 architecture — single entry point |
| [10-phase12-step1-foundation-handbook.md](10-phase12-step1-foundation-handbook.md) | Hypertable foundation, principles, and runtime behaviour |
| [11-phase12-analytical-platform-handbook.md](11-phase12-analytical-platform-handbook.md) | Continuous aggregates, refresh tiers, and analytical queries |

### Understand

| ADR | Topic |
|---|---|
| [ADR-001](adr/ADR-001-timescaledb-extension-enablement.md) | TimescaleDB extension enablement |
| [ADR-002](adr/ADR-002-hypertable-primary-key-conversion-strategy.md) | Hypertable conversion and composite PKs |
| [ADR-003](adr/ADR-003-timescaledb-compression-policy-strategy.md) | Compression policies |
| [ADR-004](adr/ADR-004-timescaledb-continuous-aggregate-strategy.md) | Continuous aggregate catalogue and refresh tiers |
| [ADR-005](adr/ADR-005-timescaledb-retention-policy-strategy.md) | Retention lifecycle and exemptions |

### Use During Development

| Resource | Location in this guide |
|---|---|
| SQL Verification Cheat Sheet | [Section 8](#8-sql-verification-cheat-sheet) |
| Platform Validation commands | [Section 7](#7-platform-validation) |
| Daily Developer Commands | [Daily Developer Commands](#daily-developer-commands) |
| Troubleshooting | [Section 11](#11-troubleshooting) |
| CDD regeneration | [Section 6](#6-canonical-development-dataset-cdd) |

### Continue With — Phase 13: AI Feature Store

Phase 12 delivers the **persistence and analytical infrastructure**. Phase 13 introduces the **AI Feature Store** — versioned feature vectors materialised from continuous aggregates (`ca_sensor_daily`, `ca_weather_daily`, `ca_satellite_daily`, etc.). No redesign of the TimescaleDB layer is required.

The completed platform provides:

- Bounded-cardinality CA reads for feature extraction
- Raw hypertable detail for audit and fine-grain replay
- Retention-governed lifecycle preserving multi-season summaries
- Zero application-layer changes — Feature Store adds new read paths, not storage replacements

Begin Phase 13 by reading the Complete Architecture Handbook [§12 AI Readiness](12-phase12-complete-architecture-handbook.md) and the Analytical Platform Handbook [§8 AI Readiness](11-phase12-analytical-platform-handbook.md).

---

## Further Reading

| Topic | Document |
|---|---|
| Complete Phase 12 architecture | [12-phase12-complete-architecture-handbook.md](12-phase12-complete-architecture-handbook.md) |
| Foundation (hypertables) | [10-phase12-step1-foundation-handbook.md](10-phase12-step1-foundation-handbook.md) |
| Analytical layer (CAs) | [11-phase12-analytical-platform-handbook.md](11-phase12-analytical-platform-handbook.md) |
| CDD generator package | [backend/app/cdd/README.md](../backend/app/cdd/README.md) |
| CDD architecture | [PHASE12_STEP2CA_CANONICAL_DEVELOPMENT_DATASET_ARCHITECTURE.md](report/PHASE12_STEP2CA_CANONICAL_DEVELOPMENT_DATASET_ARCHITECTURE.md) |
| CA implementation lessons | [PHASE12_STEP3B_IMPLEMENTATION_LESSONS_LEARNED.md](report/PHASE12_STEP3B_IMPLEMENTATION_LESSONS_LEARNED.md) |
| Runtime validation (compression) | [PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md](report/PHASE12_STEP2CD_RUNTIME_VALIDATION_AND_BENCHMARK_REPORT.md) |
| Runtime validation (CAs) | [PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md](report/PHASE12_STEP3C_CONTINUOUS_AGGREGATE_VALIDATION_REPORT.md) |
| Runtime validation (retention) | [PHASE12_STEP4C_RETENTION_RUNTIME_VALIDATION_REPORT.md](report/PHASE12_STEP4C_RETENTION_RUNTIME_VALIDATION_REPORT.md) |

---

*13-phase12-platform-bootstrap-guide.md v1.2 — 2026-06-30*
