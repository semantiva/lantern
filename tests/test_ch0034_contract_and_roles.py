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

"""TD-0034 C01-C06: Contract and role retirement verification for CH-0034.

Covers:
  C01 - Deletion safety: 29 legacy corpus files are absent on disk.
  C02 - Coverage resolution: workbench.artifacts_in_scope comes from Charter.
  C03 - Charter coverage: charter_ref is required on every workbench.
  C04 - Role retirement: resource_manifest is empty; no legacy role entries.
  C05 - Schema enforcement: §5 checks — no transitional allowance, guidance dirs empty.
  C06 - Behavioral equivalence: orient still delivers task card per active workbench.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lantern.workflow.charter import load_charter

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
WORKBENCHES_DIR = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "workbenches"

_DELETED_FILES = [
    "lantern/resources/instructions/ch_and_td_readiness.md",
    "lantern/resources/instructions/ci_authoring.md",
    "lantern/resources/instructions/ci_selection.md",
    "lantern/resources/instructions/design_candidate_authoring.md",
    "lantern/resources/instructions/design_selection.md",
    "lantern/resources/instructions/governance_onboarding.md",
    "lantern/resources/instructions/issue_operations.md",
    "lantern/resources/instructions/selected_ci_application.md",
    "lantern/resources/instructions/upstream_intake_and_baselines.md",
    "lantern/resources/instructions/verification_and_closure.md",
    "lantern/authoring_contracts/allowed_change_surface_flexibilization.md",
    "lantern/authoring_contracts/arch_authoring_guide.md",
    "lantern/authoring_contracts/change_increment_authoring_guide.md",
    "lantern/authoring_contracts/change_increment_selection_guide.md",
    "lantern/authoring_contracts/change_intention_refinement_guide.md",
    "lantern/authoring_contracts/design_baseline_authoring_guide.md",
    "lantern/authoring_contracts/design_candidate_authoring_guide.md",
    "lantern/authoring_contracts/design_candidate_selection_guide.md",
    "lantern/authoring_contracts/dip_authoring_guide.md",
    "lantern/authoring_contracts/spec_authoring_guide.md",
    "lantern/authoring_contracts/test_definition_authoring_guide.md",
    "lantern/administration_procedures/GT-030__DIP_LOCK_ADMINISTRATION.md",
    "lantern/administration_procedures/GT-050_GT-060__BASELINE_READINESS_ADMINISTRATION.md",
    "lantern/administration_procedures/GT-115__DESIGN_BASELINE_SELECTION.md",
    "lantern/administration_procedures/GT-120__CI_SELECTION_ADMINISTRATION.md",
    "lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION.md",
    "lantern/administration_procedures/INITIATIVE__AUTHORING_AND_READYING.md",
    "lantern/administration_procedures/INITIATIVE__DECOMPOSITION_AND_CH_SIZING.md",
    "lantern/administration_procedures/ISSUE__INTAKE_TRIAGE_RESOLUTION.md",
]

_GT110_ACTIVE = {
    "ch_statuses": {"CH-0003": "Ready"},
    "active_gates": ["GT-110"],
    "passed_gates": [],
}


def _import_yaml():
    import yaml

    return yaml


def _load_workbench_yaml(path: Path) -> dict:
    yaml = _import_yaml()
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _all_workbench_defs() -> list[dict]:
    return [_load_workbench_yaml(p) for p in sorted(WORKBENCHES_DIR.glob("*.yaml"))]


# ── C01: Deletion safety ──────────────────────────────────────────────────────


@pytest.mark.parametrize("rel_path", _DELETED_FILES)
def test_c01_legacy_corpus_file_is_absent(rel_path: str) -> None:
    path = PRODUCT_ROOT / rel_path
    assert not path.exists(), f"Legacy corpus file must be deleted by CH-0034: {rel_path}"


# ── C02: Coverage resolution from Charter ────────────────────────────────────


def test_c02_workbench_artifacts_in_scope_matches_charter_artifact_families() -> None:
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    mismatches: dict[str, str] = {}
    for workbench in layer.workbenches:
        if not workbench.charter_ref:
            continue
        charter_path = PRODUCT_ROOT / workbench.charter_ref
        if not charter_path.exists():
            continue
        charter = load_charter(charter_path)
        expected = tuple(charter.artifact_families)
        if workbench.artifacts_in_scope != expected:
            mismatches[workbench.workbench_id] = (
                f"artifacts_in_scope={list(workbench.artifacts_in_scope)} "
                f"!= charter.artifact_families={list(expected)}"
            )
    assert mismatches == {}, f"Coverage mismatch between workbench and Charter: {mismatches}"


def test_c02_covered_gates_workbenches_derive_gate_list_from_charter() -> None:
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    mismatches: dict[str, str] = {}
    for workbench in layer.workbenches:
        if workbench.lifecycle_placement.kind != "covered_gates":
            continue
        if not workbench.charter_ref:
            continue
        charter_path = PRODUCT_ROOT / workbench.charter_ref
        if not charter_path.exists():
            continue
        charter = load_charter(charter_path)
        expected_gates = tuple(charter.gate_refs)
        actual_gates = workbench.lifecycle_placement.covered_gates
        if actual_gates != expected_gates:
            mismatches[workbench.workbench_id] = (
                f"covered_gates={list(actual_gates)} != charter.gate_refs={list(expected_gates)}"
            )
    assert mismatches == {}, f"Covered gates mismatch between workbench and Charter: {mismatches}"


# ── C03: charter_ref required on every workbench ─────────────────────────────


def test_c03_every_workbench_yaml_has_charter_ref() -> None:
    missing: list[str] = []
    for defn in _all_workbench_defs():
        wid = defn.get("workbench_id", "<unknown>")
        if not defn.get("charter_ref"):
            missing.append(wid)
    assert missing == [], f"Workbenches without charter_ref: {missing}"


def test_c03_charter_ref_not_in_optional_fields_and_required_fields_contain_it() -> None:
    import yaml

    schema_path = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "workbench_schema.yaml"
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
    assert "charter_ref" in schema.get(
        "required_workbench_fields", []
    ), "charter_ref must be in required_workbench_fields"
    assert "charter_ref" not in (
        schema.get("optional_workbench_fields") or []
    ), "charter_ref must not be in optional_workbench_fields"


# ── C04: No legacy resource entries; operating_references slot reserved for CH-0035 ──


def test_ch0034_leaves_no_legacy_resource_entries_and_no_operating_references_yet() -> None:
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    assert (
        layer.resource_manifest == ()
    ), "CH-0034 must leave no legacy guide-resource entries and must not populate operating_references; CH-0035 owns operating-reference document binding."


def test_c04_no_legacy_role_in_workbench_response_surface_bindings() -> None:
    legacy_roles = {"instruction_resource", "authoritative_guides", "administration_guides"}
    for defn in _all_workbench_defs():
        wid = defn.get("workbench_id", "<unknown>")
        bindings = (defn.get("workflow_surface") or {}).get("response_surface_bindings") or []
        for binding in bindings:
            roles = set(binding.get("allowed_resource_roles") or [])
            assert not roles & legacy_roles, (
                f"{wid}: binding {binding.get('transaction_kind')!r}/{binding.get('response_envelope')!r} "
                f"still declares legacy roles: {roles & legacy_roles}"
            )


# ── C05: §5 mechanical checks — no transitional allowance, guidance dirs empty ──


def test_c05_no_deferred_membrane_gap_allowlist_in_static_checks() -> None:
    """TD-0034-C05: no transitional-duplicate allowance or exception survives."""
    static_checks = PRODUCT_ROOT / "tests" / "test_arch0002_static_checks.py"
    assert "DEFERRED_MEMBRANE_GAP" not in static_checks.read_text(
        encoding="utf-8"
    ), "DEFERRED_MEMBRANE_GAP allowlist must be removed from test_arch0002_static_checks.py"


def test_c05_guidance_directories_are_empty() -> None:
    """TD-0034-C05: all 29 corpus files deleted — guidance directories must be empty."""
    guidance_dirs = (
        "lantern/authoring_contracts",
        "lantern/administration_procedures",
        "lantern/resources/instructions",
    )
    for directory in guidance_dirs:
        dir_path = PRODUCT_ROOT / directory
        remaining = list(dir_path.glob("*.md")) if dir_path.exists() else []
        assert not remaining, f"guidance directory {directory} still contains files: {[p.name for p in remaining]}"


# ── C06: Behavioral equivalence — orient still delivers task card ─────────────


@pytest.fixture(scope="module")
def _workflow_layer():
    from lantern.workflow.loader import load_workflow_layer

    return load_workflow_layer()


def test_c06_orient_still_delivers_task_card_for_active_workbench(_workflow_layer) -> None:
    from lantern.mcp.orient import handle_orient

    result = handle_orient(
        workflow_layer=_workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    workbench_entries = result.runtime_exposure_posture.get("workbenches", [])
    chartered = [wb for wb in workbench_entries if wb.get("task_card") is not None]
    assert chartered, "orient: no workbench entry carries a task_card after CH-0034"


def test_c06_orient_task_card_has_source_pointer_and_layers(_workflow_layer) -> None:
    from lantern.mcp.orient import handle_orient
    from lantern.workflow.charter import CHARTER_SCHEMA_ID

    result = handle_orient(
        workflow_layer=_workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    for wb in result.runtime_exposure_posture.get("workbenches", []):
        tc = wb.get("task_card")
        if tc is None:
            continue
        sp = tc.get("source_pointer", {})
        assert (
            sp.get("schema_id") == CHARTER_SCHEMA_ID
        ), f"{wb['workbench_id']}: task_card.source_pointer.schema_id mismatch"
        assert tc.get("layers"), f"{wb['workbench_id']}: task_card.layers is absent or empty"
