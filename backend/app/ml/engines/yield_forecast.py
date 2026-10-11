"""Yield forecast stub engine (Phase 14)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.core.enums import RecommendationPriority
from app.ml.engines.base import EngineRunContext, MLPredictionEngineStub, _default_validity_window
from app.ml.engines.feature_aware import confidence_with_features
from app.ml.registry import MLEngineSpec
from app.schemas.recommendation import RecommendationCreate


class YieldForecastEngineStub(MLPredictionEngineStub):
    def build_recommendation(
        self,
        field_id: uuid.UUID,
        spec: MLEngineSpec,
        context: EngineRunContext,
    ) -> RecommendationCreate:
        valid_from, valid_until = _default_validity_window()
        confidence = confidence_with_features(
            Decimal("0.550"),
            context,
            required_keys=("ndvi_90d_max", "gdd_30d_sum"),
        )
        feature_hint = ""
        if context.features:
            feature_hint = " Feature Store snapshot applied."
        return RecommendationCreate(
            crop_id=context.crop_id,
            recommendation_type=spec.recommendation_type,
            priority=RecommendationPriority.MEDIUM,
            title="Yield outlook — monitor harvest window (stub)",
            description=(
                f"Yield engine for field {field_id}."
                f"{feature_hint} Train on CDD features (NDVI, GDD, rainfall) in production."
            ),
            recommended_action="Review projected harvest timing against recent yield and NDVI trends.",
            confidence_score=confidence,
            evidence_summary=context.notes or "No Feature Store snapshot — deterministic stub.",
            engine_version=spec.engine_version,
            valid_from=valid_from,
            valid_until=valid_until,
        )
