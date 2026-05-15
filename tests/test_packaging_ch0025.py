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

"""TD-0025 proxy tests for CH-0025 first-package operator-contract truthfulness."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
README = REPO_ROOT / "README.md"
SMOKE = REPO_ROOT / "scripts" / "smoke_test_installed_package.py"

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def _read_project() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]


def _section(name: str) -> str:
    content = README.read_text(encoding="utf-8")
    match = re.search(rf"## {re.escape(name)}\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    assert match is not None, f"missing section: {name}"
    return match.group(1)


def test_td0025_c01_pyproject_declares_install_sufficient_runtime_dependencies() -> None:
    project = _read_project()
    deps = project["dependencies"]
    assert any(dep == "mcp" or dep.startswith("mcp") for dep in deps)
    assert any(dep.startswith("lantern-grammar>=0.4.0,<0.5.0") for dep in deps)


def test_td0025_c05_dev_install_target_includes_typing_dependency_for_yaml() -> None:
    project = _read_project()
    dev = project["optional-dependencies"]["dev"]
    assert any(dep == "types-PyYAML" or dep.startswith("types-PyYAML") for dep in dev)


def test_td0025_c06_readme_presents_one_public_single_operator_posture() -> None:
    content = README.read_text(encoding="utf-8")
    operator = _section("Operator guide")
    assert "single-operator" in content.lower()
    assert "concurrent team operation is unsupported" in content.lower()
    assert "pip install lantern-runtime" in operator
    assert 'pip install "lantern-grammar' not in operator


def test_td0025_c06_source_checkout_notes_are_explicitly_non_public() -> None:
    maintainer = _section("Maintainer guide")
    contributor = _section("Contributor guide")
    assert "not the public operator" in maintainer.lower() or "source-checkout" in maintainer.lower()
    assert "not the public operator" in contributor.lower() or "source-checkout" in contributor.lower()


def test_td0025_c04_smoke_script_uses_bootstrap_doctor_and_serve_preflight() -> None:
    text = SMOKE.read_text(encoding="utf-8")
    assert "bootstrap-product" in text
    assert "doctor" in text
    assert "run_cli" in text
    assert "run_server=False" in text
