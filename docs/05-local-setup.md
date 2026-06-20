# AGRIFLOW-AI Local Development Setup

**Last Updated:** Phase 8 — Irrigation Management Domain Complete  
**Status:** Current

---

## Prerequisites

| Tool | Minimum Version | Purpose |
|---|---|---|
| Docker | 24.x | Container runtime |
| Docker Compose | 2.x | Service orchestration |
| Python | 3.12 | Backend runtime |
| Git | 2.x | Version control |

---

## Repository Structure

```text
AGRIFLOW-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── fields/
│   │   │   ├── crops/
│   │   │   ├── soil_profiles/
│   │   │   ├── weather_records/
│   │   │   ├── sensor_readings/
│   │   │   ├── irrigation_events/   ← Phase 8
│   │   │   ├── health/
│   │   │   └── version/
│   │   ├── core/
│   │   │   ├── config/
│   │   │   ├── enums.py             ← Shared enums (SensorType, IrrigationMethod, WaterSource)
│   │   │   └── logging/
│   │   ├── db/
│   │   │   ├── migrations/
│   │   │   │   └── versions/        ← 8 migration files
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
└── docker-compose.yml
```

---

## 1. Clone Repository

```bash
git clone <repository-url>
cd AGRIFLOW-AI
```

---

## 2. Start Infrastructure Services

Docker Compose starts PostgreSQL (and any other configured services):

```bash
docker compose up -d
```

Verify services are running:

```bash
docker compose ps
```

Expected: PostgreSQL container in `Up` state.

**Database connection defaults:**

| Parameter | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| Database | `agriflow` |
| User | `agriflow` |
| Password | See `.env` file |

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

This applies all migrations in order:

```text
001_create_farms_table
002_create_fields_table
003_create_crops_table
13aabbe35d51_add_soil_profiles_table
004_create_weather_records_table
005_add_p1_ai_readiness_columns
006_create_sensor_readings_table
235a51cdf901_create_irrigation_events_table   ← Phase 8
```

Verify migration status:

```bash
alembic current
```

Expected output includes `235a51cdf901 (head)`.

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

The Swagger UI lists all implemented endpoints across all 8 phases.

---

## Current API Endpoints

### Health

```http
GET /api/v1/health/live
GET /api/v1/health/ready
GET /api/v1/version
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

### Sensor Readings (Phase 7)

```http
POST   /api/v1/fields/{field_id}/sensor-readings
GET    /api/v1/fields/{field_id}/sensor-readings
GET    /api/v1/sensor-readings/{sensor_reading_id}
DELETE /api/v1/sensor-readings/{sensor_reading_id}
```

### Irrigation Events (Phase 8)

```http
POST   /api/v1/fields/{field_id}/irrigation-events
GET    /api/v1/fields/{field_id}/irrigation-events
GET    /api/v1/irrigation-events/{event_id}
PATCH  /api/v1/irrigation-events/{event_id}
DELETE /api/v1/irrigation-events/{event_id}
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

Ensure Docker services are running:

```bash
docker compose up -d
docker compose ps
```

---

## Database Tables (Post Phase 8)

```text
agriflow=# \dt
           List of relations
 Schema |        Name        | Type  |  Owner   
--------+--------------------+-------+----------
 public | alembic_version    | table | agriflow
 public | crops              | table | agriflow
 public | farms              | table | agriflow
 public | fields             | table | agriflow
 public | irrigation_events  | table | agriflow
 public | sensor_readings    | table | agriflow
 public | soil_profiles      | table | agriflow
 public | weather_records    | table | agriflow
```

## PostgreSQL Enum Types

```text
agriflow=# \dT
          List of data types
 Schema |       Name        | Description 
--------+-------------------+-------------
 public | crop_status       | 
 public | irrigation_method | 
 public | sensor_type       | 
 public | soil_type         | 
 public | water_source      | 
```
