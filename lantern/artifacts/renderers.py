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

"""Canonical rendering helpers for governed Markdown artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import yaml


def canonical_render_markdown(
    *,
    header: Mapping[str, Any],
    artifact_id: str,
    title: str,
    sections: Sequence[Mapping[str, Any]],
) -> str:
    header_text = yaml.safe_dump(dict(header), sort_keys=False, allow_unicode=True).rstrip()
    blocks: list[str] = ["```yaml", header_text, "```", "", f"# {artifact_id} — {title}"]
    for section in sections:
        heading = str(section["heading"]).strip()
        body = str(section.get("body", "")).rstrip()
        blocks.extend(["", f"## {heading}", "", body])
    return "\n".join(blocks).rstrip() + "\n"


def parse_header_block(markdown_text: str) -> dict[str, Any]:
    lines = markdown_text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "```yaml":
        raise ValueError("canonical governed artifact must start with a fenced yaml header")
    try:
        end_index = lines.index("```", 1)
    except ValueError as exc:
        raise ValueError("canonical governed artifact is missing the closing yaml fence") from exc
    payload = yaml.safe_load("\n".join(lines[1:end_index]))
    if not isinstance(payload, dict):
        raise ValueError("canonical governed artifact header must decode to a mapping")
    return payload
