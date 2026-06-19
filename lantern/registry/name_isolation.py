# Copyright 2025 Lantern Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Name-isolation helpers for CH-0001."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_TEXT_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".md", ".txt", ".toml", ".ini", ".cfg", ".rst", ".sh"}
_SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv"}
_FORBIDDEN_NAME_PATTERN = re.compile(
    "(?i)(?:" + "tier" + r"[-_ ]?" + "h|_" + "tier" + "_" + "h|" + "lantern" + "-" + "governance" + ")"
)


@dataclass(frozen=True)
class NameViolation:
    path: str
    line_number: int
    line_text: str


def scan_forbidden_names(root: str | Path) -> list[NameViolation]:
    root_path = Path(root)
    violations: list[NameViolation] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix and path.suffix.lower() not in _TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if _FORBIDDEN_NAME_PATTERN.search(line):
                violations.append(
                    NameViolation(
                        path=str(path.relative_to(root_path)),
                        line_number=line_number,
                        line_text=line.strip(),
                    )
                )
    return violations


def assert_name_isolation(root: str | Path) -> None:
    violations = scan_forbidden_names(root)
    if violations:
        formatted = "; ".join(f"{item.path}:{item.line_number}:{item.line_text}" for item in violations)
        raise AssertionError(f"Forbidden repository-specific name detected: {formatted}")


__all__ = ["NameViolation", "assert_name_isolation", "scan_forbidden_names"]
