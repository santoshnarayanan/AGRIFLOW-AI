"""ML prediction engine identifiers (Phase 14 stubs)."""

from enum import StrEnum


class MLEngineId(StrEnum):
    """Registered stub engines; production models replace implementations in Phase 15+."""

    YIELD_FORECAST = "yield_forecast"
    IRRIGATION_OPTIMIZATION = "irrigation_optimization"
    DISEASE_RISK = "disease_risk"
