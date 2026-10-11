"""Aggregate queries for building dashboard read models."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AlertSeverity, RecommendationStatus
from app.db.models.alert import Alert
from app.db.models.farm import Farm
from app.db.models.field import Field
from app.db.models.recommendation import Recommendation


class ReadModelMetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_farms(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Farm))
        return int(result.scalar_one())

    async def count_fields(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Field))
        return int(result.scalar_one())

    async def alert_counts_for_field(self, field_id: uuid.UUID) -> tuple[int, int]:
        """Return (open_alerts, open_critical_alerts) for a field."""
        result = await self._session.execute(
            select(
                func.count().filter(Alert.is_acknowledged.is_(False)),
                func.count().filter(
                    Alert.is_acknowledged.is_(False),
                    Alert.severity == AlertSeverity.CRITICAL,
                ),
            ).where(Alert.field_id == field_id)
        )
        row = result.one()
        return int(row[0]), int(row[1])

    async def active_recommendation_count_for_field(self, field_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Recommendation)
            .where(
                Recommendation.field_id == field_id,
                Recommendation.status.in_(
                    [RecommendationStatus.PENDING, RecommendationStatus.ACTIVE]
                ),
            )
        )
        return int(result.scalar_one())

    async def open_alert_severity_totals(self) -> dict[str, int]:
        result = await self._session.execute(
            select(Alert.severity, func.count())
            .where(Alert.is_acknowledged.is_(False))
            .group_by(Alert.severity)
        )
        totals = {sev.value: 0 for sev in AlertSeverity}
        for severity, count in result.all():
            totals[severity.value] = int(count)
        return totals

    async def sum_field_projection_totals(
        self,
    ) -> tuple[int, int, int, int]:
        """Sum open/critical alerts and active recs across all field read models; return field row count."""
        stmt = text(
            """
            SELECT
                COALESCE(SUM(open_alerts_count), 0)::bigint,
                COALESCE(SUM(critical_alerts_count), 0)::bigint,
                COALESCE(SUM(active_recommendations_count), 0)::bigint,
                COUNT(*)::bigint
            FROM field_dashboard_read_models
            """
        )
        result = await self._session.execute(stmt)
        row = result.one()
        return int(row[0]), int(row[1]), int(row[2]), int(row[3])
