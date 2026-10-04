"""
RecommendationRepository — data access for the Recommendation domain.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import RecommendationStatus, RecommendationType
from app.db.models.recommendation import Recommendation
from app.db.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Recommendation, session)

    async def list_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Recommendation]:
        """Return all recommendations for a field, ordered by creation date descending."""
        result = await self._session.execute(
            select(Recommendation)
            .where(Recommendation.field_id == field_id)
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_field_and_status(
        self,
        field_id: uuid.UUID,
        status: RecommendationStatus,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Recommendation]:
        """Return recommendations for a field filtered by lifecycle status."""
        result = await self._session.execute(
            select(Recommendation)
            .where(
                Recommendation.field_id == field_id,
                Recommendation.status == status,
            )
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_field_and_type(
        self,
        field_id: uuid.UUID,
        recommendation_type: RecommendationType,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Recommendation]:
        """Return recommendations for a field filtered by recommendation type."""
        result = await self._session.execute(
            select(Recommendation)
            .where(
                Recommendation.field_id == field_id,
                Recommendation.recommendation_type == recommendation_type,
            )
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_crop(
        self,
        crop_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Recommendation]:
        """Return all recommendations scoped to a specific crop."""
        result = await self._session.execute(
            select(Recommendation)
            .where(Recommendation.crop_id == crop_id)
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> Recommendation:
        return await super().create(data)

    async def update(
        self, record_id: uuid.UUID, data: dict[str, Any]
    ) -> Recommendation | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)
