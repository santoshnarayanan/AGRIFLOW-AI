"""
Generic async repository providing standard CRUD operations.

Domain repositories extend BaseRepository[ConcreteModel] and inherit all
common DB operations without boilerplate.  Custom queries are added in
concrete subclasses only.

Type parameter T must be a SQLAlchemy ORM model class.
"""

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    async def get_by_id(self, record_id: uuid.UUID) -> ModelT | None:
        result = await self._session.execute(
            select(self._model).where(self._model.id == record_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self._session.execute(
            select(self._model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> ModelT:
        instance = self._model(**data)
        self._session.add(instance)
        await self._session.flush()  # populate server-side defaults (id, created_at)
        await self._session.refresh(instance)
        return instance

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> ModelT | None:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return None
        for field, value in data.items():
            setattr(instance, field, value)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, record_id: uuid.UUID) -> bool:
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        await self._session.delete(instance)
        await self._session.flush()
        return True
