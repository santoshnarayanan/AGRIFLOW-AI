# AGRIFLOW-AI Frontend

React + TypeScript single-page application for the AGRIFLOW-AI agricultural intelligence platform. It talks to the FastAPI backend at `/api/v1` (Vite dev proxy in development).

## Stack

| Layer | Technology |
|--------|------------|
| UI | React 19, TypeScript |
| Build | Vite 8 |
| Routing | React Router |
| Server state | TanStack Query |
| HTTP | Axios (`src/api/client.ts`) |
| Styling | Tailwind CSS, shadcn/ui primitives |
| Client state | Zustand (`appStore`, `authStore`) |

## Routes

| Path | Screen | Notes |
|------|--------|--------|
| `/` | Dashboard | Platform KPIs via CQRS read models (Phase 15) |
| `/farms` … `/satellite` | Core domains | Farm, field, crop, environmental, operations |
| `/recommendations`, `/alerts` | Decision intelligence | Phase 13 |
| `/events` | Domain Events | Outbox stats and catalog (Phase 14) |
| `/features` | Feature Store | Catalog, materialise, snapshots (Phase 15) |

Shell layout: `src/components/layout/AppLayout.tsx` (sidebar + header). **Sign in** in the header issues a JWT for operator APIs (materialise, refresh, outbox).

## Environment variables

Create `frontend/.env.local` as needed (do not commit secrets):

| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | API base (default: `/api/v1` via proxy) |
| `VITE_EVENTS_OPS_API_KEY` | Optional legacy ops key for `/events/outbox` when not using JWT |

Operator calls prefer `Authorization: Bearer <token>` from `authStore` after login (`POST /auth/login`).

## Local development

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000 — proxies /api to backend

### Podman / Docker Compose (with db + backend)

From the repository root:

```bash
docker compose up --build db backend frontend
```

Open **http://localhost:3000** (Vite in `frontend-1` proxies `/api` to `backend:8000`).
npm run build    # tsc + production bundle
npm run lint     # oxlint
```

Start the backend (see root `README.md` and `docs/reference/05-local-setup.md`) before exercising CRUD or intelligence screens.

## Project layout

```text
src/
  api/           # Axios clients and React Query hooks per domain
  components/    # layout, ui, auth (LoginDialog)
  pages/         # route-level screens
  stores/        # Zustand (sidebar, auth token)
  types/         # Shared TypeScript contracts aligned with backend schemas
```

## Related documentation

- [phase-implementations/frontend-ui.md](../docs/reference/phase-implementations/frontend-ui.md) — detailed route and API map (update as routes evolve)
- [15-enterprise-intelligence.md](../docs/reference/phase-implementations/15-enterprise-intelligence.md) — Feature Store, read models, auth
- [14-event-platform.md](../docs/reference/phase-implementations/14-event-platform.md) — events UI and outbox
