"""Unit tests for dashboard KPI extraction from feature snapshots."""

import uuid
from datetime import datetime, timezone

from app.db.models.field_feature_snapshot import FieldFeatureSnapshot
from app.features.types import FeatureId
from app.read_models.kpi import kpi_payload_from_snapshot


def test_kpi_payload_extracts_available_features() -> None:
    snapshot = FieldFeatureSnapshot(
        id=uuid.uuid4(),
        field_id=uuid.uuid4(),
        crop_id=None,
        registry_version="cdd-v1.0.0",
        as_of=datetime.now(timezone.utc),
        features={
            FeatureId.SM_7D_MEAN.value: {
                "value": 22.5,
                "unit": "percent",
                "available": True,
            },
            FeatureId.NDVI_90D_MAX.value: {
                "value": 0.81,
                "unit": "index",
                "available": True,
            },
            FeatureId.RAINFALL_14D_SUM.value: {
                "value": None,
                "unit": "mm",
                "available": False,
            },
        },
        materialization_notes=None,
    )
    payload = kpi_payload_from_snapshot(snapshot)
    assert payload[FeatureId.SM_7D_MEAN.value]["value"] == 22.5
    assert FeatureId.RAINFALL_14D_SUM.value not in payload


def test_kpi_payload_empty_without_snapshot() -> None:
    assert kpi_payload_from_snapshot(None) == {}
