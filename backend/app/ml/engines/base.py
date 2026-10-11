"""Base contract for Phase 14 ML engine stubs."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.ml.registry import MLEngineSpec
from app.schemas.recommendation import RecommendationCreate


@dataclass(frozen=True, slots=True)
class EngineRunContext:
    """Optional trigger context from domain events or manual API runs."""

    crop_id: uuid.UUID | None = None
    trigger_event_type: str | None = None
    trigger_aggregate_id: uuid.UUID | None = None
    notes: str | None = None


class MLPredictionEngineStub(ABC):
    @abstractmethod
    def build_recommendation(
        self,
        field_id: uuid.UUID,
        spec: MLEngineSpec,
        context: EngineRunContext,
    ) -> RecommendationCreate:
        """Return a recommendation payload without persisting."""


def _default_validity_window() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    return now, now + timedelta(days=7)
