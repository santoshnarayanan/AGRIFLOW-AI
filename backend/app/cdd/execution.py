"""
CDD execution layer — end-to-end generation, validation, persistence, and verification.

Orchestrates the complete Step 2C-C workflow without exposing APIs or modifying
repositories or services.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cdd.config import CDD_SEED, CDD_VERSION, DEFAULT_PROFILE
from app.cdd.generator import CDDGenerationResult, generate_cdd
from app.cdd.persistence import PersistenceResult, persist_cdd_dataset
from app.cdd.statistics import CDDStatistics, build_statistics
from app.cdd.types import CDDDataset, CDDDatasetMetadata
from app.cdd.validation.report import ValidationReport
from app.db.models.crop import Crop
from app.db.models.disease_observation import DiseaseObservation
from app.db.models.farm import Farm
from app.db.models.field import Field
from app.db.models.satellite_observation import SatelliteObservation
from app.db.models.sensor_reading import SensorReading
from app.db.models.weather_record import WeatherRecord
from app.db.models.yield_record import YieldRecord
from app.db.session import AsyncSessionFactory

logger = logging.getLogger(__name__)

# Domains verified against PostgreSQL after persistence (per Step 2C-C spec).
_VERIFICATION_DOMAINS: tuple[str, ...] = (
    "farms",
    "fields",
    "crops",
    "weather_records",
    "sensor_readings",
    "satellite_observations",
    "disease_observations",
    "yield_records",
)


@dataclass(frozen=True, slots=True)
class DomainVerification:
    """Expected vs actual row count for a single domain."""

    domain: str
    expected: int
    actual: int

    @property
    def matched(self) -> bool:
        return self.expected == self.actual


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of post-persistence database verification."""

    domains: tuple[DomainVerification, ...]

    @property
    def passed(self) -> bool:
        return all(d.matched for d in self.domains)

    def mismatches(self) -> list[DomainVerification]:
        return [d for d in self.domains if not d.matched]


@dataclass(slots=True)
class CDDExecutionReport:
    """Complete report for a CDD execution run."""

    success: bool
    statistics: CDDStatistics | None
    metadata: CDDDatasetMetadata | None
    validation_report: ValidationReport | None
    persistence_result: PersistenceResult | None
    verification_result: VerificationResult | None
    errors: list[str] = field(default_factory=list)


async def _count_farms(session: AsyncSession, farm_ids: list[uuid.UUID]) -> int:
    if not farm_ids:
        return 0
    result = await session.execute(
        select(func.count()).select_from(Farm).where(Farm.id.in_(farm_ids))
    )
    return int(result.scalar_one())


async def _count_fields(session: AsyncSession, farm_ids: list[uuid.UUID]) -> int:
    if not farm_ids:
        return 0
    result = await session.execute(
        select(func.count()).select_from(Field).where(Field.farm_id.in_(farm_ids))
    )
    return int(result.scalar_one())


async def _count_crops(session: AsyncSession, field_ids: list[uuid.UUID]) -> int:
    if not field_ids:
        return 0
    result = await session.execute(
        select(func.count()).select_from(Crop).where(Crop.field_id.in_(field_ids))
    )
    return int(result.scalar_one())


async def _count_weather(session: AsyncSession, field_ids: list[uuid.UUID]) -> int:
    if not field_ids:
        return 0
    result = await session.execute(
        select(func.count())
        .select_from(WeatherRecord)
        .where(WeatherRecord.field_id.in_(field_ids))
    )
    return int(result.scalar_one())


async def _count_sensors(session: AsyncSession, field_ids: list[uuid.UUID]) -> int:
    if not field_ids:
        return 0
    result = await session.execute(
        select(func.count())
        .select_from(SensorReading)
        .where(SensorReading.field_id.in_(field_ids))
    )
    return int(result.scalar_one())


async def _count_satellite(session: AsyncSession, field_ids: list[uuid.UUID]) -> int:
    if not field_ids:
        return 0
    result = await session.execute(
        select(func.count())
        .select_from(SatelliteObservation)
        .where(SatelliteObservation.field_id.in_(field_ids))
    )
    return int(result.scalar_one())


async def _count_disease(session: AsyncSession, crop_ids: list[uuid.UUID]) -> int:
    if not crop_ids:
        return 0
    result = await session.execute(
        select(func.count())
        .select_from(DiseaseObservation)
        .where(DiseaseObservation.crop_id.in_(crop_ids))
    )
    return int(result.scalar_one())


async def _count_yield(session: AsyncSession, crop_ids: list[uuid.UUID]) -> int:
    if not crop_ids:
        return 0
    result = await session.execute(
        select(func.count())
        .select_from(YieldRecord)
        .where(YieldRecord.crop_id.in_(crop_ids))
    )
    return int(result.scalar_one())


async def verify_cdd_persistence(
    session: AsyncSession,
    dataset: CDDDataset,
) -> VerificationResult:
    """
    Compare PostgreSQL row counts with the generated dataset.

    Counts are scoped to the farm, field, and crop IDs produced by this run so
    verification remains accurate when other data exists in the database.
    """
    farm_ids = [f.id for f in dataset.farms]
    field_ids = [f.id for f in dataset.fields]
    crop_ids = [c.id for c in dataset.crops]
    expected = dataset.domain_row_counts()

    counters = {
        "farms": await _count_farms(session, farm_ids),
        "fields": await _count_fields(session, farm_ids),
        "crops": await _count_crops(session, field_ids),
        "weather_records": await _count_weather(session, field_ids),
        "sensor_readings": await _count_sensors(session, field_ids),
        "satellite_observations": await _count_satellite(session, field_ids),
        "disease_observations": await _count_disease(session, crop_ids),
        "yield_records": await _count_yield(session, crop_ids),
    }

    domains = tuple(
        DomainVerification(
            domain=domain,
            expected=expected[domain],
            actual=counters[domain],
        )
        for domain in _VERIFICATION_DOMAINS
    )

    logger.info(
        "CDD persistence verification completed",
        extra={"passed": all(d.matched for d in domains)},
    )

    return VerificationResult(domains=domains)


async def execute_cdd_workflow(
    *,
    profile: str = DEFAULT_PROFILE,
    version: str = CDD_VERSION,
    seed: int = CDD_SEED,
    notes: str | None = None,
    session: AsyncSession | None = None,
) -> CDDExecutionReport:
    """
    Run the complete CDD workflow:

        Generation → Metadata → Validation → Persistence → Verification → Statistics
    """
    errors: list[str] = []
    workflow_started = time.perf_counter()

    logger.info(
        "CDD execution workflow starting",
        extra={"profile": profile, "version": version, "seed": seed},
    )

    # ── Generation + metadata + validation ───────────────────────────────────
    gen_result: CDDGenerationResult = generate_cdd(
        profile=profile,
        version=version,
        seed=seed,
        notes=notes,
    )

    if not gen_result.validation_report.passed:
        for issue in gen_result.validation_report.errors():
            errors.append(f"[{issue.rule_id}] {issue.message}")

        return CDDExecutionReport(
            success=False,
            statistics=None,
            metadata=gen_result.metadata,
            validation_report=gen_result.validation_report,
            persistence_result=None,
            verification_result=None,
            errors=errors,
        )

    persistence_result: PersistenceResult | None = None
    verification_result: VerificationResult | None = None

    async def _run_persistence_and_verification(
        active_session: AsyncSession,
    ) -> CDDExecutionReport:
        nonlocal persistence_result, verification_result

        persistence_started = time.perf_counter()
        persistence_result = await persist_cdd_dataset(active_session, gen_result.dataset)
        persistence_duration_ms = int((time.perf_counter() - persistence_started) * 1000)

        verification_result = await verify_cdd_persistence(active_session, gen_result.dataset)

        if not verification_result.passed:
            for mismatch in verification_result.mismatches():
                errors.append(
                    f"Verification failed for {mismatch.domain}: "
                    f"expected {mismatch.expected}, found {mismatch.actual}"
                )

        total_elapsed_ms = int((time.perf_counter() - workflow_started) * 1000)

        statistics = build_statistics(
            dataset=gen_result.dataset,
            metadata=gen_result.metadata,
            validation_report=gen_result.validation_report,
            persistence_result=persistence_result,
            generation_duration_ms=gen_result.generation_duration_ms,
            persistence_duration_ms=persistence_duration_ms,
            total_elapsed_ms=total_elapsed_ms,
            verification_passed=verification_result.passed,
        )

        success = verification_result.passed

        logger.info(
            "CDD execution workflow completed",
            extra={
                "success": success,
                "total_elapsed_ms": total_elapsed_ms,
                "total_persisted": persistence_result.total_rows,
            },
        )

        return CDDExecutionReport(
            success=success,
            statistics=statistics,
            metadata=gen_result.metadata,
            validation_report=gen_result.validation_report,
            persistence_result=persistence_result,
            verification_result=verification_result,
            errors=errors,
        )

    try:
        if session is not None:
            return await _run_persistence_and_verification(session)

        async with AsyncSessionFactory() as managed_session:
            return await _run_persistence_and_verification(managed_session)

    except Exception as exc:
        errors.append(f"Persistence failed: {exc}")
        logger.exception("CDD execution workflow failed")

        total_elapsed_ms = int((time.perf_counter() - workflow_started) * 1000)

        statistics = build_statistics(
            dataset=gen_result.dataset,
            metadata=gen_result.metadata,
            validation_report=gen_result.validation_report,
            persistence_result=persistence_result,
            generation_duration_ms=gen_result.generation_duration_ms,
            persistence_duration_ms=0,
            total_elapsed_ms=total_elapsed_ms,
            verification_passed=False,
        )

        return CDDExecutionReport(
            success=False,
            statistics=statistics,
            metadata=gen_result.metadata,
            validation_report=gen_result.validation_report,
            persistence_result=persistence_result,
            verification_result=verification_result,
            errors=errors,
        )
