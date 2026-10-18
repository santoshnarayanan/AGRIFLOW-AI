# Frontend UI implementation reference

**Status:** Phases 1–13 (core domains + decision intelligence), **Phase 14** (`/events`), **Phase 15** (dashboard read models, Feature Store, platform sign-in), **Phase 16** (`/copilot` Farm Copilot) — as implemented in `frontend/`.

This document maps the **React + TypeScript** client to the FastAPI backend: routing, API clients, domain types, and platform/intelligence screens.

## Stack and layout

| Layer | Location | Notes |
|--------|----------|--------|
| Entry | `frontend/src/main.tsx`, `App.tsx` | React Router, TanStack Query provider |
| Shell | `frontend/src/components/layout/AppLayout.tsx` | Sidebar + `Header` + page outlet; `pageMeta` for `/events`, `/features`, `/copilot` |
| Navigation | `frontend/src/components/layout/Sidebar.tsx` | **AI Intelligence**: recommendations, alerts, Feature Store, **Farm Copilot**; **Platform**: Domain Events |
| Auth UI | `components/auth/LoginDialog.tsx`, `stores/authStore.ts` | Phase 15 — JWT in `localStorage`; header Sign in / Sign out |
| Styling | Tailwind + shadcn/ui under `frontend/src/components/ui/` | Shared primitives |
| HTTP | `frontend/src/api/client.ts` | Axios; `Authorization: Bearer` when logged in; optional `X-Events-Ops-Key` on outbox URLs |

See also [frontend/README.md](../../../frontend/README.md) for env vars and dev commands.

## Routes (sidebar)

| Path | Page component | Primary API modules |
|------|----------------|---------------------|
| `/` | `pages/Dashboard.tsx` | `readModels` (platform dashboard KPIs), `farms`, `fields`, `alerts`, `recommendations` |
| `/farms` | `pages/Farms.tsx` | `farms` |
| `/fields` | `pages/Fields.tsx` | `fields`, `farms` |
| `/crops` | `pages/Crops.tsx` | `crops`, `fields`, `farms` |
| `/soil-profiles` | `pages/SoilProfiles.tsx` | `soil-profiles`, `fields` |
| `/weather` | `pages/Weather.tsx` | `weather`, `fields` |
| `/sensors` | `pages/Sensors.tsx` | `sensors`, `fields` |
| `/irrigation` | `pages/Irrigation.tsx` | `irrigation`, `fields`, `crops` |
| `/yield` | `pages/Yield.tsx` | `yield`, `fields`, `crops` |
| `/disease` | `pages/Disease.tsx` | `disease`, `fields`, `crops` |
| `/satellite` | `pages/Satellite.tsx` | `satellite`, `fields` |
| `/recommendations` | `pages/Recommendations.tsx` | `recommendations`, `fields`, `farms` |
| `/alerts` | `pages/Alerts.tsx` | `alerts`, `fields`, `farms` |
| `/features` | `pages/FeatureStore.tsx` | `features` (catalog, snapshots, materialise) — **Phase 15** |
| `/events` | `pages/Events.tsx` | `events` (catalog, outbox stats, outbox entries) — **Phase 14** |
| `/copilot` | `pages/Copilot.tsx` | `copilot` (`POST /copilot/fields/{id}/chat`) — **Phase 16** |

**No dedicated UI routes yet (backend APIs exist):** Digital Twin (`/digital-twin/...`), read-model **refresh** POST endpoints, ML engine (`/ml/...`), MCP tool playground (`/mcp/...`). Operators use API/Swagger or external MCP stdio host (`python -m app.mcp_stdio.server`).

## Domain types and API alignment

Shared contracts live in `frontend/src/types/index.ts`.

### Farm and field (Phase 1 / Phase 13 API)

- **Farm** mirrors `FarmResponse`: UUID `id`, `farm_code`, `farm_name`, geo fields, `total_area_hectares`, `is_active`.
- **Field** mirrors `FieldResponse`: UUID `id` / `farm_id`, `area_hectares`, optional soil and GPS.
- **Clients**: `frontend/src/api/farms.ts` — `GET/POST /farms`, `PATCH /farms/{id}`; `frontend/src/api/fields.ts` — `GET /farms/{farm_id}/fields`, `POST` same path, `PATCH /fields/{id}`.
- **Helpers**: `frontend/src/lib/farm.ts` — display labels and decimal parsing from API strings.
- **Aggregated field lists**: `useFields()` without a farm id loads all farms, then merges each farm’s field list (no global `GET /fields` on the backend).

### Phase 13 decision intelligence

- Types: `Recommendation`, `Alert` (string UUIDs, backend enums).
- Clients: `frontend/src/api/recommendations.ts`, `frontend/src/api/alerts.ts`.
- Multi-field views use `useRecommendationsForFieldIds` / `useAlertsForFieldIds` (parallel per-field queries).
- See [13-decision-intelligence.md](./13-decision-intelligence.md) for backend services and migrations.

### Phase 14 — Domain events (UI)

- Types: `EventCatalogResponse`, `OutboxStats`, `OutboxEntry`, `OutboxEntryListResponse`, `OutboxEntryStatus`.
- Client: `frontend/src/api/events.ts` — `GET /events/catalog`, `GET /events/outbox/stats`, `GET /events/outbox/entries?status=...`.
- **Operator access:** Outbox routes require `PlatformOperatorDep` on the backend. The UI sends **Bearer JWT** after sign-in (`client.ts`). Optionally set `VITE_EVENTS_OPS_API_KEY` for legacy `X-Events-Ops-Key` on outbox URLs (still attached when JWT is absent).
- Page: `Events.tsx` — stat cards, event catalog table, outbox entry list with status filter.
- See [14-event-platform.md](./14-event-platform.md).

### Phase 15 — CQRS dashboard read models (UI)

- Types: `PlatformDashboardReadModel` (and related KPI fields in `types/index.ts`).
- Client: `frontend/src/api/readModels.ts` — `GET /read-models/dashboard` via `usePlatformDashboard()`.
- **Dashboard** (`Dashboard.tsx`) renders KPI cards from the platform read model when available (field counts, alert/recommendation highlights from projection — not only live per-field alert queries).
- **Not in UI:** `POST .../dashboard/refresh`, farm/field dashboard refresh — operator-only; call via API or sign in + future admin tools.

### Phase 15 — Feature Store (UI)

- Types: `FeatureCatalogResponse`, `FeatureCatalogItem`, `FieldFeatureSnapshot`, `FieldFeatureSnapshotListResponse`.
- Client: `frontend/src/api/features.ts` — `GET /features/catalog`, `GET /features/fields/{id}/snapshots`, `POST /features/fields/{id}/materialize`.
- Page: `FeatureStore.tsx` — registry version, catalog table, field selector, materialise action, snapshot history.
- **Materialise** requires operator auth (JWT in dev with `AUTH_REQUIRED=false` may still work via backend dev bypass; production should use sign-in).

### Phase 16 — Farm Copilot (UI)

- Client: `frontend/src/api/copilot.ts` — `copilotChat(fieldId, message)` → `CopilotChatResponse` (`mode`, `answer`, `tools` trace).
- Page: `Copilot.tsx` — field selector (`useFields()`), question textarea, displays deterministic or **openai** mode from backend.
- **LLM:** Configured in `backend/.env` (`OPENAI_API_KEY`, `COPILOT_LLM_PROVIDER`); frontend has no API keys.
- **Auth:** Copilot route uses `PlatformViewerDep` when `AUTH_REQUIRED=true`; dev bypass matches other routes. Bearer token from sign-in is sent via `api/client.ts` when present.
- See [16-enterprise-ai.md](./16-enterprise-ai.md) and [application-technical-flow.md](../application-technical-flow.md) §9.1.

### Phase 15 — Platform authentication (UI)

- Types: `LoginRequest`, `TokenResponse`, `PlatformUser`, `PlatformRole`.
- Client: `frontend/src/api/auth.ts` — `POST /auth/login`, `GET /auth/me`; hooks `useLogin`, `useCurrentUser`, `useLogout`.
- Store: `stores/authStore.ts` — `agriflow_access_token` in `localStorage`.
- **Header** (`Header.tsx`): Sign in opens `LoginDialog`; signed-in state shows email + logout.

### Other domains

Several legacy pages still use simplified numeric ids in types for crops, sensors, etc.; **farm**, **field**, and **field-scoped create payloads** use string UUIDs where the backend does. Crop listing/create is aligned via `frontend/src/api/crops.ts` (`/fields/{field_id}/crops`).

## Global UX behaviors

- **Header notification bell** (`Header.tsx`): loads all fields, fetches alerts, badge for unacknowledged count, navigates to `/alerts`.
- **Header auth** (Phase 15): platform operator JWT for protected APIs (Feature Store materialise, outbox when not using ops key).
- **Dashboard**: CQRS platform read model KPIs (`usePlatformDashboard`) plus farm table and legacy alert/recommendation stats where still used.
- **Dev proxy**: Vite proxies `/api` to the backend (see `frontend/vite.config.ts`).

## Environment variables (frontend)

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | API base (default `/api/v1` via proxy) |
| `VITE_EVENTS_OPS_API_KEY` | Optional legacy ops key for `/events/outbox` requests |

## Local development

**Host (Vite):**

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
npm run build  # production typecheck + bundle
```

**Podman/Docker (from repo root):**

```bash
docker compose up -d db backend frontend
```

Open http://localhost:3000 — Vite in the `frontend` container proxies `/api` to `backend:8000` (`VITE_API_PROXY_TARGET` in compose).

Backend must be reachable at the configured API base (default proxy to port 8000). For operator flows, run migration `n8o9p0q1r2s3` and sign in with bootstrap admin (see `backend/.env.example`). Farm Copilot needs at least one field (seed data or CRUD).

## Related documentation

- [04-api-design.md](../04-api-design.md) — REST conventions
- [13-decision-intelligence.md](./13-decision-intelligence.md) — Phase 13 backend and API map
- [14-event-platform.md](./14-event-platform.md) — Phase 14 events and outbox
- [15-enterprise-intelligence.md](./15-enterprise-intelligence.md) — Feature Store, read models, Digital Twin, JWT
- [16-enterprise-ai.md](./16-enterprise-ai.md) — Farm Copilot, Temporal, MCP (backend)
- [application-technical-flow.md](../application-technical-flow.md) — runtime flows including `/copilot`
- [../../phases/phase13/phase-summary.md](../../phases/phase13/phase-summary.md) — Phase 13 product narrative
