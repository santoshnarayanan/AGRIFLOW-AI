"""
CDD execution statistics — summarise generation and persistence outcomes.

No benchmarking logic; aggregates counts, timing, and validation summary only.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.cdd.persistence import PersistenceResult
from app.cdd.types import CDDDataset, CDDDatasetMetadata
from app.cdd.validation.report import ValidationReport


@dataclass(frozen=True, slots=True)
class CDDStatistics:
    """Summary metrics for a complete CDD execution run."""

    profile: str
    version: str
    seed: int
    generator_version: str
    generated_row_counts: dict[str, int]
    persisted_row_counts: dict[str, int]
    generation_duration_ms: int
    persistence_duration_ms: int
    total_elapsed_ms: int
    validation_passed: bool
    validation_error_count: int
    validation_warning_count: int
    verification_passed: bool


def build_statistics(
    *,
    dataset: CDDDataset,
    metadata: CDDDatasetMetadata,
    validation_report: ValidationReport,
    persistence_result: PersistenceResult | None,
    generation_duration_ms: int,
    persistence_duration_ms: int,
    total_elapsed_ms: int,
    verification_passed: bool,
) -> CDDStatistics:
    """Assemble execution statistics from workflow artefacts."""
    generated = dataset.domain_row_counts()
    persisted = persistence_result.row_counts if persistence_result else {}

    return CDDStatistics(
        profile=dataset.profile,
        version=dataset.version,
        seed=dataset.seed,
        generator_version=metadata.generator_version,
        generated_row_counts=generated,
        persisted_row_counts=persisted,
        generation_duration_ms=generation_duration_ms,
        persistence_duration_ms=persistence_duration_ms,
        total_elapsed_ms=total_elapsed_ms,
        validation_passed=validation_report.passed,
        validation_error_count=validation_report.error_count,
        validation_warning_count=validation_report.warning_count,
        verification_passed=verification_passed,
    )
