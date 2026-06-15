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

"""ARCH-0002 §5 static enforcement checks for the operator guidance corpus.

CI-level corpus checks (not runtime logic) installed by
CH-0033 (rows 7–9: Charter-header, Charter-binding, task-card-derivation), and
CH-0034 (rows 10–15: projection-role-absence, class/role-alignment,
workbench-no-coverage-restatement, packaged-skill-no-projection, context-boundary,
template-refs-resolution).
Each check realizes one row of ARCH-0002 §5 and enforces the SPEC-0005
requirements.

Rows 1–6 (CH-0030 corpus checks) are retired: the legacy guidance corpus
(resources/instructions, authoring_contracts, administration_procedures) was deleted
in CH-0034, and the resource manifest no longer exists. Those checks now pass
vacuously; they are removed here to avoid dead test weight.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = PRODUCT_ROOT / "lantern" / "workflow" / "definitions"
WORKBENCHES_DIR = DEFINITIONS / "workbenches"
CHARTERS_DIR = PRODUCT_ROOT / "lantern" / "workbench_charters"


# ── CH-0033 rows 7–9: Workbench Charter static checks ──────────────────────


def _load_workbench_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _workbench_definitions() -> list[dict]:
    return [_load_workbench_yaml(p) for p in sorted(WORKBENCHES_DIR.glob("*.yaml"))]


# Row 7 — Charter-header check (REQ-CH-01)
def test_charter_header_every_workbench_has_valid_charter() -> None:
    from lantern.workflow.charter import CHARTER_SCHEMA_ID, load_charter

    missing: list[str] = []
    invalid: dict[str, str] = {}
    for defn in _workbench_definitions():
        wid = defn.get("workbench_id", "<unknown>")
        charter_ref = defn.get("charter_ref", "")
        if not charter_ref:
            missing.append(wid)
            continue
        charter_path = PRODUCT_ROOT / charter_ref
        if not charter_path.exists():
            invalid[wid] = f"charter_ref {charter_ref!r} does not exist"
            continue
        try:
            charter = load_charter(charter_path)
        except Exception as exc:
            invalid[wid] = f"load error: {exc}"
            continue
        if charter.schema_id != CHARTER_SCHEMA_ID:
            invalid[wid] = f"schema_id {charter.schema_id!r} != {CHARTER_SCHEMA_ID!r}"
    assert missing == [], f"workbenches without charter_ref: {missing}"
    assert invalid == {}, f"workbenches with invalid charter: {invalid}"


# Row 8 — Charter-binding check (REQ-CH-02)
def test_charter_binding_workbench_ref_matches_workbench_id() -> None:
    from lantern.workflow.charter import load_charter

    mismatches: dict[str, str] = {}
    for defn in _workbench_definitions():
        wid = defn.get("workbench_id", "<unknown>")
        charter_ref = defn.get("charter_ref", "")
        if not charter_ref:
            continue
        charter_path = PRODUCT_ROOT / charter_ref
        if not charter_path.exists():
            continue
        try:
            charter = load_charter(charter_path)
        except Exception:
            continue
        if charter.workbench_ref != wid:
            mismatches[wid] = f"Charter.workbench_ref={charter.workbench_ref!r}"
    assert mismatches == {}, f"Charter workbench_ref binding mismatches: {mismatches}"


# Row 9 — Task-card-derivation check (REQ-CH-03)
def test_task_card_derivation_all_layers_are_valid() -> None:
    from lantern.workflow.charter import load_charter, validate_charter_header

    failures: dict[str, list[str]] = {}
    for defn in _workbench_definitions():
        wid = defn.get("workbench_id", "<unknown>")
        charter_ref = defn.get("charter_ref", "")
        if not charter_ref:
            continue
        charter_path = PRODUCT_ROOT / charter_ref
        if not charter_path.exists():
            continue
        try:
            charter = load_charter(charter_path)
        except Exception as exc:
            failures[wid] = [str(exc)]
            continue
        errs = validate_charter_header(charter, wid)
        if errs:
            failures[wid] = errs
    assert failures == {}, f"Charter header validation failures: {failures}"


# ── CH-0034 rows 10–15: Contract and role enforcement checks ────────────────


_LEGACY_ROLE_TOKENS = {"instruction_resource", "authoritative_guides", "administration_guides"}
_SCHEMA_PATH = DEFINITIONS / "workbench_schema.yaml"
_TRANSACTION_PROFILES_PATH = DEFINITIONS / "transaction_profiles.yaml"
_SKILL_MD_PATH = PRODUCT_ROOT / "lantern" / "skills" / "packaged_default" / "SKILL.md"


def _schema() -> dict[str, Any]:
    return yaml.safe_load(_SCHEMA_PATH.read_text(encoding="utf-8")) or {}


def _workbench_yaml_texts() -> list[str]:
    return [p.read_text(encoding="utf-8") for p in sorted(WORKBENCHES_DIR.glob("*.yaml"))]


def _transaction_profiles_text() -> str:
    return _TRANSACTION_PROFILES_PATH.read_text(encoding="utf-8")


# Row 10 — Projection-role-absence check
def test_projection_role_absence_no_legacy_role_tokens_in_schema_or_workbenches() -> None:
    schema = _schema()
    allowed_roles = set(schema.get("allowed_resource_roles", []))
    assert (
        not allowed_roles & _LEGACY_ROLE_TOKENS
    ), f"Schema still lists legacy roles: {allowed_roles & _LEGACY_ROLE_TOKENS}"
    removed = set(schema.get("removed_authority_fields", []))
    assert _LEGACY_ROLE_TOKENS.issubset(
        removed
    ), f"Legacy roles not in removed_authority_fields: {_LEGACY_ROLE_TOKENS - removed}"
    for text in _workbench_yaml_texts():
        for token in _LEGACY_ROLE_TOKENS:
            assert token not in text, f"Legacy role token {token!r} still present in a workbench YAML"
    profiles_text = _transaction_profiles_text()
    for token in _LEGACY_ROLE_TOKENS:
        assert token not in profiles_text, f"Legacy role token {token!r} still present in transaction_profiles.yaml"


# Row 11 — Class/role-alignment check
def test_class_role_alignment_three_operator_classes_structurally_present() -> None:
    schema = _schema()
    allowed_roles = set(schema.get("allowed_resource_roles", []))
    assert "artifact_templates" in allowed_roles, "Template class (artifact_templates) absent from schema"
    assert "operating_references" in allowed_roles, "Operating reference class absent from schema"
    charter_dir = CHARTERS_DIR
    assert charter_dir.is_dir() and any(charter_dir.glob("*.md")), "Charter class: no Charter files found"


# Row 12 — Workbench-no-coverage-restatement check
def test_workbench_no_coverage_restatement_legacy_coverage_fields_absent() -> None:
    forbidden_top_level = {"artifacts_in_scope", "posture_constraints"}
    for defn in _workbench_definitions():
        wid = defn.get("workbench_id", "<unknown>")
        for field in forbidden_top_level:
            assert field not in defn, f"{wid}: retired coverage field {field!r} still present as top-level YAML key"
        lp = defn.get("lifecycle_placement") or {}
        assert (
            "covered_gates" not in lp
        ), f"{wid}: lifecycle_placement.covered_gates still declared in YAML (must come from Charter)"


# Row 13 — Packaged-skill-no-projection check
def test_packaged_skill_no_projection_skill_md_is_static() -> None:
    assert _SKILL_MD_PATH.exists(), f"SKILL.md not found: {_SKILL_MD_PATH}"
    skill_text = _SKILL_MD_PATH.read_text(encoding="utf-8")
    workbench_id_tokens = [
        defn.get("workbench_id", "") for defn in _workbench_definitions() if defn.get("workbench_id")
    ]
    for wid in workbench_id_tokens:
        assert wid not in skill_text, f"SKILL.md enumerates workbench_id {wid!r}: must be static and workflow-agnostic"


# Row 14 — Context-boundary check
def test_context_boundary_charter_bodies_do_not_assert_sequencing_authority() -> None:
    sequencing_terms = re.compile(
        r"\b(must\s+precede|must\s+follow|must\s+come\s+before|must\s+come\s+after"
        r"|adjacent\s+gate|gate\s+adjacency|gate\s+ordering\s+is\s+enforced"
        r"|workflow\s+sequence\s+requires)\b",
        re.IGNORECASE,
    )
    violations: dict[str, list[str]] = {}
    for path in sorted(CHARTERS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        matches = sequencing_terms.findall(text)
        if matches:
            violations[path.name] = matches
    assert violations == {}, f"Charter body asserts workflow sequencing authority (schema owns this): {violations}"


# Row 15 — Template-refs-resolution check
def test_template_refs_resolution_all_charter_template_refs_resolve() -> None:
    from lantern.workflow.charter import load_charter

    dangling: dict[str, list[str]] = {}
    for path in sorted(CHARTERS_DIR.glob("*.md")):
        try:
            charter = load_charter(path)
        except Exception:
            continue
        for layer in charter.layers:
            for ref in layer.template_refs:
                ref_path = PRODUCT_ROOT / ref
                if not ref_path.exists():
                    dangling.setdefault(path.name, []).append(ref)
    assert dangling == {}, f"Charter template_refs that do not resolve to a file on disk: {dangling}"
