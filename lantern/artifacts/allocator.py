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

"""Artifact allocation and path helpers for governed Markdown artifacts."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

FAMILY_DIRECTORY_MAP: dict[str, str] = {
    "ARCH": "arch",
    "CH": "ch",
    "CI": "ci",
    "DB": "db",
    "DC": "dc",
    "DEC": "dec",
    "DIP": "dip",
    "EV": "ev",
    "INI": "ini",
    "IS": "is",
    "Q": "q",
    "SPEC": "spec",
    "TD": "td",
}


def artifact_directory(artifact_family: str) -> str:
    try:
        return FAMILY_DIRECTORY_MAP[artifact_family.upper()]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"unsupported artifact family: {artifact_family!r}") from exc


def artifact_path(governance_root: Path, artifact_id: str) -> Path:
    family = artifact_id.split("-", 1)[0]
    directory = artifact_directory(family)
    return Path(governance_root) / directory / f"{artifact_id}.md"


def allocate_artifact_id(
    artifact_family: str,
    governance_root: Path,
    *,
    ch_id: str | None = None,
) -> str:
    family = artifact_family.upper()
    if family in {"CI", "DC"}:
        if not ch_id or not ch_id.startswith("CH-"):
            raise ValueError(f"{family} allocation requires a parent CH id")
        ch_num = ch_id.split("-", 1)[1]
        return f"{family}-{ch_num}-{uuid4()}"

    directory = Path(governance_root) / artifact_directory(family)
    max_id = 0
    prefix = f"{family}-"
    if directory.exists():
        for path in directory.glob(f"{family}-*.md"):
            stem = path.stem
            if not stem.startswith(prefix):
                continue
            suffix = stem[len(prefix) :]
            if suffix.isdigit():
                max_id = max(max_id, int(suffix))
    return f"{family}-{max_id + 1:04d}"
