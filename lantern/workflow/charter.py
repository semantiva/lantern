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

"""Workbench Charter loader and schema types (lantern.operator.workbench_charter.v1)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

CHARTER_SCHEMA_ID = "lantern.operator.workbench_charter.v1"

_FRONT_MATTER_PATTERN = re.compile(
    r"^```yaml\r?\n(.*?)```\r?\n",
    re.DOTALL,
)
_SECTION_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)


@dataclass(frozen=True)
class CharterLayerSpec:
    layer: str
    transaction_moment: str
    transaction_posture: str
    required_inputs: tuple[str, ...]
    scope_boundary: str
    stop_condition: str
    deliverables: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    template_refs: tuple[str, ...]
    label: str = ""
    body_section: str = ""


@dataclass(frozen=True)
class CharterContextSlot:
    slot_id: str
    injected_by: str
    description: str


@dataclass(frozen=True)
class WorkbenchCharter:
    schema_id: str
    charter_id: str
    title: str
    workbench_ref: str
    gate_refs: tuple[str, ...]
    artifact_families: tuple[str, ...]
    layers: tuple[CharterLayerSpec, ...]
    context_slots: tuple[CharterContextSlot, ...]
    routing_section_body: str
    raw_header: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


class CharterLoadError(Exception):
    pass


def load_charter(path: Path) -> WorkbenchCharter:
    """Load and parse a Workbench Charter file from the given path."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CharterLoadError(f"cannot read Charter file {path}: {exc}") from exc

    header_dict, body = _parse_front_matter(text, path)
    sections = _split_sections(body)
    routing_body = sections.get("Routing & applicability", "").strip()
    layers = _parse_layers(header_dict.get("layers") or [], path, sections)
    context_slots = _parse_context_slots(header_dict.get("context_slots") or [], path)

    return WorkbenchCharter(
        schema_id=str(header_dict.get("schema_id", "")),
        charter_id=str(header_dict.get("charter_id", "")),
        title=str(header_dict.get("title", "")),
        workbench_ref=str(header_dict.get("workbench_ref", "")),
        gate_refs=tuple(str(g) for g in (header_dict.get("gate_refs") or [])),
        artifact_families=tuple(str(f) for f in (header_dict.get("artifact_families") or [])),
        layers=layers,
        context_slots=context_slots,
        routing_section_body=routing_body,
        raw_header=header_dict,
    )


def validate_charter_header(charter: WorkbenchCharter, workbench_id: str) -> list[str]:
    """Return a list of validation error strings; empty means valid."""
    errors: list[str] = []
    if charter.schema_id != CHARTER_SCHEMA_ID:
        errors.append(f"schema_id must be {CHARTER_SCHEMA_ID!r}; got {charter.schema_id!r}")
    if not charter.charter_id:
        errors.append("charter_id is missing")
    if charter.workbench_ref != workbench_id:
        errors.append(f"workbench_ref {charter.workbench_ref!r} does not match workbench_id {workbench_id!r}")
    if not charter.layers:
        errors.append("Charter declares no layers")
    for i, layer in enumerate(charter.layers):
        prefix = f"layers[{i}]"
        if layer.layer not in {"authoring", "administrative", "validation"}:
            errors.append(f"{prefix}.layer must be authoring|administrative|validation; got {layer.layer!r}")
        if layer.transaction_moment not in {"draft", "commit", "validate"}:
            errors.append(
                f"{prefix}.transaction_moment must be draft|commit|validate; got {layer.transaction_moment!r}"
            )
        if layer.transaction_posture not in {"analysis_only", "administration_authorized"}:
            errors.append(
                f"{prefix}.transaction_posture must be analysis_only|administration_authorized; "
                f"got {layer.transaction_posture!r}"
            )
        if not layer.scope_boundary:
            errors.append(f"{prefix}.scope_boundary is empty")
        if not layer.stop_condition:
            errors.append(f"{prefix}.stop_condition is empty")
        if not layer.deliverables:
            errors.append(f"{prefix}.deliverables is empty")
    return errors


def build_task_card(charter: WorkbenchCharter) -> dict[str, Any]:
    """Build the generated task card dict from a Charter header."""
    return {
        "source_pointer": {
            "charter_id": charter.charter_id,
            "schema_id": charter.schema_id,
            "workbench_ref": charter.workbench_ref,
        },
        "layers": [
            {
                "layer": layer.layer,
                "label": layer.label,
                "transaction_moment": layer.transaction_moment,
                "transaction_posture": layer.transaction_posture,
                "required_inputs": list(layer.required_inputs),
                "scope_boundary": layer.scope_boundary,
                "stop_condition": layer.stop_condition,
                "deliverables": list(layer.deliverables),
                "forbidden_actions": list(layer.forbidden_actions),
                "template_refs": list(layer.template_refs),
            }
            for layer in charter.layers
        ],
    }


# ──────────────────────────── private helpers ────────────────────────────────


def _parse_front_matter(text: str, path: Path) -> tuple[dict[str, Any], str]:
    if yaml is None:
        raise CharterLoadError("PyYAML is not available; cannot parse Charter files")
    match = _FRONT_MATTER_PATTERN.match(text)
    if not match:
        raise CharterLoadError(f"Charter file {path} does not begin with a ```yaml ... ``` front matter block")
    yaml_text = match.group(1)
    body = text[match.end() :]
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise CharterLoadError(f"YAML parse error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CharterLoadError(f"Charter YAML front matter must be a mapping: {path}")
    return data, body


def get_layer_bodies(charter: WorkbenchCharter, moment: str) -> list[dict[str, str]]:
    """Return [{label, body}] for all layers whose transaction_moment matches."""
    return [
        {"label": layer.label, "body": layer.body_section}
        for layer in charter.layers
        if layer.transaction_moment == moment and layer.body_section
    ]


def _split_sections(body: str) -> dict[str, str]:
    """Return a dict of {section_heading: section_content} for level-2 headings."""
    result: dict[str, str] = {}
    parts = _SECTION_PATTERN.split(body)
    # parts[0] is content before first heading; parts then alternate heading/content
    i = 1
    while i < len(parts) - 1:
        heading = parts[i].strip()
        content = parts[i + 1]
        result[heading] = content
        i += 2
    return result


def _parse_layers(
    raw: list[Any],
    path: Path,
    sections: dict[str, str],
) -> tuple[CharterLayerSpec, ...]:
    layers: list[CharterLayerSpec] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise CharterLoadError(f"Charter {path} layers[{i}] must be a mapping")
        layer_type = str(item.get("layer", ""))
        label = str(item.get("label", ""))
        heading = f"{layer_type.capitalize()} layer — {label}" if label else ""
        body = sections.get(heading, "").strip() if heading else ""
        layers.append(
            CharterLayerSpec(
                layer=layer_type,
                transaction_moment=str(item.get("transaction_moment", "")),
                transaction_posture=str(item.get("transaction_posture", "")),
                required_inputs=tuple(str(x) for x in (item.get("required_inputs") or [])),
                scope_boundary=str(item.get("scope_boundary", "")),
                stop_condition=str(item.get("stop_condition", "")),
                deliverables=tuple(str(x) for x in (item.get("deliverables") or [])),
                forbidden_actions=tuple(str(x) for x in (item.get("forbidden_actions") or [])),
                template_refs=tuple(str(x) for x in (item.get("template_refs") or [])),
                label=label,
                body_section=body,
            )
        )
    return tuple(layers)


def _parse_context_slots(raw: list[Any], path: Path) -> tuple[CharterContextSlot, ...]:
    slots: list[CharterContextSlot] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise CharterLoadError(f"Charter {path} context_slots[{i}] must be a mapping")
        slots.append(
            CharterContextSlot(
                slot_id=str(item.get("slot_id", "")),
                injected_by=str(item.get("injected_by", "")),
                description=str(item.get("description", "")),
            )
        )
    return tuple(slots)
