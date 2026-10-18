"""Shared Temporal workflow input/output types."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SoilMoistureAlertInput:
    field_id: uuid.UUID
    sensor_reading_id: uuid.UUID
    sensor_value: float
    threshold_percent: float
    recorded_at: datetime


@dataclass(frozen=True)
class LatestSoilMoistureResult:
    field_id: uuid.UUID
    sensor_value: float | None
    unit: str | None
    recorded_at: datetime | None
    below_threshold: bool


@dataclass(frozen=True)
class IrrigationRecommendationResult:
    recommendation_id: uuid.UUID
    alert_id: uuid.UUID | None
