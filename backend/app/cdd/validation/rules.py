"""
Modular in-memory validation rules for CDD datasets.

Each rule inspects the generated dataset against manifest expectations and
referential integrity. Rules do not query PostgreSQL.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING

from app.cdd.config import CDD_REFERENCE_NOW, TEMPORAL_END, TEMPORAL_START
from app.cdd.validation.report import ValidationIssue, ValidationSeverity

if TYPE_CHECKING:
    from app.cdd.manifest import CDDManifest
    from app.cdd.types import CDDDataset

ValidationRule = Callable[["CDDDataset", "CDDManifest"], list[ValidationIssue]]

RULE_ROW_COUNTS = "row_counts"
RULE_FOREIGN_KEYS = "foreign_keys"
RULE_UNIQUE_IDS = "unique_ids"
RULE_TEMPORAL_BOUNDS = "temporal_bounds"
RULE_SEASONAL_CONSISTENCY = "seasonal_consistency"
RULE_DOMAIN_COVERAGE = "domain_coverage"
RULE_PROFILE_CONSISTENCY = "profile_consistency"

DEFAULT_RULES: tuple[str, ...] = (
    RULE_PROFILE_CONSISTENCY,
    RULE_ROW_COUNTS,
    RULE_FOREIGN_KEYS,
    RULE_UNIQUE_IDS,
    RULE_TEMPORAL_BOUNDS,
    RULE_SEASONAL_CONSISTENCY,
    RULE_DOMAIN_COVERAGE,
)


def validate_profile_consistency(
    dataset: CDDDataset,
    manifest: CDDManifest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if dataset.profile != manifest.profile_name:
        issues.append(
            ValidationIssue(
                rule_id=RULE_PROFILE_CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                message=(
                    f"Dataset profile {dataset.profile!r} does not match "
                    f"manifest profile {manifest.profile_name!r}"
                ),
                domain="metadata",
            )
        )
    if manifest.farm_count and len(dataset.farms) != manifest.farm_count:
        issues.append(
            ValidationIssue(
                rule_id=RULE_PROFILE_CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                message=(
                    f"Farm count {len(dataset.farms)} != "
                    f"manifest farm_count {manifest.farm_count}"
                ),
                domain="farms",
            )
        )
    if manifest.field_count and len(dataset.fields) != manifest.field_count:
        issues.append(
            ValidationIssue(
                rule_id=RULE_PROFILE_CONSISTENCY,
                severity=ValidationSeverity.ERROR,
                message=(
                    f"Field count {len(dataset.fields)} != "
                    f"manifest field_count {manifest.field_count}"
                ),
                domain="fields",
            )
        )
    return issues


def validate_row_counts(
    dataset: CDDDataset,
    manifest: CDDManifest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    actual = dataset.domain_row_counts()

    for domain, expected in manifest.target_row_counts.items():
        found = actual.get(domain, 0)
        if found != expected:
            severity = ValidationSeverity.WARNING
            if domain in {"farms", "fields", "soil_profiles", "crops"}:
                severity = ValidationSeverity.ERROR
            issues.append(
                ValidationIssue(
                    rule_id=RULE_ROW_COUNTS,
                    severity=severity,
                    message=f"{domain}: expected {expected}, found {found}",
                    domain=domain,
                    details={"expected": expected, "actual": found},
                )
            )

    return issues


def validate_foreign_keys(
    dataset: CDDDataset,
    manifest: CDDManifest,
) -> list[ValidationIssue]:
    del manifest
    issues: list[ValidationIssue] = []

    farm_ids = {f.id for f in dataset.farms}
    field_ids = {f.id for f in dataset.fields}
    crop_ids = {c.id for c in dataset.crops}

    for field in dataset.fields:
        if field.farm_id not in farm_ids:
            issues.append(_fk_issue("fields", field.id, "farm_id", field.farm_id))

    for soil in dataset.soil_profiles:
        if soil.field_id not in field_ids:
            issues.append(_fk_issue("soil_profiles", soil.id, "field_id", soil.field_id))

    for crop in dataset.crops:
        if crop.field_id not in field_ids:
            issues.append(_fk_issue("crops", crop.id, "field_id", crop.field_id))

    for record in dataset.weather_records:
        if record.field_id not in field_ids:
            issues.append(
                _fk_issue("weather_records", record.id, "field_id", record.field_id)
            )

    for reading in dataset.sensor_readings:
        if reading.field_id not in field_ids:
            issues.append(
                _fk_issue("sensor_readings", reading.id, "field_id", reading.field_id)
            )

    for event in dataset.irrigation_events:
        if event.field_id not in field_ids:
            issues.append(
                _fk_issue("irrigation_events", event.id, "field_id", event.field_id)
            )

    for obs in dataset.satellite_observations:
        if obs.field_id not in field_ids:
            issues.append(
                _fk_issue("satellite_observations", obs.id, "field_id", obs.field_id)
            )

    for obs in dataset.disease_observations:
        if obs.crop_id not in crop_ids:
            issues.append(_fk_issue("disease_observations", obs.id, "crop_id", obs.crop_id))
        if obs.field_id not in field_ids:
            issues.append(
                _fk_issue("disease_observations", obs.id, "field_id", obs.field_id)
            )

    for record in dataset.yield_records:
        if record.crop_id not in crop_ids:
            issues.append(_fk_issue("yield_records", record.id, "crop_id", record.crop_id))
        if record.field_id not in field_ids:
            issues.append(
                _fk_issue("yield_records", record.id, "field_id", record.field_id)
            )

    return issues


def validate_unique_ids(
    dataset: CDDDataset,
    manifest: CDDManifest,
) -> list[ValidationIssue]:
    del manifest
    issues: list[ValidationIssue] = []
    seen: dict[uuid.UUID, str] = {}

    for domain, records in _iter_domain_records(dataset):
        for record in records:
            record_id = record.id
            if record_id in seen:
                issues.append(
                    ValidationIssue(
                        rule_id=RULE_UNIQUE_IDS,
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Duplicate UUID {record_id} in {domain} "
                            f"(previously seen in {seen[record_id]})"
                        ),
                        domain=domain,
                        details={"uuid": str(record_id)},
                    )
                )
            else:
                seen[record_id] = domain

    return issues


def validate_temporal_bounds(
    dataset: CDDDataset,
    manifest: CDDManifest,
) -> list[ValidationIssue]:
    del manifest
    issues: list[ValidationIssue] = []
    reference_end = datetime.combine(
        CDD_REFERENCE_NOW,
        datetime.max.time(),
        tzinfo=TEMPORAL_END.tzinfo,
    )

    checks: list[tuple[str, list, str]] = [
        ("weather_records", dataset.weather_records, "recorded_at"),
        ("sensor_readings", dataset.sensor_readings, "recorded_at"),
        ("irrigation_events", dataset.irrigation_events, "started_at"),
        ("satellite_observations", dataset.satellite_observations, "observed_at"),
        ("disease_observations", dataset.disease_observations, "observed_at"),
        ("yield_records", dataset.yield_records, "recorded_at"),
    ]

    for domain, records, attr in checks:
        for record in records:
            ts: datetime = getattr(record, attr)
            issues.extend(
                _temporal_issues(domain, record.id, ts, reference_end)
            )

    return issues


def validate_seasonal_consistency(
    dataset: CDDDataset,
    manifest: CDDManifest,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    horizon_start = TEMPORAL_START.date()
    horizon_end = TEMPORAL_END.date()

    for crop in dataset.crops:
        if crop.planting_date < horizon_start or crop.planting_date > horizon_end:
            issues.append(
                ValidationIssue(
                    rule_id=RULE_SEASONAL_CONSISTENCY,
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Crop {crop.crop_name!r} planting_date {crop.planting_date} "
                        f"outside CDD horizon"
                    ),
                    domain="crops",
                    details={"crop_id": str(crop.id)},
                )
            )
        if crop.expected_harvest_date:
            if (
                crop.expected_harvest_date < horizon_start
                or crop.expected_harvest_date > horizon_end
            ):
                issues.append(
                    ValidationIssue(
                        rule_id=RULE_SEASONAL_CONSISTENCY,
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Crop {crop.crop_name!r} expected_harvest_date "
                            f"{crop.expected_harvest_date} outside CDD horizon"
                        ),
                        domain="crops",
                        details={"crop_id": str(crop.id)},
                    )
                )

    expected_rotations = len(manifest.crop_rotations)
    if len(dataset.crops) != expected_rotations:
        issues.append(
            ValidationIssue(
                rule_id=RULE_SEASONAL_CONSISTENCY,
                severity=ValidationSeverity.WARNING,
                message=(
                    f"Crop rotation count {len(dataset.crops)} != "
                    f"manifest entries {expected_rotations}"
                ),
                domain="crops",
            )
        )

    return issues


def validate_domain_coverage(
    dataset: CDDDataset,
    manifest: CDDManifest,
) -> list[ValidationIssue]:
    del manifest
    issues: list[ValidationIssue] = []
    required_domains = (
        "farms",
        "fields",
        "soil_profiles",
        "crops",
        "weather_records",
        "sensor_readings",
        "satellite_observations",
        "irrigation_events",
        "disease_observations",
        "yield_records",
    )
    counts = dataset.domain_row_counts()

    for domain in required_domains:
        if counts.get(domain, 0) == 0:
            issues.append(
                ValidationIssue(
                    rule_id=RULE_DOMAIN_COVERAGE,
                    severity=ValidationSeverity.ERROR,
                    message=f"Mandatory domain {domain!r} has zero records",
                    domain=domain,
                )
            )

    # One soil profile per field
    if dataset.soil_profiles and dataset.fields:
        if len(dataset.soil_profiles) != len(dataset.fields):
            issues.append(
                ValidationIssue(
                    rule_id=RULE_DOMAIN_COVERAGE,
                    severity=ValidationSeverity.ERROR,
                    message=(
                        "Soil profile count must match field count (1:1 constraint)"
                    ),
                    domain="soil_profiles",
                    details={
                        "fields": len(dataset.fields),
                        "soil_profiles": len(dataset.soil_profiles),
                    },
                )
            )

    return issues


_RULE_REGISTRY: dict[str, ValidationRule] = {
    RULE_PROFILE_CONSISTENCY: validate_profile_consistency,
    RULE_ROW_COUNTS: validate_row_counts,
    RULE_FOREIGN_KEYS: validate_foreign_keys,
    RULE_UNIQUE_IDS: validate_unique_ids,
    RULE_TEMPORAL_BOUNDS: validate_temporal_bounds,
    RULE_SEASONAL_CONSISTENCY: validate_seasonal_consistency,
    RULE_DOMAIN_COVERAGE: validate_domain_coverage,
}


def get_rule(rule_id: str) -> ValidationRule:
    if rule_id not in _RULE_REGISTRY:
        available = ", ".join(sorted(_RULE_REGISTRY))
        raise ValueError(f"Unknown validation rule {rule_id!r}. Available: {available}")
    return _RULE_REGISTRY[rule_id]


def list_rules() -> tuple[str, ...]:
    return DEFAULT_RULES


def _fk_issue(
    domain: str,
    record_id: uuid.UUID,
    column: str,
    missing_ref: uuid.UUID,
) -> ValidationIssue:
    return ValidationIssue(
        rule_id=RULE_FOREIGN_KEYS,
        severity=ValidationSeverity.ERROR,
        message=f"Missing FK {column}={missing_ref} on {domain} record {record_id}",
        domain=domain,
        details={"column": column, "referenced_id": str(missing_ref)},
    )


def _temporal_issues(
    domain: str,
    record_id: uuid.UUID,
    ts: datetime,
    reference_end: datetime,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if ts.tzinfo is None:
        issues.append(
            ValidationIssue(
                rule_id=RULE_TEMPORAL_BOUNDS,
                severity=ValidationSeverity.ERROR,
                message=f"Naive timestamp on {domain} record {record_id}",
                domain=domain,
            )
        )
    if ts < TEMPORAL_START or ts > TEMPORAL_END:
        issues.append(
            ValidationIssue(
                rule_id=RULE_TEMPORAL_BOUNDS,
                severity=ValidationSeverity.ERROR,
                message=(
                    f"Timestamp {ts.isoformat()} outside CDD window on "
                    f"{domain} record {record_id}"
                ),
                domain=domain,
            )
        )
    if ts > reference_end:
        issues.append(
            ValidationIssue(
                rule_id=RULE_TEMPORAL_BOUNDS,
                severity=ValidationSeverity.ERROR,
                message=(
                    f"Future timestamp relative to CDD_REFERENCE_NOW on "
                    f"{domain} record {record_id}"
                ),
                domain=domain,
            )
        )
    return issues


def _iter_domain_records(dataset: CDDDataset):
    yield "farms", dataset.farms
    yield "fields", dataset.fields
    yield "soil_profiles", dataset.soil_profiles
    yield "crops", dataset.crops
    yield "weather_records", dataset.weather_records
    yield "sensor_readings", dataset.sensor_readings
    yield "satellite_observations", dataset.satellite_observations
    yield "irrigation_events", dataset.irrigation_events
    yield "disease_observations", dataset.disease_observations
    yield "yield_records", dataset.yield_records
