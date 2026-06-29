"""
Deterministic UUID v5 generation for CDD entities.

Same CDD_VERSION + CDD_SEED + entity_type + ordinal always yields the same UUID.
"""

from __future__ import annotations

import uuid

from app.cdd.config import CDD_SEED, CDD_UUID_NAMESPACE_NAME, CDD_VERSION


class DeterministicUUIDGenerator:
    """
    Produces stable UUIDs from version, seed, entity type, and ordinal.

    Uses UUID v5 with a fixed namespace derived from the CDD domain name.
  """

    def __init__(
        self,
        version: str = CDD_VERSION,
        seed: int = CDD_SEED,
        namespace_name: str = CDD_UUID_NAMESPACE_NAME,
    ) -> None:
        self._version = version
        self._seed = seed
        self._namespace = uuid.uuid5(uuid.NAMESPACE_DNS, namespace_name)

    @property
    def version(self) -> str:
        return self._version

    @property
    def seed(self) -> int:
        return self._seed

    def generate(self, entity_type: str, ordinal: int | str) -> uuid.UUID:
        """
        Generate a deterministic UUID for an entity.

        Args:
            entity_type: Domain label, e.g. ``farm``, ``field``, ``sensor_reading``.
            ordinal: Unique sequence key within the entity type scope.
        """
        name = f"{self._version}:{self._seed}:{entity_type}:{ordinal}"
        return uuid.uuid5(self._namespace, name)

    def generate_scoped(
        self,
        entity_type: str,
        scope: str,
        ordinal: int | str,
    ) -> uuid.UUID:
        """Generate a UUID with an additional scope segment (e.g. field_code)."""
        name = f"{self._version}:{self._seed}:{entity_type}:{scope}:{ordinal}"
        return uuid.uuid5(self._namespace, name)
