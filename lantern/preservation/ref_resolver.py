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

import re
from pathlib import Path
from typing import Iterable

import yaml

_DOC_REF_PATTERN = re.compile(r"lantern/[A-Za-z0-9_./-]+\.md")


def collect_emitted_refs(registry_path: Path, instructions_root: Path) -> list[str]:
    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    refs: list[str] = []

    for workbench in payload.get("workbenches", []):
        instruction_resource = workbench.get("instruction_resource")
        if instruction_resource:
            refs.append(str(instruction_resource))
        for item in workbench.get("administration_guides", []):
            refs.append(str(item))

    for path in sorted(instructions_root.glob("*.md")):
        refs.extend(_DOC_REF_PATTERN.findall(path.read_text(encoding="utf-8")))

    return sorted(dict.fromkeys(ref.lstrip("/") for ref in refs))


def resolve_guide_refs(
    manifest: Path | Iterable[str],
    emitted_refs: Iterable[str],
    product_root: Path,
) -> list[str]:
    if isinstance(manifest, Path):
        payload = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        manifest_targets = {entry["target"] for entry in payload.get("entries", [])}
    else:
        manifest_targets = {ref.lstrip("/") for ref in manifest}

    unresolved: list[str] = []
    for ref in emitted_refs:
        normalized = ref.lstrip("/")
        if normalized not in manifest_targets:
            unresolved.append(normalized)
            continue
        if not (product_root / normalized).exists():
            unresolved.append(normalized)
    return sorted(dict.fromkeys(unresolved))
