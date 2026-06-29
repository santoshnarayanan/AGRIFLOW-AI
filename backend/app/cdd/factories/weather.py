"""Weather domain factory."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from app.cdd.context import GenerationContext
from app.cdd.types import CDDFieldRecord, CDDWeatherRecord


def _quantize(value: float, places: int = 2) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)


def _seasonal_temperature(day_offset: int, hour: int, rng_noise: float) -> float:
    """Parameterised seasonal temperature curve with diurnal variation."""
    seasonal_base = 8.0 + 22.0 * _seasonal_sine(day_offset)
    diurnal = 6.0 * _diurnal_sine(hour)
    return seasonal_base + diurnal + rng_noise


def _seasonal_sine(day_offset: int) -> float:
    import math

    return (math.sin((day_offset / 365.0) * 2 * math.pi - math.pi / 2) + 1) / 2


def _diurnal_sine(hour: int) -> float:
    import math

    return math.sin((hour / 24.0) * 2 * math.pi - math.pi / 2)


class WeatherFactory:
    """Generates weather observations at manifest cadence per field."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
    ) -> list[CDDWeatherRecord]:
        records: list[CDDWeatherRecord] = []
        timestamps = ctx.iter_weather_timestamps()
        ordinal = 0

        for field in fields:
            field_rng = ctx.scoped_rng("weather", field.field_code)

            for ts in timestamps:
                ordinal += 1
                day_offset = ctx.day_offset(ts)
                day_rng = field_rng.for_scope(day_offset)
                noise = day_rng.gauss(0, 1.2)

                temp_c = _seasonal_temperature(day_offset, ts.hour, noise)
                humidity = max(
                    35.0,
                    min(
                        98.0,
                        55.0
                        + 25.0 * _seasonal_sine(day_offset + 30)
                        - (temp_c - 20.0) * 1.5
                        + day_rng.gauss(0, 3.0),
                    ),
                )

                rain_prob = 0.18 if ctx.season_for_day(day_offset) in {
                    "planting",
                    "early_growth",
                    "post_harvest",
                } else 0.08
                rainfall = (
                    day_rng.uniform(2.0, 18.0) if day_rng.random() < rain_prob else 0.0
                )

                wind = max(0.0, day_rng.uniform(4.0, 28.0))
                solar = max(
                    0.0,
                    850.0 * max(0.0, _diurnal_sine(ts.hour)) * _seasonal_sine(day_offset),
                )

                records.append(
                    CDDWeatherRecord(
                        id=ctx.uuid_generator.generate_scoped(
                            "weather_record", field.field_code, ordinal
                        ),
                        field_id=field.id,
                        recorded_at=ts,
                        temperature_c=_quantize(temp_c),
                        humidity_percent=_quantize(humidity),
                        rainfall_mm=_quantize(rainfall),
                        wind_speed_kmh=_quantize(wind),
                        solar_radiation_wm2=_quantize(solar, 3),
                        temperature_min_c=_quantize(temp_c - 4.0),
                        temperature_max_c=_quantize(temp_c + 5.0),
                        data_source="CDD",
                    )
                )

        return records
