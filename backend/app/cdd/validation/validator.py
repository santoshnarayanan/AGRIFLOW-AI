"""
CDD dataset validator — orchestrates modular in-memory validation rules.

Validation runs entirely against the generated ``CDDDataset`` bundle before any
database persistence step (Step 2C-C).
"""

from __future__ import annotations

from app.cdd.manifest import get_manifest
from app.cdd.types import CDDDataset
from app.cdd.validation.report import ValidationIssue, ValidationReport, ValidationSeverity
from app.cdd.validation.rules import (
    DEFAULT_RULES,
    ValidationRule,
    get_rule,
    list_rules,
)


class CDDValidator:
    """
    Runs modular validation rules against an in-memory dataset.

    The validator is profile-aware via the manifest but does not execute generation
    or interact with PostgreSQL.
    """

    def __init__(self, rules: tuple[str, ...] | None = None) -> None:
        self._rule_ids = rules or DEFAULT_RULES

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return self._rule_ids

    def validate(
        self,
        dataset: CDDDataset,
        *,
        profile: str | None = None,
    ) -> ValidationReport:
        """
        Validate a dataset and return an aggregated report.

        Args:
            dataset: In-memory generated dataset to inspect.
            profile: Manifest profile override; defaults to ``dataset.profile``.
        """
        manifest = get_manifest(profile or dataset.profile)
        issues: list[ValidationIssue] = []

        for rule_id in self._rule_ids:
            rule: ValidationRule = get_rule(rule_id)
            issues.extend(rule(dataset, manifest))

        passed = not any(i.severity == ValidationSeverity.ERROR for i in issues)

        return ValidationReport(
            profile=manifest.profile_name,
            dataset_version=dataset.version,
            passed=passed,
            issues=issues,
            rules_executed=self._rule_ids,
        )
