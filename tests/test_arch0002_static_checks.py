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

CI-level corpus checks (not runtime logic) installed by CH-0030 (rows 1–6)
and CH-0033 (rows 7–9: Charter-header, Charter-binding, task-card-derivation).
Each check realizes one row of ARCH-0002 §5 and enforces the SPEC-0005
requirements.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = PRODUCT_ROOT / "lantern" / "workflow" / "definitions"
MANIFEST = DEFINITIONS / "resource_manifest.json"
WORKBENCHES_DIR = DEFINITIONS / "workbenches"
CHARTERS_DIR = PRODUCT_ROOT / "lantern" / "workbench_charters"

# Guidance classes that are delivered as resource-manifest entries.
GUIDANCE_DIRS = (
    "lantern/authoring_contracts",
    "lantern/administration_procedures",
    "lantern/resources/instructions",
)

ARCH0002_OPERATOR_KINDS = {"instruction", "authoring_contract", "administration_guide"}


def _manifest() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _manifest_paths() -> set[str]:
    return {entry["path"] for entry in _manifest()}


def _guidance_files() -> set[str]:
    files: set[str] = set()
    for directory in GUIDANCE_DIRS:
        for path in (PRODUCT_ROOT / directory).glob("*.md"):
            files.add(f"lantern/{path.relative_to(PRODUCT_ROOT / 'lantern').as_posix()}")
    return files


# Row 1 — Membrane check (REQ-GS-01)
def test_membrane_check_all_guidance_files_are_reachable() -> None:
    manifest = _manifest_paths()
    unreachable = sorted(_guidance_files() - manifest)
    assert unreachable == [], f"present-but-unreachable guidance files: {unreachable}"


# Row 2 — Single-authority check (REQ-GA-01, REQ-GA-03)
def test_single_authority_no_projection_class_and_no_duplicate_documents() -> None:
    import hashlib

    kinds = {entry["kind"] for entry in _manifest()}
    assert "authoritative_guide" not in kinds, "projection layer (authoritative_guide kind) must be removed"
    # A document may serve multiple workbenches, but no two distinct governed
    # documents may carry identical content (that would duplicate authority).
    seen: dict[str, str] = {}
    for path in _guidance_files():
        digest = hashlib.sha256((PRODUCT_ROOT / path).read_bytes()).hexdigest()
        assert digest not in seen, f"duplicate-authority documents: {path} == {seen[digest]}"
        seen[digest] = path


# Row 3 — Semantic-authority check (REQ-GA-02)
def test_semantic_authority_no_shadow_corpus_or_semantic_definitions() -> None:
    preservation = PRODUCT_ROOT / "lantern" / "preservation"
    assert sorted(preservation.glob("*.md")) == [], "preservation shadow-corpus markdown must be removed"
    forbidden_definition_headings = (
        "## Gate definitions",
        "## Status definitions",
        "## Canonical statuses",
        "## Artifact families (normative)",
    )
    for path in _guidance_files():
        text = (PRODUCT_ROOT / path).read_text(encoding="utf-8")
        for heading in forbidden_definition_headings:
            assert heading not in text, f"{path} redefines grammar-owned semantics: {heading!r}"


# Row 4 — Audience/class declaration check (REQ-GA-04, REQ-GA-05)
def test_audience_class_each_resource_resolves_to_one_kind() -> None:
    by_path: dict[str, set[str]] = {}
    for entry in _manifest():
        by_path.setdefault(entry["path"], set()).add(entry["kind"])
    ambiguous = {path: kinds for path, kinds in by_path.items() if len(kinds) != 1}
    assert ambiguous == {}, f"resources without a single declared class: {ambiguous}"
    assert {entry["kind"] for entry in _manifest()} <= ARCH0002_OPERATOR_KINDS


# Row 5 — Reference-resolution check (REQ-GS-04)
def test_reference_resolution_no_dangling_corpus_references() -> None:
    manifest = _manifest_paths()
    ref_pattern = re.compile(r"lantern/[A-Za-z0-9_./-]+\.md")
    # Bare guides/ references (deleted layer); catches backtick-quoted and plain forms.
    bare_guides_pattern = re.compile(r"`?guides/[A-Za-z0-9_./-]+\.md`?")
    dangling: dict[str, list[str]] = {}
    bare_guides: dict[str, list[str]] = {}
    for path in _guidance_files():
        text = (PRODUCT_ROOT / path).read_text(encoding="utf-8")
        for ref in set(ref_pattern.findall(text)):
            if ref in manifest:
                continue
            if (PRODUCT_ROOT / ref).exists():
                continue  # delivery-reachable peer (e.g., a template present on disk)
            dangling.setdefault(path, []).append(ref)
        for match in set(bare_guides_pattern.findall(text)):
            bare_guides.setdefault(path, []).append(match)
    assert dangling == {}, f"references that resolve to no delivery-reachable target: {dangling}"
    assert bare_guides == {}, f"bare guides/ references to deleted layer: {bare_guides}"


# Row 6 — Non-governed-content check (REQ-GS-02, REQ-GS-03)
def test_non_governed_content_absent_from_corpus() -> None:
    for path in _manifest_paths():
        name = path.rsplit("/", 1)[-1]
        assert not name.startswith("MIGRATION__"), f"historical/migration document inside corpus: {path}"
        assert "POC_VALUE_EXTRACTION" not in name, f"historical document inside corpus: {path}"
    preservation = PRODUCT_ROOT / "lantern" / "preservation"
    assert not (preservation / "MIGRATION__TD_DC_DB_GT115_v0.1.0.md").exists()
    assert not (preservation / "POC_VALUE_EXTRACTION_MAP.md").exists()


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
