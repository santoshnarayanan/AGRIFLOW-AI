# Frontend UI implementation reference

This document maps the **React + TypeScript** client to the FastAPI backend: routing, API clients, domain types, and Phase 13 intelligence screens.

## Stack and layout

| Layer | Location | Notes |
|--------|----------|--------|
| Entry | `frontend/src/main.tsx`, `App.tsx` | React Router, TanStack Query provider |
| Shell | `frontend/src/components/layout/AppLayout.tsx` | Sidebar + `Header` + page outlet |
| Navigation | `frontend/src/components/layout/Sidebar.tsx` | All 13 feature routes |
| Styling | Tailwind + shadcn/ui under `frontend/src/components/ui/` | Shared primitives |
| HTTP | `frontend/src/api/client.ts` | Axios, base URL `VITE_API_URL` or `/api/v1` |

## Routes (sidebar)

| Path | Page component | Primary API modules |
|------|----------------|---------------------|
| `/` | `pages/Dashboard.tsx` | `farms`, `fields`, `alerts`, `recommendations` |
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
- See also [13-decision-intelligence.md](./13-decision-intelligence.md) for backend services and migrations.

### Other domains

Several legacy pages still use simplified numeric ids in types for crops, sensors, etc.; **farm**, **field**, and **field-scoped create payloads** use string UUIDs where the backend does. Crop listing/create is aligned via `frontend/src/api/crops.ts` (`/fields/{field_id}/crops`).

## Global UX behaviors

- **Header notification bell** (`Header.tsx`): loads all fields, fetches alerts, shows a badge count of unacknowledged alerts, navigates to `/alerts` on click.
- **Dashboard**: farm table and alert/recommendation stats use the same field-scoped alert/recommendation hooks as the intelligence pages.
- **Dev proxy**: Vite proxies `/api` to the backend (see `frontend/vite.config.ts`).

## Local development

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000
npm run build  # production typecheck + bundle
```

Backend must be reachable at the configured API base (default proxy to port 8000).

## Related documentation

- [04-api-design.md](../04-api-design.md) — REST conventions
- [13-decision-intelligence.md](./13-decision-intelligence.md) — Phase 13 backend and API map
- [../../phases/phase13/phase-summary.md](../../phases/phase13/phase-summary.md) — product narrative
