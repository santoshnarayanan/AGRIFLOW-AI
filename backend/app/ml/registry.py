"""ML engine catalog metadata (Phase 14)."""

from dataclasses import dataclass

from app.core.enums import RecommendationType
from app.events.types import DomainEventType
from app.ml.types import MLEngineId


@dataclass(frozen=True, slots=True)
class MLEngineSpec:
    engine_id: MLEngineId
    display_name: str
    description: str
    engine_version: str
    recommendation_type: RecommendationType
    trigger_events: tuple[DomainEventType, ...]


ML_ENGINE_REGISTRY: dict[MLEngineId, MLEngineSpec] = {
    MLEngineId.YIELD_FORECAST: MLEngineSpec(
        engine_id=MLEngineId.YIELD_FORECAST,
        display_name="Yield forecast (stub)",
        description="Deterministic placeholder for harvest yield outlook; Phase 15 Feature Store integration.",
        engine_version="yield-stub-v1.0",
        recommendation_type=RecommendationType.HARVEST_TIMING,
        trigger_events=(DomainEventType.YIELD_RECORDED, DomainEventType.SATELLITE_OBSERVED),
    ),
    MLEngineId.IRRIGATION_OPTIMIZATION: MLEngineSpec(
        engine_id=MLEngineId.IRRIGATION_OPTIMIZATION,
        display_name="Irrigation optimization (stub)",
        description="Rule-based irrigation suggestion from spectral and moisture signals (stub).",
        engine_version="irrigation-stub-v1.0",
        recommendation_type=RecommendationType.IRRIGATION,
        trigger_events=(
            DomainEventType.SENSOR_READING_CREATED,
            DomainEventType.SATELLITE_OBSERVED,
            DomainEventType.WEATHER_RECORD_CREATED,
        ),
    ),
    MLEngineId.DISEASE_RISK: MLEngineSpec(
        engine_id=MLEngineId.DISEASE_RISK,
        display_name="Disease risk scoring (stub)",
        description="Severity-weighted disease treatment placeholder; trains on DiseaseObserved labels in Phase 15.",
        engine_version="disease-risk-stub-v1.0",
        recommendation_type=RecommendationType.DISEASE_TREATMENT,
        trigger_events=(DomainEventType.DISEASE_OBSERVED,),
    ),
}


def get_engine_spec(engine_id: MLEngineId) -> MLEngineSpec:
    return ML_ENGINE_REGISTRY[engine_id]
