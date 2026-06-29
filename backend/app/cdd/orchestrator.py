"""
CDD generation orchestrator.

Manages FK-safe generation sequencing only. Domain logic lives in factories;
cross-domain physics lives in the correlation engine.
"""

from __future__ import annotations

import logging

from app.cdd.config import CDD_SEED, CDD_VERSION, DEFAULT_PROFILE
from app.cdd.context import GenerationContext
from app.cdd.factories.crop import CropFactory
from app.cdd.factories.disease import DiseaseFactory
from app.cdd.factories.farm import FarmFactory
from app.cdd.factories.field import FieldFactory
from app.cdd.factories.irrigation import IrrigationFactory
from app.cdd.factories.satellite import SatelliteFactory
from app.cdd.factories.sensor import SensorFactory
from app.cdd.factories.soil import SoilProfileFactory
from app.cdd.factories.weather import WeatherFactory
from app.cdd.factories.yield_ import YieldFactory
from app.cdd.manifest import get_manifest
from app.cdd.types import CDDDataset

logger = logging.getLogger(__name__)


class CDDOrchestrator:
    """
    Central orchestrator for Canonical Development Dataset generation.

    Generation order (FK-safe):
        Farm → Fields → Soil Profiles → Crops → Weather → Sensors →
        Satellite → Irrigation → Disease → Yield
    """

    def __init__(
        self,
        profile: str = DEFAULT_PROFILE,
        version: str = CDD_VERSION,
        seed: int = CDD_SEED,
    ) -> None:
        self._profile = profile
        self._version = version
        self._seed = seed

    @property
    def profile(self) -> str:
        return self._profile

    @property
    def version(self) -> str:
        return self._version

    @property
    def seed(self) -> int:
        return self._seed

    def generate(self) -> CDDDataset:
        """
        Execute the full generation pipeline and return an in-memory dataset.

        This method does not persist data or interact with the database.
        """
        manifest = get_manifest(self._profile)
        ctx = GenerationContext(manifest=manifest, version=self._version, seed=self._seed)

        logger.info(
            "CDD generation started",
            extra={
                "cdd_version": self._version,
                "cdd_seed": self._seed,
                "profile": self._profile,
            },
        )

        dataset = CDDDataset(
            version=self._version,
            profile=self._profile,
            seed=self._seed,
        )

        dataset.farms = FarmFactory.generate(ctx)
        dataset.fields = FieldFactory.generate(ctx, dataset.farms)
        dataset.soil_profiles = SoilProfileFactory.generate(ctx, dataset.fields)
        dataset.crops = CropFactory.generate(ctx, dataset.fields)
        dataset.weather_records = WeatherFactory.generate(ctx, dataset.fields)
        dataset.sensor_readings = SensorFactory.generate(
            ctx,
            dataset.fields,
            dataset.soil_profiles,
            dataset.weather_records,
        )
        dataset.satellite_observations = SatelliteFactory.generate(
            ctx,
            dataset.fields,
            dataset.crops,
            dataset.soil_profiles,
            dataset.weather_records,
            dataset.sensor_readings,
        )
        dataset.irrigation_events = IrrigationFactory.generate(
            ctx,
            dataset.fields,
            dataset.sensor_readings,
        )
        dataset.disease_observations = DiseaseFactory.generate(
            ctx,
            dataset.fields,
            dataset.crops,
            dataset.weather_records,
            dataset.sensor_readings,
        )
        dataset.yield_records = YieldFactory.generate(
            ctx,
            dataset.fields,
            dataset.crops,
            dataset.disease_observations,
            dataset.sensor_readings,
        )

        logger.info(
            "CDD generation completed",
            extra={
                "cdd_version": self._version,
                "total_rows": dataset.total_row_count,
            },
        )

        return dataset
