"""Read-only feature extraction queries against CAs and approved raw tables."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SensorType, SpectralIndex


class FeatureExtractionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def soil_moisture_7d_mean(
        self,
        field_id: uuid.UUID,
        window_start: datetime,
        as_of: datetime,
    ) -> float | None:
        stmt = text(
            """
            SELECT AVG(avg_sensor_value)::double precision AS value
            FROM ca_sensor_hourly
            WHERE field_id = :field_id
              AND sensor_type = :sensor_type
              AND bucket >= :window_start
              AND bucket < :as_of
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "field_id": field_id,
                "sensor_type": SensorType.SOIL_MOISTURE.value,
                "window_start": window_start,
                "as_of": as_of,
            },
        )
        row = result.first()
        return float(row.value) if row and row.value is not None else None

    async def rainfall_14d_sum(
        self,
        field_id: uuid.UUID,
        window_start: datetime,
        as_of: datetime,
    ) -> float | None:
        stmt = text(
            """
            SELECT COALESCE(SUM(total_rainfall_mm), 0)::double precision AS value
            FROM ca_weather_daily
            WHERE field_id = :field_id
              AND bucket >= :window_start
              AND bucket < :as_of
            """
        )
        result = await self._session.execute(
            stmt,
            {"field_id": field_id, "window_start": window_start, "as_of": as_of},
        )
        row = result.first()
        return float(row.value) if row and row.value is not None else None

    async def gdd_30d_sum(
        self,
        field_id: uuid.UUID,
        window_start: datetime,
        as_of: datetime,
        *,
        gdd_base: float,
    ) -> float | None:
        stmt = text(
            """
            SELECT COALESCE(
                SUM(
                    GREATEST(
                        0,
                        ((min_temperature_c + max_temperature_c) / 2.0) - :gdd_base
                    )
                ),
                0
            )::double precision AS value
            FROM ca_weather_daily
            WHERE field_id = :field_id
              AND bucket >= :window_start
              AND bucket < :as_of
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "field_id": field_id,
                "window_start": window_start,
                "as_of": as_of,
                "gdd_base": gdd_base,
            },
        )
        row = result.first()
        return float(row.value) if row and row.value is not None else None

    async def ndvi_90d_max(
        self,
        field_id: uuid.UUID,
        window_start: datetime,
        as_of: datetime,
    ) -> float | None:
        stmt = text(
            """
            SELECT MAX(max_index_value)::double precision AS value
            FROM ca_satellite_daily
            WHERE field_id = :field_id
              AND spectral_index = :spectral_index
              AND bucket >= :window_start
              AND bucket < :as_of
            """
        )
        result = await self._session.execute(
            stmt,
            {
                "field_id": field_id,
                "spectral_index": SpectralIndex.NDVI.value,
                "window_start": window_start,
                "as_of": as_of,
            },
        )
        row = result.first()
        return float(row.value) if row and row.value is not None else None

    async def irrigation_volume_liters_30d(
        self,
        field_id: uuid.UUID,
        window_start: datetime,
        as_of: datetime,
    ) -> float | None:
        stmt = text(
            """
            SELECT COALESCE(SUM(water_volume_liters), 0)::double precision AS value
            FROM irrigation_events
            WHERE field_id = :field_id
              AND started_at >= :window_start
              AND started_at < :as_of
            """
        )
        result = await self._session.execute(
            stmt,
            {"field_id": field_id, "window_start": window_start, "as_of": as_of},
        )
        row = result.first()
        return float(row.value) if row and row.value is not None else None

    async def disease_severity_max(
        self,
        field_id: uuid.UUID,
        window_start: datetime,
        as_of: datetime,
        crop_id: uuid.UUID | None,
    ) -> str | None:
        crop_clause = "AND crop_id = :crop_id" if crop_id else ""
        stmt = text(
            f"""
            SELECT severity::text AS value
            FROM disease_observations
            WHERE field_id = :field_id
              AND observed_at >= :window_start
              AND observed_at < :as_of
              {crop_clause}
            ORDER BY
              CASE severity
                WHEN 'CRITICAL' THEN 4
                WHEN 'HIGH' THEN 3
                WHEN 'MODERATE' THEN 2
                WHEN 'LOW' THEN 1
                ELSE 0
              END DESC
            LIMIT 1
            """
        )
        params: dict[str, object] = {
            "field_id": field_id,
            "window_start": window_start,
            "as_of": as_of,
        }
        if crop_id:
            params["crop_id"] = crop_id
        result = await self._session.execute(stmt, params)
        row = result.first()
        if row and row.value:
            return str(row.value)
        return None

    async def latest_yield_tons_ha(
        self,
        field_id: uuid.UUID,
        crop_id: uuid.UUID | None,
    ) -> float | None:
        crop_clause = "AND crop_id = :crop_id" if crop_id else ""
        stmt = text(
            f"""
            SELECT yield_value_tons_ha::double precision AS value
            FROM yield_records
            WHERE field_id = :field_id
              {crop_clause}
            ORDER BY recorded_at DESC
            LIMIT 1
            """
        )
        params: dict[str, object] = {"field_id": field_id}
        if crop_id:
            params["crop_id"] = crop_id
        result = await self._session.execute(stmt, params)
        row = result.first()
        return float(row.value) if row and row.value is not None else None

    @staticmethod
    def liters_to_mm(liters: float, area_hectares: Decimal | float | None) -> float | None:
        if area_hectares is None or float(area_hectares) <= 0:
            return None
        area_m2 = float(area_hectares) * 10_000.0
        return (liters / area_m2) * 1000.0
