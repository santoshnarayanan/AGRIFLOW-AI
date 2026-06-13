"""
SoilProfile repository.

Extends BaseRepository with the one query that BaseRepository cannot provide
generically: resolving a SoilProfile by its parent field_id.

Because the Field → SoilProfile relationship is one-to-one, ``get_by_field_id``
returns a single instance (or None) rather than a list.  The uniqueness
invariant is enforced at the database level (UNIQUE constraint on field_id) and
validated at the service layer — not here.

All write operations (create, update, delete) and get_by_id are inherited from
BaseRepository unchanged.

Methods
-------
get_by_id        — fetch by primary key UUID (inherited)
create           — insert a new row from a field-value dict (inherited)
update           — sparse patch by primary key UUID (inherited)
delete           — remove by primary key UUID (inherited)
get_by_field_id  — fetch the profile that belongs to a specific field
exists_for_field — lightweight presence probe by field_id; avoids hydrating
                   the full row when the service layer only needs a boolean
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.soil_profile import SoilProfile
from app.db.repositories.base import BaseRepository


class SoilProfileRepository(BaseRepository[SoilProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SoilProfile, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> SoilProfile | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> SoilProfile:
        return await super().create(data)

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> SoilProfile | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)

    # ── SoilProfile-specific queries ──────────────────────────────────────────

    async def get_by_field_id(self, field_id: uuid.UUID) -> SoilProfile | None:
        """
        Return the SoilProfile for the given field, or None if one does not
        exist yet.

        The one-to-one cardinality means this query always returns at most one
        row, enforced by the UNIQUE constraint on ``soil_profiles.field_id``.
        ``scalar_one_or_none`` is used rather than ``scalars().first()`` to
        surface any accidental constraint violation as a DB error rather than
        silently returning only the first match.
        """
        result = await self._session.execute(
            select(SoilProfile).where(SoilProfile.field_id == field_id)
        )
        return result.scalar_one_or_none()

    async def exists_for_field(self, field_id: uuid.UUID) -> bool:
        """
        Return True if a SoilProfile already exists for the given field.

        Uses a SELECT on the primary key column only — avoids hydrating the
        full ORM instance when only presence needs to be confirmed.  The
        service layer uses this probe to decide whether to create or reject
        a duplicate profile request; no business rule is encoded here.
        """
        result = await self._session.execute(
            select(SoilProfile.id).where(SoilProfile.field_id == field_id)
        )
        return result.scalar_one_or_none() is not None
