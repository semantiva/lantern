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

"""Derived views of a context-policy unit (DB-0001 D5).

Everything delivered from a unit is a derived view: the orient task card (every
unit), and the human template and validation rules (units carrying an
``artifact_contract``). Views embed a source pointer to the generating unit and
are mechanically asserted derived — a manually edited, missing, or unexpected
delivered view is a named drift finding.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import (
    KIND_ARTIFACT_CONTRACT,
    KIND_AUTHORING_INSTRUCTIONS,
    KIND_DECISION_POSTURE,
    KIND_EVIDENCE_EXPECTATIONS,
    KIND_VERIFICATION_POSTURE,
    UNIT_SCHEMA_ID,
    VIEW_HUMAN_TEMPLATE_SCHEMA_ID,
    VIEW_TASK_CARD_SCHEMA_ID,
    VIEW_VALIDATION_RULES_SCHEMA_ID,
    PolicyCorpus,
    PolicyUnit,
    ViewDriftError,
)

_INVOCATION_FIELDS = ("required_inputs", "scope_boundary", "stop_condition", "deliverables", "forbidden_actions")


def _source_pointer(unit: PolicyUnit) -> dict[str, str]:
    return {
        "unit_id": unit.unit_id,
        "version": unit.version,
        "schema_id": UNIT_SCHEMA_ID,
        "content_digest": unit.content_digest,
    }


def task_card(unit: PolicyUnit) -> dict[str, Any]:
    """The orient task card: the unit's invocation contract, generated, never authored."""
    card: dict[str, Any] = {
        "view_schema_id": VIEW_TASK_CARD_SCHEMA_ID,
        "source_pointer": _source_pointer(unit),
        "pattern": unit.pattern.as_payload(),
        "title": unit.title,
        "component_kinds": [c.kind for c in unit.components],
        "decision_posture": None,
        "verification_posture": None,
        "evidence_expectations": None,
        "invocation": None,
    }
    decision = unit.component(KIND_DECISION_POSTURE)
    if decision is not None:
        card["decision_posture"] = dict(decision.payload)
    verification = unit.component(KIND_VERIFICATION_POSTURE)
    if verification is not None:
        card["verification_posture"] = dict(verification.payload)
    evidence = unit.component(KIND_EVIDENCE_EXPECTATIONS)
    if evidence is not None:
        card["evidence_expectations"] = list(evidence.payload["expectations"])
    authoring = unit.component(KIND_AUTHORING_INSTRUCTIONS)
    if authoring is not None:
        invocation = {f: authoring.payload[f] for f in _INVOCATION_FIELDS if f in authoring.payload}
        card["invocation"] = invocation
    return card


def validation_rules(unit: PolicyUnit) -> dict[str, Any] | None:
    """Machine validation rules derived from the artifact contract; None without one."""
    contract = unit.component(KIND_ARTIFACT_CONTRACT)
    if contract is None:
        return None
    return {
        "view_schema_id": VIEW_VALIDATION_RULES_SCHEMA_ID,
        "source_pointer": _source_pointer(unit),
        "pattern": unit.pattern.as_payload(),
        "rules": {
            "required_header_keys": list(contract.payload.get("required_header_keys") or []),
            "required_sections": list(contract.payload.get("required_sections") or []),
            "obligations": list(contract.payload.get("obligations") or []),
        },
    }


def human_template(unit: PolicyUnit) -> str | None:
    """Markdown authoring template derived from the artifact contract; None without one."""
    contract = unit.component(KIND_ARTIFACT_CONTRACT)
    if contract is None:
        return None
    lines: list[str] = [
        f"<!-- derived view: {VIEW_HUMAN_TEMPLATE_SCHEMA_ID};"
        f" unit_id={unit.unit_id}; version={unit.version}; content_digest={unit.content_digest};"
        " generated from the context-policy unit — do not edit, regenerate -->",
        "",
        f"# {unit.title} — authoring template",
        "",
        f"Pattern: `{unit.pattern.label()}`",
        "",
    ]
    header_keys = contract.payload.get("required_header_keys") or []
    if header_keys:
        lines.append("```yaml")
        lines.extend(f"{key}: <{key}>" for key in header_keys)
        lines.append("```")
        lines.append("")
    obligations = contract.payload.get("obligations") or []
    if obligations:
        lines.append("> Obligations of this artifact:")
        lines.extend(f"> - {obligation}" for obligation in obligations)
        lines.append("")
    for section in contract.payload.get("required_sections") or []:
        lines.append(f"## {section}")
        lines.append("")
        lines.append("_Required section._")
        lines.append("")
    return "\n".join(lines)


# ──────────────────── materialization and derived-assertion ────────────────────


def _render_json(view: dict[str, Any]) -> bytes:
    return (json.dumps(view, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def expected_views(corpus: PolicyCorpus) -> dict[str, bytes]:
    """Regenerate every defined view: delivered filename -> exact expected bytes."""
    expected: dict[str, bytes] = {}
    for unit in sorted(corpus.units_by_pattern.values(), key=lambda u: u.unit_id):
        expected[f"{unit.unit_id}.task_card.json"] = _render_json(task_card(unit))
        rules = validation_rules(unit)
        if rules is not None:
            expected[f"{unit.unit_id}.validation_rules.json"] = _render_json(rules)
        template = human_template(unit)
        if template is not None:
            expected[f"{unit.unit_id}.template.md"] = template.encode("utf-8")
    return expected


def write_derived_views(corpus: PolicyCorpus, out_dir: Path) -> list[str]:
    """Materialize the defined views into ``out_dir``; returns written filenames."""
    out_dir.mkdir(parents=True, exist_ok=True)
    expected = expected_views(corpus)
    for name, content in expected.items():
        (out_dir / name).write_bytes(content)
    return sorted(expected)


def assert_views_derived(corpus: PolicyCorpus, out_dir: Path) -> tuple[str, ...]:
    """Byte-compare delivered views against regeneration; returns drift findings."""
    if not out_dir.is_dir():
        return (f"delivered-views directory {out_dir.name!r} does not exist",)
    expected = expected_views(corpus)
    actual = {path.name: path.read_bytes() for path in sorted(out_dir.iterdir()) if path.is_file()}
    findings: list[str] = []
    for name in sorted(set(expected) - set(actual)):
        findings.append(f"missing derived view: {name}")
    for name in sorted(set(actual) - set(expected)):
        findings.append(f"unexpected file not derived from any unit: {name}")
    for name in sorted(set(expected) & set(actual)):
        if expected[name] != actual[name]:
            findings.append(f"drifted view (differs from regeneration from its unit): {name}")
    return tuple(findings)


def assert_views_derived_strict(corpus: PolicyCorpus, out_dir: Path) -> None:
    """Raise ``ViewDriftError`` if any delivered view drifted from its unit."""
    findings = assert_views_derived(corpus, out_dir)
    if findings:
        raise ViewDriftError(findings)
