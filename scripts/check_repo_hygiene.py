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

"""Reject tracked cache, temp, and build-output artifacts."""

from __future__ import annotations

import subprocess
import sys

FORBIDDEN_PATTERNS = [
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".venv/",
    "venv/",
    "build/",
    "dist/",
    ".venv-smoke/",
    "/artifacts/",
]
FORBIDDEN_SUFFIXES = [".pyc", ".pyo", ".pyd", ".tmp", ".temp"]


def _tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], capture_output=True, check=True, text=True)
    return result.stdout.splitlines()


def main() -> None:
    try:
        tracked_files = _tracked_files()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"git ls-files failed: {exc}") from exc

    violations: list[str] = []
    for path in tracked_files:
        for pattern in FORBIDDEN_PATTERNS:
            if pattern == "/artifacts/":
                if path.startswith("artifacts/"):
                    violations.append(f"{path} (matches forbidden pattern 'artifacts/')")
                    break
                continue
            if pattern in path or path.startswith(pattern.rstrip("/")):
                violations.append(f"{path} (matches forbidden pattern {pattern!r})")
                break
        else:
            for suffix in FORBIDDEN_SUFFIXES:
                if path.endswith(suffix):
                    violations.append(f"{path} (forbidden suffix {suffix!r})")
                    break

    if violations:
        print("Repository hygiene check failed:")
        for violation in violations:
            print(f"  {violation}")
        sys.exit(1)

    print(f"Repository hygiene check passed ({len(tracked_files)} tracked files, 0 violations).")


if __name__ == "__main__":
    main()
