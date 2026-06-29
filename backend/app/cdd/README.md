# Canonical Development Dataset (CDD) Generator

## Purpose

The **Canonical Development Dataset (CDD)** is the official engineering dataset for AGRIFLOW-AI. It provides a versioned, deterministically regenerable synthetic farm environment used for local development, TimescaleDB validation, AI feature engineering, and demonstrations.

This package (`backend/app/cdd/`) is an **engineering utility** — not a service, repository, or API layer. Step 2C-B implements the generation framework only; database persistence and CLI execution are deferred to later steps.

**Reference:** `docs/report/PHASE12_STEP2CA_CANONICAL_DEVELOPMENT_DATASET_ARCHITECTURE.md`

---

## Architecture

The generator follows a layered design aligned with Domain-Driven Design:

| Layer | Responsibility |
|---|---|
| **config** | Global constants: version, seed, temporal anchor |
| **manifest** | All configurable parameters (counts, cadences, field portfolio, rotations) |
| **deterministic** | UUID v5 identity and scoped PRNG |
| **correlation** | Cross-domain agricultural causal rules |
| **factories** | Per-domain record generation |
| **orchestrator** | FK-safe sequencing only |
| **types** | In-memory record dataclasses (pre-persistence) |

```mermaid
flowchart TD
    CFG["config.py"]
    MAN["manifest.py"]
    DET["deterministic/"]
    COR["correlation/"]
    FAC["factories/"]
    ORC["orchestrator.py"]

    CFG --> ORC
    MAN --> ORC
    DET --> FAC
    COR --> FAC
    MAN --> FAC
    FAC --> ORC
```

### Determinism Contract

Identical inputs produce identical outputs:

- `CDD_VERSION` + `CDD_SEED` → same UUIDs and values on every run
- UUID v5 from `(version, seed, entity_type, ordinal)`
- Scoped PRNG derived via SHA-256 from base seed + scope string

### Causal Model

The correlation engine implements approved cross-domain rules:

| Relationship | Function |
|---|---|
| Rainfall → Soil Moisture | `compute_soil_moisture_from_rainfall` |
| Temperature → NDVI | `compute_ndvi_from_context` |
| Soil Moisture → Irrigation | `compute_irrigation_trigger` |
| Leaf Wetness → Disease | `compute_disease_probability` |
| Disease → Yield | `apply_disease_yield_reduction` |

---

## Folder Structure

```
backend/app/cdd/
├── __init__.py           # Public package exports
├── config.py             # CDD_VERSION, CDD_SEED, temporal anchors
├── manifest.py           # Profile definitions and domain parameters
├── context.py            # Shared generation context
├── types.py              # Record dataclasses and CDDDataset bundle
├── orchestrator.py       # FK-safe generation sequencing
├── README.md             # This file
├── correlation/
│   ├── __init__.py
│   └── engine.py         # Agricultural causal utilities
├── deterministic/
│   ├── __init__.py
│   ├── uuid.py           # UUID v5 generator
│   └── rng.py            # Scoped deterministic PRNG
└── factories/
    ├── __init__.py
    ├── farm.py
    ├── field.py
    ├── soil.py
    ├── crop.py
    ├── weather.py
    ├── sensor.py
    ├── satellite.py
    ├── irrigation.py
    ├── disease.py
    └── yield_.py
```

---

## Execution Flow

The orchestrator enforces referential generation order:

```
Farm
  ↓
Fields
  ↓
Soil Profiles
  ↓
Crops
  ↓
Weather
  ↓
Sensors
  ↓
Satellite
  ↓
Irrigation
  ↓
Disease
  ↓
Yield
```

Example usage (framework only — no automatic execution in Step 2C-B):

```python
from app.cdd import CDDOrchestrator

orchestrator = CDDOrchestrator(profile="cdd-dev")
dataset = orchestrator.generate()

print(dataset.version)       # cdd-v1.0.0
print(dataset.total_row_count)
print(len(dataset.sensor_readings))  # target: ~438,000
```

---

## Default Profile (`cdd-dev`)

| Domain | Target Rows |
|---|---|
| farms | 1 |
| fields | 10 |
| soil_profiles | 10 |
| crops | 18 |
| weather_records | 14,600 |
| sensor_readings | 438,000 |
| irrigation_events | 96 |
| satellite_observations | 5,840 |
| disease_observations | 54 |
| yield_records | 22 |

Temporal window: `2025-06-01` → `2026-05-31` (America/Chicago)

---

## Extension Guidelines

1. **Add parameters to `manifest.py`** — never hard-code counts or cadences in factories.
2. **Bump `CDD_VERSION`** per SemVer rules when changing row counts, temporal anchor, or schema-breaking fields.
3. **Add new domains** by creating a factory and inserting it in the orchestrator after existing FK dependencies.
4. **Add new profiles** (e.g. `cdd-benchmark`) by registering a new `CDDManifest` in `manifest.py`.
5. **Keep correlation logic in `correlation/`** — factories call pure functions; they do not embed physics.
6. **Do not modify** repositories, services, APIs, ORM models, or migrations from this package.

---

## Constraints (Step 2C-B)

- No database writes
- No CLI / `make cdd-regenerate` yet
- No automatic execution on import or application startup
- Synthetic data only — no production or PII data
