"""Irrigation event domain factory."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.core.enums import SensorType
from app.cdd.context import GenerationContext
from app.cdd.context import GenerationContext
from app.cdd.correlation.engine import (
    apply_irrigation_moisture_recovery,
    compute_irrigation_trigger,
)
from app.cdd.types import (
    CDDFieldRecord,
    CDDIrrigationEventRecord,
    CDDSensorReadingRecord,
)


def _quantize(value: float, places: int = 2) -> Decimal:
    quantizer = Decimal("1").scaleb(-places)
    return Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)


class IrrigationFactory:
    """Generates soil-moisture-triggered irrigation events for irrigated fields."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
        sensor_readings: list[CDDSensorReadingRecord],
    ) -> list[CDDIrrigationEventRecord]:
        rules = ctx.manifest.irrigation
        target_total = ctx.manifest.target_row_counts.get("irrigation_events", 96)
        irrigated_fields = [f for f in fields if f.is_irrigated]
        per_field_targets = IrrigationFactory._distribute_event_targets(
            target_total, len(irrigated_fields), ctx
        )
        field_defs = {f.field_code: f for f in ctx.manifest.fields}
        moisture_series = IrrigationFactory._moisture_series(sensor_readings)
        events: list[CDDIrrigationEventRecord] = []
        ordinal = 0

        for field_idx, field in enumerate(irrigated_fields):
            field_def = field_defs[field.field_code]
            series = moisture_series.get(str(field.id), [])
            if not series:
                continue

            target_count = per_field_targets[field_idx]
            deficit_hours = 0
            generated = 0
            adjusted_moisture = series[0][1] if series else 30.0

            for ts, moisture in series:
                if generated >= target_count:
                    break

                in_season = rules.season_start_month <= ts.month <= rules.season_end_month
                if moisture < field_def.soil_moisture_threshold_pct:
                    deficit_hours += 1
                else:
                    deficit_hours = 0

                if compute_irrigation_trigger(
                    soil_moisture_pct=moisture,
                    threshold_pct=field_def.soil_moisture_threshold_pct,
                    consecutive_deficit_hours=deficit_hours,
                    deficit_hours_required=rules.deficit_hours_required,
                    is_irrigated=True,
                    in_season=in_season,
                ):
                    ordinal += 1
                    generated += 1
                    deficit_hours = 0

                    volume = rules.default_water_volume_liters * (
                        0.85 + ctx.scoped_rng("irrigation_vol", field.field_code, ordinal).random() * 0.3
                    )
                    duration = rules.default_duration_minutes
                    ended_at = ts + timedelta(minutes=float(duration))
                    water_mm = volume / (field.area_hectares * 10000.0) * 10.0
                    adjusted_moisture = apply_irrigation_moisture_recovery(
                        adjusted_moisture, water_mm
                    )

                    events.append(
                        CDDIrrigationEventRecord(
                            id=ctx.uuid_generator.generate_scoped(
                                "irrigation_event", field.field_code, ordinal
                            ),
                            field_id=field.id,
                            started_at=ts,
                            ended_at=ended_at,
                            duration_minutes=_quantize(duration),
                            water_volume_liters=_quantize(volume, 3),
                            irrigation_method=field.irrigation_method,
                            water_source=field_def.water_source,
                            notes="CDD soil-moisture-triggered irrigation",
                        )
                    )

        return events

    @staticmethod
    def _moisture_series(
        readings: list[CDDSensorReadingRecord],
    ) -> dict[str, list[tuple[datetime, float]]]:
        series: dict[str, list[tuple[datetime, float]]] = {}
        for reading in readings:
            if reading.sensor_type != SensorType.SOIL_MOISTURE:
                continue
            series.setdefault(str(reading.field_id), []).append(
                (reading.recorded_at, reading.sensor_value)
            )
        for field_id in series:
            series[field_id].sort(key=lambda item: item[0])
        return series

    @staticmethod
    def _distribute_event_targets(
        target_total: int,
        field_count: int,
        ctx: GenerationContext,
    ) -> list[int]:
        """Distribute manifest irrigation target across irrigated fields."""
        if field_count == 0:
            return []
        rules = ctx.manifest.irrigation
        base = target_total // field_count
        remainder = target_total % field_count
        counts = []
        for idx in range(field_count):
            count = base + (1 if idx < remainder else 0)
            count = max(rules.events_per_irrigated_field_min, count)
            count = min(rules.events_per_irrigated_field_max, count)
            counts.append(count)
        return counts
