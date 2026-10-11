"""AI Feature Registry — maps CDD features to continuous aggregate sources (Phase 15)."""

from __future__ import annotations

from dataclasses import dataclass

from app.features.types import FEATURE_REGISTRY_VERSION, FeatureId


@dataclass(frozen=True, slots=True)
class FeatureCatalogEntry:
    feature_id: FeatureId
    display_name: str
    description: str
    unit: str
    window_days: int
    primary_source: str
    secondary_source: str | None = None


FEATURE_CATALOG: dict[FeatureId, FeatureCatalogEntry] = {
    FeatureId.SM_7D_MEAN: FeatureCatalogEntry(
        feature_id=FeatureId.SM_7D_MEAN,
        display_name="7-day mean soil moisture",
        description="Rolling mean soil moisture from hourly sensor continuous aggregate.",
        unit="percent",
        window_days=7,
        primary_source="ca_sensor_hourly",
        secondary_source="ca_sensor_daily",
    ),
    FeatureId.GDD_30D_SUM: FeatureCatalogEntry(
        feature_id=FeatureId.GDD_30D_SUM,
        display_name="30-day growing degree days",
        description="Sum of daily GDD (base 10°C) from weather daily aggregate.",
        unit="gdd",
        window_days=30,
        primary_source="ca_weather_daily",
    ),
    FeatureId.NDVI_90D_MAX: FeatureCatalogEntry(
        feature_id=FeatureId.NDVI_90D_MAX,
        display_name="90-day maximum NDVI",
        description="Peak canopy greenness from satellite daily aggregate.",
        unit="index",
        window_days=90,
        primary_source="ca_satellite_daily",
    ),
    FeatureId.RAINFALL_14D_SUM: FeatureCatalogEntry(
        feature_id=FeatureId.RAINFALL_14D_SUM,
        display_name="14-day rainfall total",
        description="Accumulated rainfall from weather daily aggregate.",
        unit="mm",
        window_days=14,
        primary_source="ca_weather_daily",
    ),
    FeatureId.IRRIGATION_30D_MM: FeatureCatalogEntry(
        feature_id=FeatureId.IRRIGATION_30D_MM,
        display_name="30-day irrigation depth",
        description="Irrigation applied depth derived from event volumes and field area.",
        unit="mm",
        window_days=30,
        primary_source="irrigation_events",
        secondary_source="ca_irrigation_monthly",
    ),
    FeatureId.DISEASE_SEVERITY_MAX: FeatureCatalogEntry(
        feature_id=FeatureId.DISEASE_SEVERITY_MAX,
        display_name="Peak disease severity (90d)",
        description="Maximum observed disease severity in the rolling window.",
        unit="severity",
        window_days=90,
        primary_source="ca_disease_weekly",
        secondary_source="disease_observations",
    ),
    FeatureId.YIELD_ACTUAL: FeatureCatalogEntry(
        feature_id=FeatureId.YIELD_ACTUAL,
        display_name="Latest harvest yield",
        description="Most recent yield observation for the field (optionally crop-scoped).",
        unit="t/ha",
        window_days=365,
        primary_source="yield_records",
        secondary_source="ca_yield_seasonal",
    ),
}


def get_feature_entry(feature_id: FeatureId) -> FeatureCatalogEntry:
    return FEATURE_CATALOG[feature_id]


def registry_version() -> str:
    return FEATURE_REGISTRY_VERSION
