# Podman migration — archived troubleshooting reports

**Date:** 2026-08-16  
**Status:** Historical session artifacts (diagnostic and repair steps on a Windows 11 + Podman 6 host).

Use these when you need the full investigation trail. For day-to-day development, prefer:

- [Podman compatibility audit](../../architecture/PODMAN_COMPATIBILITY_AUDIT.md) — stack compatibility and configuration checklist
- [Podman final validation report](../../architecture/PODMAN_FINAL_VALIDATION_REPORT.md) — validated end state (WSL mirrored networking, `localhost:25432`, migrations)
- [Local setup guide](../../reference/05-local-setup.md) — how to run the stack

## Archived reports

| File | Purpose |
|------|---------|
| [PODMAN_RUNTIME_VALIDATION_REPORT.md](./PODMAN_RUNTIME_VALIDATION_REPORT.md) | Initial Podman bring-up attempt; bridge/netavark blockers and `POSTGRES_PORT` env note |
| [PODMAN_HOST_PORT_25432_DIAGNOSTIC_REPORT.md](./PODMAN_HOST_PORT_25432_DIAGNOSTIC_REPORT.md) | Why Windows `localhost:25432` failed while in-VM networking worked |
| [PODMAN_NETWORKING_REPAIR_REPORT.md](./PODMAN_NETWORKING_REPAIR_REPORT.md) | Podman Machine bridge repair without changing repo compose or app code |

These documents are **not** required to run AGRIFLOW-AI; they document host-specific fixes applied during migration from Docker Desktop to Podman Desktop.
