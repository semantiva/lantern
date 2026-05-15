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

"""Validate Lantern Runtime version, distribution, and Grammar alignment."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.version_info >= (3, 11):
    import tomllib  # type: ignore
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        import tomllib  # type: ignore


def _load_pyproject(pyproject_path: Path) -> dict:
    return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))


def _package_version(pyproject_data: dict) -> str:
    project = pyproject_data.get("project", {})
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit("pyproject.toml must define a static [project].version string")
    return version


def _dynamic_version_present(pyproject_data: dict) -> bool:
    dynamic = pyproject_data.get("tool", {}).get("setuptools", {}).get("dynamic", {})
    return "version" in dynamic


def _distribution_name(pyproject_data: dict) -> str:
    name = pyproject_data.get("project", {}).get("name")
    return name if isinstance(name, str) else ""


def _extract_grammar_dependency(pyproject_data: dict) -> str:
    dependencies = pyproject_data.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        raise SystemExit("pyproject.toml [project].dependencies must be a list")
    for dependency in dependencies:
        if isinstance(dependency, str) and dependency.startswith("lantern-grammar"):
            return dependency
    raise SystemExit("pyproject.toml must declare a lantern-grammar runtime dependency")


def _extract_version_number(version_str: str) -> tuple[int, ...]:
    numbers = [int(value) for value in re.findall(r"\d+", version_str)]
    return tuple(numbers[:3])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--print-package-version", action="store_true")
    args = parser.parse_args()

    pyproject_path = Path(args.pyproject)
    pyproject_data = _load_pyproject(pyproject_path)
    package_version = _package_version(pyproject_data)

    if args.print_package_version:
        print(package_version)
        return

    if _dynamic_version_present(pyproject_data):
        raise SystemExit("pyproject.toml must not define tool.setuptools.dynamic.version")

    dist_name = _distribution_name(pyproject_data)
    if dist_name != "lantern-runtime":
        raise SystemExit(f"Distribution name must be 'lantern-runtime', got {dist_name!r}")

    grammar_dependency = _extract_grammar_dependency(pyproject_data)

    import lantern
    from lantern._compat import GRAMMAR_COMPAT_RANGE

    if lantern.__version__ != package_version:
        raise SystemExit(
            "lantern.__version__ must match [project].version in pyproject.toml: "
            f"{lantern.__version__!r} != {package_version!r}"
        )

    expected_dependency = f"lantern-grammar{GRAMMAR_COMPAT_RANGE}"
    if grammar_dependency != expected_dependency:
        raise SystemExit(
            "lantern-grammar dependency must match lantern.GRAMMAR_COMPAT_RANGE: "
            f"{grammar_dependency!r} != {expected_dependency!r}"
        )

    print(f"Distribution name: {dist_name}")
    print(f"Package version source: {pyproject_path} -> [project].version = {package_version}")
    print(f"Grammar dependency: {grammar_dependency}")

    print("Version alignment checks passed.")


if __name__ == "__main__":
    main()
