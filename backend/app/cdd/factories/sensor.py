"""Sensor reading domain factory."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.enums import SensorType
from app.cdd.context import GenerationContext
from app.cdd.correlation.engine import compute_leaf_wetness, compute_soil_moisture_from_rainfall
from app.cdd.types import (
    CDDFieldRecord,
    CDDSensorReadingRecord,
    CDDSoilProfileRecord,
    CDDWeatherRecord,
)

_SENSOR_UNITS: dict[SensorType, str] = {
    SensorType.SOIL_MOISTURE: "%",
    SensorType.SOIL_TEMPERATURE: "°C",
    SensorType.AIR_TEMPERATURE: "°C",
    SensorType.AIR_HUMIDITY: "%",
    SensorType.LEAF_WETNESS: "%",
}


class SensorFactory:
    """Generates hourly sensor readings using weather-driven correlation."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
        soil_profiles: list[CDDSoilProfileRecord],
        weather_records: list[CDDWeatherRecord],
    ) -> list[CDDSensorReadingRecord]:
        soil_by_field = {s.field_id: s for s in soil_profiles}
        weather_by_field: dict[str, list[CDDWeatherRecord]] = {}
        for record in weather_records:
            weather_by_field.setdefault(str(record.field_id), []).append(record)

        readings: list[CDDSensorReadingRecord] = []
        frequency = ctx.manifest.sensor.frequency_hours
        sensor_types = ctx.manifest.sensor.sensor_types
        ordinal = 0

        for field in fields:
            soil = soil_by_field[field.id]
            field_weather = sorted(
                weather_by_field.get(str(field.id), []),
                key=lambda r: r.recorded_at,
            )
            weather_index = 0
            moisture_state = 32.0
            leaf_wetness_state = 5.0
            field_rng = ctx.scoped_rng("sensor", field.field_code)

            current = ctx.temporal_start
            hour_index = 0

            while current <= ctx.temporal_end:
                while (
                    weather_index + 1 < len(field_weather)
                    and field_weather[weather_index + 1].recorded_at <= current
                ):
                    weather_index += 1

                weather = field_weather[weather_index] if field_weather else None
                hour_rng = field_rng.for_scope(hour_index)

                if weather is not None:
                    temp_c = float(weather.temperature_c)
                    humidity = float(weather.humidity_percent)
                    rainfall = float(weather.rainfall_mm)
                    et0 = max(0.05, (temp_c - 5.0) * 0.04)

                    moisture_state = compute_soil_moisture_from_rainfall(
                        previous_moisture_pct=moisture_state,
                        rainfall_mm=rainfall if current.hour % 6 == 0 else 0.0,
                        evapotranspiration_mm=et0,
                        soil_texture_label=field.soil_type,
                        hours_elapsed=float(frequency),
                    )
                    leaf_wetness_state = compute_leaf_wetness(
                        air_temperature_c=temp_c,
                        humidity_percent=humidity,
                        rainfall_mm=rainfall if current.hour % 6 == 0 else 0.0,
                        previous_wetness=leaf_wetness_state,
                    )
                else:
                    temp_c = 20.0
                    humidity = 60.0

                for sensor_type in sensor_types:
                    ordinal += 1
                    value = SensorFactory._sensor_value(
                        sensor_type=sensor_type,
                        moisture=moisture_state,
                        temp_c=temp_c,
                        humidity=humidity,
                        soil_temp_offset=soil.infiltration_rate_mm_hr,
                        leaf_wetness=leaf_wetness_state,
                        noise=hour_rng.gauss(0, 0.4),
                    )
                    readings.append(
                        CDDSensorReadingRecord(
                            id=ctx.uuid_generator.generate_scoped(
                                "sensor_reading",
                                field.field_code,
                                f"{sensor_type.value}:{hour_index}",
                            ),
                            field_id=field.id,
                            sensor_type=sensor_type,
                            sensor_value=round(value, 4),
                            unit=_SENSOR_UNITS[sensor_type],
                            recorded_at=current,
                        )
                    )

                current += timedelta(hours=frequency)
                hour_index += 1

        return readings

    @staticmethod
    def _sensor_value(
        *,
        sensor_type: SensorType,
        moisture: float,
        temp_c: float,
        humidity: float,
        soil_temp_offset: float,
        leaf_wetness: float,
        noise: float,
    ) -> float:
        if sensor_type == SensorType.SOIL_MOISTURE:
            return max(10.0, min(55.0, moisture + noise))
        if sensor_type == SensorType.SOIL_TEMPERATURE:
            return max(-5.0, min(35.0, temp_c - 2.5 + soil_temp_offset * 0.02 + noise))
        if sensor_type == SensorType.AIR_TEMPERATURE:
            return max(-15.0, min(42.0, temp_c + noise))
        if sensor_type == SensorType.AIR_HUMIDITY:
            return max(20.0, min(100.0, humidity + noise * 2))
        if sensor_type == SensorType.LEAF_WETNESS:
            return max(0.0, min(100.0, leaf_wetness + noise * 3))
        return noise
