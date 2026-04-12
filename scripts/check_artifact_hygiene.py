#!/usr/bin/env python3

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

"""Verify built wheel and sdist artifacts contain the required runtime resources only."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path

DIST_ROOT = Path(__file__).resolve().parents[1] / "dist"
FORBIDDEN_PATTERNS = [
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv/",
    "build/",
    ".venv-smoke",
    "artifacts/",
]
FORBIDDEN_SUFFIXES = [".pyc", ".pyo", ".pyd", ".tmp", ".temp"]
REQUIRED_WHEEL_PATHS = [
    "lantern/skills/packaged_default/SKILL.md",
    "lantern/skills/packaged_default/skill-manifest.json",
    "lantern/workflow/definitions/workbench_registry.yaml",
    "lantern/workflow/definitions/resource_manifest.json",
    "lantern/artifacts/schemas/workbench_schema.json",
]


def _wheel_members(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return archive.namelist()


def _sdist_members(path: Path) -> list[str]:
    with tarfile.open(path, "r:gz") as archive:
        return archive.getnames()


def _check_forbidden(members: list[str], archive_name: str) -> list[str]:
    violations: list[str] = []
    for member in members:
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in member:
                violations.append(f"[{archive_name}] {member} (forbidden pattern {pattern!r})")
                break
        else:
            for suffix in FORBIDDEN_SUFFIXES:
                if member.endswith(suffix):
                    violations.append(f"[{archive_name}] {member} (forbidden suffix {suffix!r})")
                    break
    return violations


def _check_required(members: list[str], archive_name: str) -> list[str]:
    missing: list[str] = []
    for required in REQUIRED_WHEEL_PATHS:
        if not any(member.endswith(required) or member == required for member in members):
            missing.append(f"[{archive_name}] missing required path: {required}")
    return missing


def main() -> None:
    wheels = sorted(DIST_ROOT.glob("*.whl"))
    sdists = sorted(DIST_ROOT.glob("*.tar.gz"))
    if not wheels and not sdists:
        raise SystemExit(f"No distributions found in {DIST_ROOT}. Run the staged build first.")

    violations: list[str] = []
    missing: list[str] = []

    for wheel in wheels:
        members = _wheel_members(wheel)
        violations.extend(_check_forbidden(members, wheel.name))
        missing.extend(_check_required(members, wheel.name))

    for sdist in sdists:
        members = _sdist_members(sdist)
        violations.extend(_check_forbidden(members, sdist.name))

    if violations:
        print("Artifact hygiene violations:")
        for violation in violations:
            print(f"  {violation}")
    if missing:
        print("Artifact hygiene missing required content:")
        for item in missing:
            print(f"  {item}")
    if violations or missing:
        sys.exit(1)

    print(f"Artifact hygiene check passed ({len(wheels)} wheel(s), {len(sdists)} sdist(s)).")


if __name__ == "__main__":
    main()