"""Unit tests for Phase 14 ML engine stubs."""

import uuid
from decimal import Decimal

from app.core.enums import RecommendationType
from app.ml.engines.base import EngineRunContext
from app.ml.engines.disease_risk import DiseaseRiskEngineStub
from app.ml.engines.irrigation import IrrigationOptimizationEngineStub
from app.ml.engines.yield_forecast import YieldForecastEngineStub
from app.ml.registry import get_engine_spec
from app.ml.types import MLEngineId


def test_yield_stub_recommendation_shape() -> None:
    field_id = uuid.uuid4()
    spec = get_engine_spec(MLEngineId.YIELD_FORECAST)
    payload = YieldForecastEngineStub().build_recommendation(
        field_id, spec, context=EngineRunContext()
    )

    assert payload.recommendation_type == RecommendationType.HARVEST_TIMING
    assert payload.engine_version == "yield-stub-v1.0"
    assert payload.confidence_score == Decimal("0.550")


def test_irrigation_stub_has_quantified_action() -> None:
    field_id = uuid.uuid4()
    spec = get_engine_spec(MLEngineId.IRRIGATION_OPTIMIZATION)
    payload = IrrigationOptimizationEngineStub().build_recommendation(
        field_id, spec, context=EngineRunContext()
    )
    assert payload.recommended_value == Decimal("25.0")
    assert payload.recommended_unit == "mm"


def test_disease_stub_uses_disease_treatment_type() -> None:
    field_id = uuid.uuid4()
    spec = get_engine_spec(MLEngineId.DISEASE_RISK)
    payload = DiseaseRiskEngineStub().build_recommendation(
        field_id, spec, context=EngineRunContext()
    )
    assert payload.recommendation_type == RecommendationType.DISEASE_TREATMENT
