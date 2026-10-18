# Phase 16 — Enterprise AI Platform & Production Readiness

**Status:** Complete (platform + hardening slices)  
**ADR:** [ADR-011](../../../adr/ADR-011-phase16-temporal-copilot.md)

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

Configuration: `TEMPORAL_ENABLED`, `TEMPORAL_HOST`, `TEMPORAL_TASK_QUEUE`, `TEMPORAL_SOIL_MOISTURE_PERSISTENCE_MINUTES`.

## Delivered — Farm Copilot / GaaS

| Component | Location |
|-----------|----------|
| Tool registry (field, moisture, alerts, twin, KPIs) | `backend/app/copilot/tools.py` |
| Copilot service (deterministic + optional OpenAI/Azure) | `backend/app/services/copilot.py` |
| REST API | `POST /api/v1/copilot/fields/{field_id}/chat` |
| UI | `frontend/src/pages/Copilot.tsx` |

Configuration: `COPILOT_ENABLED`, `COPILOT_LLM_PROVIDER` (`none` \| `openai` \| `azure`), provider API keys in `.env`.

## Delivered — MCP evaluation

| Component | Location |
|-----------|----------|
| Tool catalog (JSON Schema) | `GET /api/v1/mcp/tools` |
| Direct tool invoke (evaluation) | `POST /api/v1/mcp/tools/invoke` |

Same tool implementations as Farm Copilot (`app/copilot/tools.py`).

## Delivered — Observability

| Component | Location |
|-----------|----------|
| Prometheus HTTP metrics | `app/core/observability/metrics.py`, middleware in `app/main.py` |
| Scrape endpoint | `GET /api/v1/metrics` |

Configuration: `METRICS_ENABLED`.

## Tests

- `backend/app/tests/test_temporal_workflow.py` — time-skipping workflow unit test
- `backend/app/tests/test_copilot.py` — MCP catalog + Copilot 404

## Delivered — Production hardening (Phase 16b)

| Component | Location |
|-----------|----------|
| Copilot / MCP JWT (VIEWER+) | `PlatformViewerDep` on `/copilot` and MCP invoke |
| Auto OpenAI when key set | `Settings.apply_copilot_openai_default` |
| Security headers middleware | `app/core/security/headers.py` |
| GitHub Actions CI | `.github/workflows/backend-ci.yml` |
| MCP stdio server | `pip install -r requirements-mcp.txt` then `python -m app.mcp_stdio.server` |
| DR runbook + backup script | `docs/ops/disaster-recovery-runbook.md`, `scripts/ops/backup-postgres.ps1` |
| Extra tests | `test_security_hardening.py` |

Configuration: `COPILOT_AUTH_REQUIRED`, `SECURITY_HEADERS_ENABLED`, `AGRIFLOW_API_URL` / `AGRIFLOW_BEARER_TOKEN` for stdio MCP.

## Operational follow-up (non-code)

Per-farm user tenancy (not just platform roles), large-scale load testing in a dedicated environment, and Azure-specific DR automation remain environment/ops tasks.
