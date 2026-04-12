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

from __future__ import annotations

from pathlib import Path

from lantern.registry.name_isolation import assert_name_isolation, scan_forbidden_names


def test_name_isolation_passes_for_repo_contents() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert_name_isolation(repo_root)


def test_name_isolation_catches_a_violation(tmp_path: Path) -> None:
    tmp_root = tmp_path / "name_violation"
    tmp_root.mkdir(parents=True, exist_ok=True)
    bad_file = tmp_root / "bad.md"
    bad_file.write_text("legacy name: " + "Tier" + "-" + "H" + "\n", encoding="utf-8")
    violations = scan_forbidden_names(tmp_root)
    assert violations
    assert violations[0].path == "bad.md"
    assert violations[0].line_number == 1


def test_name_isolation_catches_companion_repo_name_leak(tmp_path: Path) -> None:
    tmp_root = tmp_path / "governance_name_violation"
    tmp_root.mkdir(parents=True, exist_ok=True)
    bad_file = tmp_root / "bad.md"
    bad_file.write_text(
        "leaked repo alias: " + "lantern" + "-" + "governance" + "\n",
        encoding="utf-8",
    )
    violations = scan_forbidden_names(tmp_root)
    assert violations
    assert violations[0].path == "bad.md"
    assert violations[0].line_number == 1
