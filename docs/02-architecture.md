# AGRIFLOW-AI Technical Architecture

## Overview

AGRIFLOW-AI is an Agricultural Intelligence Platform built using a layered architecture that emphasizes maintainability, scalability, separation of concerns, and domain-driven development.

The platform currently implements Farm, Field, Crop, Soil Profile, Weather Intelligence, and Phase 6 AI Readiness Foundation domains and follows a Clean Architecture approach with clearly separated responsibilities across API, Service, Repository, and Database layers.

---

# Architecture Principles

AGRIFLOW-AI follows the following design principles:

* Clean Architecture
* SOLID Principles
* Repository Pattern
* Service Layer Pattern
* Separation of Concerns
* Dependency Injection
* Domain-Driven Design
* Migration-Driven Database Evolution
* API-First Development

---

# Technology Stack

| Layer                | Technology      |
| -------------------- | --------------- |
| Backend API          | FastAPI         |
| Language             | Python 3.12     |
| ORM                  | SQLAlchemy 2.x  |
| Database             | PostgreSQL      |
| Migration Framework  | Alembic         |
| Validation           | Pydantic        |
| Dependency Injection | FastAPI Depends |
| Containerization     | Docker          |
| Version Control      | Git + GitHub    |
| IDE                  | Cursor          |

---

# High-Level System Architecture

```text
Frontend
    │
    ▼
FastAPI API Layer
    │
    ▼
Service Layer
    │
    ▼
Repository Layer
    │
    ▼
SQLAlchemy ORM
    │
    ▼
PostgreSQL
```

---

# Current Domain Hierarchy

```text
Farm
 └── Field
      ├── Crop
      ├── SoilProfile
      └── WeatherRecord
```

Current business domains:

* Farm Management
* Field Management
* Crop Management
* Soil Intelligence
* Weather Intelligence

Future domains:
* Sensor Intelligence (Phase 7)
* Irrigation Intelligence (Phase 8)
* Yield Intelligence (Phase 9)
* Disease Observation (Phase 10)
* Satellite Observation (Phase 11)

Future AI Layer:
* Yield Prediction Engine
* Disease Prediction Engine
* Irrigation Recommendation Engine
* Farm Intelligence Platform

---

# Backend Project Structure

```text
backend/
├── app
│   ├── api
│   │   ├── farms
│   │   ├── fields
│   │   ├── crops
│   │   ├── soil_profiles
│   │   ├── health
│   │   └── version
│   │
│   ├── core
│   │   ├── config
│   │   ├── logging
│   │   └── security
│   │
│   ├── db
│   │   ├── migrations
│   │   ├── models
│   │   ├── repositories
│   │   └── session
│   │
│   ├── schemas
│   ├── services
│   └── main.py
│
├── Dockerfile
├── alembic.ini
└── requirements.txt
```

---

# Layered Architecture

AGRIFLOW-AI uses five primary layers.

## API Layer

Responsibilities:

* HTTP endpoint definitions
* Request handling
* Response handling
* Exception translation
* Dependency injection

Examples:

```text
app/api/fields
app/api/crops
app/api/soil_profiles
app/api/weather_records
```

The API layer should not contain business logic.

---

## Schema Layer

Responsibilities:

* Request validation
* Response serialization
* API contracts

Examples:

```text
FieldCreate
FieldUpdate
FieldResponse

CropCreate
CropUpdate
CropResponse

SoilProfileCreate
SoilProfileUpdate
SoilProfileResponse
```

The schema layer defines what data enters and exits the application.

---

## Service Layer

Responsibilities:

* Business rules
* Validation
* Domain orchestration
* Cross-domain coordination

Examples:

```text
FieldService
CropService
SoilProfileService
WeatherRecordService
```

Business rules belong here.

Examples:

* Farm must exist before Field creation
* Field must exist before Crop creation
* Field must exist before SoilProfile creation
* Only one SoilProfile allowed per Field
* Harvest date validation

---

## Repository Layer

Responsibilities:

* Database access
* CRUD operations
* Query execution
* Persistence

Examples:

```text
FarmRepository
FieldRepository
CropRepository
SoilProfileRepository
WeatherRecordRepository
```

Repositories should not contain business rules.

---

## Model Layer

Responsibilities:

* Database entity definitions
* Table mapping
* Relationships

Examples:

```text
Farm
Field
Crop
SoilProfile
```

Models represent PostgreSQL tables.

---

# Request Lifecycle

```text
Client Request
      │
      ▼
FastAPI Router
      │
      ▼
Pydantic Schema Validation
      │
      ▼
Service Layer
      │
      ▼
Repository Layer
      │
      ▼
SQLAlchemy ORM
      │
      ▼
PostgreSQL
```

Response Flow:

```text
PostgreSQL
      │
      ▼
SQLAlchemy ORM
      │
      ▼
Repository Layer
      │
      ▼
Service Layer
      │
      ▼
Response Schema
      │
      ▼
Client Response
```

---

# Dependency Injection Architecture

AGRIFLOW-AI uses FastAPI dependency injection.

```text
HTTP Request
      │
      ▼
Router
      │
      ▼
Dependency Provider
      │
      ▼
Service
      │
      ▼
Repository
      │
      ▼
AsyncSession
      │
      ▼
PostgreSQL
```

Benefits:

* Centralized transaction management
* Reduced coupling
* Improved testability
* Cleaner service construction

---

# Repository Pattern

AGRIFLOW-AI implements a generic repository architecture.

```text
BaseRepository
      │
      ├── FarmRepository
      ├── FieldRepository
      ├── CropRepository
      ├── SoilProfileRepository
      └── WeatherRecordRepository
```

Benefits:

* Reduced code duplication
* Consistent CRUD implementation
* Reusable query patterns
* Easier maintenance

---

# Database Architecture

Current tables:

```text
alembic_version
farms
fields
crops
soil_profiles
weather_records
```

Relationships:

```text
Farm (1)
   │
   ▼
Field (N)
   ├────────────► Crop (N)
   ├────────────► WeatherRecord (N)
   │
   └────────────► SoilProfile (1)
```

---

# Database Migration Architecture

AGRIFLOW-AI uses Alembic for schema evolution.

Migration sequence:

```text
001_create_farms_table
002_create_fields_table
003_create_crops_table
004_create_weather_records_table
005_add_soil_profiles_table
```

Migration flow:

```text
Model Change
      │
      ▼
Alembic Revision
      │
      ▼
Migration Script
      │
      ▼
Database Upgrade
```

Benefits:

* Version-controlled schema changes
* Repeatable deployments
* Environment consistency

---

# Current API Architecture

Implemented APIs:

## Health

* GET /api/v1/health/live
* GET /api/v1/health/ready

## Version

* GET /api/v1/version

## Fields

* POST   /api/v1/farms/{farm_id}/fields
* GET    /api/v1/farms/{farm_id}/fields
* GET    /api/v1/fields/{field_id}
* PATCH  /api/v1/fields/{field_id}
* DELETE /api/v1/fields/{field_id}

## Crops

* POST   /api/v1/fields/{field_id}/crops
* GET    /api/v1/fields/{field_id}/crops
* GET    /api/v1/crops/{crop_id}
* PATCH  /api/v1/crops/{crop_id}
* DELETE /api/v1/crops/{crop_id}

## Soil Profiles

* POST   /api/v1/fields/{field_id}/soil-profile
* GET    /api/v1/fields/{field_id}/soil-profile
* PATCH  /api/v1/soil-profiles/{soil_profile_id}
* DELETE /api/v1/soil-profiles/{soil_profile_id}

## Weather Records

* POST   /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/fields/{field_id}/weather-records
* GET    /api/v1/weather-records/{weather_record_id}
* PATCH  /api/v1/weather-records/{weather_record_id}
* DELETE /api/v1/weather-records/{weather_record_id}

---

# Current Platform Status

Completed Domains:

* Farm Domain
* Field Domain
* Crop Domain
* Soil Intelligence Domain
* Weather Intelligence Domain

Implemented Architecture:

* Model Layer
* Schema Layer
* Repository Layer
* Service Layer
* API Layer
* Dependency Injection
* PostgreSQL Integration
* Alembic Migration Framework

---

# Future Architecture Evolution

Planned domains:

```text
Farm
 └── Field
      ├── Crop
      ├── SoilProfile
      ├── Weather Records
      ├── Sensor Readings
      ├── Irrigation Events
      ├── Yield Records
      └── Satellite Observations
```

Future architectural capabilities:

* PostGIS Integration
* Event-Driven Architecture
* Message Queues
* AI Recommendation Engine
* Data Lake Integration
* MLOps Platform
* Digital Twin Architecture
* Farm Copilot
* Advanced Observability

---

# Architectural Vision

AGRIFLOW-AI is evolving from a farm management platform into a comprehensive Agricultural Intelligence Platform.

The architecture is designed to support the long-term vision of:

* Precision Agriculture
* Predictive Agriculture
* AI-Assisted Farming
* Agricultural Digital Twins
* Autonomous Agricultural Intelligence

while maintaining clear separation of concerns, scalability, and maintainability.
