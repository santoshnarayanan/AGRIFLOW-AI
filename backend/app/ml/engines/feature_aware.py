"""Shared helpers when Feature Store snapshots are attached to engine runs."""

from __future__ import annotations

from decimal import Decimal

from app.ml.engines.base import EngineRunContext


def confidence_with_features(
    base: Decimal,
    context: EngineRunContext,
    *,
    required_keys: tuple[str, ...],
    boost: Decimal = Decimal("0.120"),
) -> Decimal:
    features = context.features or {}
    if all(key in features for key in required_keys):
        return min(base + boost, Decimal("0.950"))
    return base
