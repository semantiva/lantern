"""Name-isolation helpers for CH-0001."""

from __future__ import annotations

from pathlib import Path

from .loader import scan_forbidden_names
from .models import NameViolation


def assert_name_isolation(root: str | Path) -> None:
    violations = scan_forbidden_names(root)
    if violations:
        formatted = "; ".join(f"{item.path}:{item.line_number}:{item.line_text}" for item in violations)
        raise AssertionError(f"Forbidden repository-specific name detected: {formatted}")


__all__ = ["NameViolation", "assert_name_isolation", "scan_forbidden_names"]
