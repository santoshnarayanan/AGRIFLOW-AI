# AGRIFLOW-AI — Podman Runtime Validation Report

| Field | Value |
|---|---|
| **Document type** | Runtime validation (execute existing stack under Podman) |
| **Date** | 2026-08-16 |
| **Host** | Windows 11 (`win32 10.0.26200`), PowerShell |
| **Canonical compose** | `docker-compose.yml` (unchanged) |
| **Repository changes** | **This report only** — no compose, Dockerfile, application, migration, or `.env` modifications |
| **Destructive actions** | None (`down -v`, volume rm, DB reset, migration downgrade not used) |

---

## Final classification

**B. Minor runtime/configuration change required**

The existing `docker-compose.yml` is Compose-valid under Podman and does **not** require a Podman-specific compose file. Full stack bring-up was **blocked on this machine** by Podman bridge networking (`netavark` + `nftables`), and a **pre-existing env mistake** (`POSTGRES_PORT=25432` in `backend/.env`) would block in-container DB connectivity even after networking is fixed.

---

## 1. Environment

| Item | Result |
|---|---|
| OS | Windows 11 (host); Podman Machine guest = Linux (WSL2) |
| Architecture | Host client `windows/amd64`; server `linux/amd64` |
| Podman Desktop | Running (multiple `Podman Desktop` processes observed) |
| Docker Desktop CLI present | Yes (`docker.exe` 29.6.1; `docker-compose.exe` under Docker resources) |
| Rancher Desktop | WSL distros present but **Stopped**; `docker-compose` also present under Rancher paths |
| Validation working directory | Repository root `C:\Projects\langchain\AGRIFLOW-AI` |

Podman Machine was initially **not connected** (`Currently starting` / inspect `stopped`, TCP `127.0.0.1:59829` refused). Machine was started with `podman machine start` (runtime start only; no repo config change) so validation could proceed.

---

## 2. Podman version

| Component | Version |
|---|---|
| Client | Podman Engine **6.0.2** (API 6.0.2, Go 1.26.5, `windows/amd64`) |
| Server | Podman Engine **6.0.2** (API 6.0.2, `linux/amd64`) |
| OCI runtime | `crun` |
| Network backend | `netavark` (+ `aardvark-dns` 2.0.0) |

---

## 3. Podman Machine status

| Field | Value |
|---|---|
| Name | `podman-machine-default` |
| VM type | WSL |
| Status (after start) | **Currently running** |
| CPUs / Memory / Disk | 8 / 2 GiB / 100 GiB |
| Rootful / rootless | **Rootful** (`Rootless=false`) |
| User-mode networking | `false` (from `podman machine inspect`) |

---

## 4. Compose provider

| Item | Value |
|---|---|
| Command used | `podman compose …` |
| Actual provider | External: `C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe` |
| Provider version | **Docker Compose v5.1.4** |
| `podman-compose` (Python) | Not found on PATH |
| `docker-compose` available to Podman | **Yes** (takes precedence per Podman compose wrapper) |

Podman prints: *Executing external compose provider … docker-compose.exe*.

---

## 5. Port availability

| Host port | Occupied before stack start? | Notes |
|---|---|---|
| **8000** | **No** | No listeners via `netstat` / `Get-NetTCPConnection` |
| **25432** | **No** | No listeners |

No Docker Desktop / Rancher Desktop / other Podman containers were observed owning those ports during checks. Docker Desktop and Rancher WSL distros were **Stopped**.

After failed `db` start, host TCP `localhost:25432` still failed (expected — container never reached running).

---

## 6. Environment / configuration findings

Secrets are **not** printed. Values below are non-secret or presence-only.

### Files inspected

| File | Present | Role |
|---|---|---|
| `backend/.env` | Yes | Backend `env_file` |
| `backend/.env.example` | Yes | Template (`POSTGRES_PORT=5432`, `POSTGRES_HOST=localhost`) |
| Root `.env` | Yes (1 line) | Compose **interpolation** for `${POSTGRES_PASSWORD:?…}` |

### Compose interpolation (root `.env`)

| Variable | Status |
|---|---|
| `POSTGRES_PASSWORD` | **Present and nonempty** (value redacted) — required by compose `${POSTGRES_PASSWORD:?…}` |

### Effective DB-related settings in `backend/.env` (non-secret)

| Variable | Value in `backend/.env` | Notes |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | Compose overrides to `db` for the `backend` service |
| `POSTGRES_PORT` | **`25432`** | **Configuration issue** (see below) |
| `POSTGRES_DB` | `agriflow` | Matches example / compose default |
| `POSTGRES_USER` | `agriflow` | Matches example / compose default |
| `POSTGRES_PASSWORD` | nonempty (redacted) | Present |

### Configuration issue (reported, not fixed)

`POSTGRES_PORT=25432` in `backend/.env` is the **host publish port**, not the PostgreSQL listen port inside the Compose network.

- Host mapping: `localhost:25432` → container `5432`
- Backend container must use: **`db:5432`**
- Resolved compose config showed backend env: `POSTGRES_HOST=db` and **`POSTGRES_PORT: "25432"`**

This would cause the backend to attempt `db:25432` (wrong). Compose overrides `POSTGRES_HOST` but **not** `POSTGRES_PORT`. This affects Docker and Podman equally. **Not fixed in this validation.**

---

## 7. Compose validation

Command: `podman compose config` → **exit 0**

Verified from rendered config (secrets redacted in this report):

| Check | Result |
|---|---|
| `db` service exists | Pass |
| `backend` service exists | Pass |
| Image `timescale/timescaledb:2.28.1-pg17` | Pass |
| Backend build `target: runtime` | Pass |
| Ports `25432→5432`, `8000→8000` | Pass |
| `POSTGRES_HOST=db` | Pass |
| Healthcheck present | Pass (`pg_isready`) |
| `depends_on` / `condition: service_healthy` | Pass |
| Named volume `postgres_data` (`agriflow-ai_postgres_data`) | Pass |

**Also observed:** backend effective `POSTGRES_PORT: "25432"` (env issue above).

Config validation **succeeded**. Validation continued.

---

## 8. Backend build result

Command: `podman compose build backend` → **exit 0** (~90 s)

| Question | Answer |
|---|---|
| Image build successful? | **Yes** |
| Target `runtime` built? | **Yes** (multi-stage `[1/2] builder` then `[2/2] runtime`; final commit `agriflow-ai-backend`) |
| Permission errors? | No |
| Architecture errors? | No (`amd64` / `linux/amd64`) |
| Package/build errors? | No |

Image: `docker.io/library/agriflow-ai-backend:latest` (ID `fb8fa5614658`, ~260 MB).

---

## 9. TimescaleDB image result

| Item | Value |
|---|---|
| Image | `timescale/timescaledb:2.28.1-pg17` |
| Pull | Required and succeeded via Podman |
| Architecture | `amd64` / `linux` |
| Image ID | `f7f3ec414ee70dd0b8d4cebe78e872c6110d7d19d86adfb49dc004199bb9c103` |
| Digest | `sha256:891c202251e619b7c5d3c97a404b2aa9f0be151d45d00b70ab6822b4ef43e8f2` |
| PostgreSQL (image env) | `PG_MAJOR=17`, `PG_VERSION=17.10` |
| TimescaleDB version label | Tag implies **2.28.1**; deeper package probe via `podman run` failed because **bridge networking** was broken (see §10) |

Image tag was **not** changed.

---

## 10. Database startup

Command: `podman compose up -d db` → **failed** (exit 1)

```text
Error response from daemon: netavark (exit code 1): nftables error:
"nft" did not return successfully while applying ruleset:
```

| Observation | Detail |
|---|---|
| Network created | `agriflow-ai_default` |
| Volume created | `agriflow-ai_postgres_data` (**not removed**) |
| Container created | `agriflow-ai-db-1` status **Created** (never Running) |
| Port publish configured | `0.0.0.0:25432->5432/tcp` (inactive until start) |
| Volumes destroyed? | **No** |

Additional diagnostics (no repo changes):

| Test | Result |
|---|---|
| `podman run --rm alpine echo ok` (default bridge) | **Fail** — same netavark/nftables error |
| `podman run --rm --network=host alpine …` | **Success** |
| `podman run --rm --network=none alpine …` | **Success** |
| Simple `nft add table` / `delete table` inside machine | Succeeded |
| Loaded nft modules observed | Only `nft_ct` listed at check time |
| Guest kernel | `6.6.87.2-microsoft-standard-WSL2` |

**Conclusion:** Failure is **Podman Machine bridge firewall/netavark**, not AGRIFLOW compose syntax. Compose project networks require bridge networking; therefore `db` could not start under the existing stack on this host.

A host-level diagnostic (`firewall_driver = "none"` inside the machine) was **not** applied (blocked as out-of-scope system config change during this validation).

---

## 11. Healthcheck result

| Item | Result |
|---|---|
| Healthcheck defined in compose | Yes |
| `db` became `healthy` | **No** — container never started |
| `podman compose ps` during wait | Empty / no running services |

**STOP condition for health:** triggered. Remaining stack steps could not be completed with the unmodified compose path.

---

## 12. Backend startup

| Item | Result |
|---|---|
| `podman compose up -d backend` | **Not run** — blocked by `db` start failure |
| `depends_on: condition: service_healthy` honored? | **Not observable** (backend never started) |
| Both containers running? | **No** |

---

## 13. DNS / networking result

| Item | Result |
|---|---|
| Resolve `db` from backend | **Not tested** — backend not running |
| Compose service DNS expected | Would use project bridge network (`agriflow-ai_default`) once containers run |

Bridge network setup is currently broken on this Podman Machine (see §10).

---

## 14. Database connectivity

| Check | Result |
|---|---|
| Host `localhost:25432` → container `5432` | **Not confirmed** (db not running; TCP test failed) |
| Backend → `db:5432` | **Not tested** |
| Effective config from `podman compose config` | `POSTGRES_HOST=db`, **`POSTGRES_PORT=25432`** |

Per validation rules: because effective `POSTGRES_PORT` is **25432**, migrations must **not** be run until corrected. Even if networking were fixed, Alembic would be expected to fail against `db:25432`.

**STOP before Alembic** (env misconfiguration + db not healthy).

---

## 15. Alembic result

| Item | Result |
|---|---|
| `podman compose run --rm backend alembic upgrade head` | **Not run** (blocked) |
| Migrations / head revision | **Not verified** |

---

## 16. FastAPI result

| Endpoint (intended) | Result |
|---|---|
| `http://localhost:8000` | **Not verified** (backend not started) |
| `/docs`, `/openapi.json` | **Not verified** |
| `/api/v1/health/live`, `/api/v1/health/ready` | **Not verified** |

---

## 17. Live reload result

| Item | Result |
|---|---|
| Bind mount `./backend:/app` + `uvicorn --reload` | **Not verified** |
| Temporary source tweak / restore | **Not performed** (no running backend) |
| Possible mitigation (not applied) | `WATCHFILES_FORCE_POLLING=true` — **OPTIONAL / unproven** on this run |

---

## 18. Persistence result

| Item | Result |
|---|---|
| `podman compose stop` / `start` cycle | **Not performed** (services never healthy/running) |
| Volume left in place | `agriflow-ai_postgres_data` exists; **not destroyed** |
| DB container left | `agriflow-ai-db-1` remains in **Created** state (no data initialized) |

---

## 19. Problems discovered

1. **REQUIRED (host Podman runtime):** Default bridge networking fails with `netavark` / `nftables` on this Podman 6.0.2 WSL machine. Blocks `podman compose up` for any project using the default Compose network (including AGRIFLOW `db` + `backend`).
2. **REQUIRED (application env, not Podman-specific):** `backend/.env` has `POSTGRES_PORT=25432`. Backend inside Compose must use **5432**. Compose does not override this today.
3. **Operational:** Podman Machine was stopped / stuck starting at session begin; must be running before compose.
4. **Informational:** Compose provider is Docker’s `docker-compose.exe` (v5.1.4), not `podman-compose`.
5. **Not proven on this run:** health gating order, DNS `db`, Alembic, FastAPI reachability, live reload, persistence after stop/start.

---

## 20. Required changes

Minimum to make the **existing** canonical compose usable under Podman on this machine:

| # | Change | Scope | Why |
|---|---|---|---|
| 1 | Repair Podman Machine **bridge** networking so netavark can start containers (host/VM fix — e.g. working nftables stack or an explicit supported `firewall_driver` for this WSL kernel). | Host / Podman Machine (**not** repo compose) | Without bridge nets, Compose service DNS and published ports cannot work as designed |
| 2 | Set `POSTGRES_PORT=5432` in `backend/.env` (keep host publish mapping `25432:5432` in compose). | Env file only | Backend must connect to `db:5432`, not `db:25432` |

**NOT REQUIRED:** a second Podman-specific compose file.  
**NOT REQUIRED:** Dockerfile or application code changes for Podman compatibility (build already succeeded).

---

## 21. Optional changes

| Change | Classification | Notes |
|---|---|---|
| `WATCHFILES_FORCE_POLLING=true` for uvicorn reload on Windows bind mounts | **OPTIONAL** (untested here) | Same class of issue as Docker Desktop/WSL bind mounts |
| Document `podman machine start` prerequisite | **RECOMMENDED** | Machine was not running at validation start |
| Document Compose provider (`docker-compose.exe` via `podman compose`) | **RECOMMENDED** | Avoid assuming `podman-compose` |
| Root `.env` with `POSTGRES_PASSWORD` for interpolation | **REQUIRED operationally** (already present here) | Compose `${POSTGRES_PASSWORD:?…}`; already satisfied on this machine |
| Override `POSTGRES_PORT: "5432"` in compose `environment:` | **OPTIONAL alternative** to editing `backend/.env` | Prefer fixing `.env` to keep one canonical compose |

---

## 22. Final recommendation

**Classification: B — Minor runtime/configuration change required.**

Preferred architecture remains:

```text
Docker Desktop  OR  Podman  OR  Rancher Desktop
        ↓
same canonical docker-compose.yml
        ↓
same db + backend architecture
        ↓
same application
```

**Do not** introduce a Podman-specific compose file based on this run: the compose file validated and the backend image built cleanly. Failures were (1) host Podman bridge/nftables and (2) `POSTGRES_PORT` env misuse shared with Docker.

### What was proven

- Podman 6.0.2 + Docker Compose v5.1.4 can parse and build this stack.
- TimescaleDB `2.28.1-pg17` pulls on `linux/amd64`.
- Canonical compose structure (healthcheck, `depends_on`, volume, ports, `POSTGRES_HOST=db`) is intact under `podman compose config`.

### What was not proven

- End-to-end `db` healthy → backend up → DNS → Alembic → FastAPI → reload → persistence.

### Next validation (after REQUIRED fixes only)

1. Fix Podman Machine bridge networking on the host.
2. Correct `POSTGRES_PORT=5432` in `backend/.env` (still a separate change; not done here).
3. Re-run from step 7 (`podman compose up -d db`) through persistence — still without a second compose file.

---

## Appendix A — Commands executed (high level)

- `podman version` / `podman info` / `podman machine list` / `podman machine start`
- `podman compose version` / `podman compose config` / `podman compose build backend`
- `podman pull timescale/timescaledb:2.28.1-pg17`
- `podman compose up -d db` (failed)
- Port / process / WSL status checks
- Non-destructive network probes (`--network=host` / `none`)

## Appendix B — Artifacts left on the machine (not cleaned)

| Artifact | State | Action taken |
|---|---|---|
| Volume `agriflow-ai_postgres_data` | Exists | Left in place (no `down -v` / volume rm) |
| Container `agriflow-ai-db-1` | Created, not started | Left in place |
| Network `agriflow-ai_default` | Exists | Left in place |
| Image `agriflow-ai-backend` | Built | Left in place |
| Image `timescale/timescaledb:2.28.1-pg17` | Pulled | Left in place |

No passwords, API keys, tokens, or other secrets are included in this report.
