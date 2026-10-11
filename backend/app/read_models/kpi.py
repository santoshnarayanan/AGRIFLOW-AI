"""KPI extraction from Feature Store snapshots for dashboard read models."""

from __future__ import annotations

from typing import Any

from app.db.models.field_feature_snapshot import FieldFeatureSnapshot
from app.features.types import FeatureId

_DASHBOARD_KPI_KEYS = (
    FeatureId.SM_7D_MEAN,
    FeatureId.NDVI_90D_MAX,
    FeatureId.RAINFALL_14D_SUM,
    FeatureId.DISEASE_SEVERITY_MAX,
    FeatureId.GDD_30D_SUM,
)


def kpi_payload_from_snapshot(snapshot: FieldFeatureSnapshot | None) -> dict[str, Any]:
    if snapshot is None:
        return {}
    raw = snapshot.features or {}
    payload: dict[str, Any] = {}
    for feature_id in _DASHBOARD_KPI_KEYS:
        meta = raw.get(feature_id.value)
        if not isinstance(meta, dict) or not meta.get("available"):
            continue
        payload[feature_id.value] = {
            "value": meta.get("value"),
            "unit": meta.get("unit"),
        }
    return payload
