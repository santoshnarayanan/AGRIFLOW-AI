"""
Validation report types for in-memory CDD datasets.

Reports aggregate rule outcomes without referencing PostgreSQL or persistence layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(str, Enum):
    """Issue severity for pre-persistence validation."""

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Single validation finding produced by a modular rule."""

    rule_id: str
    severity: ValidationSeverity
    message: str
    domain: str | None = None
    details: dict[str, object] | None = None


@dataclass(slots=True)
class ValidationReport:
    """
    Aggregated outcome of validating an in-memory ``CDDDataset``.

    A report passes when no ERROR-severity issues are present. Warnings are
    informational and do not block persistence by default.
    """

    profile: str
    dataset_version: str
    passed: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    rules_executed: tuple[str, ...] = ()

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
