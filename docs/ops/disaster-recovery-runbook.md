# Disaster recovery runbook (PostgreSQL)

Operational guide for **local / self-hosted** AGRIFLOW-AI. Adapt paths for Azure Database for PostgreSQL in production.

## Scope

- Primary data store: PostgreSQL 17 + TimescaleDB (`db` service, host port **25432**).
- RPO/RTO targets are environment-specific; this runbook validates **backup → restore → migrate**.

## Backup (logical)

From the repository root with the database container running:

**PowerShell (Windows):**

```powershell
.\scripts\ops\backup-postgres.ps1
```

**Manual:**

```bash
podman exec agriflow-ai-db-1 pg_dump -U agriflow -Fc agriflow > backups/agriflow-$(date +%Y%m%d).dump
```

Store dumps off-machine (object storage, encrypted volume).

## Restore drill

1. Stop API and workers (`backend`, `temporal-worker`, consumers).
2. Create empty database or drop/recreate `agriflow` (destructive).
3. `pg_restore -U agriflow -d agriflow -c your.dump`
4. `alembic upgrade head` (should be no-op if dump matches head).
5. `GET /api/v1/health/ready` → database `connected`.
6. Smoke: list farms, dashboard read model, Copilot deterministic chat.

## TimescaleDB notes

Hypertables and policies are included in `pg_dump` custom format. After restore, verify:

```sql
SELECT hypertable_name FROM timescaledb_information.hypertables;
```

## Secrets

Never commit `.env` or dumps containing production data. Rotate `SECRET_KEY` and operator passwords after incident recovery.
