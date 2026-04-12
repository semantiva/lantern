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

"""TD-0013 proxy tests for the CH-0012 packaging closeout slice."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
README = REPO_ROOT / "README.md"


def test_pyproject_distribution_identity() -> None:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib  # type: ignore

    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    project = data["project"]
    assert project["name"] == "lantern-runtime"
    assert isinstance(project.get("version"), str) and project["version"]
    assert "version" not in data.get("tool", {}).get("setuptools", {}).get("dynamic", {})


def test_lantern_package_version_matches_pyproject() -> None:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib  # type: ignore

    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    import lantern

    assert lantern.__version__ == data["project"]["version"]


def test_console_entrypoints_declared() -> None:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib  # type: ignore

    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = data["project"].get("scripts", {})
    assert scripts.get("lantern") == "lantern.cli.main:main"
    assert scripts.get("lantern-runtime") == "lantern.cli.main:main"


def test_cli_main_importable() -> None:
    from lantern.cli.main import main  # noqa: F401


def test_packaged_default_assets_exist() -> None:
    from lantern._compat import get_package_resource_path

    assert get_package_resource_path("skills/packaged_default/SKILL.md").exists()
    assert get_package_resource_path("skills/packaged_default/skill-manifest.json").exists()


def test_build_verify_only_exits_cleanly() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "build_runtime_release.py"), "--verify-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"build_runtime_release.py --verify-only failed:\n{result.stdout}\n{result.stderr}"
    assert "verified" in result.stdout.lower()


def test_grammar_compat_range_declared() -> None:
    from lantern._compat import GRAMMAR_COMPAT_RANGE

    assert GRAMMAR_COMPAT_RANGE
    assert GRAMMAR_COMPAT_RANGE.startswith(">=")


def test_grammar_compatibility_returns_structured_result() -> None:
    from lantern._compat import check_grammar_compatibility

    result = check_grammar_compatibility()
    assert result["status"] in {"ok", "missing", "unsupported"}
    assert {"supported_range", "installed_package_version", "installed_model_version", "message"} <= result.keys()


def test_grammar_compatibility_unsupported_is_descriptive() -> None:
    import lantern._compat as compat_mod

    original_max = compat_mod._GRAMMAR_MAX_EXCLUSIVE
    try:
        compat_mod._GRAMMAR_MAX_EXCLUSIVE = (0, 0, 0)
        result = compat_mod.check_grammar_compatibility()
    finally:
        compat_mod._GRAMMAR_MAX_EXCLUSIVE = original_max

    if result["status"] == "missing":
        pytest.skip("lantern-grammar is not installed in the active test environment")

    assert result["status"] == "unsupported"
    assert result["installed_package_version"]
    assert compat_mod.GRAMMAR_COMPAT_RANGE in result["message"]
    assert result["installed_package_version"] in result["message"]


def test_doctor_probe_grammar_uses_structured_result() -> None:
    from lantern.cli.doctor import _probe_grammar

    findings: list[dict[str, str]] = []
    result = _probe_grammar(findings)
    assert result["status"] in {"ok", "missing", "unsupported"}
    assert "supported_range" in result


@pytest.mark.parametrize(
    "script_name",
    [
        "check_version_alignment.py",
        "build_runtime_release.py",
        "check_license_headers.py",
        "generate_sbom.py",
        "generate_license_report.py",
        "smoke_test_installed_package.py",
        "check_repo_hygiene.py",
        "check_artifact_hygiene.py",
    ],
)
def test_release_script_exists_and_is_importable(script_name: str) -> None:
    script_path = REPO_ROOT / "scripts" / script_name
    assert script_path.exists()
    result = subprocess.run([sys.executable, "-m", "py_compile", str(script_path)], capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()


def test_ci_pipeline_yaml_exists() -> None:
    assert (REPO_ROOT / ".github" / "workflows" / "ci-pipeline.yaml").exists()


def test_pre_commit_config_exists() -> None:
    assert (REPO_ROOT / ".pre-commit-config.yaml").exists()


def test_license_and_notice_exist() -> None:
    assert (REPO_ROOT / "LICENSE").exists()
    assert (REPO_ROOT / "NOTICE").exists()


def test_readme_role_sections_present() -> None:
    content = README.read_text(encoding="utf-8")
    assert "## Operator guide" in content
    assert "## Maintainer guide" in content
    assert "## Contributor guide" in content


def test_readme_operator_section_no_editable_install() -> None:
    content = README.read_text(encoding="utf-8")
    operator_match = re.search(r"## Operator guide\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    assert operator_match is not None
    operator_section = operator_match.group(1)
    assert "pip install -e" not in operator_section
    assert "sibling" not in operator_section.lower()
