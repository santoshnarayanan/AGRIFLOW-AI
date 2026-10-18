# Phase 16 — Enterprise AI Platform & Production Readiness

**Status:** Complete (platform + hardening slices)  
**ADR:** [ADR-011](../../../adr/ADR-011-phase16-temporal-copilot.md)  
**Migrations:** None (Phase 16 is application, Compose, CI, and docs — no new Alembic revisions)

## Primary objective

Enterprise AI assistants, durable agricultural workflows, MCP tool evaluation, and production observability hooks — without changing the Phase 12–15 persistence and event contracts.

## Delivered — Temporal workflows

| Component | Location |
|-----------|----------|
| `SoilMoistureAlertWorkflow` | `backend/app/temporal/workflows/soil_moisture_alert.py` |
| Activities (moisture check, irrigation rec) | `backend/app/temporal/activities/soil_moisture.py` |
| API trigger (low soil moisture ingest) | `SensorReadingService.create_sensor_reading` + `app/temporal/starter.py` |
| Worker | `python -m app.temporal.worker` |
| Compose (dev server + worker) | `docker-compose.yml` → `temporal`, `temporal-worker` |

Configuration: `TEMPORAL_ENABLED`, `TEMPORAL_HOST`, `TEMPORAL_NAMESPACE`, `TEMPORAL_TASK_QUEUE`, `TEMPORAL_SOIL_MOISTURE_PERSISTENCE_MINUTES`.

## Delivered — Farm Copilot / GaaS

| Component | Location |
|-----------|----------|
| Tool registry (field, moisture, alerts, twin, KPIs) | `backend/app/copilot/tools.py` |
| Copilot service (deterministic + optional OpenAI/Azure) | `backend/app/services/copilot.py` |
| REST API | `POST /api/v1/copilot/fields/{field_id}/chat` |
| UI | `frontend/src/pages/Copilot.tsx`, `frontend/src/api/copilot.ts` |

Configuration: `COPILOT_ENABLED`, `COPILOT_LLM_PROVIDER` (`none` \| `openai` \| `azure`), `OPENAI_*` or `AZURE_OPENAI_*` in `backend/.env`.

**OpenAI convenience:** If `OPENAI_API_KEY` is set and `COPILOT_LLM_PROVIDER=none`, settings auto-select `openai` (`Settings.apply_copilot_openai_default`). Restart the API after changing `.env`.

## Delivered — MCP evaluation

| Component | Location |
|-----------|----------|
| Tool catalog (JSON Schema) | `GET /api/v1/mcp/tools` |
| Direct tool invoke (evaluation) | `POST /api/v1/mcp/tools/invoke` |
| Stdio server (optional, separate venv) | `python -m app.mcp_stdio.server` — see `backend/requirements-mcp.txt` |

Same tool implementations as Farm Copilot (`app/copilot/tools.py`). Configuration: `MCP_TOOLS_ENABLED`.

## Delivered — Observability

| Component | Location |
|-----------|----------|
| Prometheus HTTP metrics | `app/core/observability/metrics.py`, middleware in `app/main.py` |
| Scrape endpoint | `GET /api/v1/metrics` |

Configuration: `METRICS_ENABLED`.

## Delivered — Production hardening (Phase 16b)

| Component | Location |
|-----------|----------|
| Copilot / MCP JWT (VIEWER+) | `PlatformViewerDep` on `/copilot` and MCP invoke (`platform_auth.py`) |
| Auto OpenAI when key set | `Settings.apply_copilot_openai_default` |
| Security headers middleware | `app/core/security/headers.py` |
| GitHub Actions CI | `.github/workflows/backend-ci.yml` |
| DR runbook + backup script | `docs/ops/disaster-recovery-runbook.md`, `scripts/ops/backup-postgres.ps1` |
| Git co-author stripping (local) | `.githooks/commit-msg`, `docs/contributing-git-hooks.md` |
| Cursor rule (no AI co-authors) | `.cursor/rules/no-ai-coauthors.mdc` |

Configuration: `COPILOT_AUTH_REQUIRED` (when true, also sets `AUTH_REQUIRED`), `SECURITY_HEADERS_ENABLED`, `AGRIFLOW_API_URL` / `AGRIFLOW_BEARER_TOKEN` for stdio MCP.

## Delivered — Frontend & Compose

| Component | Location |
|-----------|----------|
| Vite dev container | `frontend/Dockerfile`, Compose service `frontend` (port **3000**) |
| API proxy in container | `VITE_API_PROXY_TARGET=http://backend:8000` in `docker-compose.yml` |

```bash
docker compose up -d db backend frontend
```

## Tests

| Test module | Coverage |
|-------------|----------|
| `test_temporal_workflow.py` | Time-skipping `SoilMoistureAlertWorkflow` |
| `test_copilot.py` | MCP catalog, invoke errors, Copilot 404 |
| `test_security_hardening.py` | Security headers, OpenAI provider auto-default |

CI runs the full `backend/app/tests` suite on push/PR (see `backend-ci.yml`).

## Configuration (summary)

See `backend/.env.example` for all keys. Phase 16–specific:

| Variable | Purpose |
|----------|---------|
| `TEMPORAL_*` | Optional workflow worker |
| `COPILOT_*`, `OPENAI_*`, `AZURE_OPENAI_*` | Farm Copilot / LLM |
| `MCP_TOOLS_ENABLED` | HTTP MCP routes |
| `METRICS_ENABLED` | Prometheus middleware + `/metrics` |
| `SECURITY_HEADERS_ENABLED` | Response security headers |
| `COPILOT_AUTH_REQUIRED` | Require JWT for Copilot/MCP invoke |

## Operational follow-up (non-code)

Per-farm user tenancy (not just platform roles), large-scale load testing in a dedicated environment, Azure-specific DR automation, frontend E2E tests, and full production ML training pipelines remain environment/ops tasks.

## Related documentation

- [frontend-ui.md](./frontend-ui.md) — `/copilot` route and dev setup
- [application-technical-flow.md](../application-technical-flow.md) — §9.1 Copilot / Temporal / MCP flows
- [09-architecture-diagrams.md](../09-architecture-diagrams.md) — §17 as-built summary
- [06-roadmap.md](../06-roadmap.md) — long-term backlog
