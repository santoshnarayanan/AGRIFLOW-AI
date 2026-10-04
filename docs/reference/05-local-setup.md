# AGRIFLOW-AI Local Development Setup

**Last Updated:** Phase 13 — AI Decision Intelligence Layer Complete  
**Status:** Current

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|---|---|---|
| Podman Desktop | 1.x | Container runtime (replaces Docker Desktop) |
| Python | 3.12 | Backend runtime |
| Git | 2.x | Version control |

**Container image:** `timescale/timescaledb:2.28.1-pg17` — PostgreSQL 17.10 with TimescaleDB 2.28.1 extension pre-installed. Standard `postgres:17` does not include TimescaleDB and will fail migration `f1e2d3c4b5a6`.

---

## Repository Structure

```text
AGRIFLOW-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── farms/
│   │   │   ├── fields/
│   │   │   ├── crops/
│   │   │   ├── soil_profiles/
│   │   │   ├── weather_records/
│   │   │   ├── sensor_readings/
│   │   │   ├── irrigation_events/
│   │   │   ├── yield_records/
│   │   │   ├── disease_observations/
│   │   │   ├── satellite_observations/
│   │   │   ├── recommendations/         ← Phase 13
│   │   │   ├── alerts/                  ← Phase 13
│   │   │   ├── health/
│   │   │   ├── version/
│   │   │   ├── deps.py
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config/
│   │   │   ├── enums.py             ← 14 shared enums (Phase 13)
│   │   │   └── logging/
│   │   ├── db/
│   │   │   ├── migrations/
│   │   │   │   └── versions/        ← 18 migration files (Phases 1–13)
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── docs/
├── infrastructure/
└── compose.yaml
```

---

## 1. Clone Repository

```bash
git clone <repository-url>
cd AGRIFLOW-AI
```

---

## 2. Start Infrastructure Services

Podman Compose starts the TimescaleDB container (PostgreSQL 17 + TimescaleDB 2.28.1):

```bash
podman compose up -d
```

Verify services are running:

```bash
podman compose ps
```

Expected: `agriflow-db` container in `Up` state running `timescale/timescaledb:2.28.1-pg17`.

**Database connection defaults:**

| Parameter | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| Database | `agriflow` |
| User | `agriflow` |
| Password | See `.env` file |

> **Note:** The compose file uses `timescale/timescaledb:2.28.1-pg17`, not `postgres:17`. This is required — Phase 12 migrations enable the TimescaleDB extension and convert six tables to hypertables. A plain PostgreSQL image will fail at migration `f1e2d3c4b5a6`.

---

## 3. Configure Environment

Copy the example environment file and set values:

```bash
cp backend/.env.example backend/.env
```

Key environment variables:

```env
DATABASE_URL=postgresql+asyncpg://agriflow:<password>@localhost:5432/agriflow
SECRET_KEY=<your-secret-key>
```

---

## 4. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## 5. Run Database Migrations

From inside the `backend/` directory:

```bash
alembic upgrade head
```

This applies all 18 migrations in order:

```text
001_create_farms_table
002_create_fields_table
003_create_crops_table
13aabbe35d51_add_soil_profiles_table
004_create_weather_records_table
005_add_p1_ai_readiness_columns
006_create_sensor_readings_table
235a51cdf901_create_irrigation_events_table
b7e2a9f4c8d3_create_yield_records_table
d3e7b2a9f1c4_create_disease_observations_table
a1b2c3d4e5f6_create_satellite_observations_table
f1e2d3c4b5a6_enable_timescaledb_extension         ← requires TimescaleDB image
c9d8e7f6a5b4_convert_time_series_tables_to_hypertables
d4f5e6a7b8c9_enable_hypertable_compression_policies
e5f6a7b8c9d0_create_continuous_aggregates
f6a7b8c9d0e1_enable_retention_policies
g1h2i3j4k5l6_create_recommendations_table
h2i3j4k5l6m7_create_alerts_table                  ← HEAD
```

Verify migration status:

```bash
alembic current
```

Expected output includes `h2i3j4k5l6m7 (head)`.

---

## 6. Start the Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

For production-like startup (no auto-reload):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 7. Verify Installation

### Health Check

```bash
curl http://localhost:8000/api/v1/health/live
```

Expected response:

```json
{"status": "ok"}
```

### Readiness Check

```bash
curl http://localhost:8000/api/v1/health/ready
```

### API Documentation

Open in browser:

```text
http://localhost:8000/docs
```

The Swagger UI lists all implemented endpoints across all 13 phases.

---

## Current API Endpoints

### Health

```http
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/version
```

### Farms

```http
POST   /api/v1/farms
GET    /api/v1/farms
GET    /api/v1/farms/{farm_id}
PATCH  /api/v1/farms/{farm_id}
DELETE /api/v1/farms/{farm_id}
```

### Fields

```http
POST   /api/v1/farms/{farm_id}/fields
GET    /api/v1/farms/{farm_id}/fields
GET    /api/v1/fields/{field_id}
PATCH  /api/v1/fields/{field_id}
DELETE /api/v1/fields/{field_id}
```

### Crops

```http
POST   /api/v1/fields/{field_id}/crops
GET    /api/v1/fields/{field_id}/crops
GET    /api/v1/crops/{crop_id}
PATCH  /api/v1/crops/{crop_id}
DELETE /api/v1/crops/{crop_id}
```

### Soil Profiles

```http
POST   /api/v1/fields/{field_id}/soil-profile
GET    /api/v1/fields/{field_id}/soil-profile
PATCH  /api/v1/soil-profiles/{soil_profile_id}
DELETE /api/v1/soil-profiles/{soil_profile_id}
```

### Weather Records

```http
POST   /api/v1/fields/{field_id}/weather-records
GET    /api/v1/fields/{field_id}/weather-records
GET    /api/v1/weather-records/{weather_record_id}
PATCH  /api/v1/weather-records/{weather_record_id}
DELETE /api/v1/weather-records/{weather_record_id}
```

### Sensor Readings

```http
POST   /api/v1/fields/{field_id}/sensor-readings
GET    /api/v1/fields/{field_id}/sensor-readings
GET    /api/v1/sensor-readings/{sensor_reading_id}
DELETE /api/v1/sensor-readings/{sensor_reading_id}
```

### Irrigation Events

```http
POST   /api/v1/fields/{field_id}/irrigation-events
GET    /api/v1/fields/{field_id}/irrigation-events
GET    /api/v1/irrigation-events/{event_id}
PATCH  /api/v1/irrigation-events/{event_id}
DELETE /api/v1/irrigation-events/{event_id}
```

### Yield Records

```http
POST   /api/v1/crops/{crop_id}/yield-records
GET    /api/v1/crops/{crop_id}/yield-records
GET    /api/v1/yield-records/{yield_record_id}
PATCH  /api/v1/yield-records/{yield_record_id}
DELETE /api/v1/yield-records/{yield_record_id}
```

### Disease Observations

```http
POST   /api/v1/crops/{crop_id}/disease-observations
GET    /api/v1/crops/{crop_id}/disease-observations
GET    /api/v1/fields/{field_id}/disease-observations
GET    /api/v1/disease-observations/{observation_id}
PATCH  /api/v1/disease-observations/{observation_id}
DELETE /api/v1/disease-observations/{observation_id}
```

### Satellite Observations

```http
POST   /api/v1/fields/{field_id}/satellite-observations
GET    /api/v1/fields/{field_id}/satellite-observations
GET    /api/v1/fields/{field_id}/satellite-observations/range
GET    /api/v1/fields/{field_id}/satellite-observations/latest
GET    /api/v1/satellite-observations/by-provider/{satellite_provider}
GET    /api/v1/satellite-observations/by-processing-level/{processing_level}
GET    /api/v1/satellite-observations/{observation_id}
PATCH  /api/v1/satellite-observations/{observation_id}
DELETE /api/v1/satellite-observations/{observation_id}
```

### Recommendations (Phase 13)

```http
POST   /api/v1/fields/{field_id}/recommendations
GET    /api/v1/fields/{field_id}/recommendations
GET    /api/v1/recommendations/{recommendation_id}
PATCH  /api/v1/recommendations/{recommendation_id}
DELETE /api/v1/recommendations/{recommendation_id}
```

### Alerts (Phase 13)

```http
POST   /api/v1/fields/{field_id}/alerts
GET    /api/v1/fields/{field_id}/alerts
GET    /api/v1/alerts/{alert_id}
PATCH  /api/v1/alerts/{alert_id}
DELETE /api/v1/alerts/{alert_id}
```

---

## Common Alembic Commands

| Command | Description |
|---|---|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Revert the most recent migration |
| `alembic current` | Show current migration revision |
| `alembic history` | Show full migration history |
| `alembic revision --autogenerate -m "description"` | Generate new migration from model changes |

---

## Troubleshooting

### DuplicateObjectError on migration

**Symptom:** `DuplicateObjectError: type "irrigation_method" already exists`

**Cause:** Prior failed migration left orphan PostgreSQL ENUM types. Phase 8 migration uses `checkfirst=True` during upgrade.

**Fix:**

```sql
-- Connect to the agriflow database and drop orphan types
DROP TYPE IF EXISTS irrigation_method;
DROP TYPE IF EXISTS water_source;
```

Then re-run:

```bash
alembic upgrade head
```

### Port already in use

```bash
# Check what is using port 8000
lsof -i :8000

# Or start on a different port
uvicorn app.main:app --reload --port 8001
```

### Database connection refused

Ensure Podman services are running:

```bash
podman compose up -d
podman compose ps
```

---

## Database Tables (Post Phase 13)

After `alembic upgrade head`, the database contains 13 domain tables plus `alembic_version`. Six of the domain tables are **TimescaleDB hypertables** (marked below).

```text
agriflow=# \dt
           List of relations
 Schema |          Name           | Type  |  Owner   
--------+-------------------------+-------+----------
 public | alembic_version         | table | agriflow
 public | alerts                  | table | agriflow
 public | crops                   | table | agriflow
 public | disease_observations    | table | agriflow  ← hypertable
 public | farms                   | table | agriflow
 public | fields                  | table | agriflow
 public | irrigation_events       | table | agriflow  ← hypertable
 public | recommendations         | table | agriflow
 public | satellite_observations  | table | agriflow  ← hypertable
 public | sensor_readings         | table | agriflow  ← hypertable
 public | soil_profiles           | table | agriflow
 public | weather_records         | table | agriflow  ← hypertable
 public | yield_records           | table | agriflow  ← hypertable
```

> Hypertables are managed by TimescaleDB. `SELECT * FROM timescaledb_information.hypertables;` lists them.

## PostgreSQL Enum Types

```text
agriflow=# \dT
          List of data types
 Schema |           Name             | Description 
--------+----------------------------+-------------
 public | alert_severity             | 
 public | alert_type                 | 
 public | crop_status                | 
 public | diagnosis_method           | 
 public | disease_severity           | 
 public | irrigation_method          | 
 public | processing_level           | 
 public | recommendation_priority    | 
 public | recommendation_status      | 
 public | recommendation_type        | 
 public | satellite_provider         | 
 public | sensor_type                | 
 public | soil_type                  | 
 public | spectral_index             | 
 public | water_source               | 
 public | yield_measurement_method   | 
```
