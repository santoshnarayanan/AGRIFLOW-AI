"""Disease risk scoring stub engine (Phase 14)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.core.enums import RecommendationPriority
from app.ml.engines.base import EngineRunContext, MLPredictionEngineStub, _default_validity_window
from app.ml.registry import MLEngineSpec
from app.schemas.recommendation import RecommendationCreate


class DiseaseRiskEngineStub(MLPredictionEngineStub):
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
            priority=RecommendationPriority.HIGH,
            title="Elevated disease pressure — scouting recommended (stub)",
            description=(
                f"Stub disease risk scorer for field {field_id}. "
                "Future: severity time-series + humidity features from Phase 12 aggregates."
            ),
            recommended_action="Scout affected zones within 48h and confirm diagnosis before treatment.",
            confidence_score=Decimal("0.580"),
            evidence_summary=context.notes or "Phase 14 stub — severity label placeholder.",
            engine_version=spec.engine_version,
            valid_from=valid_from,
            valid_until=valid_until,
        )
