"""Disease observation domain factory."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.core.enums import SensorType
from app.cdd.context import GenerationContext
from app.cdd.correlation.engine import compute_disease_probability
from app.cdd.types import (
    CDDCropRecord,
    CDDDiseaseObservationRecord,
    CDDFieldRecord,
    CDDSensorReadingRecord,
    CDDWeatherRecord,
)


def _quantize(value: float, places: int = 2) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)


class DiseaseFactory:
    """Generates episodic disease observations during humid/warm windows."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
        crops: list[CDDCropRecord],
        weather_records: list[CDDWeatherRecord],
        sensor_readings: list[CDDSensorReadingRecord],
    ) -> list[CDDDiseaseObservationRecord]:
        config = ctx.manifest.disease
        field_by_id = {f.id: f for f in fields}
        rotations = {
            (r.field_code, r.crop_name): r
            for r in ctx.manifest.crop_rotations
        }
        weather_by_field = DiseaseFactory._index_weather(weather_records)
        leaf_wetness_by_field = DiseaseFactory._index_leaf_wetness(sensor_readings)

        observations: list[CDDDiseaseObservationRecord] = []
        ordinal = 0

        for crop in crops:
            if not crop.is_susceptible_to_disease:
                continue

            field = field_by_id[crop.field_id]
            rotation = rotations.get((crop.field_code, crop.crop_name))
            disease_name = (
                rotation.primary_disease if rotation and rotation.primary_disease else "Unspecified Blight"
            )
            crop_rng = ctx.scoped_rng("disease", crop.field_code, crop.crop_name)

            candidate_hours = DiseaseFactory._humid_windows(
                weather_by_field.get(str(field.id), []),
                crop.planting_date,
                crop.expected_harvest_date,
            )
            if len(candidate_hours) < config.observations_per_crop:
                candidate_hours = DiseaseFactory._fallback_windows(
                    crop.planting_date,
                    crop.expected_harvest_date,
                    config.observations_per_crop,
                    crop_rng,
                )

            selected = DiseaseFactory._select_observation_times(
                candidate_hours,
                config.observations_per_crop,
                crop_rng,
            )

            for obs_idx, observed_at in enumerate(selected, start=1):
                ordinal += 1
                severity = crop_rng.choices(
                    [s for s, _ in config.severity_distribution],
                    weights=[w for _, w in config.severity_distribution],
                    k=1,
                )[0]
                diagnosis = crop_rng.choice(config.diagnosis_methods)
                leaf_wetness = DiseaseFactory._leaf_wetness_at(
                    leaf_wetness_by_field.get(str(field.id), {}),
                    observed_at,
                    default=45.0,
                )
                weather = DiseaseFactory._nearest_weather(
                    weather_by_field.get(str(field.id), []),
                    observed_at,
                )
                temp_c = float(weather.temperature_c) if weather else 20.0
                humidity = float(weather.humidity_percent) if weather else 85.0

                probability = compute_disease_probability(
                    leaf_wetness=leaf_wetness,
                    air_temperature_c=temp_c,
                    humidity_percent=humidity,
                    consecutive_humid_hours=8,
                    is_susceptible=True,
                )
                severity_boost = 0.0
                if probability < 0.15:
                    severity_boost = 0.0
                affected = _quantize(
                    5.0 + crop_rng.uniform(0, 35.0) + (probability + severity_boost) * 20.0
                )

                observations.append(
                    CDDDiseaseObservationRecord(
                        id=ctx.uuid_generator.generate_scoped(
                            "disease_observation",
                            crop.field_code,
                            f"{crop.crop_name}:{obs_idx}",
                        ),
                        crop_id=crop.id,
                        field_id=field.id,
                        observed_at=observed_at,
                        disease_name=disease_name,
                        severity=severity,
                        affected_area_percent=affected,
                        diagnosis_method=diagnosis,
                        treatment_applied="CDD synthetic scouting follow-up",
                    )
                )

        return observations

    @staticmethod
    def _index_weather(
        records: list[CDDWeatherRecord],
    ) -> dict[str, list[CDDWeatherRecord]]:
        indexed: dict[str, list[CDDWeatherRecord]] = {}
        for record in records:
            indexed.setdefault(str(record.field_id), []).append(record)
        return indexed

    @staticmethod
    def _index_leaf_wetness(
        readings: list[CDDSensorReadingRecord],
    ) -> dict[str, dict[int, float]]:
        indexed: dict[str, dict[int, float]] = {}
        for reading in readings:
            if reading.sensor_type != SensorType.LEAF_WETNESS:
                continue
            indexed.setdefault(str(reading.field_id), {})[
                int(reading.recorded_at.timestamp())
            ] = reading.sensor_value
        return indexed

    @staticmethod
    def _humid_windows(
        weather: list[CDDWeatherRecord],
        planting_date,
        harvest_date,
    ) -> list[datetime]:
        windows: list[datetime] = []
        for record in weather:
            if not (planting_date <= record.recorded_at.date() <= harvest_date):
                continue
            temp = float(record.temperature_c)
            humidity = float(record.humidity_percent)
            if 15.0 <= temp <= 25.0 and humidity > 80.0:
                windows.append(record.recorded_at)
        return windows

    @staticmethod
    def _fallback_windows(
        planting_date,
        harvest_date,
        count: int,
        rng,
    ) -> list[datetime]:
        """Evenly spaced growing-season timestamps when humid windows are sparse."""
        from datetime import timedelta
        from app.cdd.config import CDD_TIMEZONE

        total_days = max(1, (harvest_date - planting_date).days)
        step = max(1, total_days // max(count, 1))
        windows: list[datetime] = []
        for i in range(count):
            day = planting_date + timedelta(days=min(total_days - 1, (i + 1) * step))
            windows.append(
                datetime.combine(day, time(hour=10, minute=0), tzinfo=CDD_TIMEZONE)
            )
        rng.shuffle(windows)
        return sorted(windows)

    @staticmethod
    def _select_observation_times(
        candidates: list[datetime],
        count: int,
        rng,
    ) -> list[datetime]:
        if not candidates:
            return []
        if len(candidates) <= count:
            return candidates[:count]
        step = max(1, len(candidates) // count)
        selected = [candidates[i * step] for i in range(count)]
        rng.shuffle(selected)
        return sorted(selected)

    @staticmethod
    def _nearest_weather(
        records: list[CDDWeatherRecord],
        target: datetime,
    ) -> CDDWeatherRecord | None:
        if not records:
            return None
        return min(records, key=lambda r: abs((r.recorded_at - target).total_seconds()))

    @staticmethod
    def _leaf_wetness_at(
        wetness_map: dict[int, float],
        target: datetime,
        default: float,
    ) -> float:
        if not wetness_map:
            return default
        target_ts = int(target.timestamp())
        nearest = min(wetness_map, key=lambda k: abs(k - target_ts))
        return wetness_map[nearest]
