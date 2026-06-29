"""
Agricultural causal correlation engine.

Implements cross-domain relationships defined in CDD architecture Section 5.
Correlation logic is isolated from factories — factories call these pure functions.
"""

from __future__ import annotations

import math
from datetime import date

from app.core.enums import DiseaseSeverity


# ── Soil texture infiltration (Rainfall → Soil Moisture) ─────────────────────

_INFILTRATION_MM_HR: dict[str, float] = {
    "Sandy": 18.0,
    "Sandy Loam": 14.0,
    "Loam": 10.0,
    "Silt Loam": 8.0,
    "Clay Loam": 6.0,
    "Silty Clay": 4.0,
    "Clay": 3.0,
}


def infiltration_rate_for_texture(soil_texture_label: str) -> float:
    """Return mm/hr absorption rate for a soil texture label."""
    return _INFILTRATION_MM_HR.get(soil_texture_label, 10.0)


def compute_soil_moisture_from_rainfall(
    *,
    previous_moisture_pct: float,
    rainfall_mm: float,
    evapotranspiration_mm: float,
    soil_texture_label: str,
    hours_elapsed: float = 1.0,
) -> float:
    """
    Rainfall → Soil Moisture with texture-dependent infiltration.

    Loam absorbs ~10 mm/hr; sand faster; clay slower. ET draws moisture down.
    """
    infiltration = infiltration_rate_for_texture(soil_texture_label)
    absorbed = min(rainfall_mm, infiltration * (hours_elapsed / 1.0))
    delta = (absorbed * 0.35) - (evapotranspiration_mm * 0.25)
    moisture = previous_moisture_pct + delta
    return max(12.0, min(55.0, moisture))


# ── Temperature → NDVI trend ─────────────────────────────────────────────────

def _sigmoid_ndvi(day_in_cycle: int, cycle_length: int, peak_ndvi: float) -> float:
    if cycle_length <= 0:
        return 0.2
    midpoint = cycle_length * 0.55
    steepness = 12.0 / max(cycle_length, 1)
    x = day_in_cycle - midpoint
    value = peak_ndvi / (1.0 + math.exp(-steepness * x))
    dormancy_floor = 0.12
    return max(dormancy_floor, min(peak_ndvi, value))


def compute_ndvi_from_context(
    *,
    planting_date: date,
    observation_date: date,
    expected_harvest_date: date,
    season_name: str,
    temperature_c: float,
    soil_moisture_pct: float,
    is_perennial: bool,
) -> float:
    """
    Temperature + crop lifecycle → NDVI sigmoid aligned to growth stage.

    Perennials maintain a higher baseline; senescence reduces NDVI after harvest.
    """
    cycle_length = max(1, (expected_harvest_date - planting_date).days)
    day_in_cycle = max(0, (observation_date - planting_date).days)

    if season_name in {"dormancy", "dormancy_late"} and not is_perennial:
        base = 0.15
    elif is_perennial:
        peak = 0.72
        base = _sigmoid_ndvi(day_in_cycle % 120, 120, peak)
    else:
        peak = 0.82 if temperature_c > 10 else 0.55
        base = _sigmoid_ndvi(day_in_cycle, cycle_length, peak)

    moisture_factor = 0.95 + (soil_moisture_pct - 30.0) * 0.002
    temp_factor = 1.0 if 15.0 <= temperature_c <= 32.0 else 0.92
    ndvi = base * moisture_factor * temp_factor

    if day_in_cycle > cycle_length * 0.92 and not is_perennial:
        ndvi *= 0.65

    return max(0.08, min(0.92, ndvi))


# ── Soil Moisture → Irrigation trigger ───────────────────────────────────────

def compute_irrigation_trigger(
    *,
    soil_moisture_pct: float,
    threshold_pct: float,
    consecutive_deficit_hours: int,
    deficit_hours_required: int,
    is_irrigated: bool,
    in_season: bool,
) -> bool:
    """Irrigation fires when SM < threshold for >= required consecutive hours."""
    if not is_irrigated or not in_season:
        return False
    if soil_moisture_pct >= threshold_pct:
        return False
    return consecutive_deficit_hours >= deficit_hours_required


def apply_irrigation_moisture_recovery(
    soil_moisture_pct: float,
    water_applied_mm: float,
) -> float:
    """Irrigation event raises soil moisture proportionally to applied water."""
    recovery = water_applied_mm * 0.18
    return max(12.0, min(55.0, soil_moisture_pct + recovery))


# ── Leaf Wetness → Disease probability ───────────────────────────────────────

def compute_leaf_wetness(
    *,
    air_temperature_c: float,
    humidity_percent: float,
    rainfall_mm: float,
    previous_wetness: float,
) -> float:
    """
    Temperature + Humidity → Leaf Wetness.

    Elevated when temp 15–25°C and humidity > 80% for sustained periods.
    """
    wetness = previous_wetness * 0.85
    if rainfall_mm > 0.5:
        wetness += min(40.0, rainfall_mm * 3.0)
    if 15.0 <= air_temperature_c <= 25.0 and humidity_percent > 80.0:
        wetness += (humidity_percent - 80.0) * 0.8
    return max(0.0, min(100.0, wetness))


def compute_disease_probability(
    *,
    leaf_wetness: float,
    air_temperature_c: float,
    humidity_percent: float,
    consecutive_humid_hours: int,
    is_susceptible: bool,
) -> float:
    """
    Leaf Wetness + temperature/humidity window → disease probability.

    Requires humid/warm windows (temp 15–25°C, humidity > 80%, ≥ 6 hours).
    """
    if not is_susceptible:
        return 0.0
    if consecutive_humid_hours < 6:
        return 0.0
    if not (15.0 <= air_temperature_c <= 25.0 and humidity_percent > 80.0):
        return 0.0
    base = (leaf_wetness / 100.0) * 0.6
    humidity_boost = (humidity_percent - 80.0) / 20.0 * 0.3
    return max(0.0, min(1.0, base + humidity_boost))


# ── Disease Severity → Yield reduction ───────────────────────────────────────

_SEVERITY_YIELD_REDUCTION: dict[DiseaseSeverity, tuple[float, float]] = {
    DiseaseSeverity.LOW: (0.0, 0.02),
    DiseaseSeverity.MEDIUM: (0.03, 0.08),
    DiseaseSeverity.HIGH: (0.05, 0.15),
    DiseaseSeverity.CRITICAL: (0.15, 0.25),
}


def apply_disease_yield_reduction(
    expected_yield_tons_ha: float,
    severities: list[DiseaseSeverity],
    *,
    water_stress_factor: float = 0.0,
) -> float:
    """
    Disease Severity → Yield reduction (5–25% for HIGH/CRITICAL).

    Rain-fed water stress during reproductive stage adds 10–30% reduction.
    """
    reduction = water_stress_factor
    for severity in severities:
        low, high = _SEVERITY_YIELD_REDUCTION[severity]
        reduction += (low + high) / 2.0
    reduction = min(0.45, reduction)
    return max(0.0, expected_yield_tons_ha * (1.0 - reduction))


def compute_water_stress_factor(
    *,
    is_irrigated: bool,
    min_soil_moisture_reproductive: float,
    threshold_pct: float,
    in_reproductive_stage: bool,
) -> float:
    """Water stress on rain-fed fields during reproductive stage reduces yield 10–30%."""
    if is_irrigated or not in_reproductive_stage:
        return 0.0
    if min_soil_moisture_reproductive >= threshold_pct:
        return 0.0
    deficit_ratio = (threshold_pct - min_soil_moisture_reproductive) / threshold_pct
    return min(0.30, max(0.10, deficit_ratio * 0.30))
