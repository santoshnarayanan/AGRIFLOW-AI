"""Platform user persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.platform_user import PlatformUser
from app.db.repositories.base import BaseRepository


class PlatformUserRepository(BaseRepository[PlatformUser]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PlatformUser, session)

    async def get_by_email(self, email: str) -> PlatformUser | None:
        result = await self._session.execute(
            select(PlatformUser).where(PlatformUser.email == email.lower())
        )
        return result.scalar_one_or_none()
