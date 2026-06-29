"""
Deterministic pseudo-random number generation for CDD.

Uses Python's ``random.Random`` with explicitly derived seeds so identical
version + seed + scope inputs produce identical value sequences.
"""

from __future__ import annotations

import hashlib
import random
from typing import Sequence


class DeterministicRNG:
    """
    Seedable PRNG with hierarchical scope derivation.

    Architecture reference:
    - Weather noise: base seed + day offset
    - Sensor noise: base seed + field scope + hour offset
    """

    def __init__(self, seed: int) -> None:
        self._base_seed = seed
        self._root = random.Random(seed)

    @property
    def base_seed(self) -> int:
        return self._base_seed

    @staticmethod
    def _derive_seed(base_seed: int, scope: str) -> int:
        digest = hashlib.sha256(f"{base_seed}:{scope}".encode()).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False)

    def for_scope(self, scope: str) -> DeterministicRNG:
        """Return a child RNG bound to a derived scope seed."""
        child = DeterministicRNG(self._derive_seed(self._base_seed, scope))
        return child

    def random(self) -> float:
        return self._root.random()

    def uniform(self, a: float, b: float) -> float:
        return self._root.uniform(a, b)

    def gauss(self, mu: float, sigma: float) -> float:
        return self._root.gauss(mu, sigma)

    def randint(self, a: int, b: int) -> int:
        return self._root.randint(a, b)

    def choice(self, seq: Sequence):
        return self._root.choice(seq)

    def choices(self, population: Sequence, weights: Sequence[float] | None = None, k: int = 1):
        return self._root.choices(population, weights=weights, k=k)

    def shuffle(self, items: list) -> None:
        self._root.shuffle(items)
