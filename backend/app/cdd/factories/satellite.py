"""Satellite observation domain factory."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.core.enums import ProcessingLevel, SatelliteProvider, SpectralIndex
from app.cdd.context import GenerationContext
from app.cdd.correlation.engine import compute_ndvi_from_context
from app.cdd.types import (
    CDDCropRecord,
    CDDFieldRecord,
    CDDSatelliteObservationRecord,
    CDDSoilProfileRecord,
    CDDSensorReadingRecord,
    CDDWeatherRecord,
)


def _quantize(value: float, places: int = 6) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)


_INDEX_FROM_NAME: dict[str, SpectralIndex] = {e.value: e for e in SpectralIndex}


def _derive_index_value(
    base_ndvi: float,
    spectral_index: SpectralIndex,
    rng_value: float,
) -> float:
    """Derive correlated spectral index values from NDVI baseline."""
    if spectral_index == SpectralIndex.NDVI:
        return base_ndvi
    if spectral_index == SpectralIndex.EVI:
        return base_ndvi * 0.92 + 0.03
    if spectral_index == SpectralIndex.SAVI:
        return base_ndvi * 0.88 + 0.05
    if spectral_index == SpectralIndex.NDRE:
        return base_ndvi * 0.75 + rng_value * 0.02
    if spectral_index == SpectralIndex.NDWI:
        return (base_ndvi - 0.35) * 0.6
    if spectral_index == SpectralIndex.LAI:
        return max(0.0, min(8.0, base_ndvi * 9.5))
    if spectral_index == SpectralIndex.GNDVI:
        return base_ndvi * 0.95 + 0.02
    if spectral_index == SpectralIndex.MSAVI:
        return base_ndvi * 0.90 + 0.04
    return base_ndvi


class SatelliteFactory:
    """Generates satellite passes with 8 spectral indices per field per pass."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
        crops: list[CDDCropRecord],
        soil_profiles: list[CDDSoilProfileRecord],
        weather_records: list[CDDWeatherRecord],
        sensor_readings: list[CDDSensorReadingRecord],
    ) -> list[CDDSatelliteObservationRecord]:
        soil_by_field = {s.field_id: s for s in soil_profiles}
        crops_by_field: dict[str, list[CDDCropRecord]] = {}
        for crop in crops:
            crops_by_field.setdefault(crop.field_code, []).append(crop)

        moisture_by_field_hour: dict[str, dict[int, float]] = {}
        for reading in sensor_readings:
            if reading.sensor_type.value != "SOIL_MOISTURE":
                continue
            hour_key = int(reading.recorded_at.timestamp())
            moisture_by_field_hour.setdefault(str(reading.field_id), {})[hour_key] = (
                reading.sensor_value
            )

        weather_by_field: dict[str, list[CDDWeatherRecord]] = {}
        for record in weather_records:
            weather_by_field.setdefault(str(record.field_id), []).append(record)

        sat_config = ctx.manifest.satellite
        indices = [
            _INDEX_FROM_NAME[name] for name in sat_config.spectral_indices
        ]
        processing = ProcessingLevel(sat_config.processing_level)
        pass_dates = ctx.iter_satellite_pass_dates()
        observations: list[CDDSatelliteObservationRecord] = []
        ordinal = 0

        for pass_idx, pass_ts in enumerate(pass_dates):
            provider = (
                SatelliteProvider.SENTINEL_2
                if pass_idx % 4 != 3
                else SatelliteProvider.LANDSAT_8
            )
            resolution = (
                Decimal(str(sat_config.resolution_m))
                if provider == SatelliteProvider.SENTINEL_2
                else Decimal("30.0")
            )

            for field in fields:
                field_crops = crops_by_field.get(field.field_code, [])
                active_crop = SatelliteFactory._active_crop(field_crops, pass_ts.date())
                soil = soil_by_field[field.id]
                field_weather = weather_by_field.get(str(field.id), [])
                nearest_weather = SatelliteFactory._nearest_weather(
                    field_weather, pass_ts
                )
                temp_c = (
                    float(nearest_weather.temperature_c) if nearest_weather else 20.0
                )
                moisture = SatelliteFactory._nearest_moisture(
                    moisture_by_field_hour.get(str(field.id), {}),
                    pass_ts,
                    default=30.0,
                )
                season = ctx.season_for_day(ctx.day_offset(pass_ts))

                if active_crop:
                    base_ndvi = compute_ndvi_from_context(
                        planting_date=active_crop.planting_date,
                        observation_date=pass_ts.date(),
                        expected_harvest_date=active_crop.expected_harvest_date,
                        season_name=season,
                        temperature_c=temp_c,
                        soil_moisture_pct=moisture,
                        is_perennial=active_crop.is_perennial,
                    )
                else:
                    base_ndvi = 0.15

                field_rng = ctx.scoped_rng("satellite", field.field_code, pass_idx)
                cloud_cover = _quantize(field_rng.uniform(2.0, 25.0), 2)

                for index in indices:
                    ordinal += 1
                    index_value = _derive_index_value(
                        base_ndvi,
                        index,
                        field_rng.random(),
                    )
                    if index == SpectralIndex.LAI:
                        value = _quantize(index_value, 3)
                    else:
                        value = _quantize(max(-1.0, min(1.0, index_value)))

                    observations.append(
                        CDDSatelliteObservationRecord(
                            id=ctx.uuid_generator.generate_scoped(
                                "satellite_observation",
                                field.field_code,
                                f"{pass_idx}:{index.value}",
                            ),
                            field_id=field.id,
                            observed_at=pass_ts,
                            satellite_provider=provider,
                            processing_level=processing,
                            spectral_index=index,
                            index_value=value,
                            cloud_cover_percent=cloud_cover,
                            resolution_m=resolution,
                            scene_id=(
                                f"CDD-{field.field_code}-{pass_ts.date().isoformat()}-"
                                f"{index.value}"
                            ),
                            notes="CDD synthetic Sentinel-2 analogue",
                        )
                    )

        return observations

    @staticmethod
    def _active_crop(
        field_crops: list[CDDCropRecord],
        observation_date,
    ) -> CDDCropRecord | None:
        for crop in field_crops:
            if crop.planting_date <= observation_date <= crop.expected_harvest_date:
                return crop
        return field_crops[0] if field_crops else None

    @staticmethod
    def _nearest_weather(
        records: list[CDDWeatherRecord],
        target,
    ) -> CDDWeatherRecord | None:
        if not records:
            return None
        return min(records, key=lambda r: abs((r.recorded_at - target).total_seconds()))

    @staticmethod
    def _nearest_moisture(
        moisture_map: dict[int, float],
        target,
        default: float,
    ) -> float:
        if not moisture_map:
            return default
        target_ts = int(target.timestamp())
        nearest_key = min(moisture_map, key=lambda k: abs(k - target_ts))
        return moisture_map[nearest_key]
