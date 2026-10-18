# ADR-011: Phase 16 Temporal Workflows, Farm Copilot, and MCP Tool Surface

## Status

Accepted — Phase 16

## Context

Phases 14–15 delivered transactional domain events, Feature Store, CQRS read models, Digital Twin state, and platform JWT. Phase 16 must add:

1. Durable multi-step agronomic processes (soil moisture persistence before irrigation guidance).
2. A GaaS-ready natural language interface over existing APIs and projections.
3. A machine-evaluable tool catalog aligned with MCP discovery patterns.
4. Baseline Prometheus metrics for production readiness.

## Decision

### Temporal

- Use `temporalio` Python SDK with a dedicated worker process (`app.temporal.worker`).
- Trigger `SoilMoistureAlertWorkflow` from `SensorReadingService` when `TEMPORAL_ENABLED` and soil moisture is below `SOIL_MOISTURE_LOW_THRESHOLD_PERCENT`.
- Activities own database sessions; workflows remain deterministic and delegate I/O to activities.

### Farm Copilot

- Implement a shared tool registry in `app/copilot/tools.py` used by Copilot and MCP routes.
- Default to **deterministic** responses (`COPILOT_LLM_PROVIDER=none`) for local/dev without API keys.
- Optional OpenAI-compatible or Azure OpenAI chat completion for production GaaS.

### MCP evaluation

- Expose `GET /mcp/tools` and `POST /mcp/tools/invoke` for catalog and direct invocation — evaluation and agent prototyping without a separate stdio server in v1.

### Observability

- Prometheus client counters/histograms on HTTP traffic; scrape via `/api/v1/metrics`.

## Consequences

- Compose stack optionally runs Temporal dev server + worker; API remains functional with `TEMPORAL_ENABLED=false`.
- Alert evaluation consumer (Phase 14) and Temporal workflow can both react to low moisture — operators should tune thresholds and disable one path if duplicate alerts are undesirable.
- LLM paths require secrets via environment variables; never commit keys.
