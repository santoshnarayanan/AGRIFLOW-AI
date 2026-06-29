"""
In-memory validation framework for CDD datasets.

Validates generated data before database persistence. No PostgreSQL interaction.
"""

from app.cdd.validation.report import ValidationIssue, ValidationReport, ValidationSeverity
from app.cdd.validation.rules import DEFAULT_RULES, list_rules
from app.cdd.validation.validator import CDDValidator

__all__ = [
    "CDDValidator",
    "DEFAULT_RULES",
    "ValidationIssue",
    "ValidationReport",
    "ValidationSeverity",
    "list_rules",
]
