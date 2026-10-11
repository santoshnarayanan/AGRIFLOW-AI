"""Orchestrates ML engine stub runs and persists recommendations (Phase 14)."""

from __future__ import annotations

import uuid

from app.core.logging.logger import get_logger
from app.db.models.recommendation import Recommendation
from app.ml.engines.base import EngineRunContext
from app.ml.engines.disease_risk import DiseaseRiskEngineStub
from app.ml.engines.irrigation import IrrigationOptimizationEngineStub
from app.ml.engines.yield_forecast import YieldForecastEngineStub
from app.ml.registry import ML_ENGINE_REGISTRY, get_engine_spec
from app.ml.types import MLEngineId
from app.services.recommendation import RecommendationService

logger = get_logger(__name__)

_ENGINE_IMPL = {
    MLEngineId.YIELD_FORECAST: YieldForecastEngineStub(),
    MLEngineId.IRRIGATION_OPTIMIZATION: IrrigationOptimizationEngineStub(),
    MLEngineId.DISEASE_RISK: DiseaseRiskEngineStub(),
}


class UnknownMLEngineError(ValueError):
    """Raised when ``engine_id`` is not registered."""


class MLEngineService:
    def __init__(self, recommendation_service: RecommendationService) -> None:
        self._recommendations = recommendation_service

    async def run_engine(
        self,
        field_id: uuid.UUID,
        engine_id: MLEngineId,
        *,
        context: EngineRunContext | None = None,
    ) -> Recommendation:
        if engine_id not in ML_ENGINE_REGISTRY:
            raise UnknownMLEngineError(f"Unknown ML engine '{engine_id}'.")

        spec = get_engine_spec(engine_id)
        impl = _ENGINE_IMPL[engine_id]
        ctx = context or EngineRunContext()

        payload = impl.build_recommendation(field_id, spec, ctx)
        rec = await self._recommendations.create_recommendation(field_id, payload)

        logger.info(
            "ml_engine.run.success",
            engine_id=engine_id.value,
            field_id=str(field_id),
            recommendation_id=str(rec.id),
        )
        return rec
