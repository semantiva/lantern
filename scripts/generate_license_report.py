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

"""Generate a deterministic JSON license report for runtime dependencies."""

from __future__ import annotations

import argparse
import json
import re
from importlib import metadata
from pathlib import Path

NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+")


def _canonicalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_name(requirement: str) -> str | None:
    match = NAME_RE.match(requirement.strip())
    if match is None:
        return None
    return _canonicalize(match.group(0))


def _include_requirement(requirement: str) -> bool:
    marker = requirement.partition(";")[2].strip().lower()
    return "extra ==" not in marker and "extra!=" not in marker


def _license_name(dist: metadata.Distribution) -> str:
    license_field = (dist.metadata.get("License") or "").strip()  # type: ignore[arg-type]
    if license_field and license_field.upper() != "UNKNOWN":
        return license_field

    classifiers = dist.metadata.get_all("Classifier") or []
    license_classifiers = [classifier for classifier in classifiers if classifier.startswith("License ::")]
    if license_classifiers:
        return " | ".join(sorted(license_classifiers))

    return "UNKNOWN"


def _homepage(dist: metadata.Distribution) -> str:
    homepage = (dist.metadata.get("Home-page") or "").strip()  # type: ignore[arg-type]
    if homepage:
        return homepage
    project_urls = dist.metadata.get_all("Project-URL") or []
    return sorted(project_urls)[0] if project_urls else ""


def _dependency_closure(root_names: list[str]) -> list[metadata.Distribution]:
    queue = [_canonicalize(name) for name in root_names]
    seen: set[str] = set()
    ordered: list[metadata.Distribution] = []

    while queue:
        current = queue.pop(0)
        if current in seen:
            continue

        dist = metadata.distribution(current)
        canonical_name = _canonicalize(dist.metadata["Name"])
        if canonical_name in seen:
            continue

        seen.add(canonical_name)
        ordered.append(dist)

        for requirement in dist.requires or []:
            if not _include_requirement(requirement):
                continue
            requirement_name = _requirement_name(requirement)
            if requirement_name and requirement_name not in seen:
                queue.append(requirement_name)

    return sorted(ordered, key=lambda dist: _canonicalize(dist.metadata["Name"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distribution", action="append", dest="distributions", default=["lantern-runtime"])
    parser.add_argument("--output", default="artifacts/license-report.json")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    packages = []
    for dist in _dependency_closure(args.distributions):
        packages.append(
            {
                "name": dist.metadata["Name"],
                "normalized_name": _canonicalize(dist.metadata["Name"]),
                "version": dist.version,
                "license": _license_name(dist),
                "summary": (dist.metadata.get("Summary") or "").strip(),  # type: ignore[arg-type]
                "homepage": _homepage(dist),
                "dependencies": sorted(
                    {
                        requirement_name
                        for requirement in dist.requires or []
                        if _include_requirement(requirement)
                        if (requirement_name := _requirement_name(requirement)) is not None
                    }
                ),
            }
        )

    report = {
        "root_distributions": sorted({_canonicalize(name) for name in args.distributions}),
        "packages": packages,
    }
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(f"License report generated: {output_path}")


if __name__ == "__main__":
    main()