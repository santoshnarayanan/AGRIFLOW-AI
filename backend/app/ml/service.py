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
from app.features.snapshot_utils import flatten_snapshot_features, format_feature_evidence
from app.services.feature_store import FeatureStoreService
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
    def __init__(
        self,
        recommendation_service: RecommendationService,
        feature_store_service: FeatureStoreService | None = None,
    ) -> None:
        self._recommendations = recommendation_service
        self._feature_store = feature_store_service

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
        ctx = await self._enrich_context_from_feature_store(field_id, ctx)

        payload = impl.build_recommendation(field_id, spec, ctx)
        rec = await self._recommendations.create_recommendation(field_id, payload)

        logger.info(
            "ml_engine.run.success",
            engine_id=engine_id.value,
            field_id=str(field_id),
            recommendation_id=str(rec.id),
        )
        return rec

    async def _enrich_context_from_feature_store(
        self,
        field_id: uuid.UUID,
        context: EngineRunContext,
    ) -> EngineRunContext:
        if self._feature_store is None or context.features is not None:
            return context
        try:
            snapshot = await self._feature_store.get_latest_snapshot(field_id)
        except Exception:
            logger.warning(
                "ml_engine.feature_store.lookup_failed",
                field_id=str(field_id),
            )
            return context
        if snapshot is None:
            return context
        features = flatten_snapshot_features(snapshot)
        evidence = format_feature_evidence(features)
        notes = context.notes or evidence or None
        return EngineRunContext(
            crop_id=context.crop_id,
            trigger_event_type=context.trigger_event_type,
            trigger_aggregate_id=context.trigger_aggregate_id,
            notes=notes,
            feature_snapshot_id=snapshot.id,
            features=features or None,
        )
