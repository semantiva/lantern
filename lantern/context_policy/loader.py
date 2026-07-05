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

"""Fail-closed loader for context-policy units and groupings (DB-0001 D3).

Every schema violation is a named defect; a defective unit's pattern refuses to
serve; two units declaring the same pattern are a collision refusing both. The
loader never raises on content defects — ``load_corpus_strict`` is the raising
variant for CI checks and hooks.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from .model import (
    GROUPING_SCHEMA_ID,
    KIND_ARTIFACT_CONTRACT,
    KIND_AUTHORING_INSTRUCTIONS,
    KIND_DECISION_POSTURE,
    KIND_EVIDENCE_EXPECTATIONS,
    KIND_VERIFICATION_POSTURE,
    UNIT_SCHEMA_ID,
    PatternKey,
    PolicyComponent,
    PolicyCorpus,
    PolicyDefect,
    PolicyGrouping,
    PolicyLoadError,
    PolicyUnit,
    TransitionPattern,
    Vocabulary,
)

UNITS_DIR = "units"
GROUPINGS_DIR = "groupings"

_FRONT_MATTER_PATTERN = re.compile(r"^```yaml\r?\n(.*?)```\r?\n?", re.DOTALL)
_SECTION_PATTERN = re.compile(r"^## (.+)$", re.MULTILINE)
_IDENTIFIER_RE = re.compile(r"\A[a-z][a-z0-9_]*\Z")
_ID_RE = re.compile(r"\A[a-z][a-z0-9_.-]*\Z")

_UNIT_HEADER_FIELDS = {"schema_id", "unit_id", "version", "title", "pattern", "components"}
_PATTERN_FIELDS = ("family", "from_status", "to_status")
_GROUPING_FIELDS = {"schema_id", "grouping_id", "title", "patterns"}

_ARTIFACT_CONTRACT_FIELDS = {"required_header_keys", "required_sections", "obligations"}
_AUTHORING_LIST_FIELDS = {"required_inputs", "deliverables", "forbidden_actions"}
_AUTHORING_STR_FIELDS = {"scope_boundary", "stop_condition"}
_DECISION_AUTHORITIES = ("explicit_human_approval", "bounded_authorization")


def load_corpus(root: Path, vocabulary: Vocabulary | None = None) -> PolicyCorpus:
    """Load the policy corpus under ``root`` (units/*.md, groupings/*.yaml)."""
    defects: list[PolicyDefect] = []
    if not root.is_dir():
        defect = PolicyDefect(root.name, "root.missing", "policy root is not an existing directory")
        return PolicyCorpus(defects=(defect,))

    parsed: list[tuple[str, PolicyUnit | None, TransitionPattern | None, list[PolicyDefect]]] = []
    units_dir = root / UNITS_DIR
    if units_dir.is_dir():
        for path in sorted(units_dir.glob("*.md")):
            rel = f"{UNITS_DIR}/{path.name}"
            unit, pattern, unit_defects = _parse_unit(path, rel, vocabulary)
            parsed.append((rel, unit, pattern, unit_defects))

    parsed = _check_unit_id_uniqueness(parsed)

    by_pattern: dict[PatternKey, list[tuple[str, PolicyUnit | None, list[PolicyDefect]]]] = {}
    for rel, unit, pattern, unit_defects in parsed:
        defects.extend(unit_defects)
        if pattern is not None:
            by_pattern.setdefault(pattern.key, []).append((rel, unit, unit_defects))

    units_by_pattern: dict[PatternKey, PolicyUnit] = {}
    refused: dict[PatternKey, tuple[PolicyDefect, ...]] = {}
    for key, declarers in by_pattern.items():
        if len(declarers) > 1:
            sources = sorted(rel for rel, _unit, _d in declarers)
            label = TransitionPattern(*key).label()
            collision = PolicyDefect(
                ", ".join(sources),
                "unit.pattern.collision",
                f"pattern ({label}) is declared by {len(sources)} units: {', '.join(sources)}; "
                "exactly one unit may own a transition pattern",
            )
            defects.append(collision)
            per_unit = tuple(d for _rel, _unit, ds in declarers for d in ds)
            refused[key] = (collision,) + per_unit
            continue
        rel, unit, unit_defects = declarers[0]
        if unit is not None and not unit_defects:
            units_by_pattern[key] = unit
        else:
            refused[key] = tuple(unit_defects)

    groupings = _load_groupings(root, units_by_pattern, defects)

    return PolicyCorpus(
        units_by_pattern=units_by_pattern,
        refused_patterns=refused,
        defects=tuple(sorted(defects, key=lambda d: (d.source, d.rule, d.detail))),
        groupings=groupings,
    )


def load_corpus_strict(root: Path, vocabulary: Vocabulary | None = None) -> PolicyCorpus:
    """Load the policy corpus; raise ``PolicyLoadError`` naming every defect."""
    corpus = load_corpus(root, vocabulary)
    if corpus.defects:
        raise PolicyLoadError(corpus.defects)
    return corpus


# ──────────────────────────── unit parsing ────────────────────────────────


def _parse_unit(
    path: Path, rel: str, vocabulary: Vocabulary | None
) -> tuple[PolicyUnit | None, TransitionPattern | None, list[PolicyDefect]]:
    defects: list[PolicyDefect] = []

    raw = path.read_bytes()
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, None, [PolicyDefect(rel, "unit.file.encoding", f"unit file is not valid UTF-8: {exc}")]

    match = _FRONT_MATTER_PATTERN.match(text)
    if not match:
        return (
            None,
            None,
            [PolicyDefect(rel, "unit.header.missing", "unit does not begin with a ```yaml fenced header block")],
        )
    try:
        header = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, None, [PolicyDefect(rel, "unit.header.parse", f"YAML parse error in header: {exc}")]
    if not isinstance(header, dict):
        return None, None, [PolicyDefect(rel, "unit.header.parse", "unit header must be a YAML mapping")]
    body = text[match.end() :]

    for key in sorted(set(header) - _UNIT_HEADER_FIELDS):
        defects.append(PolicyDefect(rel, "unit.header.unknown_field", f"unknown header field {key!r}"))

    schema_id = header.get("schema_id")
    if schema_id != UNIT_SCHEMA_ID:
        defects.append(
            PolicyDefect(rel, "unit.header.schema_id", f"schema_id must be {UNIT_SCHEMA_ID!r}; got {schema_id!r}")
        )

    unit_id = header.get("unit_id")
    if not isinstance(unit_id, str) or not _ID_RE.match(unit_id):
        defects.append(
            PolicyDefect(
                rel, "unit.header.unit_id", f"missing required header field 'unit_id' or bad form: {unit_id!r}"
            )
        )
        unit_id = None
    elif path.name != f"{unit_id}.md":
        defects.append(
            PolicyDefect(rel, "unit.filename", f"filename must be {unit_id}.md to match unit_id {unit_id!r}")
        )

    version = header.get("version")
    if isinstance(version, int) and not isinstance(version, bool):
        version = str(version)
    if not isinstance(version, str) or not version.strip():
        defects.append(
            PolicyDefect(
                rel, "unit.header.version", f"missing required header field 'version' (non-empty): {version!r}"
            )
        )
        version = None

    title = header.get("title")
    if not isinstance(title, str) or not title.strip():
        defects.append(
            PolicyDefect(rel, "unit.header.title", "missing required header field 'title' (non-empty string)")
        )
        title = None

    pattern = _parse_pattern(header.get("pattern"), rel, defects, vocabulary)
    components = _parse_components(header.get("components"), rel, defects)
    components = _bind_bodies(components, body, rel, defects)

    if defects or pattern is None or unit_id is None or version is None or title is None:
        return None, pattern, defects

    unit = PolicyUnit(
        unit_id=unit_id,
        version=version,
        title=title,
        pattern=pattern,
        components=components,
        content_digest=digest,
        source_name=rel,
    )
    return unit, pattern, defects


def _parse_pattern(
    raw: Any, rel: str, defects: list[PolicyDefect], vocabulary: Vocabulary | None
) -> TransitionPattern | None:
    if not isinstance(raw, dict):
        defects.append(
            PolicyDefect(
                rel,
                "unit.pattern.missing",
                "missing required header field 'pattern' (mapping: family, from_status, to_status)",
            )
        )
        return None
    ok = True
    for key in sorted(set(raw) - set(_PATTERN_FIELDS)):
        defects.append(PolicyDefect(rel, "unit.pattern.unknown_field", f"unknown pattern field {key!r}"))
        ok = False
    values: dict[str, str] = {}
    for field_name in _PATTERN_FIELDS:
        value = raw.get(field_name)
        if not isinstance(value, str) or not _IDENTIFIER_RE.match(value):
            defects.append(
                PolicyDefect(
                    rel,
                    "unit.pattern.field",
                    f"pattern.{field_name} must be a lowercase identifier ([a-z][a-z0-9_]*); got {value!r}",
                )
            )
            ok = False
        else:
            values[field_name] = value
    if not ok:
        return None
    pattern = TransitionPattern(values["family"], values["from_status"], values["to_status"])
    if vocabulary is not None:
        if pattern.family not in vocabulary.families:
            defects.append(
                PolicyDefect(
                    rel, "unit.pattern.unknown_family", f"family {pattern.family!r} is not in the supplied vocabulary"
                )
            )
        for field_name in ("from_status", "to_status"):
            status = getattr(pattern, field_name)
            if status not in vocabulary.statuses:
                defects.append(
                    PolicyDefect(
                        rel, "unit.pattern.unknown_status", f"{field_name} {status!r} is not in the supplied vocabulary"
                    )
                )
    return pattern


def _parse_components(raw: Any, rel: str, defects: list[PolicyDefect]) -> tuple[PolicyComponent, ...]:
    if not isinstance(raw, list) or not raw:
        defects.append(
            PolicyDefect(rel, "unit.components.missing", "missing required header field 'components' (non-empty list)")
        )
        return ()
    components: list[PolicyComponent] = []
    seen_kinds: set[str] = set()
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            defects.append(PolicyDefect(rel, "unit.component.entry", f"components[{i}] must be a mapping"))
            continue
        kind = entry.get("kind")
        if not isinstance(kind, str) or not _IDENTIFIER_RE.match(kind):
            defects.append(
                PolicyDefect(
                    rel, "unit.component.kind", f"components[{i}].kind is missing or not an identifier: {kind!r}"
                )
            )
            continue
        if kind in seen_kinds:
            defects.append(
                PolicyDefect(
                    rel, "unit.component.duplicate_kind", f"component kind {kind!r} is declared more than once"
                )
            )
            continue
        seen_kinds.add(kind)
        payload = {k: v for k, v in entry.items() if k != "kind"}
        _validate_payload_json(kind, payload, rel, defects)
        _validate_known_kind(kind, payload, rel, defects)
        components.append(PolicyComponent(kind=kind, payload=payload))
    return tuple(components)


def _validate_known_kind(kind: str, payload: dict[str, Any], rel: str, defects: list[PolicyDefect]) -> None:
    def unknown_fields(allowed: set[str]) -> None:
        for key in sorted(set(payload) - allowed):
            defects.append(
                PolicyDefect(rel, "unit.component.unknown_field", f"component {kind!r} does not accept field {key!r}")
            )

    def str_list_field(field_name: str, required: bool = False) -> list[str] | None:
        value = payload.get(field_name)
        if value is None:
            if required:
                defects.append(
                    PolicyDefect(rel, "unit.component.field", f"component {kind!r} requires field {field_name!r}")
                )
            return None
        if not _is_str_list(value) or not value:
            defects.append(
                PolicyDefect(
                    rel,
                    "unit.component.field",
                    f"component {kind!r} field {field_name!r} must be a non-empty list of non-empty strings",
                )
            )
            return None
        return value

    def str_field(field_name: str, required: bool = False) -> str | None:
        value = payload.get(field_name)
        if value is None:
            if required:
                defects.append(
                    PolicyDefect(rel, "unit.component.field", f"component {kind!r} requires field {field_name!r}")
                )
            return None
        if not isinstance(value, str) or not value.strip():
            defects.append(
                PolicyDefect(
                    rel, "unit.component.field", f"component {kind!r} field {field_name!r} must be a non-empty string"
                )
            )
            return None
        return value

    if kind == KIND_ARTIFACT_CONTRACT:
        unknown_fields(_ARTIFACT_CONTRACT_FIELDS)
        present = [f for f in sorted(_ARTIFACT_CONTRACT_FIELDS) if payload.get(f)]
        for field_name in sorted(_ARTIFACT_CONTRACT_FIELDS):
            if field_name in payload:
                str_list_field(field_name)
        if not present:
            defects.append(
                PolicyDefect(
                    rel,
                    "unit.component.empty_contract",
                    "artifact_contract must state at least one of required_header_keys, required_sections, obligations",
                )
            )
    elif kind == KIND_AUTHORING_INSTRUCTIONS:
        unknown_fields(_AUTHORING_LIST_FIELDS | _AUTHORING_STR_FIELDS)
        for field_name in sorted(_AUTHORING_LIST_FIELDS):
            if field_name in payload:
                str_list_field(field_name)
        for field_name in sorted(_AUTHORING_STR_FIELDS):
            if field_name in payload:
                str_field(field_name)
    elif kind == KIND_EVIDENCE_EXPECTATIONS:
        unknown_fields({"expectations"})
        str_list_field("expectations", required=True)
    elif kind == KIND_DECISION_POSTURE:
        unknown_fields({"authority", "scope", "stop_conditions"})
        authority = payload.get("authority")
        if authority not in _DECISION_AUTHORITIES:
            defects.append(
                PolicyDefect(
                    rel,
                    "unit.component.authority",
                    f"decision_posture.authority must be one of {_DECISION_AUTHORITIES}; got {authority!r}",
                )
            )
        elif authority == "bounded_authorization":
            str_field("scope", required=True)
            str_list_field("stop_conditions", required=True)
        else:
            for forbidden in ("scope", "stop_conditions"):
                if forbidden in payload:
                    defects.append(
                        PolicyDefect(
                            rel,
                            "unit.component.authority",
                            f"decision_posture field {forbidden!r} is only valid under bounded_authorization",
                        )
                    )
    elif kind == KIND_VERIFICATION_POSTURE:
        unknown_fields({"retention", "replacement_discipline"})
        str_field("retention", required=True)
        if "replacement_discipline" in payload:
            str_list_field("replacement_discipline")


def _bind_bodies(
    components: tuple[PolicyComponent, ...], body: str, rel: str, defects: list[PolicyDefect]
) -> tuple[PolicyComponent, ...]:
    declared = {c.kind for c in components}
    parts = _SECTION_PATTERN.split(body)
    if parts[0].strip():
        defects.append(
            PolicyDefect(
                rel,
                "unit.body.stray_content",
                "unit body content before the first '## <kind>' section belongs to no component",
            )
        )
    sections: dict[str, str] = {}
    i = 1
    while i < len(parts) - 1:
        heading = parts[i].strip()
        content = parts[i + 1]
        if heading not in declared:
            defects.append(
                PolicyDefect(
                    rel,
                    "unit.body.undeclared_component",
                    f"body section {heading!r} references no declared component kind",
                )
            )
        elif heading in sections:
            defects.append(
                PolicyDefect(rel, "unit.body.duplicate_section", f"body section {heading!r} appears more than once")
            )
        else:
            sections[heading] = content.strip()
        i += 2

    bound: list[PolicyComponent] = []
    for comp in components:
        section = sections.get(comp.kind, "")
        if comp.kind == KIND_AUTHORING_INSTRUCTIONS and not section:
            defects.append(
                PolicyDefect(
                    rel,
                    "unit.component.body_required",
                    "component 'authoring_instructions' requires a '## authoring_instructions' body section (the method prose)",
                )
            )
        bound.append(PolicyComponent(kind=comp.kind, payload=comp.payload, body=section))
    return tuple(bound)


def _check_unit_id_uniqueness(
    parsed: list[tuple[str, PolicyUnit | None, TransitionPattern | None, list[PolicyDefect]]],
) -> list[tuple[str, PolicyUnit | None, TransitionPattern | None, list[PolicyDefect]]]:
    seen: dict[str, str] = {}
    out: list[tuple[str, PolicyUnit | None, TransitionPattern | None, list[PolicyDefect]]] = []
    for rel, unit, pattern, unit_defects in parsed:
        if unit is not None:
            first = seen.get(unit.unit_id)
            if first is not None:
                unit_defects = unit_defects + [
                    PolicyDefect(
                        rel,
                        "unit.header.duplicate_unit_id",
                        f"unit_id {unit.unit_id!r} is already declared by {first}",
                    )
                ]
                unit = None
            else:
                seen[unit.unit_id] = rel
        out.append((rel, unit, pattern, unit_defects))
    return out


# ──────────────────────────── groupings ────────────────────────────────


def _load_groupings(
    root: Path,
    units_by_pattern: dict[PatternKey, PolicyUnit],
    defects: list[PolicyDefect],
) -> tuple[PolicyGrouping, ...]:
    groupings_dir = root / GROUPINGS_DIR
    if not groupings_dir.is_dir():
        return ()
    groupings: list[PolicyGrouping] = []
    seen_ids: dict[str, str] = {}
    for path in sorted(groupings_dir.glob("*.yaml")):
        rel = f"{GROUPINGS_DIR}/{path.name}"
        grouping = _parse_grouping(path, rel, units_by_pattern, defects)
        if grouping is None:
            continue
        first = seen_ids.get(grouping.grouping_id)
        if first is not None:
            defects.append(
                PolicyDefect(
                    rel, "grouping.duplicate_id", f"grouping_id {grouping.grouping_id!r} is already declared by {first}"
                )
            )
            continue
        seen_ids[grouping.grouping_id] = rel
        groupings.append(grouping)
    return tuple(groupings)


def _parse_grouping(
    path: Path,
    rel: str,
    units_by_pattern: dict[PatternKey, PolicyUnit],
    defects: list[PolicyDefect],
) -> PolicyGrouping | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        defects.append(PolicyDefect(rel, "grouping.parse", f"cannot parse grouping file: {exc}"))
        return None
    if not isinstance(data, dict):
        defects.append(PolicyDefect(rel, "grouping.parse", "grouping file must be a YAML mapping"))
        return None

    found = len(defects)
    for key in sorted(set(data) - _GROUPING_FIELDS):
        defects.append(
            PolicyDefect(
                rel,
                "grouping.unknown_field",
                f"unknown grouping field {key!r} — groupings carry pattern references only, no contract content",
            )
        )
    if data.get("schema_id") != GROUPING_SCHEMA_ID:
        defects.append(
            PolicyDefect(
                rel, "grouping.schema_id", f"schema_id must be {GROUPING_SCHEMA_ID!r}; got {data.get('schema_id')!r}"
            )
        )
    grouping_id = data.get("grouping_id")
    if not isinstance(grouping_id, str) or not _ID_RE.match(grouping_id):
        defects.append(PolicyDefect(rel, "grouping.grouping_id", f"missing or bad grouping_id: {grouping_id!r}"))
        grouping_id = None
    elif path.name != f"{grouping_id}.yaml":
        defects.append(PolicyDefect(rel, "grouping.filename", f"filename must be {grouping_id}.yaml"))
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        defects.append(PolicyDefect(rel, "grouping.title", "missing title (non-empty string)"))
        title = None

    patterns: list[TransitionPattern] = []
    raw_patterns = data.get("patterns")
    if not isinstance(raw_patterns, list) or not raw_patterns:
        defects.append(
            PolicyDefect(rel, "grouping.patterns", "patterns must be a non-empty list of pattern references")
        )
    else:
        seen: set[PatternKey] = set()
        for i, entry in enumerate(raw_patterns):
            sub: list[PolicyDefect] = []
            pattern = _parse_pattern(entry, rel, sub, None)
            if pattern is None or sub:
                defects.append(
                    PolicyDefect(rel, "grouping.pattern_ref", f"patterns[{i}] is not a valid pattern reference")
                )
                continue
            if pattern.key in seen:
                defects.append(
                    PolicyDefect(rel, "grouping.duplicate_pattern", f"patterns[{i}] duplicates ({pattern.label()})")
                )
                continue
            seen.add(pattern.key)
            if pattern.key not in units_by_pattern:
                defects.append(
                    PolicyDefect(
                        rel,
                        "grouping.dangling_pattern",
                        f"patterns[{i}] ({pattern.label()}) resolves to no healthy covered unit",
                    )
                )
                continue
            patterns.append(pattern)

    if len(defects) > found or grouping_id is None or title is None:
        return None
    return PolicyGrouping(grouping_id=grouping_id, title=title, patterns=tuple(patterns), source_name=rel)


# ──────────────────────────── helpers ────────────────────────────────


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def _validate_payload_json(kind: str, payload: dict[str, Any], rel: str, defects: list[PolicyDefect]) -> None:
    if not _is_json_value(payload):
        defects.append(
            PolicyDefect(
                rel,
                "unit.component.payload_not_json",
                f"component {kind!r} payload must contain only JSON-representable values "
                "(strings, numbers, booleans, null, lists, string-keyed mappings)",
            )
        )


def _is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, bool, int, float)):
        return True
    if isinstance(value, list):
        return all(_is_json_value(v) for v in value)
    if isinstance(value, dict):
        return all(isinstance(k, str) and _is_json_value(v) for k, v in value.items())
    return False
