# Phase 10 – Step A: Disease Observation Enums

## Pattern Reference

The single authoritative file is [`backend/app/core/enums.py`](../../../backend/app/core/enums.py).

All four existing enums follow an identical structure:
- Inherit `(str, enum.Enum)` — stores the label as a plain `VARCHAR` in PostgreSQL, readable without a type cast
- Values are upper-snake-case strings matching the attribute name
- Each class carries a docstring describing business meaning, usage domains, and future consumers
- No sub-modules, no separate files — all shared enums live in the single flat file

## Scope

**1 file modified:** `backend/app/core/enums.py`

**0 files created**

## Code to Append

Append two new classes at the end of `enums.py`, after `YieldMeasurementMethod`:

```python
class DiseaseSeverity(str, enum.Enum):
    """
    Severity classification of a disease observation on a crop.

    Used by:
    - DiseaseObservation  (Phase 10)
    - Disease Risk Scoring Engine  (Phase 13 — label for model training)
    - GaaS PlantHealthAdvisor      (future — natural language risk queries)
    - Digital Twin crop health state  (future)

    Severity definitions:
    - LOW      minor symptoms; localised; no immediate yield threat
    - MEDIUM   moderate spread; intervention recommended
    - HIGH     significant disease pressure; yield loss expected
    - CRITICAL severe outbreak; urgent action required
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DiagnosisMethod(str, enum.Enum):
    """
    Method by which a disease observation was identified or confirmed.

    Placed in this shared module for cross-domain reuse across:
    - DiseaseObservation  (Phase 10)
    - Disease Risk Scoring Engine  (Phase 13 — data quality weighting)
    - GaaS PlantHealthAdvisor      (future)
    - Digital Twin plant health state  (future)

    Method-specific confidence notes:
    - LAB_ANALYSIS      highest confidence; pathogen confirmed at species level
    - AGRONOMIST        high confidence; expert field assessment
    - IMAGE_AI          moderate confidence; depends on model accuracy and image quality
    - VISUAL_INSPECTION moderate confidence; farmer assessment without instruments
    - SENSOR_DETECTED   future capability; environmental threshold inference
    """

    VISUAL_INSPECTION = "VISUAL_INSPECTION"
    LAB_ANALYSIS = "LAB_ANALYSIS"
    IMAGE_AI = "IMAGE_AI"
    AGRONOMIST = "AGRONOMIST"
    SENSOR_DETECTED = "SENSOR_DETECTED"
```

## Validation Plan

After the edit, run startup verification from the `backend/` directory:

```bash
docker compose up -d
uvicorn app.main:app --reload
```

Confirm no import errors and `/docs` loads cleanly.

## What is NOT changed

- No ORM model
- No Alembic migration
- No Pydantic schema
- No repository
- No service
- No router
- No `deps.py` change
- No `__init__.py` export change (enums are imported directly from `app.core.enums`)

---

*Plan created: Phase 10 Step A — June 2026*  
*Next step: Phase 10 Step B — DiseaseObservation ORM model*
