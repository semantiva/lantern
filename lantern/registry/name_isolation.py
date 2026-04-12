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

from pathlib import Path

from .loader import scan_forbidden_names
from .models import NameViolation


def assert_name_isolation(root: str | Path) -> None:
    violations = scan_forbidden_names(root)
    if violations:
        formatted = "; ".join(f"{item.path}:{item.line_number}:{item.line_text}" for item in violations)
        raise AssertionError(f"Forbidden repository-specific name detected: {formatted}")


__all__ = ["NameViolation", "assert_name_isolation", "scan_forbidden_names"]
