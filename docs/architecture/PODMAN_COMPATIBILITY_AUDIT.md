# AGRIFLOW-AI — Podman Compatibility Audit

| Field | Value |
|---|---|
| **Document type** | Discovery / compatibility analysis |
| **Scope** | Local development container stack (`docker-compose.yml`) |
| **Target runtime** | Podman / Podman Compose on Windows 11 |
| **Repository changes in this audit** | Report only — no compose, Dockerfile, application, migration, or `.env` modifications |
| **Canonical compose file** | `docker-compose.yml` (repository root) |
| **Date** | 2026-08-16 |
| **See also** | [Final validation](./PODMAN_FINAL_VALIDATION_REPORT.md) · [Archive troubleshooting](../archive/podman/README.md) · [Local setup](../reference/05-local-setup.md) |

---

## 1. Executive Summary

AGRIFLOW-AI’s local stack is a standard two-service Compose Spec workload: TimescaleDB (`db`) and a multi-stage FastAPI image (`backend`) with a named volume, bind-mounted source for `uvicorn --reload`, healthcheck-gated `depends_on`, and service-name DNS (`POSTGRES_HOST=db`).

**Verdict:** The application architecture does not need to change for Podman. The existing `docker-compose.yml` and `backend/Dockerfile` are OCI/Compose-compatible and should be usable **without a second compose file**, provided the host uses a capable Compose provider and a running Podman machine.

**Final recommendation:** **B. Minor compatibility changes required** — host/runtime configuration and optional developer-experience tweaks only; not a redesign and not a separate Podman compose file.

Key caveats (documented in detail below):

1. On Windows 11, Podman runs containers inside a Linux VM (Podman Machine). Bind-mount live reload is **not guaranteed** without polling (`WATCHFILES_FORCE_POLLING`) — same class of issue as Docker Desktop / WSL2.
2. `podman compose` is a thin wrapper around an external provider (`docker-compose` preferred; `podman-compose` historically weaker for `condition: service_healthy`).
3. A **pre-existing** Docker Compose operational issue remains: if `backend/.env` sets `POSTGRES_PORT=25432` (host publish port), in-container connections to `db:25432` fail. Compose already overrides `POSTGRES_HOST=db` but not `POSTGRES_PORT`. This affects Docker and Podman equally.
4. Root `.env` with `POSTGRES_PASSWORD` is required by `${POSTGRES_PASSWORD:?…}` interpolation — documented in bootstrap guides; there is **no** committed root `.env.example`.

Items that could not be proven from the repository alone are marked **Requires runtime verification**.

---

## 2. Current Container Architecture

### 2.1 Discovery inventory

| Artifact | Present? | Path / notes |
|---|---|---|
| Canonical compose | Yes | `docker-compose.yml` |
| `compose.yaml` / `compose.yml` | No | — |
| Backend Dockerfile | Yes | `backend/Dockerfile` (multi-stage: `builder` → `runtime`) |
| `.dockerignore` | Yes | `backend/.dockerignore` |
| Root `.env.example` | No | Root `.env` is operationally required for compose interpolation |
| Backend env example | Yes | `backend/.env.example` |
| Alembic | Yes | `backend/alembic.ini`, `backend/app/db/migrations/` |
| TimescaleDB references | Yes | Compose image pin; Alembic Phase 12 migrations; ADRs under `docs/adr/` |
| Docker/Compose scripts | No | No `scripts/` directory found |
| Makefile / task runner | No | — |
| CI/CD container config | No | No `.github/` workflows found |
| Docker documentation | Yes | `README.md`, `docs/05-local-setup.md`, `docs/13-phase12-platform-bootstrap-guide.md`, Phase 12 reports |
| Hard-coded Docker CLI in app code | No | CLI references are documentation / comments only |
| Docker socket usage | No | No `/var/run/docker.sock`, Docker SDK, or DinD patterns in `backend/app/` |
| Docker-specific app assumptions | Minimal | Settings comment mentions “Docker secrets”; connection uses env vars only |

### 2.2 Runtime topology (unchanged intent)

```text
┌─────────────────────────────────────────────────────────────┐
│ Compose project (service DNS network)                       │
│                                                             │
│  ┌──────────────────────┐    POSTGRES_HOST=db               │
│  │ backend              │ ───────────────────────────────►  │
│  │ build: runtime       │    port 5432 (container)          │
│  │ uvicorn --reload     │                                   │
│  │ ./backend → /app     │                                   │
│  │ host:8000 → 8000     │                                   │
│  └──────────▲───────────┘                                   │
│             │ depends_on: service_healthy                   │
│  ┌──────────┴───────────┐                                   │
│  │ db                   │                                   │
│  │ timescale/…:2.28.1   │                                   │
│  │ volume: postgres_data│                                   │
│  │ host:25432 → 5432    │                                   │
│  │ healthcheck: pg_isready                                  │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Services (from `docker-compose.yml`)

| Service | Image / build | Ports | Volumes | Notable config |
|---|---|---|---|---|
| `db` | `timescale/timescaledb:2.28.1-pg17` | `25432:5432` | named `postgres_data` → `/var/lib/postgresql/data` | `restart: unless-stopped`; env from root compose interpolation; `pg_isready` healthcheck |
| `backend` | build `./backend` Dockerfile target `runtime` | `8000:8000` | bind `./backend:/app` | `env_file: ./backend/.env`; overrides `POSTGRES_HOST=db`; `uvicorn --reload`; waits for healthy `db` |

### 2.4 Application connectivity model

- Settings assemble DSN as `postgresql+asyncpg://{user}:{password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{db}` (`backend/app/core/config/settings.py`).
- Compose intentionally overrides host to service name `db`.
- Container-internal PostgreSQL port remains **5432**; host publish port is **25432**.

---

## 3. Docker Compose Directive Compatibility Matrix

Classification key:

| Class | Meaning |
|---|---|
| **SUPPORTED** | Standard Compose Spec / Podman-supported feature |
| **LIKELY SUPPORTED** | Expected to work; confirm with installed provider/version |
| **POTENTIALLY PROBLEMATIC** | Works in many setups but has known failure modes |
| **DOCKER-SPECIFIC** | Tied to Docker Engine/Desktop semantics |
| **UNKNOWN** | Cannot be asserted from repo alone |

| Directive / concern | Location | Classification | Notes |
|---|---|---|---|
| `services` | root | SUPPORTED | Compose Spec core |
| `image` | `db` | SUPPORTED | Pull from Docker Hub via Podman (`docker.io/…`) |
| `build` | `backend` | SUPPORTED | Podman builds OCI images |
| `build.context` | `./backend` | SUPPORTED | Relative context |
| `build.dockerfile` | `Dockerfile` | SUPPORTED | |
| `build.target` | `runtime` | SUPPORTED | Multi-stage target selection |
| `restart: unless-stopped` | both | LIKELY SUPPORTED | Semantics depend on Podman restart policy + machine lifecycle; **Requires runtime verification** on Windows Podman Machine stop/start |
| `environment` | both | SUPPORTED | |
| `env_file` | `backend` | SUPPORTED | Path `./backend/.env` |
| `ports` (`25432:5432`, `8000:8000`) | both | SUPPORTED | Host publish via Podman Machine port forwarding — **Requires runtime verification** that ports are free (Docker Desktop / Rancher may already bind them) |
| named volume `postgres_data` | volumes | SUPPORTED | `driver: local` |
| bind mount `./backend:/app` | `backend` | POTENTIALLY PROBLEMATIC | Windows path → VM mount; performance + inotify (see §10) |
| `healthcheck` + `CMD-SHELL` | `db` | SUPPORTED | Podman supports container healthchecks |
| `depends_on` + `condition: service_healthy` | `backend` | POTENTIALLY PROBLEMATIC | Fully reliable with Docker Compose V2; historically buggy / version-gated in `podman-compose`; better when `podman compose` uses `docker-compose` provider (see §8) |
| `command` (uvicorn multiline) | `backend` | SUPPORTED | Overrides Dockerfile `CMD` |
| Service-name DNS (`db`) | network | SUPPORTED | Compose project network DNS |
| `${VAR:-default}` | `db` env/healthcheck | SUPPORTED | Compose interpolation |
| `${VAR:?error}` | `POSTGRES_PASSWORD` | SUPPORTED | Fails fast if root `.env` missing — same as Docker |
| Windows path handling | bind mount | POTENTIALLY PROBLEMATIC | Relative `./backend` usually translated by Podman Desktop/CLI; absolute Windows paths can surprise — **Requires runtime verification** |
| `version:` key | n/a | N/A | Not present (Compose Spec modern style) — good for both engines |
| Docker socket / privileged | n/a | DOCKER-SPECIFIC | **Not used** by this stack |
| Swarm / stack deploy | n/a | DOCKER-SPECIFIC | **Not used** |

### Potentially problematic items — why

1. **`depends_on.condition: service_healthy`** — Depends on Compose provider implementation. Docker Compose V2 enforces it. `podman compose` delegates to whichever provider is installed (`docker-compose` preferred over `podman-compose` per Podman docs). Older/buggy `podman-compose` releases started dependents early or hung on `podman wait --condition=healthy` (issues/PRs in containers/podman-compose; Podman ≥ 4.6 required for healthy wait).
2. **Bind mount `./backend:/app` on Windows** — Crosses Windows ↔ Podman Machine filesystem boundary; file watchers may miss events; I/O slower than native Linux.
3. **Port publishing with multiple runtimes installed** — Docker Desktop, Rancher Desktop, and Podman Machine competing for `8000` / `25432` is an environmental conflict, not a compose syntax problem.
4. **`restart: unless-stopped` across VM reboots** — Behavior after Podman Machine stop is **Requires runtime verification**.

---

## 4. Dockerfile Compatibility

**File:** `backend/Dockerfile`

| Aspect | Finding | Podman impact |
|---|---|---|
| Base image | `python:3.12-slim` | Standard OCI; Podman pulls from Docker Hub |
| Multi-stage | `builder` → `runtime` | Supported |
| Build target `runtime` | Used by compose | Supported (`podman build --target runtime`) |
| `RUN` apt/pip/venv | Debian packages + venv | No Docker-specific APIs |
| `COPY` / `COPY --from=builder` | Standard | Supported |
| `COPY --chown=appuser:appgroup` | Ownership at build | Supported in Podman builds |
| `USER appuser` (uid/gid 1000) | Non-root runtime | Compatible; bind-mounted host files may not be owned by 1000 — usually fine for read/execute of source; write-backs to host may create permission quirks — **Requires runtime verification** |
| `EXPOSE 8000` | Metadata | Supported |
| `CMD` (not `ENTRYPOINT`) | Allows `compose run … alembic` | Desired; works with Podman Compose `run` |
| Architecture assumptions | Implicit linux/amd64 or arm64 of base | Windows hosts use Podman Machine arch (typically amd64 on Intel/AMD PCs) — **Requires runtime verification** on ARM Windows if applicable |
| Shell assumptions | `/bin/bash` for `useradd`; build uses default shell | Linux container; independent of Windows host shell |

**Conclusion:** Podman can build this image **unchanged**. No Docker BuildKit-only syntax, no `RUN --mount=type=cache` BuildKit mounts, no Docker socket in build.

---

## 5. TimescaleDB Image Compatibility

**Image:** `timescale/timescaledb:2.28.1-pg17`

| Check | Status |
|---|---|
| OCI compatibility | **Likely yes** — published as a standard container image on Docker Hub; Podman consumes OCI/Docker images |
| Architecture | Docker Hub lists multi-arch digests for this tag family (including `linux/amd64`; other arches present in tag metadata). Exact digest pulled on the audit machine: **Requires runtime verification** (`podman pull` / `podman image inspect`) |
| PostgreSQL 17 | Yes — tag suffix `-pg17` matches project Phase 12 baseline |
| TimescaleDB 2.28.1 | Yes — pin matches ADRs / bootstrap docs |
| Known Podman-specific image bugs | No repository evidence of Podman-exclusive TimescaleDB failures; none assumed |
| Rootless vs rootful | PostgreSQL images traditionally expect writable data dir with specific UIDs. Named volumes under rootful Podman Machine (typical Desktop default) usually behave like Docker. **Rootless-on-Windows-host** is atypical for Desktop Machine workflows; if someone runs fully rootless Linux Podman against this compose, volume UID mapping is **Requires runtime verification** |

**Do not change the image** (audit constraint). External verification steps are listed in §15.

---

## 6. Windows 11 Considerations

| Topic | Analysis |
|---|---|
| Podman Machine | On Windows, containers run in a Linux VM/WSL-based machine. Compose commands from PowerShell talk to that engine. |
| Coexistence | Docker Desktop + Rancher Desktop + Podman all installed → risk of port conflicts, different compose contexts, and “which engine am I talking to?” confusion. |
| Path translation | Relative bind `./backend:/app` from repo on `C:\…` is normally mapped into the machine; prefer launching compose from the repo root. |
| Line endings | Bind-mounted `.py` / `.env` with CRLF rarely break Python; shell scripts (none mounted as entrypoints here) are more sensitive. Healthcheck uses image-local `pg_isready`, not host scripts. |
| Permissions | Non-root `appuser` + Windows-origin files: usually readable; creating files from container onto the bind mount may yield unexpected ACLs — **Requires runtime verification** if the app writes into `/app`. |
| Resource usage | Podman’s lower overhead claim vs Docker Desktop is environmental, not architectural — **Requires runtime verification** on this machine. |

---

## 7. Networking Analysis

### 7.1 `POSTGRES_HOST=db`

| Question | Answer |
|---|---|
| Will `db` resolve inside the backend container? | **Yes, under Compose networking** — service names are DNS names on the project network for both Docker Compose and Podman Compose (when using a compliant provider). |
| Is this Docker-specific? | No — Compose Spec service discovery. |

**Requires runtime verification:** `podman compose exec backend getent hosts db` (or equivalent) and a successful DB connection.

### 7.2 Published ports

| Mapping | Compatibility | Notes |
|---|---|---|
| `25432:5432` | SUPPORTED | Host tools / local uvicorn outside compose use `localhost:25432` |
| `8000:8000` | SUPPORTED | FastAPI / OpenAPI on host |

Conflicts if another runtime already binds those ports: **Requires runtime verification**.

### 7.3 Pre-existing port semantics (Docker and Podman)

Compose sets `POSTGRES_HOST=db` but does **not** set `POSTGRES_PORT=5432`.

- `backend/.env.example` defaults `POSTGRES_PORT=5432` (correct for in-container).
- Documented host access often uses `localhost:25432`.
- Phase 12 Step 1C report recorded a real failure mode: `backend/.env` with `POSTGRES_PORT=25432` causes in-container `db:25432` connection failures.

This is **not introduced by Podman**; it remains an operational correctness requirement for any Compose runtime.

---

## 8. Healthcheck Analysis

### 8.1 Configured healthcheck

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-agriflow} -d ${POSTGRES_DB:-agriflow}"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

| Aspect | Assessment |
|---|---|
| `CMD-SHELL` + `pg_isready` | Standard; available in TimescaleDB/Postgres images |
| Variable interpolation in healthcheck | Compose interpolates before send; **LIKELY SUPPORTED** — **Requires runtime verification** that the resolved command matches intended user/db |
| Podman health state | Podman tracks healthy/unhealthy similarly to Docker |

### 8.2 `depends_on` condition

```yaml
depends_on:
  db:
    condition: service_healthy
```

| Implementation | Behavior |
|---|---|
| **Docker Compose V2** | Waits until healthcheck reports healthy before starting `backend` |
| **`podman compose` + `docker-compose` provider** | Preferred path per Podman documentation (docker-compose takes precedence if installed); expected to honor Compose Spec conditions — **Requires runtime verification** |
| **`podman-compose` (Python project)** | Conditional dependency support added/fixed over time; historical bugs where `service_healthy` was not enforced or `podman wait --condition=healthy` hung on Podman &lt; 4.6; later regressions reported — treat as **POTENTIALLY PROBLEMATIC** until version-proven |

**Operational guidance (no file changes in this audit):** Prefer configuring Podman to use the Docker Compose CLI as the compose provider, or verify `podman-compose` version explicitly before relying on healthy startup ordering.

---

## 9. Volume Analysis

| Volume | Type | Compatibility | Notes |
|---|---|---|---|
| `postgres_data` | Named, `driver: local` | SUPPORTED | Persists across `compose down` (without `-v`) |
| Lifecycle | `compose down -v` | Destructive | Same semantics as Docker; wipe only when intentional |
| Cross-engine sharing | Docker volume ≠ Podman volume | **Important** | Switching from Docker Desktop to Podman does **not** automatically reuse Docker’s `postgres_data`. Data migration requires dump/restore. Architecture unchanged; storage identity is runtime-local. |

---

## 10. Bind Mount / Live Reload Analysis

| Item | Detail |
|---|---|
| Mount | `./backend:/app` |
| Process | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` |
| Dependency | `uvicorn[standard]==0.32.1` → includes WatchFiles |

### Expected reliability on Windows 11 + Podman

| Scenario | Expectation |
|---|---|
| Native Linux Podman | Live reload usually reliable via inotify |
| Windows Podman Machine | **Unreliable without polling** — filesystem events often do not cross the VM/bind boundary (same class of issue as Docker Desktop / WSL bind mounts) |
| Mitigation (optional, not implemented here) | Set `WATCHFILES_FORCE_POLLING` in the backend environment (any non-empty value per WatchFiles docs) |

**Conclusion:** Live reload is **not guaranteed** out of the box on Windows Podman. It may work depending on mount technology and WatchFiles behavior, but teams should plan for polling if reload is required. This does **not** change application architecture; it is a developer-experience runtime concern.

**Requires runtime verification:** Edit a Python file under `backend/app/` and confirm uvicorn worker reload in logs.

---

## 11. Alembic Migration Analysis

### Documented Docker command

```bash
docker compose run --rm backend alembic upgrade head
```

### Podman equivalent

```bash
podman compose run --rm backend alembic upgrade head
```

| Aspect | Analysis |
|---|---|
| Override of `CMD` | Supported — Dockerfile intentionally uses `CMD` not `ENTRYPOINT` |
| `--rm` | Supported by Compose `run` |
| Network / DNS | One-off container should join project network and resolve `db` — **Requires runtime verification** |
| Env | Same `env_file` + `POSTGRES_HOST=db` overrides as the long-running service — **Requires runtime verification** of provider parity |
| Differences vs Docker | CLI binary name / compose provider; possible slight differences in how `run` attaches networks or inherits `depends_on` (some providers do not wait for healthy on `run`) — **Requires runtime verification** |
| Pre-existing port pitfall | If `POSTGRES_PORT=25432` in `backend/.env`, Alembic inside the container fails against `db` — same as Docker |

Migrations themselves are SQL/Alembic artifacts and are runtime-agnostic.

---

## 12. Docker vs Podman Differences

| Dimension | Docker Desktop (current docs) | Podman on Windows 11 | Impact on AGRIFLOW-AI architecture |
|---|---|---|---|
| Engine | Docker Engine in VM/WSL | Podman in Podman Machine | None |
| Compose CLI | `docker compose` | `podman compose` → external provider | Docs/commands only |
| Images | Docker Hub | Same registries (often need `docker.io/` prefix implicitly handled) | None |
| Networking | Compose project network | Equivalent Compose network | None if DNS works |
| Named volumes | Docker volume store | Podman volume store | Data not shared across engines |
| Rootless story | Usually rootful VM | Machine often rootful; true rootless more Linux-native | Ops only |
| Socket / API | Docker API | Podman API (Docker-compatible subset) | Irrelevant — app does not use socket |
| SELinux labels | Rarely on Windows | N/A on Windows Machine guest in typical use | None |
| Application code | — | — | **Unchanged** |

**Preferred outcome (achieved conceptually):** Application architecture remains unchanged; only the local container runtime changes.

---

## 13. Required Changes, If Any

### Must not change for Podman (and not changed by this audit)

- Application domain architecture
- Alembic migrations
- TimescaleDB image pin
- Service topology (`db` + `backend`)
- Second compose file (not recommended)

### Host / operational requirements (not repository redesign)

1. Running **Podman Machine** (Windows).
2. Root **`.env`** with `POSTGRES_PASSWORD` (and optional `POSTGRES_DB` / `POSTGRES_USER`).
3. **`backend/.env`** with `POSTGRES_PORT=5432` for in-container use (or otherwise ensure container port, not host publish port).
4. Confirm Compose provider: prefer **`docker-compose`** as the provider behind `podman compose`, or a `podman-compose` version proven to enforce `service_healthy`.
5. Ensure ports **8000** and **25432** are free of Docker Desktop / Rancher listeners if switching runtimes.

### Optional compatibility tweaks (only if runtime validation fails)

| Change | When | Nature |
|---|---|---|
| Add `WATCHFILES_FORCE_POLLING=true` to `backend.environment` | Live reload misses file edits on Windows | Minor compose env addition — same compose file, not a fork |
| Add `POSTGRES_PORT: "5432"` under `backend.environment` | `backend/.env` uses host port 25432 | Fixes pre-existing Docker/Podman connectivity bug; architecture unchanged |
| Document Podman command aliases in docs | Onboarding | Documentation only |

None of these require a separate Podman compose file or application redesign.

---

## 14. Recommended Architecture

**Keep the current architecture.**

```text
Runtime choice (host):
  Docker Desktop  ─┐
  Podman Machine  ─┼─► same docker-compose.yml ─► db + backend
  Rancher (optional)┘
```

- **Single** `docker-compose.yml` remains canonical.
- Backend continues to talk to PostgreSQL via Compose DNS name `db`.
- Persistence remains named volume `postgres_data` (per runtime).
- Production path (Azure Container Apps / AKS) is unaffected; Dockerfile non-root user remains valid.

Do not introduce application-level abstractions merely to accommodate Podman.

---

## 15. Validation / Test Plan

**Do not execute destructive commands** (`compose down -v`, volume wipes) unless explicitly approved. Prefer read-only / additive checks first.

| # | Step | Suggested command / check | Pass criteria |
|---|---|---|---|
| 1 | Verify Podman version | `podman version` | Client/server versions reported; machine reachable |
| 2 | Verify Compose provider | `podman compose version` / inspect `PODMAN_COMPOSE_PROVIDER` / `containers.conf` | Provider identified (`docker-compose` preferred) |
| 3 | Verify Podman machine | `podman machine list` (or Podman Desktop UI) | Machine **Running** |
| 4 | Validate compose config | `podman compose config` from repo root | Resolves without `POSTGRES_PASSWORD` error; shows image + services |
| 5 | Build backend | `podman compose build backend` | Image builds target `runtime` successfully |
| 6 | Pull TimescaleDB | `podman pull docker.io/timescale/timescaledb:2.28.1-pg17` | Pull succeeds; inspect arch matches machine |
| 7 | Start db only | `podman compose up -d db` | Container running |
| 8 | Verify healthcheck | `podman compose ps` / `podman inspect` Health | Status **healthy** |
| 9 | Start backend | `podman compose up -d backend` | Starts after healthy db (confirm ordering) |
| 10 | Resolve `db` | Exec into backend; DNS lookup / TCP to `db:5432` | Resolves and connects |
| 11 | Alembic | `podman compose run --rm backend alembic upgrade head` | Migrations apply (or already at head) |
| 12 | PostgreSQL / TimescaleDB | `podman compose exec db psql …` extension/version queries | PG17 + timescaledb available/installed per project stage |
| 13 | FastAPI | `curl http://localhost:8000/docs` or health endpoints | HTTP success |
| 14 | Uvicorn reload | Edit a `.py` file; watch logs | Reload observed **or** document need for polling |
| 15 | Stop stack | `podman compose stop` | Containers stopped; volume retained |
| 16 | Restart stack | `podman compose start` or `up -d` | Services return |
| 17 | Persistent volume | Query data / `\dt` after restart | Data retained without `-v` |

Optional: compare resource usage vs Docker Desktop (CPU/RAM) — environmental, not architectural.

---

## 16. Risks and Limitations

| Risk | Severity | Mitigation |
|---|---|---|
| Compose provider does not honor `service_healthy` | Medium | Use docker-compose provider; verify versions; backend may retry DB anyway but startup race remains |
| Live reload flaky on Windows mounts | Medium | `WATCHFILES_FORCE_POLLING`; or run API on host against published `25432` |
| Port conflict with Docker/Rancher | Medium | Stop other stacks or remap ports (remap = compose change — avoid unless necessary) |
| Volume data not shared across engines | Medium | `pg_dump` / `pg_restore` when switching runtimes |
| `POSTGRES_PORT` host/container mismatch | High (if misconfigured) | Keep `5432` in container env; use `25432` only on host clients |
| Rootless UID mapping (non-Desktop setups) | Low–Medium | Prefer Podman Machine defaults used by Podman Desktop |
| Documentation still says `docker compose` | Low | Docs drift only; runtime can still be Podman |
| Healthcheck interpolation edge cases | Low | Runtime `podman compose config` inspection |

**Unknowns requiring runtime verification** are called out throughout this report and must not be treated as proven facts.

---

## 17. Final Recommendation

### **B. Minor compatibility changes required**

**Interpretation:**

- **No** separate Podman compose file.
- **No** application architecture changes.
- **No** TimescaleDB image change.
- Existing `docker-compose.yml` and `backend/Dockerfile` are expected to run under Podman with Compose Spec support.
- “Minor” items are **host/runtime configuration** and **optional** env tweaks if validation exposes Windows reload or pre-existing `POSTGRES_PORT` issues.

### Why not A?

Pure “no changes” would understate Windows bind-mount reload risk and Compose-provider variance for `service_healthy`, both of which can require small operational or env adjustments.

### Why not C or D?

The stack does not need a Podman-specific architecture or fork. It is not unsuitable for Podman: there is no Docker socket dependency, no Swarm-only feature, and no non-OCI build requirement.

### Success criteria for adopting Podman locally

1. Same services, same image pin, same ports, same volume intent.
2. Backend resolves and connects to `db:5432`.
3. Alembic `upgrade head` works via `podman compose run`.
4. FastAPI serves on `localhost:8000`.
5. Reload either works or is consciously enabled via polling — without redesigning the app.

---

## Appendix A — Repository discovery summary

| Category | Result |
|---|---|
| Compose files | Only `docker-compose.yml` |
| Dockerfiles | Only `backend/Dockerfile` |
| Ignore files | `backend/.dockerignore` |
| Env examples | `backend/.env.example` only (no root `.env.example`) |
| CI container jobs | None found |
| Makefiles / scripts | None found |
| Docker socket in app | None |
| Hard-coded Docker CLI | Documentation and comments only |

## Appendix B — Sources consulted (non-repo)

- Podman `podman-compose` man page: `podman compose` wraps external providers; `docker-compose` preferred when installed.
- containers/podman-compose issues/PRs regarding `service_healthy` enforcement and Podman ≥ 4.6 `wait --condition=healthy`.
- Docker Hub tag metadata for `timescale/timescaledb:2.28.1-pg17` (multi-arch listings).
- Uvicorn / WatchFiles guidance: `WATCHFILES_FORCE_POLLING` for WSL/VM bind mounts.
- Internal project evidence: `docs/report/PHASE12_STEP1C_IMPLEMENTATION_REPORT.md` (`POSTGRES_PORT=25432` in-container failure).

---

*End of audit. This document is the only artifact produced for this discovery task.*
