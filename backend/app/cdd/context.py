"""
Generation context shared across factories during orchestration.

Carries manifest parameters, deterministic identity utilities, and temporal helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.cdd.config import CDD_SEED, CDD_VERSION, TEMPORAL_END, TEMPORAL_START
from app.cdd.deterministic.rng import DeterministicRNG
from app.cdd.deterministic.uuid import DeterministicUUIDGenerator
from app.cdd.manifest import CDDManifest


@dataclass(slots=True)
class GenerationContext:
    """Shared state for a single deterministic generation run."""

    manifest: CDDManifest
    version: str = CDD_VERSION
    seed: int = CDD_SEED
    uuid_generator: DeterministicUUIDGenerator = field(default_factory=DeterministicUUIDGenerator)
    rng: DeterministicRNG = field(default_factory=lambda: DeterministicRNG(CDD_SEED))

    @property
    def temporal_start(self) -> datetime:
        return TEMPORAL_START

    @property
    def temporal_end(self) -> datetime:
        return TEMPORAL_END

    @property
    def duration_days(self) -> int:
        return self.manifest.temporal_duration_days

    def day_offset(self, ts: datetime) -> int:
        """Whole-day offset from temporal start (0-based)."""
        delta = ts.date() - self.temporal_start.date()
        return max(0, delta.days)

    def iter_hourly_timestamps(self) -> list[datetime]:
        """Yield every hourly timestamp across the temporal horizon."""
        timestamps: list[datetime] = []
        current = self.temporal_start
        while current <= self.temporal_end:
            timestamps.append(current)
            current += timedelta(hours=1)
        return timestamps

    def iter_weather_timestamps(self) -> list[datetime]:
        """Yield weather observation timestamps at manifest cadence."""
        hours = self.manifest.weather.hours_between_observations
        timestamps: list[datetime] = []
        current = self.temporal_start
        while current <= self.temporal_end:
            timestamps.append(current)
            current += timedelta(hours=hours)
        return timestamps

    def iter_satellite_pass_dates(self) -> list[datetime]:
        """Yield satellite pass timestamps at manifest revisit cadence."""
        revisit = self.manifest.satellite.revisit_days
        timestamps: list[datetime] = []
        current = self.temporal_start.replace(hour=10, minute=30, second=0)
        while current <= self.temporal_end:
            timestamps.append(current)
            current += timedelta(days=revisit)
        return timestamps

    def season_for_day(self, day_offset: int) -> str:
        """Return the dominant season phase name for a day offset."""
        for phase in self.manifest.season_phases:
            if phase.start_day <= day_offset <= phase.end_day:
                return phase.name
        return "dormancy"

    def scoped_rng(self, *scope_parts: str | int) -> DeterministicRNG:
        """Derive a scoped RNG for domain-specific stochastic variation."""
        scope = ":".join(str(part) for part in scope_parts)
        return self.rng.for_scope(scope)
