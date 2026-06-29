"""
CDD generator — public entry point for in-memory dataset production.

Orchestrates generation, metadata attachment, and pre-persistence validation.
This module does not write to PostgreSQL.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.cdd.config import CDD_SEED, CDD_VERSION, DEFAULT_PROFILE
from app.cdd.orchestrator import CDDOrchestrator
from app.cdd.types import CDDDataset, CDDDatasetMetadata
from app.cdd.validation import CDDValidator, ValidationReport

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CDDGenerationResult:
    """Outcome of a generator run including validation before persistence."""

    dataset: CDDDataset
    metadata: CDDDatasetMetadata
    validation_report: ValidationReport
    generation_duration_ms: int


def generate_cdd(
    *,
    profile: str = DEFAULT_PROFILE,
    version: str = CDD_VERSION,
    seed: int = CDD_SEED,
    notes: str | None = None,
    validate: bool = True,
) -> CDDGenerationResult:
    """
    Generate a Canonical Development Dataset in memory.

    Steps:
        1. Create orchestrator and execute generation
        2. Attach session metadata (including timing)
        3. Run pre-persistence validator

    Does not persist data to PostgreSQL.
    """
    orchestrator = CDDOrchestrator(profile=profile, version=version, seed=seed)

    logger.info(
        "CDD generator starting",
        extra={"profile": profile, "version": version, "seed": seed},
    )

    started = time.perf_counter()
    dataset = orchestrator.generate()
    generation_duration_ms = int((time.perf_counter() - started) * 1000)

    metadata = dataset.attach_metadata(
        generation_duration_ms=generation_duration_ms,
        notes=notes,
    )

    validation_report = (
        CDDValidator().validate(dataset) if validate else _skipped_validation(dataset)
    )

    logger.info(
        "CDD generator completed",
        extra={
            "profile": profile,
            "total_rows": dataset.total_row_count,
            "validation_passed": validation_report.passed,
            "generation_duration_ms": generation_duration_ms,
        },
    )

    return CDDGenerationResult(
        dataset=dataset,
        metadata=metadata,
        validation_report=validation_report,
        generation_duration_ms=generation_duration_ms,
    )


def _skipped_validation(dataset: CDDDataset) -> ValidationReport:
    """Placeholder report when validation is explicitly disabled."""
    return ValidationReport(
        profile=dataset.profile,
        dataset_version=dataset.version,
        passed=True,
        issues=[],
        rules_executed=(),
    )
