"""Yield record domain factory."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from app.core.enums import SensorType
from app.cdd.config import CDD_REFERENCE_NOW, CDD_TIMEZONE, TEMPORAL_END
from app.cdd.context import GenerationContext
from app.cdd.correlation.engine import (
    apply_disease_yield_reduction,
    compute_water_stress_factor,
)
from app.cdd.types import (
    CDDCropRecord,
    CDDDiseaseObservationRecord,
    CDDFieldRecord,
    CDDSensorReadingRecord,
    CDDYieldRecord,
)


def _quantize(value: float, places: int = 4) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)


class YieldFactory:
    """Generates harvest yield records with disease and water-stress correlation."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
        crops: list[CDDCropRecord],
        disease_observations: list[CDDDiseaseObservationRecord],
        sensor_readings: list[CDDSensorReadingRecord],
    ) -> list[CDDYieldRecord]:
        rules = ctx.manifest.yield_rules
        field_by_id = {f.id: f for f in fields}
        field_defs = {f.field_code: f for f in ctx.manifest.fields}
        diseases_by_crop: dict[str, list[CDDDiseaseObservationRecord]] = {}
        for obs in disease_observations:
            diseases_by_crop.setdefault(str(obs.crop_id), []).append(obs)

        moisture_by_field = YieldFactory._min_moisture_during_reproductive(
            sensor_readings, crops
        )

        records: list[CDDYieldRecord] = []
        ordinal = 0

        for crop in crops:
            if crop.is_perennial and "Cut" in crop.crop_name:
                record_count = 1
            elif crop.is_perennial:
                record_count = rules.records_per_perennial_crop
            else:
                record_count = rules.records_per_annual_crop

            field = field_by_id[crop.field_id]
            field_def = field_defs[crop.field_code]
            crop_diseases = diseases_by_crop.get(str(crop.id), [])
            severities = [d.severity for d in crop_diseases]

            min_moisture = moisture_by_field.get(
                (str(crop.field_id), crop.crop_name), field_def.soil_moisture_threshold_pct
            )
            stress = compute_water_stress_factor(
                is_irrigated=field.is_irrigated,
                min_soil_moisture_reproductive=min_moisture,
                threshold_pct=field_def.soil_moisture_threshold_pct,
                in_reproductive_stage=True,
            )
            adjusted_yield = apply_disease_yield_reduction(
                crop.expected_yield_tons_ha,
                severities,
                water_stress_factor=stress,
            )

            crop_rng = ctx.scoped_rng("yield", crop.field_code, crop.crop_name)
            harvest_dates = YieldFactory._harvest_dates(
                crop, record_count, crop_rng
            )

            for harvest_idx, harvest_date in enumerate(harvest_dates, start=1):
                ordinal += 1
                method = crop_rng.choice(rules.measurement_methods)
                recorded_at = datetime.combine(
                    harvest_date,
                    time(hour=14, minute=0),
                    tzinfo=CDD_TIMEZONE,
                )
                yield_noise = crop_rng.uniform(-0.08, 0.08)
                yield_value = max(0.0, adjusted_yield * (1.0 + yield_noise))

                records.append(
                    CDDYieldRecord(
                        id=ctx.uuid_generator.generate_scoped(
                            "yield_record",
                            crop.field_code,
                            f"{crop.crop_name}:{harvest_idx}",
                        ),
                        crop_id=crop.id,
                        field_id=field.id,
                        recorded_at=recorded_at,
                        yield_value_tons_ha=_quantize(yield_value),
                        measurement_method=method,
                        area_harvested_ha=_quantize(
                            field.area_hectares * crop_rng.uniform(0.85, 1.0), 4
                        ),
                        moisture_content_percent=_quantize(
                            crop_rng.uniform(12.0, 18.0), 2
                        ),
                        quality_grade=crop_rng.choice(
                            ["Grade 1", "Grade 2", "Feed Grade"]
                        ),
                        notes="CDD synthetic harvest measurement",
                    )
                )

        return records

    @staticmethod
    def _harvest_dates(crop: CDDCropRecord, count: int, rng) -> list[date]:
        if crop.expected_harvest_date is None:
            return []

        max_harvest = min(TEMPORAL_END.date(), CDD_REFERENCE_NOW)

        if count == 1:
            return [min(crop.expected_harvest_date, max_harvest)]

        midpoint = min(crop.expected_harvest_date, max_harvest)
        dates = sorted(
            [
                midpoint - timedelta(days=rng.randint(5, 15)),
                midpoint + timedelta(days=rng.randint(0, 5)),
            ][:count]
        )
        return [min(d, max_harvest) for d in dates]

    @staticmethod
    def _min_moisture_during_reproductive(
        readings: list[CDDSensorReadingRecord],
        crops: list[CDDCropRecord],
    ) -> dict[tuple[str, str], float]:
        crop_windows = {
            (str(c.field_id), c.crop_name): (c.planting_date, c.expected_harvest_date)
            for c in crops
        }
        minima: dict[tuple[str, str], float] = {}

        for reading in readings:
            if reading.sensor_type != SensorType.SOIL_MOISTURE:
                continue
            obs_date = reading.recorded_at.date()
            for key, (plant, harvest) in crop_windows.items():
                reproductive_start = plant + (harvest - plant) * 2 // 3
                if reproductive_start <= obs_date <= harvest:
                    current = minima.get(key, reading.sensor_value)
                    minima[key] = min(current, reading.sensor_value)

        return minima
