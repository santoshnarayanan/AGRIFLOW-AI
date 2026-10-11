"""Yield forecast stub engine (Phase 14)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.core.enums import RecommendationPriority
from app.ml.engines.base import EngineRunContext, MLPredictionEngineStub, _default_validity_window
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
        return RecommendationCreate(
            crop_id=context.crop_id,
            recommendation_type=spec.recommendation_type,
            priority=RecommendationPriority.MEDIUM,
            title="Yield outlook — monitor harvest window (stub)",
            description=(
                f"Stub yield engine for field {field_id}. "
                "Replace with TimescaleDB continuous-aggregate features in Phase 15."
            ),
            recommended_action="Review projected harvest timing against recent yield and NDVI trends.",
            confidence_score=Decimal("0.550"),
            evidence_summary=context.notes or "Phase 14 deterministic stub — no model inference.",
            engine_version=spec.engine_version,
            valid_from=valid_from,
            valid_until=valid_until,
        )
