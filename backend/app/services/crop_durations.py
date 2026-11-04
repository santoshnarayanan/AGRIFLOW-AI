"""
Crop growth-duration reference data — business rule for expected harvest.

Expected harvest date = planting date + typical days-to-harvest for the crop.

This module is the single source of truth for that rule. CropService applies
it on create (and when planting_date changes), and the API exposes the table
via ``GET /crops/growth-durations`` so the UI shows the same numbers.

Durations are typical planting-to-harvest averages for common field crops;
real values vary by variety, season and region, so callers may always supply
an explicit expected_harvest_date which takes precedence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True, slots=True)
class CropGrowthDuration:
    crop: str
    days_to_harvest: int
    aliases: tuple[str, ...] = ()


CROP_GROWTH_DURATIONS: tuple[CropGrowthDuration, ...] = (
    CropGrowthDuration("Rice", 120, ("paddy",)),
    CropGrowthDuration("Wheat", 120),
    CropGrowthDuration("Maize", 100, ("corn",)),
    CropGrowthDuration("Soybean", 100, ("soya", "soy", "soybeans")),
    CropGrowthDuration("Cotton", 160),
    CropGrowthDuration("Sugarcane", 365),
    CropGrowthDuration("Potato", 90, ("potatoes",)),
    CropGrowthDuration("Tomato", 75, ("tomatoes",)),
    CropGrowthDuration("Onion", 120, ("onions",)),
    CropGrowthDuration("Groundnut", 110, ("peanut", "peanuts")),
    CropGrowthDuration("Barley", 100),
    CropGrowthDuration("Sorghum", 110, ("jowar",)),
    CropGrowthDuration("Pearl Millet", 85, ("bajra", "millet")),
    CropGrowthDuration("Finger Millet", 110, ("ragi",)),
    CropGrowthDuration("Chickpea", 100, ("gram", "chana")),
    CropGrowthDuration("Pigeon Pea", 160, ("tur", "arhar", "red gram")),
    CropGrowthDuration("Mustard", 110, ("rapeseed",)),
    CropGrowthDuration("Sunflower", 95),
    CropGrowthDuration("Chilli", 150, ("chili", "pepper")),
    CropGrowthDuration("Cabbage", 90),
)

# Lower-cased crop name / alias → duration, built once at import.
_LOOKUP: dict[str, CropGrowthDuration] = {
    key.lower(): entry
    for entry in CROP_GROWTH_DURATIONS
    for key in (entry.crop, *entry.aliases)
}


def find_growth_duration(crop_name: str | None) -> CropGrowthDuration | None:
    """Return the duration entry for a crop name or alias (case-insensitive)."""
    if not crop_name:
        return None
    return _LOOKUP.get(crop_name.strip().lower())


def estimate_expected_harvest_date(crop_name: str | None, planting_date: date | None) -> date | None:
    """planting_date + typical days-to-harvest, or None if the crop is unknown."""
    entry = find_growth_duration(crop_name)
    if entry is None or planting_date is None:
        return None
    return planting_date + timedelta(days=entry.days_to_harvest)
