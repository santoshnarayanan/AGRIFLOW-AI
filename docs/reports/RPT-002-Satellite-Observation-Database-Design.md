# RPT-002 — Satellite Observation Database Design

**Document Type:** Post-Migration Engineering Report  
**Phase:** 11 — Satellite Observation Domain  
**Step:** D — Alembic Migration  
**Migration Revision:** `a1b2c3d4e5f6`  
**Revises:** `d3e7b2a9f1c4` (Phase 10 — Disease Observation)  
**Migration File:** `backend/app/db/migrations/versions/a1b2c3d4e5f6_create_satellite_observations_table.py`  
**ORM File:** `backend/app/db/models/satellite_observation.py`  
**Status:** Delivered  
**Version:** 1.0  
**Date:** June 2026  
**Audience:** Software Engineers, Data Engineers, ML Engineers, Solution Architects, Future Contributors, Future AI Agents

---

## Table of Contents

1. [Overview](#1-overview)
2. [Domain Position](#2-domain-position)
3. [Table Schema Reference](#3-table-schema-reference)
4. [Column Design Decisions](#4-column-design-decisions)
5. [PostgreSQL ENUM Types](#5-postgresql-enum-types)
6. [Constraints](#6-constraints)
7. [Index Strategy](#7-index-strategy)
8. [Migration Lifecycle](#8-migration-lifecycle)
9. [ORM–Migration Parity](#9-ormmigration-parity)
10. [Query Patterns](#10-query-patterns)
11. [AI & Feature Engineering Readiness](#11-ai--feature-engineering-readiness)
12. [TimescaleDB Promotion Readiness](#12-timescaledb-promotion-readiness)
13. [Future Architecture Compatibility](#13-future-architecture-compatibility)
14. [Migration Revision Chain](#14-migration-revision-chain)
15. [Decisions and Rationale Summary](#15-decisions-and-rationale-summary)

---

## 1. Overview

This report documents the database design decisions, DDL, and engineering rationale for the `satellite_observations` table introduced in Phase 11, Step D of AGRIFLOW-AI.

The migration creates:

- **3 PostgreSQL native ENUM types** — `satellite_provider`, `spectral_index`, `processing_level`
- **1 table** — `satellite_observations`
- **1 foreign key constraint** — `fk_satellite_observations_field_id`
- **1 primary key constraint** — `pk_satellite_observations`
- **7 indexes** — 5 individual B-tree, 2 compound B-tree

The table stores derived spectral index observations computed from satellite imagery, anchored to agricultural fields in the AGRIFLOW-AI domain hierarchy.

---

## 2. Domain Position

### 2.1 Hierarchy Placement

```
Farm
 └── Field
      ├── Crop
      │    ├── YieldRecord           (Phase 9  — mutable, per crop cycle)
      │    └── DiseaseObservation    (Phase 10 — mutable, per crop cycle)
      ├── SoilProfile                (Phase 4  — one-to-one)
      ├── WeatherRecord              (Phase 5  — time-series)
      ├── SensorReading              (Phase 7  — append-only telemetry)
      ├── IrrigationEvent            (Phase 8  — mutable, operational)
      └── SatelliteObservation       (Phase 11 — mutable, field-level ← NEW)
```

### 2.2 Field-Anchored vs Crop-Anchored

`SatelliteObservation` anchors on `Field`, not `Crop`. This is a deliberate design decision that diverges from Phase 9 (`YieldRecord`) and Phase 10 (`DiseaseObservation`), which both anchor on `Crop`.

**Rationale:** Satellite imagery is captured by a scheduled overpass that covers a geographic area. The satellite does not know or care which crop is planted in the field at the time of acquisition. A field's satellite observation history must persist across crop cycle boundaries — an NDVI time series that crosses a planting date is still valid and useful.

The structural analogy is:
- `SensorReading` (Phase 7): field-level IoT telemetry → anchored on `Field`
- `IrrigationEvent` (Phase 8): field-level operational event → anchored on `Field`
- `SatelliteObservation` (Phase 11): field-level Earth observation → anchored on `Field`

### 2.3 Mutability

`SatelliteObservation` is **mutable**. PATCH operations are permitted to allow data engineers and operators to correct:

- `processing_level` when imagery is reprocessed (L1C → L2A upgrade)
- `cloud_cover_percent` when a revised cloud mask is applied
- `index_value` when a computation error is identified
- `source_url` and `scene_id` for provenance traceability

This contrasts with `SensorReading` (Phase 7), which is immutable (append-only telemetry).

---

## 3. Table Schema Reference

### 3.1 Full DDL

```sql
CREATE TABLE satellite_observations (
    -- Primary key
    id                  UUID        NOT NULL,

    -- Domain anchor
    field_id            UUID        NOT NULL,

    -- Primary time key
    observed_at         TIMESTAMPTZ NOT NULL,

    -- Source classification
    satellite_provider  satellite_provider  NOT NULL,
    processing_level    processing_level    NOT NULL,

    -- Spectral measurement
    spectral_index      spectral_index      NOT NULL,
    index_value         NUMERIC(9, 6)       NOT NULL,

    -- Image quality metadata
    cloud_cover_percent NUMERIC(5, 2)       NULL,
    resolution_m        NUMERIC(8, 2)       NULL,

    -- Provenance
    scene_id            VARCHAR(255)        NULL,
    source_url          VARCHAR(500)        NULL,

    -- Operator metadata
    notes               TEXT                NULL,

    -- Audit timestamps (PostgreSQL server-side)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT pk_satellite_observations PRIMARY KEY (id),
    CONSTRAINT fk_satellite_observations_field_id
        FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
);
```

### 3.2 Column Summary

| Column | PostgreSQL Type | Nullable | Default | Description |
|---|---|---|---|---|
| `id` | `UUID` | NOT NULL | — | UUID v4 primary key |
| `field_id` | `UUID` | NOT NULL | — | FK → `fields.id` |
| `observed_at` | `TIMESTAMPTZ` | NOT NULL | — | Satellite overpass timestamp |
| `satellite_provider` | `satellite_provider` | NOT NULL | — | Imagery source platform |
| `processing_level` | `processing_level` | NOT NULL | — | Data processing tier |
| `spectral_index` | `spectral_index` | NOT NULL | — | Derived index type |
| `index_value` | `NUMERIC(9,6)` | NOT NULL | — | Computed index value |
| `cloud_cover_percent` | `NUMERIC(5,2)` | NULL | — | Scene cloud coverage % |
| `resolution_m` | `NUMERIC(8,2)` | NULL | — | Pixel resolution in metres |
| `scene_id` | `VARCHAR(255)` | NULL | — | Provider scene identifier |
| `source_url` | `VARCHAR(500)` | NULL | — | COG / product URL |
| `notes` | `TEXT` | NULL | — | Operator annotations |
| `created_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | Row creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL | `now()` | Row last-update timestamp |

---

## 4. Column Design Decisions

### 4.1 `id` — UUID v4 Primary Key

**Type:** `UUID`

Consistent with the `AuditableModel` base class used across all AGRIFLOW-AI domain models. UUID v4 primary keys prevent sequential ID enumeration in public APIs and are compatible with distributed write patterns (future Redpanda ingestion pipeline can generate IDs client-side without a database round-trip).

### 4.2 `field_id` — Foreign Key

**Type:** `UUID NOT NULL`  
**References:** `fields.id ON DELETE CASCADE`

Direct child of `Field`. No denormalization is required (unlike `YieldRecord` and `DiseaseObservation` which carry a denormalized `field_id` as a shortcut through the `Crop` ancestor). `field_id` is the native FK anchor.

### 4.3 `observed_at` — Primary Time Key

**Type:** `TIMESTAMPTZ NOT NULL`

The timezone-aware timestamp of the satellite overpass (not the observation submission time). This is the primary ordering key for all list queries (`observed_at DESC`) and the designated partition key for future TimescaleDB hypertable promotion.

**Why `TIMESTAMPTZ` and not `TIMESTAMP`:** Satellite imagery timestamps are defined in UTC. Using `TIMESTAMPTZ` (PostgreSQL `timestamp with time zone`) ensures that timestamps from different UTC offsets are stored, compared, and sorted correctly without ambiguity. Naive timestamps (`TIMESTAMP`) would silently ignore timezone offsets, causing ordering errors in cross-timezone deployments.

**Validation (enforced at service layer):**
- Must be timezone-aware; naive datetimes are rejected with HTTP 422
- Must not be in the future (satellite overpasses cannot be logged before they happen)

### 4.4 `satellite_provider` — Source Classification

**Type:** `satellite_provider ENUM NOT NULL`

Encodes which satellite platform captured the imagery. Acts as a data provenance and quality weighting attribute in AI training pipelines — SENTINEL_2 at 10 m carries different spatial information content than MODIS at 250 m.

See [Section 5](#5-postgresql-enum-types) and REPORT-001 Section 6 for full provider comparison.

### 4.5 `processing_level` — Data Quality Tier

**Type:** `processing_level ENUM NOT NULL`

Records the processing state of the source data before the spectral index was computed. This is a critical data quality gate: `L1C` (top-of-atmosphere) values cannot be meaningfully compared across dates or regions; `L2A`/`ARD` (surface reflectance) observations are normalized and directly comparable.

The column is NOT NULL — every observation must declare its processing provenance. The AI feature engineering pipeline uses this column to enforce quality thresholds (`WHERE processing_level IN ('ARD', 'L2A')`).

### 4.6 `spectral_index` — Measurement Discriminator

**Type:** `spectral_index ENUM NOT NULL`

The primary measurement classification — the satellite equivalent of `SensorType` in the `sensor_readings` table. Without this column, a value of `0.73` has no meaning; with it, `0.73` as `NDVI` means a moderately healthy canopy.

### 4.7 `index_value` — Computed Index Value

**Type:** `NUMERIC(9, 6) NOT NULL`

**Precision rationale:**

| Index | Typical Range | Example Value |
|---|---|---|
| NDVI, EVI, NDWI, SAVI, NDRE, MSAVI, GNDVI | [-1.0, 1.0] | 0.723456 |
| LAI | [0, ~10] | 3.820000 |

`NUMERIC(9, 6)` provides:
- Up to 3 digits before the decimal point (covers LAI up to 999 — far exceeds realistic values)
- 6 decimal places (sufficient for all computed index precision)
- Exact decimal representation — avoids IEEE-754 floating-point accumulation errors in `SUM`, `AVG`, and time-series aggregate queries used by the Feature Store

`DOUBLE PRECISION` was considered and rejected. While sensor telemetry (`sensor_readings.sensor_value`) uses `DOUBLE PRECISION` to preserve raw ADC resolution, spectral indices are derived values where 6 decimal places of precision is sufficient and exact arithmetic is more important than 15-digit binary floating-point storage.

### 4.8 `cloud_cover_percent` — Image Quality Filter

**Type:** `NUMERIC(5, 2) NULL`

Optional. Percentage of the scene covered by cloud or cloud shadow. Valid range: [0, 100]. Stored with 2 decimal places — consistent with `affected_area_percent` in `disease_observations` (Phase 10).

This column is the primary data quality filter for AI training pipelines:
```sql
-- Typical AI feature pipeline quality gate
SELECT * FROM satellite_observations
WHERE cloud_cover_percent < 20.0
  AND processing_level IN ('ARD', 'L2A');
```

**Nullable rationale:** Not all data providers or processing pipelines compute a per-scene cloud cover estimate. Ingested data without cloud mask information is stored with `NULL` rather than a synthetic value, preserving data quality transparency.

### 4.9 `resolution_m` — Spatial Resolution

**Type:** `NUMERIC(8, 2) NULL`

Effective pixel resolution of the source imagery in metres. Captured to enable resolution-aware spatial feature engineering — NDVI computed from a 10 m pixel is not directly comparable to NDVI from a 250 m pixel when used as input to a spatially explicit model.

| Provider | Typical `resolution_m` |
|---|---|
| WORLDVIEW | 0.30 – 1.24 |
| PLANET | 3.00 – 5.00 |
| SENTINEL_2 | 10.00 |
| LANDSAT_8/9 | 30.00 |
| MODIS | 250.00 – 1000.00 |

**Nullable rationale:** `resolution_m` can be inferred from `satellite_provider` in many cases and may not be explicitly recorded in older ingested data. It is nullable to avoid blocking ingestion when metadata is incomplete.

### 4.10 `scene_id` — Source Traceability

**Type:** `VARCHAR(255) NULL`

Provider-assigned scene or tile identifier. Used by the ingestion pipeline for:
- Deduplication — prevent the same scene being ingested twice
- Reprocessing — identify which scenes need to be re-fetched when a new processing algorithm is deployed
- Provenance audit — trace an index value back to its original imagery

Example values by provider:
- Sentinel-2: `S2A_MSIL2A_20240615T102021_N0510_R065_T32UMD_20240615T130512`
- Landsat-9: `LC09_L2SP_197029_20240615_20240617_02_T1`
- Planet: `20240615_082341_1025`

The `scene_id` index (`ix_satellite_observations_scene_id`) supports efficient deduplication checks during batch ingestion.

### 4.11 `source_url` — COG Location

**Type:** `VARCHAR(500) NULL`

URL or cloud storage path (e.g., S3, Azure Blob Storage, Google Cloud Storage) pointing to the Cloud Optimised GeoTIFF (COG) or derived product. Supports reprocessing workflows and ingestion pipeline traceability.

`VARCHAR(500)` accommodates long pre-signed cloud storage URLs. Nullable — populated when available from the provider API, omitted for historical data ingestion.

### 4.12 `notes` — Operator Annotations

**Type:** `TEXT NULL`

Free-text field for pipeline and operator annotations. Examples: "Reprocessed with improved cloud mask v2.1", "Manual correction — EVI sensor glitch on eastern edge", "Preliminary L1C until L2A product released."

### 4.13 `created_at` / `updated_at` — Audit Timestamps

**Type:** `TIMESTAMPTZ NOT NULL DEFAULT now()`

Server-side audit timestamps from the `AuditableModel` base class. Set by PostgreSQL `now()`, not the application clock, avoiding clock-skew issues in distributed deployments. `updated_at` is refreshed by the ORM `onupdate=func.now()` trigger on every PATCH operation.

---

## 5. PostgreSQL ENUM Types

### 5.1 Overview

Three native PostgreSQL ENUM types are created by this migration. All follow the pattern established in ADR-008-01 (`postgresql.ENUM` with `create_type=False`, explicit `.create()` / `.drop()` lifecycle management).

### 5.2 `satellite_provider`

```sql
CREATE TYPE satellite_provider AS ENUM (
    'SENTINEL_2', 'LANDSAT_8', 'LANDSAT_9', 'PLANET',
    'MODIS', 'SPOT', 'WORLDVIEW', 'UNKNOWN'
);
```

| Value | Platform | Nominal Resolution |
|---|---|---|
| `SENTINEL_2` | ESA / Copernicus | 10 m |
| `LANDSAT_8` | USGS / NASA | 30 m |
| `LANDSAT_9` | USGS / NASA | 30 m |
| `PLANET` | Planet Labs | 3–5 m |
| `MODIS` | NASA | 250 m – 1 km |
| `SPOT` | Airbus Defence & Space | 1.5–6 m |
| `WORLDVIEW` | Maxar Technologies | 0.3–1.2 m |
| `UNKNOWN` | Not recorded | — |

### 5.3 `spectral_index`

```sql
CREATE TYPE spectral_index AS ENUM (
    'NDVI', 'EVI', 'NDWI', 'SAVI', 'NDRE', 'LAI', 'MSAVI', 'GNDVI'
);
```

| Value | Full Name | Primary Use |
|---|---|---|
| `NDVI` | Normalized Difference Vegetation Index | General canopy greenness |
| `EVI` | Enhanced Vegetation Index | High-biomass correction |
| `NDWI` | Normalized Difference Water Index | Crop water stress |
| `SAVI` | Soil-Adjusted Vegetation Index | Sparse vegetation |
| `NDRE` | Normalized Difference Red Edge | Early stress / N deficiency |
| `LAI` | Leaf Area Index | Structural canopy measure |
| `MSAVI` | Modified Soil-Adjusted Vegetation Index | Improved SAVI |
| `GNDVI` | Green NDVI | Chlorophyll concentration |

### 5.4 `processing_level`

```sql
CREATE TYPE processing_level AS ENUM (
    'L1C', 'L2A', 'ARD', 'DERIVED'
);
```

| Value | Full Name | Atmospheric Correction | AI Training Use |
|---|---|---|---|
| `L1C` | Top-of-Atmosphere Reflectance | None | Down-weighted / excluded |
| `L2A` | Surface Reflectance (BOA) | Full | Standard |
| `ARD` | Analysis-Ready Data | Full + cloud mask + BRDF | Preferred |
| `DERIVED` | Composite / Mosaic | Inherited | Trend analysis only |

### 5.5 ENUM Lifecycle Management

The `postgresql.ENUM` with `create_type=False` pattern is used for all three enums. This is the project-standard pattern (ADR-008-01) established in Phase 8:

```python
# Module-level — enum object manages its own lifecycle
satellite_provider_enum = postgresql.ENUM(
    "SENTINEL_2", ...,
    name="satellite_provider",
    create_type=False,          # prevents op.create_table() from emitting CREATE TYPE
)

# upgrade(): enum must exist before the table that references it
satellite_provider_enum.create(op.get_bind(), checkfirst=True)

# downgrade(): enum must be dropped after the table is removed
satellite_provider_enum.drop(op.get_bind(), checkfirst=False)
```

**Why `postgresql.ENUM` instead of `sa.Enum`?**  
`sa.Enum._copy()` — called internally by `op.create_table()` when the type is cloned into the temporary `Table` object — does not forward `create_type=False` in SQLAlchemy 2.0.x. This causes a `DuplicateObjectError` on fresh databases when the explicit `.create()` call above has already created the type. `postgresql.ENUM` preserves `create_type=False` through `_set_table()` and `_copy()`, eliminating this problem.

**Why `checkfirst=True` on create?**  
Makes the migration idempotent for the ENUM creation step. If a previous partial migration left the type in the database, the upgrade does not fail.

**Why `checkfirst=False` on drop?**  
Downgrade should be exact and explicit. If the type does not exist during downgrade, something has gone wrong and the error should surface rather than be silently swallowed.

---

## 6. Constraints

### 6.1 Primary Key

```sql
CONSTRAINT pk_satellite_observations PRIMARY KEY (id)
```

Named PK constraint, consistent with all AGRIFLOW-AI table conventions (`pk_{table_name}`).

### 6.2 Foreign Key

```sql
CONSTRAINT fk_satellite_observations_field_id
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE
```

`ON DELETE CASCADE` means that deleting a `Field` row atomically removes all its `SatelliteObservation` rows. This is the database-level enforcement of the parent-child relationship.

**Complementary ORM cascade:** The SQLAlchemy `Field.satellite_observations` relationship carries `cascade="all, delete-orphan"`, which handles cascading deletion when `Field` records are deleted via the SQLAlchemy session. The database-level FK cascade provides defence in depth for direct SQL deletes that bypass the ORM.

### 6.3 NOT NULL Enforcement

The following columns are `NOT NULL`:

| Column | Reason |
|---|---|
| `id` | Primary key |
| `field_id` | Domain anchor — no orphan observations |
| `observed_at` | Primary time key — cannot be absent |
| `satellite_provider` | Every observation must declare its source |
| `processing_level` | Every observation must declare its quality tier |
| `spectral_index` | Every observation must identify what was measured |
| `index_value` | The measurement itself — cannot be absent |
| `created_at` | Audit trail completeness |
| `updated_at` | Audit trail completeness |

### 6.4 ENUM Constraints

PostgreSQL ENUM columns implicitly reject any string not in the type's member set. Attempting to insert `satellite_provider = 'INVALID'` raises:

```
ERROR:  invalid input value for enum satellite_provider: "INVALID"
```

This is independent of application-layer validation and provides a third line of defence (after Pydantic schema validation and SQLAlchemy enum type checking).

---

## 7. Index Strategy

### 7.1 Summary

| Index Name | Columns | Type | Primary Query Pattern |
|---|---|---|---|
| `ix_satellite_observations_field_id` | `field_id` | B-tree | FK lookup; all observations for a field |
| `ix_satellite_observations_observed_at` | `observed_at` | B-tree | Time-range scans; TimescaleDB partition key |
| `ix_satellite_observations_satellite_provider` | `satellite_provider` | B-tree | AI training filter by provider |
| `ix_satellite_observations_spectral_index` | `spectral_index` | B-tree | Single-index type filter |
| `ix_satellite_observations_scene_id` | `scene_id` | B-tree | Provenance lookup; deduplication |
| `ix_satellite_observations_field_id_observed_at` | `field_id, observed_at` | B-tree | **Field history — primary access** |
| `ix_satellite_observations_spectral_index_observed_at` | `spectral_index, observed_at` | B-tree | **AI feature pipeline — primary access** |

### 7.2 Compound Index 1 — `field_id_observed_at`

```sql
CREATE INDEX ix_satellite_observations_field_id_observed_at
    ON satellite_observations (field_id, observed_at);
```

**Supports:**
- `GET /api/v1/fields/{field_id}/satellite-observations` — paginated field history
- "Get all observations for this field in the last growing season"
- TimescaleDB chunk exclusion after hypertable promotion (time range scans on a single field)

```sql
-- Canonical query this index supports
SELECT * FROM satellite_observations
WHERE field_id = '...'
  AND observed_at BETWEEN '2024-04-01' AND '2024-09-30'
ORDER BY observed_at DESC;
```

This index covers the most common read operation — fetching the observation history of a specific field for a time window.

### 7.3 Compound Index 2 — `spectral_index_observed_at`

```sql
CREATE INDEX ix_satellite_observations_spectral_index_observed_at
    ON satellite_observations (spectral_index, observed_at);
```

**Supports:**
- "Get all NDVI observations in the last 12 months for Phase 12 training batch"
- "Get all NDRE observations since Jan 2024 for Phase 13 early-stress feature engineering"
- Index-specific time-series analytics

```sql
-- Canonical query this index supports (AI feature extraction)
SELECT field_id, observed_at, index_value, satellite_provider, processing_level
FROM satellite_observations
WHERE spectral_index = 'NDVI'
  AND processing_level IN ('ARD', 'L2A')
  AND cloud_cover_percent < 20.0
  AND observed_at >= '2024-01-01'
ORDER BY field_id, observed_at;
```

This index is the primary access pattern for the Phase 12–14 AI feature extraction pipelines, which query observations by index type across all fields in a time window.

### 7.4 Individual Index Rationale

**`ix_satellite_observations_satellite_provider`**  
Supports AI training data quality filters: `WHERE satellite_provider = 'SENTINEL_2'`. Allows the feature pipeline to restrict training features to a single provider's data for consistency.

**`ix_satellite_observations_spectral_index`** (individual)  
Covers single-predicate queries before the compound index is considered: `WHERE spectral_index = 'NDVI'` without a time constraint.

**`ix_satellite_observations_scene_id`**  
Supports the ingestion pipeline deduplication check: `WHERE scene_id = '...'`. Without this index, every ingestion event would trigger a full table scan to detect duplicate scenes.

**`ix_satellite_observations_observed_at`** (individual)  
Covers temporal range scans without a field or index predicate: `WHERE observed_at > NOW() - INTERVAL '30 days'`. Also serves as the TimescaleDB partition key scan pattern after Phase 12 hypertable promotion.

### 7.5 Naming Convention

```
ix_{table_name}_{column(s)}
```

Single-column indexes are created via `op.f("ix_{table}_{column}")`, applying Alembic's naming convention prefix automatically. Compound indexes use explicit string names that match the ORM `__table_args__` definitions exactly, ensuring ORM and migration stay in sync.

---

## 8. Migration Lifecycle

### 8.1 `upgrade()` Execution Order

```
1. CREATE TYPE satellite_provider   (checkfirst=True)
2. CREATE TYPE spectral_index        (checkfirst=True)
3. CREATE TYPE processing_level      (checkfirst=True)
4. CREATE TABLE satellite_observations
   ├── all columns
   ├── CONSTRAINT pk_satellite_observations PRIMARY KEY (id)
   └── CONSTRAINT fk_satellite_observations_field_id FK → fields.id CASCADE
5. CREATE INDEX ix_satellite_observations_field_id
6. CREATE INDEX ix_satellite_observations_observed_at
7. CREATE INDEX ix_satellite_observations_satellite_provider
8. CREATE INDEX ix_satellite_observations_spectral_index
9. CREATE INDEX ix_satellite_observations_scene_id
10. CREATE INDEX ix_satellite_observations_field_id_observed_at
11. CREATE INDEX ix_satellite_observations_spectral_index_observed_at
```

### 8.2 `downgrade()` Execution Order

```
1. DROP INDEX ix_satellite_observations_spectral_index_observed_at
2. DROP INDEX ix_satellite_observations_field_id_observed_at
3. DROP INDEX ix_satellite_observations_scene_id
4. DROP INDEX ix_satellite_observations_spectral_index
5. DROP INDEX ix_satellite_observations_satellite_provider
6. DROP INDEX ix_satellite_observations_observed_at
7. DROP INDEX ix_satellite_observations_field_id
8. DROP TABLE satellite_observations
   (PK and FK constraints drop automatically with the table)
9. DROP TYPE processing_level   (checkfirst=False)
10. DROP TYPE spectral_index     (checkfirst=False)
11. DROP TYPE satellite_provider (checkfirst=False)
```

**Why indexes before table?** PostgreSQL drops indexes when a table is dropped. Explicit `DROP INDEX` before `DROP TABLE` keeps the downgrade semantically clear and avoids implicit side effects.

**Why enum types after table?** PostgreSQL ENUM types are schema-level objects independent of any table. They must be dropped explicitly and after the columns that reference them are gone.

**Why reverse ENUM creation order on drop?** Symmetric consistency and defensive correctness. If dependencies between types ever develop (e.g., a type referencing another), reverse-order drop is always safe.

### 8.3 Idempotency

The migration is idempotent for ENUM creation (`checkfirst=True`). The table creation and index creation are not idempotent by default — running `upgrade()` twice on the same database will fail at `CREATE TABLE`. This is the expected Alembic behaviour; idempotency is provided by the migration framework's revision tracking (`alembic_version` table), not by individual migration scripts.

---

## 9. ORM–Migration Parity

This section verifies that every element of the ORM model is faithfully represented in the migration.

### 9.1 Column Parity

| ORM Column | ORM Type | Migration Column | Migration Type | Match |
|---|---|---|---|---|
| `id` | `UUID(as_uuid=True)` | `id` | `postgresql.UUID(as_uuid=True)` | ✅ |
| `field_id` | `UUID(as_uuid=True)` | `field_id` | `postgresql.UUID(as_uuid=True)` | ✅ |
| `observed_at` | `DateTime(timezone=True)` | `observed_at` | `sa.DateTime(timezone=True)` | ✅ |
| `satellite_provider` | `Enum(SatelliteProvider)` | `satellite_provider` | `satellite_provider_enum` | ✅ |
| `processing_level` | `Enum(ProcessingLevel)` | `processing_level` | `processing_level_enum` | ✅ |
| `spectral_index` | `Enum(SpectralIndex)` | `spectral_index` | `spectral_index_enum` | ✅ |
| `index_value` | `Numeric(9, 6)` | `index_value` | `sa.Numeric(9, 6)` | ✅ |
| `cloud_cover_percent` | `Numeric(5, 2) NULL` | `cloud_cover_percent` | `sa.Numeric(5, 2) NULL` | ✅ |
| `resolution_m` | `Numeric(8, 2) NULL` | `resolution_m` | `sa.Numeric(8, 2) NULL` | ✅ |
| `scene_id` | `String(255) NULL` | `scene_id` | `sa.String(255) NULL` | ✅ |
| `source_url` | `String(500) NULL` | `source_url` | `sa.String(500) NULL` | ✅ |
| `notes` | `Text NULL` | `notes` | `sa.Text() NULL` | ✅ |
| `created_at` | `DateTime(timezone=True)` | `created_at` | `sa.DateTime(timezone=True)` | ✅ |
| `updated_at` | `DateTime(timezone=True)` | `updated_at` | `sa.DateTime(timezone=True)` | ✅ |

### 9.2 Index Parity

| ORM Index Definition | Migration Index | Match |
|---|---|---|
| `index=True` on `field_id` | `ix_satellite_observations_field_id` | ✅ |
| `index=True` on `observed_at` | `ix_satellite_observations_observed_at` | ✅ |
| `index=True` on `satellite_provider` | `ix_satellite_observations_satellite_provider` | ✅ |
| `index=True` on `spectral_index` | `ix_satellite_observations_spectral_index` | ✅ |
| `index=True` on `scene_id` | `ix_satellite_observations_scene_id` | ✅ |
| `Index("ix_satellite_observations_field_id_observed_at", ...)` | Same name in migration | ✅ |
| `Index("ix_satellite_observations_spectral_index_observed_at", ...)` | Same name in migration | ✅ |

### 9.3 ENUM Value Parity

Verified programmatically against `app/core/enums.py`:

| ENUM | ORM Values | Migration Values | Match |
|---|---|---|---|
| `satellite_provider` | 8 values | 8 values (identical order) | ✅ |
| `spectral_index` | 8 values | 8 values (identical order) | ✅ |
| `processing_level` | 4 values | 4 values (identical order) | ✅ |

---

## 10. Query Patterns

### 10.1 Field Observation History (API Primary Pattern)

```sql
-- GET /api/v1/fields/{field_id}/satellite-observations
-- Uses: ix_satellite_observations_field_id_observed_at
SELECT *
FROM satellite_observations
WHERE field_id = $1
ORDER BY observed_at DESC
LIMIT $2 OFFSET $3;
```

### 10.2 Index-Specific Field History

```sql
-- Get NDVI history for a specific field
-- Uses: ix_satellite_observations_field_id_observed_at (field_id leading column)
SELECT observed_at, index_value, satellite_provider, processing_level, cloud_cover_percent
FROM satellite_observations
WHERE field_id = $1
  AND spectral_index = 'NDVI'
ORDER BY observed_at DESC;
```

### 10.3 AI Feature Extraction — Growing Season NDVI

```sql
-- Phase 12 Yield Prediction feature extraction
-- Uses: ix_satellite_observations_spectral_index_observed_at
SELECT field_id, observed_at, index_value, satellite_provider, resolution_m
FROM satellite_observations
WHERE spectral_index = 'NDVI'
  AND processing_level IN ('ARD', 'L2A')
  AND cloud_cover_percent < 20.0
  AND observed_at BETWEEN '2024-04-01' AND '2024-09-30'
ORDER BY field_id, observed_at;
```

### 10.4 Early Stress Detection — NDRE Time Series

```sql
-- Phase 13 Disease Risk feature extraction — NDRE early-stress signal
-- Uses: ix_satellite_observations_spectral_index_observed_at
SELECT field_id, observed_at, index_value, cloud_cover_percent
FROM satellite_observations
WHERE spectral_index = 'NDRE'
  AND processing_level IN ('ARD', 'L2A')
  AND observed_at >= NOW() - INTERVAL '60 days'
ORDER BY field_id, observed_at;
```

### 10.5 Ingestion Deduplication Check

```sql
-- Prevents double-ingestion of the same scene
-- Uses: ix_satellite_observations_scene_id
SELECT id FROM satellite_observations
WHERE scene_id = 'S2A_MSIL2A_20240615T102021_N0510_R065_T32UMD_20240615T130512'
LIMIT 1;
```

### 10.6 Water Stress Monitoring — NDWI

```sql
-- Phase 14 Irrigation Recommendation — NDWI water-deficit signal
-- Uses: ix_satellite_observations_spectral_index_observed_at
SELECT field_id, observed_at, index_value
FROM satellite_observations
WHERE spectral_index = 'NDWI'
  AND field_id = $1
  AND observed_at >= NOW() - INTERVAL '14 days'
ORDER BY observed_at DESC;
```

---

## 11. AI & Feature Engineering Readiness

### 11.1 Quality Gate Columns

The schema provides two explicit data quality gate columns for AI pipelines:

| Column | AI Pipeline Role |
|---|---|
| `processing_level` | Primary quality gate — exclude `L1C` from training |
| `cloud_cover_percent` | Secondary quality gate — filter `> 20%` cloud cover |

Combined gate:
```sql
WHERE processing_level IN ('ARD', 'L2A')
  AND (cloud_cover_percent IS NULL OR cloud_cover_percent < 20.0)
```

### 11.2 Feature Engineering Inputs by Phase

| Phase | Engine | Columns Used |
|---|---|---|
| Phase 12 | Yield Prediction | `spectral_index IN ('NDVI','EVI','LAI')`, `index_value`, `observed_at`, `field_id` |
| Phase 13 | Disease Risk | `spectral_index IN ('NDRE','NDWI','NDVI')`, `index_value`, `observed_at`, `field_id` |
| Phase 14 | Irrigation Optimization | `spectral_index = 'NDWI'`, `index_value`, `observed_at`, `field_id` |
| Phase 15+ | Digital Twin | All columns — real-time field canopy state |

### 11.3 Spatial Resolution Feature

`resolution_m` enables resolution-aware feature engineering without joining to a provider lookup table:

```python
# Resolution weighting in feature pipeline
df['spatial_weight'] = np.where(
    df['resolution_m'] <= 10,  1.0,   # Sentinel-2
    np.where(df['resolution_m'] <= 30,  0.8,   # Landsat
    np.where(df['resolution_m'] <= 100, 0.5,   # SPOT
             0.3))                             # MODIS
)
df['weighted_index'] = df['index_value'] * df['spatial_weight']
```

### 11.4 Provenance for Explainability

`satellite_provider` and `processing_level` enable Explainable AI (XAI) annotation:

> "The NDVI feature for Field 47 on 2024-06-15 was computed from SENTINEL_2 ARD data (10 m, cloud cover 4.2 %). Feature confidence: HIGH."

---

## 12. TimescaleDB Promotion Readiness

This migration is designed for zero-friction TimescaleDB hypertable promotion in Phase 12.

### 12.1 Hypertable Conversion Command

When Phase 12 is implemented, a single call converts `satellite_observations` to a hypertable:

```sql
SELECT create_hypertable(
    'satellite_observations',
    'observed_at',
    chunk_time_interval => INTERVAL '1 week'
);
```

No schema changes, no ORM changes, and no migration file modifications are required.

### 12.2 Why This Schema Is Hypertable-Compatible

| Design Choice | TimescaleDB Requirement | Status |
|---|---|---|
| `observed_at TIMESTAMPTZ NOT NULL` | Non-null partition key of temporal type | ✅ |
| No unique constraint on `observed_at` alone | Hypertable primary key must include partition key | ✅ (PK is `id` only) |
| Compound index `(field_id, observed_at)` | TimescaleDB uses this for chunk exclusion on filtered queries | ✅ |
| Compound index `(spectral_index, observed_at)` | TimescaleDB chunk exclusion for index-type time-series | ✅ |
| No application-level partitioning | TimescaleDB manages chunk creation — no conflict | ✅ |

### 12.3 TimescaleDB Query Benefits After Promotion

After `create_hypertable()`, the query from Section 10.3 becomes:

```sql
-- TimescaleDB will automatically prune chunks outside the time range,
-- scanning only the April–September 2024 chunks rather than the full table
EXPLAIN SELECT field_id, observed_at, index_value
FROM satellite_observations
WHERE spectral_index = 'NDVI'
  AND processing_level IN ('ARD', 'L2A')
  AND observed_at BETWEEN '2024-04-01' AND '2024-09-30';

-- Result: Chunk Exclusion → only 26 weekly chunks scanned instead of full table
```

---

## 13. Future Architecture Compatibility

### 13.1 Apache Cassandra

The table is designed with a Cassandra migration path in mind. The natural Cassandra data model maps to the existing schema:

```
Cassandra table: satellite_observations
├── Partition key:  field_id          (distribute by field)
└── Clustering key: observed_at DESC  (time-ordered within partition)
```

A CQRS architecture with Redpanda projecting writes from PostgreSQL to Cassandra requires no schema changes.

### 13.2 Redpanda Event Streaming

The `SatelliteObservationCreated` domain event payload maps directly to the table columns:

```json
{
  "event": "SatelliteObservationCreated",
  "id": "...",
  "field_id": "...",
  "observed_at": "2024-06-15T10:20:21Z",
  "satellite_provider": "SENTINEL_2",
  "spectral_index": "NDVI",
  "processing_level": "ARD",
  "index_value": "0.712300",
  "cloud_cover_percent": "4.20",
  "resolution_m": "10.00"
}
```

### 13.3 Digital Twin Field State

The Digital Twin consumes `SatelliteObservationCreated` events and updates the field canopy state:

```
FieldDigitalTwinState.ndvi      ← latest NDVI index_value
FieldDigitalTwinState.ndwi      ← latest NDWI index_value  
FieldDigitalTwinState.ndre      ← latest NDRE index_value
FieldDigitalTwinState.lai       ← latest LAI index_value
```

The `(spectral_index, field_id, observed_at)` access pattern supports real-time state lookups.

### 13.4 PostGIS Integration (Phase 18)

When PostGIS is introduced, spatial correlations between field boundary polygons and satellite pixel footprints require the `resolution_m` and `satellite_provider` columns to determine pixel extraction methodology. No schema changes are required.

---

## 14. Migration Revision Chain

```
8f3a1c2d9e04  Phase 1  — farms
      ↓
3b7e9f1a2c85  Phase 2  — fields
      ↓
5c2d8e3f7a19  Phase 3  — crops
      ↓
13aabbe35d51  Phase 4  — soil_profiles
      ↓
7d4f2a9b1e63  Phase 5  — weather_records
      ↓
f3a8c1d9e047  Phase 6  — AI readiness columns
      ↓
a8f3d1b6e924  Phase 7  — sensor_readings
      ↓
235a51cdf901  Phase 8  — irrigation_events
      ↓
b7e2a9f4c8d3  Phase 9  — yield_records
      ↓
d3e7b2a9f1c4  Phase 10 — disease_observations
      ↓
a1b2c3d4e5f6  Phase 11 — satellite_observations  ← CURRENT HEAD
```

**Current migration head:** `a1b2c3d4e5f6`

---

## 15. Decisions and Rationale Summary

| Decision | Rationale |
|---|---|
| Anchor on `Field`, not `Crop` | Satellite imagery is field-level; must persist across crop cycle boundaries |
| `observed_at TIMESTAMPTZ NOT NULL` | Timezone-aware; TimescaleDB partition key candidate; not nullable |
| `index_value NUMERIC(9, 6)` | Exact decimal arithmetic for aggregates; avoids IEEE-754 float drift |
| Three separate ENUM columns | Provider, index type, and processing level are independent categorical attributes |
| `postgresql.ENUM(create_type=False)` | Prevents `DuplicateObjectError` from `sa.Enum._copy()` in SQLAlchemy 2.0.x (ADR-008-01) |
| `cloud_cover_percent NULLABLE` | Not all providers supply cloud masks; NULL preserves data quality transparency |
| `resolution_m NULLABLE` | Can be inferred from provider; nullable to avoid blocking ingestion |
| `scene_id` with index | Enables efficient deduplication during batch ingestion |
| `ondelete="CASCADE"` on FK | Consistent with all Field-child migrations; atomic parent-child deletion |
| 2 compound + 5 individual indexes | Covers all dominant API, AI, and operational access patterns without over-indexing |
| Mutable (PATCH permitted) | Data engineers need to correct processing level, cloud masks, and provenance |

---

*End of RPT-002*

---

**Document Metadata**

| Field | Value |
|---|---|
| Report ID | RPT-002 |
| Migration documented | `a1b2c3d4e5f6_create_satellite_observations_table.py` |
| ORM documented | `satellite_observation.py` |
| Phase | 11 — Satellite Observation Domain |
| Step | D — Alembic Migration |
| Migration head after this step | `a1b2c3d4e5f6` |
| Previous head | `d3e7b2a9f1c4` (Phase 10 Disease Observation) |
| Tables created | `satellite_observations` |
| ENUM types created | `satellite_provider`, `spectral_index`, `processing_level` |
| Indexes created | 7 |
| Document version | 1.0 |
| Created | June 2026 |
| Next report | RPT-003 — Satellite Observation Pydantic Schemas (Phase 11 Step E) |
