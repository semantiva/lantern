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