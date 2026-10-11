"""Helpers for consuming persisted feature snapshots."""

from __future__ import annotations

from typing import Any

from app.db.models.field_feature_snapshot import FieldFeatureSnapshot


def flatten_snapshot_features(
    snapshot: FieldFeatureSnapshot | None,
) -> dict[str, float | str]:
    if snapshot is None:
        return {}
    raw: dict[str, Any] = snapshot.features or {}
    out: dict[str, float | str] = {}
    for key, meta in raw.items():
        if not isinstance(meta, dict) or not meta.get("available"):
            continue
        value = meta.get("value")
        if isinstance(value, (int, float)):
            out[key] = float(value)
        elif isinstance(value, str):
            out[key] = value
    return out


def format_feature_evidence(features: dict[str, float | str], *, max_items: int = 4) -> str:
    if not features:
        return ""
    parts: list[str] = []
    for key in sorted(features.keys())[:max_items]:
        parts.append(f"{key}={features[key]}")
    return "Feature Store: " + ", ".join(parts)
