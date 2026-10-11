"""Feature Store identifiers aligned with CDD v1.0.0 (ADR-004 §10)."""

from __future__ import annotations

import enum


class FeatureId(str, enum.Enum):
    SM_7D_MEAN = "sm_7d_mean"
    GDD_30D_SUM = "gdd_30d_sum"
    NDVI_90D_MAX = "ndvi_90d_max"
    RAINFALL_14D_SUM = "rainfall_14d_sum"
    IRRIGATION_30D_MM = "irrigation_30d_mm"
    DISEASE_SEVERITY_MAX = "disease_severity_max"
    YIELD_ACTUAL = "yield_actual"


FEATURE_REGISTRY_VERSION = "cdd-v1.0.0"
