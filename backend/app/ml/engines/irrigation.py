"""Irrigation optimization stub engine (Phase 14)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.core.enums import RecommendationPriority
from app.ml.engines.base import EngineRunContext, MLPredictionEngineStub, _default_validity_window
from app.ml.engines.feature_aware import confidence_with_features
from app.ml.registry import MLEngineSpec
from app.schemas.recommendation import RecommendationCreate


class IrrigationOptimizationEngineStub(MLPredictionEngineStub):
    def build_recommendation(
        self,
        field_id: uuid.UUID,
        spec: MLEngineSpec,
        context: EngineRunContext,
    ) -> RecommendationCreate:
        valid_from, valid_until = _default_validity_window()
        confidence = confidence_with_features(
            Decimal("0.620"),
            context,
            required_keys=("sm_7d_mean", "rainfall_14d_sum"),
        )
        recommended_mm = Decimal("25.0")
        if context.features and "irrigation_30d_mm" in context.features:
            try:
                recommended_mm = Decimal(str(max(10.0, 30.0 - float(context.features["irrigation_30d_mm"]))))
            except (TypeError, ValueError):
                pass
        return RecommendationCreate(
            crop_id=context.crop_id,
            recommendation_type=spec.recommendation_type,
            priority=RecommendationPriority.HIGH,
            title="Irrigation adjustment suggested (stub)",
            description=(
                f"Stub irrigation optimizer for field {field_id}. "
                "Future: FAO-56 balance using sensor moisture and weather forecasts."
            ),
            recommended_action="Schedule a short irrigation cycle and verify soil moisture recovery within 24h.",
            recommended_value=recommended_mm,
            recommended_unit="mm",
            confidence_score=confidence,
            evidence_summary=context.notes or "No Feature Store snapshot — rule-based placeholder.",
            engine_version=spec.engine_version,
            valid_from=valid_from,
            valid_until=valid_until,
        )
