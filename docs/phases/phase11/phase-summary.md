# Phase 11 — Satellite Observation Domain

**Status:** ✅ Complete  
**Date:** June 2026  
**Migration revision:** `a1b2c3d4e5f6`  
**Revises:** `d3e7b2a9f1c4` (Phase 10 — disease_observations)

---

## What This Phase Achieved

Phase 11 introduced the SatelliteObservation domain — AGRIFLOW-AI's **Earth observation** domain. A SatelliteObservation stores a derived spectral index value (e.g., NDVI, EVI, NDWI) computed from satellite imagery for a specific field at a specific point in time.

Satellite-derived spectral indices are the highest-resolution synoptic view of crop health available to the platform. They provide:
- Canopy greenness trends (NDVI / EVI / LAI)
- Crop water stress signals (NDWI)
- Early nitrogen deficiency detection (NDRE)
- Soil-adjusted vegetation for sparse cover (SAVI / MSAVI)

Three major decisions established here:

1. **Field-anchored, not crop-anchored.** A satellite overpass covers a geographic area regardless of which crop is planted. Observations must persist across crop cycle boundaries — an NDVI time series crossing a planting date is still valid.
2. **`NUMERIC(9,6)` for index values — not `DOUBLE PRECISION`.** Spectral indices are derived values where 6 decimal places of precision is sufficient and exact decimal arithmetic in aggregates is more important than binary floating-point resolution (unlike `sensor_readings.sensor_value` which uses `DOUBLE PRECISION` for raw ADC fidelity).
3. **`processing_level` and `cloud_cover_percent` as explicit AI quality gates.** The schema bakes data quality metadata directly into the table so AI pipelines can enforce quality thresholds in SQL without external metadata joins.

> **Detailed engineering reference:** See [RPT-002-Satellite-Observation-Design.md](RPT-002-Satellite-Observation-Design.md) for full DDL, ORM parity table, index rationale, and query pattern analysis.

---

## Domain Hierarchy After Phase 11

```
Farm
└── Field
     ├── Crop
     │    ├── YieldRecord           (Phase 9)
     │    └── DiseaseObservation    (Phase 10)
     ├── SoilProfile                (Phase 4 — one-to-one)
     ├── WeatherRecord              (Phase 5 — mutable time-series)
     ├── SensorReading              (Phase 7 — append-only telemetry)
     ├── IrrigationEvent            (Phase 8 — mutable event)
     └── SatelliteObservation       ← introduced (mutable, field-level EO)
```

---

## Database Changes

**PostgreSQL ENUM types created:**

`satellite_provider` (8 values):

| Value | Platform | Nominal Resolution |
|-------|----------|--------------------|
| `SENTINEL_2` | ESA / Copernicus | 10 m |
| `LANDSAT_8` | USGS / NASA | 30 m |
| `LANDSAT_9` | USGS / NASA | 30 m |
| `PLANET` | Planet Labs | 3–5 m |
| `MODIS` | NASA | 250 m – 1 km |
| `SPOT` | Airbus | 1.5–6 m |
| `WORLDVIEW` | Maxar | 0.3–1.2 m |
| `UNKNOWN` | Not recorded | — |

`spectral_index` (8 values):

| Value | Full Name | Primary Agricultural Use |
|-------|-----------|--------------------------|
| `NDVI` | Normalized Difference Vegetation Index | General canopy greenness |
| `EVI` | Enhanced Vegetation Index | High-biomass areas |
| `NDWI` | Normalized Difference Water Index | Crop water stress |
| `SAVI` | Soil-Adjusted Vegetation Index | Sparse vegetation |
| `NDRE` | Normalized Difference Red Edge | Early N deficiency / stress |
| `LAI` | Leaf Area Index | Structural canopy measurement |
| `MSAVI` | Modified SAVI | Improved SAVI |
| `GNDVI` | Green NDVI | Chlorophyll concentration |

`processing_level` (4 values):

| Value | Meaning | AI Training Use |
|-------|---------|----------------|
| `L1C` | Top-of-Atmosphere (no atmospheric correction) | Excluded or down-weighted |
| `L2A` | Surface Reflectance (Bottom-of-Atmosphere) | Standard |
| `ARD` | Analysis-Ready Data (full correction + cloud mask) | Preferred |
| `DERIVED` | Composite / Mosaic | Trend analysis only |

**Table created:** `satellite_observations`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID (PK) | NOT NULL | UUID v4 |
| `field_id` | UUID (FK → fields.id, CASCADE) | NOT NULL | Parent field |
| `observed_at` | TIMESTAMPTZ | NOT NULL | Satellite overpass time — primary time key |
| `satellite_provider` | ENUM `satellite_provider` | NOT NULL | Data provenance and spatial resolution weight |
| `processing_level` | ENUM `processing_level` | NOT NULL | **AI quality gate 1** — must be `ARD` or `L2A` for training |
| `spectral_index` | ENUM `spectral_index` | NOT NULL | Measurement type |
| `index_value` | NUMERIC(9,6) | NOT NULL | Computed index value; range typically [-1.0, 1.0], up to ~10 for LAI |
| `cloud_cover_percent` | NUMERIC(5,2) | NULL | **AI quality gate 2** — filter `> 20%` for training |
| `resolution_m` | NUMERIC(8,2) | NULL | Pixel resolution in metres — enables resolution-aware feature engineering |
| `scene_id` | VARCHAR(255) | NULL | Provider scene ID — used for ingestion deduplication |
| `source_url` | VARCHAR(500) | NULL | COG / cloud storage URL for reprocessing traceability |
| `notes` | TEXT | NULL | Operator annotations |
| `created_at` | TIMESTAMPTZ | NOT NULL | Server-set |
| `updated_at` | TIMESTAMPTZ | NOT NULL | Server-set |

**Constraints and indexes (7 total):**

| Name | Type | Columns | Purpose |
|------|------|---------|---------|
| `fk_satellite_observations_field_id` | FK → `fields.id` CASCADE | `field_id` | Cascade delete |
| `pk_satellite_observations` | PRIMARY KEY | `id` | Named PK |
| `ix_satellite_observations_field_id` | B-tree | `field_id` | Field history queries |
| `ix_satellite_observations_observed_at` | B-tree | `observed_at` | Time-range scans; partition key |
| `ix_satellite_observations_satellite_provider` | B-tree | `satellite_provider` | Filter by provider for training consistency |
| `ix_satellite_observations_spectral_index` | B-tree | `spectral_index` | Single-index type filter |
| `ix_satellite_observations_scene_id` | B-tree | `scene_id` | Ingestion deduplication |
| `ix_satellite_observations_field_id_observed_at` | Compound B-tree | `(field_id, observed_at)` | **Primary API access pattern** |
| `ix_satellite_observations_spectral_index_observed_at` | Compound B-tree | `(spectral_index, observed_at)` | **Primary AI feature pipeline access pattern** |

---

## Phase 12 Upgrade (TimescaleDB)

`satellite_observations` was promoted to a **TimescaleDB hypertable** in Phase 12, partitioned by `observed_at` with a 7-day chunk interval (matching typical satellite overpass frequencies). Retention policy: 36 months (3 years of satellite imagery). The continuous aggregate `ca_satellite_daily` computes daily per-field NDVI/EVI/NDWI summaries for the AI feature engineering pipeline.

---

## APIs Delivered

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fields/{field_id}/satellite-observations` | Ingest a satellite observation |
| GET | `/api/v1/fields/{field_id}/satellite-observations` | List observations for a field (paginated) |
| GET | `/api/v1/satellite-observations/{observation_id}` | Get a single observation |
| PATCH | `/api/v1/satellite-observations/{observation_id}` | Update (correct `processing_level`, `cloud_cover_percent`, `scene_id`) |
| DELETE | `/api/v1/satellite-observations/{observation_id}` | Delete |

---

## Business Rules Enforced

| Rule | Where enforced |
|------|---------------|
| Field must exist before observation creation | `SatelliteObservationService` |
| `observed_at` must be timezone-aware | `SatelliteObservationService` |
| `observed_at` cannot be in the future | `SatelliteObservationService` |
| `cloud_cover_percent` must be in [0, 100] if provided | Pydantic schema validator |
| Observation is mutable (PATCH permitted) for data quality corrections | Service allows PATCH on `processing_level`, `cloud_cover_percent`, `index_value`, `scene_id`, `source_url`, `notes` |

---

## Architecture Established

**AI quality gate pattern** — Phase 11 established the practice of storing data quality metadata columns (`processing_level`, `cloud_cover_percent`) directly in the observation table so AI pipelines can enforce quality thresholds in SQL without external joins. This pattern should be followed by any future external data ingestion domain.

**Earth observation data model** — spectral indices as rows (not columns) means adding a new index type (e.g., `MSAVI2`) requires only an ENUM value addition, not a schema migration. Each `(field_id, spectral_index, observed_at)` triple uniquely identifies a measurement.

**Ingestion deduplication** — `scene_id` indexed for efficient idempotent ingestion. A batch ingestion pipeline can check `WHERE scene_id = ?` before inserting to prevent duplicate observations from the same satellite scene.

---

## Business Value

- NDVI / EVI trends for season-long canopy health monitoring
- NDWI water stress signals for Phase 13 `DROUGHT_STRESS` alert engine
- NDRE early-stress signal (7–14 days ahead of visual symptoms) for Phase 13 disease risk alerting
- LAI structural measurement for yield prediction models (Phase 12 AI engine)
- `ca_satellite_daily` continuous aggregate feeds real-time field dashboards

---

## What Was Deferred

- Automated satellite imagery ingestion pipeline (scheduled Sentinel-2 downloads)
- Multi-polygon field boundary intersections (PostGIS — Phase 18)
- Cloud-optimized GeoTIFF (COG) processing pipeline
- Automated API tests
