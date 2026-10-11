"""Contract tests for Phase 15 Feature Store registry and API catalog shape."""

from app.features.catalog import FEATURE_CATALOG
from app.features.types import FEATURE_REGISTRY_VERSION, FeatureId


def test_feature_registry_covers_cdd_core_features() -> None:
    expected = {
        FeatureId.SM_7D_MEAN,
        FeatureId.GDD_30D_SUM,
        FeatureId.NDVI_90D_MAX,
        FeatureId.RAINFALL_14D_SUM,
        FeatureId.IRRIGATION_30D_MM,
        FeatureId.DISEASE_SEVERITY_MAX,
        FeatureId.YIELD_ACTUAL,
    }
    assert set(FEATURE_CATALOG.keys()) == expected


def test_feature_registry_version_matches_cdd() -> None:
    assert FEATURE_REGISTRY_VERSION == "cdd-v1.0.0"


def test_each_feature_has_positive_window() -> None:
    for entry in FEATURE_CATALOG.values():
        assert entry.window_days > 0
        assert entry.primary_source
