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

"""TD-0033 C01-C10: Workbench Charter authority and runtime wiring verification.

Covers:
  C01 - Charter schema and body layer sections for every shipped workbench.
  C02 - Selection-gate posture pinning (design_selection + ci_selection).
  C03 - orient delivers task card + charter routing per active workbench.
  C04 - IS-0041 disposition table coverage across all Charters.
  C05 - Custom workbench Charter produces same task card structure as shipped.
  C06 - [Closed by CH-0034] Transitional-duplicate allowance removed.
  C07 - draft delivers Charter authoring-layer body for a Charter-bound workbench.
  C08 - commit delivers Charter administrative-layer body for a Charter-bound workbench.
  C09 - validate delivers Charter validation-layer body for a Charter-bound workbench.
  C10 - FC-6 negative: charter_layer_bodies absent when no match or no workbench_id.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from lantern.workflow.charter import (
    CHARTER_SCHEMA_ID,
    WorkbenchCharter,
    build_task_card,
    load_charter,
    validate_charter_header,
)

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
WORKBENCHES_DIR = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "workbenches"
CHARTERS_DIR = PRODUCT_ROOT / "lantern" / "workbench_charters"

# IS-0041 disposition table — 14 tasks to (workbench_ref, layer_type, posture).
# Tasks 0A/D/G share the upstream_intake_and_baselines administrative tuple.
# Four selection-gate postures are pinned per IS-0041 (marked with [PINNED]).
_IS0041_DISPOSITION = [
    ("governance_onboarding", "authoring", "analysis_only"),  # 0
    ("upstream_intake_and_baselines", "administrative", "administration_authorized"),  # 0A
    ("ch_and_td_readiness", "authoring", "analysis_only"),  # 0B
    ("ch_and_td_readiness", "administrative", "administration_authorized"),  # A
    ("design_candidate_authoring", "authoring", "analysis_only"),  # A1
    ("design_selection", "authoring", "analysis_only"),  # A2 [PINNED]
    ("design_selection", "administrative", "administration_authorized"),  # A3 [PINNED]
    ("ci_selection", "authoring", "analysis_only"),  # B  [PINNED]
    ("ci_selection", "administrative", "administration_authorized"),  # C  [PINNED]
    ("upstream_intake_and_baselines", "administrative", "administration_authorized"),  # D
    ("upstream_intake_and_baselines", "authoring", "analysis_only"),  # E
    ("upstream_intake_and_baselines", "validation", "analysis_only"),  # F
    ("upstream_intake_and_baselines", "administrative", "administration_authorized"),  # G
    ("verification_and_closure", "administrative", "administration_authorized"),  # H
]

_GT110_ACTIVE = {
    "ch_statuses": {"CH-0003": "Ready"},
    "active_gates": ["GT-110"],
    "passed_gates": [],
}


def _load_workbench_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _all_workbench_defs() -> list[dict]:
    return [_load_workbench_yaml(p) for p in sorted(WORKBENCHES_DIR.glob("*.yaml"))]


def _charter_for(workbench_id: str) -> WorkbenchCharter:
    charter_path = CHARTERS_DIR / f"{workbench_id}.md"
    return load_charter(charter_path)


# ── C01: Charter schema and body layer sections ───────────────────────────────


def test_c01_every_shipped_workbench_has_loadable_charter() -> None:
    for defn in _all_workbench_defs():
        wid = defn["workbench_id"]
        charter = _charter_for(wid)
        assert charter.schema_id == CHARTER_SCHEMA_ID, f"{wid}: schema_id mismatch"
        assert charter.charter_id, f"{wid}: charter_id is empty"
        assert charter.workbench_ref == wid, f"{wid}: workbench_ref mismatch"


def test_c01_every_charter_has_at_least_one_layer() -> None:
    for defn in _all_workbench_defs():
        wid = defn["workbench_id"]
        charter = _charter_for(wid)
        assert len(charter.layers) >= 1, f"{wid}: Charter declares no layers"


def test_c01_every_charter_layer_has_required_fields() -> None:
    for defn in _all_workbench_defs():
        wid = defn["workbench_id"]
        charter = _charter_for(wid)
        errs = validate_charter_header(charter, wid)
        assert errs == [], f"{wid}: header validation errors: {errs}"


def test_c01_every_charter_has_routing_section_body() -> None:
    for defn in _all_workbench_defs():
        wid = defn["workbench_id"]
        charter = _charter_for(wid)
        assert charter.routing_section_body, f"{wid}: routing_section_body is empty"


def test_c01_every_charter_layer_has_non_empty_body_section() -> None:
    for defn in _all_workbench_defs():
        wid = defn["workbench_id"]
        charter = _charter_for(wid)
        for layer in charter.layers:
            assert layer.body_section, (
                f"{wid}: layer {layer.label!r} ({layer.layer}/{layer.transaction_moment}) " f"has empty body_section"
            )


# ── C02: Selection-gate posture pinning ──────────────────────────────────────


@pytest.mark.parametrize("workbench_id", ["design_selection", "ci_selection"])
def test_c02_selection_workbench_has_analysis_only_authoring_layer(workbench_id: str) -> None:
    charter = _charter_for(workbench_id)
    matches = [lyr for lyr in charter.layers if lyr.layer == "authoring" and lyr.transaction_posture == "analysis_only"]
    assert matches, f"{workbench_id}: missing authoring/analysis_only layer"


@pytest.mark.parametrize("workbench_id", ["design_selection", "ci_selection"])
def test_c02_selection_workbench_has_administration_authorized_administrative_layer(workbench_id: str) -> None:
    charter = _charter_for(workbench_id)
    matches = [
        lyr
        for lyr in charter.layers
        if lyr.layer == "administrative" and lyr.transaction_posture == "administration_authorized"
    ]
    assert matches, f"{workbench_id}: missing administrative/administration_authorized layer"


def test_c02_design_selection_authoring_layer_is_not_administration_authorized() -> None:
    charter = _charter_for("design_selection")
    authoring_layers = [lyr for lyr in charter.layers if lyr.layer == "authoring"]
    for layer in authoring_layers:
        assert (
            layer.transaction_posture == "analysis_only"
        ), f"design_selection authoring layer must be analysis_only; got {layer.transaction_posture!r}"


def test_c02_ci_selection_authoring_layer_is_not_administration_authorized() -> None:
    charter = _charter_for("ci_selection")
    authoring_layers = [lyr for lyr in charter.layers if lyr.layer == "authoring"]
    for layer in authoring_layers:
        assert (
            layer.transaction_posture == "analysis_only"
        ), f"ci_selection authoring layer must be analysis_only; got {layer.transaction_posture!r}"


# ── C03: orient delivers task card + charter routing ─────────────────────────


@pytest.fixture(scope="module")
def _workflow_layer():
    from lantern.workflow.loader import load_workflow_layer

    return load_workflow_layer()


def test_c03_orient_active_workbench_has_task_card(_workflow_layer) -> None:
    from lantern.mcp.orient import handle_orient

    result = handle_orient(
        workflow_layer=_workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    workbench_entries = result.runtime_exposure_posture.get("workbenches", [])
    chartered = [wb for wb in workbench_entries if wb.get("task_card") is not None]
    assert chartered, "orient: no workbench entry carries a task_card"


def test_c03_task_card_has_source_pointer(_workflow_layer) -> None:
    from lantern.mcp.orient import handle_orient

    result = handle_orient(
        workflow_layer=_workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    for wb in result.runtime_exposure_posture.get("workbenches", []):
        tc = wb.get("task_card")
        if tc is None:
            continue
        assert "source_pointer" in tc, f"{wb['workbench_id']}: task_card missing source_pointer"
        sp = tc["source_pointer"]
        assert sp.get("charter_id"), f"{wb['workbench_id']}: source_pointer.charter_id is empty"
        assert sp.get("schema_id") == CHARTER_SCHEMA_ID, f"{wb['workbench_id']}: schema_id mismatch"
        assert (
            sp.get("workbench_ref") == wb["workbench_id"]
        ), f"{wb['workbench_id']}: source_pointer.workbench_ref mismatch"


def test_c03_task_card_has_layers_list(_workflow_layer) -> None:
    from lantern.mcp.orient import handle_orient

    result = handle_orient(
        workflow_layer=_workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    for wb in result.runtime_exposure_posture.get("workbenches", []):
        tc = wb.get("task_card")
        if tc is None:
            continue
        assert "layers" in tc, f"{wb['workbench_id']}: task_card missing layers"
        assert isinstance(tc["layers"], list), f"{wb['workbench_id']}: task_card.layers must be a list"
        assert tc["layers"], f"{wb['workbench_id']}: task_card.layers is empty"


def test_c03_charter_routing_present_when_task_card_present(_workflow_layer) -> None:
    from lantern.mcp.orient import handle_orient

    result = handle_orient(
        workflow_layer=_workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    for wb in result.runtime_exposure_posture.get("workbenches", []):
        if wb.get("task_card") is not None:
            assert wb.get(
                "charter_routing"
            ), f"{wb['workbench_id']}: charter_routing is missing or empty when task_card is present"


# ── C04: IS-0041 disposition table coverage ──────────────────────────────────


def test_c04_all_is0041_disposition_tuples_present_in_charters() -> None:
    missing: list[tuple[str, str, str]] = []
    for workbench_ref, layer_type, posture in set(_IS0041_DISPOSITION):
        charter_path = CHARTERS_DIR / f"{workbench_ref}.md"
        assert charter_path.exists(), f"Charter file missing for {workbench_ref!r}"
        charter = load_charter(charter_path)
        has_match = any(lyr.layer == layer_type and lyr.transaction_posture == posture for lyr in charter.layers)
        if not has_match:
            missing.append((workbench_ref, layer_type, posture))
    assert missing == [], f"IS-0041 disposition tuples with no matching Charter layer: {missing}"


def test_c04_selection_gate_pinned_postures_are_present() -> None:
    pinned = [
        ("design_selection", "authoring", "analysis_only"),
        ("design_selection", "administrative", "administration_authorized"),
        ("ci_selection", "authoring", "analysis_only"),
        ("ci_selection", "administrative", "administration_authorized"),
    ]
    for wid, layer_type, posture in pinned:
        charter = _charter_for(wid)
        has_match = any(lyr.layer == layer_type and lyr.transaction_posture == posture for lyr in charter.layers)
        assert has_match, f"Pinned posture missing in {wid}: ({layer_type}, {posture})"


# ── C05: Custom workbench Charter task card structure ────────────────────────


_CUSTOM_CHARTER_YAML = textwrap.dedent(
    """\
    schema_id: lantern.operator.workbench_charter.v1
    charter_id: charter.custom_test_workbench
    title: Custom Test Charter
    workbench_ref: custom_test_workbench
    gate_refs: []
    artifact_families:
      - CH
    layers:
      - layer: authoring
        label: Custom authoring layer
        transaction_moment: draft
        transaction_posture: analysis_only
        required_inputs:
          - A required input
        scope_boundary: The scope boundary for this custom layer.
        stop_condition: The stop condition for this custom layer.
        deliverables:
          - A deliverable artifact
        forbidden_actions:
          - A forbidden action
        template_refs: []
    context_slots: []
"""
)

_CUSTOM_CHARTER_BODY = textwrap.dedent(
    """\
    # Custom Test Charter

    ## Routing & applicability

    Custom workbench for test fixture purposes only.
"""
)


def test_c05_custom_charter_task_card_has_same_structure_as_shipped(tmp_path: Path) -> None:
    charter_text = f"```yaml\n{_CUSTOM_CHARTER_YAML}```\n\n{_CUSTOM_CHARTER_BODY}"
    charter_file = tmp_path / "custom_test_workbench.md"
    charter_file.write_text(charter_text, encoding="utf-8")

    custom = load_charter(charter_file)
    custom_tc = build_task_card(custom)

    # Load any shipped charter to compare structure
    shipped = _charter_for("ch_and_td_readiness")
    shipped_tc = build_task_card(shipped)

    assert set(custom_tc.keys()) == set(shipped_tc.keys()), "task card top-level keys differ"
    assert "source_pointer" in custom_tc
    assert "layers" in custom_tc
    assert set(custom_tc["source_pointer"].keys()) == set(shipped_tc["source_pointer"].keys())
    assert custom_tc["layers"]
    assert set(custom_tc["layers"][0].keys()) == set(shipped_tc["layers"][0].keys())


def test_c05_custom_charter_source_pointer_fields_are_correct(tmp_path: Path) -> None:
    charter_text = f"```yaml\n{_CUSTOM_CHARTER_YAML}```\n\n{_CUSTOM_CHARTER_BODY}"
    charter_file = tmp_path / "custom_test_workbench.md"
    charter_file.write_text(charter_text, encoding="utf-8")

    charter = load_charter(charter_file)
    tc = build_task_card(charter)

    sp = tc["source_pointer"]
    assert sp["charter_id"] == "charter.custom_test_workbench"
    assert sp["schema_id"] == CHARTER_SCHEMA_ID
    assert sp["workbench_ref"] == "custom_test_workbench"


# ── C07: draft delivers Charter authoring-layer body ─────────────────────────


def test_c07_draft_response_includes_charter_layer_bodies_for_chartered_workbench(
    _workflow_layer,
) -> None:
    from lantern.mcp.draft import handle_draft

    result = handle_draft(
        workflow_layer=_workflow_layer,
        workbench_id="design_candidate_authoring",
        artifact_family="DC",
        payload=None,
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    assert (
        "charter_layer_bodies" in result
    ), "draft response missing charter_layer_bodies for design_candidate_authoring"
    bodies = result["charter_layer_bodies"]
    assert isinstance(bodies, list) and bodies, "charter_layer_bodies must be a non-empty list"


def test_c07_draft_charter_layer_bodies_have_label_and_body(
    _workflow_layer,
) -> None:
    from lantern.mcp.draft import handle_draft

    result = handle_draft(
        workflow_layer=_workflow_layer,
        workbench_id="design_candidate_authoring",
        artifact_family="DC",
        payload=None,
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    for entry in result.get("charter_layer_bodies", []):
        assert "label" in entry, f"charter_layer_bodies entry missing 'label': {entry}"
        assert "body" in entry, f"charter_layer_bodies entry missing 'body': {entry}"
        assert entry["body"], f"body is empty for label {entry.get('label')!r}"


def test_c07_draft_body_matches_charter_authoring_layer(
    _workflow_layer,
) -> None:
    from lantern.mcp.draft import handle_draft

    result = handle_draft(
        workflow_layer=_workflow_layer,
        workbench_id="design_candidate_authoring",
        artifact_family="DC",
        payload=None,
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    bodies = result.get("charter_layer_bodies", [])
    charter = _charter_for("design_candidate_authoring")
    authoring_layers = [lyr for lyr in charter.layers if lyr.transaction_moment == "draft"]
    assert len(bodies) == len(
        authoring_layers
    ), f"expected {len(authoring_layers)} authoring layer(s), got {len(bodies)}"
    for entry, layer in zip(bodies, authoring_layers):
        assert entry["label"] == layer.label
        assert entry["body"] == layer.body_section


# ── C08: commit delivers Charter administrative-layer body ────────────────────


def test_c08_commit_response_includes_charter_layer_bodies_for_chartered_workbench(
    _workflow_layer,
) -> None:
    from lantern.mcp.commit import handle_commit

    result = handle_commit(
        workflow_layer=_workflow_layer,
        workbench_id="design_selection",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    assert "charter_layer_bodies" in result, "commit response missing charter_layer_bodies for design_selection"
    bodies = result["charter_layer_bodies"]
    assert isinstance(bodies, list) and bodies, "charter_layer_bodies must be a non-empty list"


def test_c08_commit_charter_layer_bodies_have_label_and_body(
    _workflow_layer,
) -> None:
    from lantern.mcp.commit import handle_commit

    result = handle_commit(
        workflow_layer=_workflow_layer,
        workbench_id="design_selection",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    for entry in result.get("charter_layer_bodies", []):
        assert "label" in entry, f"charter_layer_bodies entry missing 'label': {entry}"
        assert "body" in entry, f"charter_layer_bodies entry missing 'body': {entry}"
        assert entry["body"], f"body is empty for label {entry.get('label')!r}"


def test_c08_commit_body_matches_charter_administrative_layer(
    _workflow_layer,
) -> None:
    from lantern.mcp.commit import handle_commit

    result = handle_commit(
        workflow_layer=_workflow_layer,
        workbench_id="design_selection",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    bodies = result.get("charter_layer_bodies", [])
    charter = _charter_for("design_selection")
    admin_layers = [lyr for lyr in charter.layers if lyr.transaction_moment == "commit"]
    assert len(bodies) == len(admin_layers), f"expected {len(admin_layers)} administrative layer(s), got {len(bodies)}"
    for entry, layer in zip(bodies, admin_layers):
        assert entry["label"] == layer.label
        assert entry["body"] == layer.body_section


# ── C09: validate delivers Charter validation-layer body ──────────────────────


def test_c09_validate_response_includes_charter_layer_bodies_when_workbench_has_validation_layer(
    _workflow_layer,
) -> None:
    from lantern.mcp.validate import handle_validate

    result = handle_validate(
        workflow_layer=_workflow_layer,
        scope="workspace",
        workbench_id="upstream_intake_and_baselines",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    assert (
        "charter_layer_bodies" in result
    ), "validate response missing charter_layer_bodies for upstream_intake_and_baselines"
    bodies = result["charter_layer_bodies"]
    assert isinstance(bodies, list) and bodies, "charter_layer_bodies must be a non-empty list"


def test_c09_validate_charter_layer_bodies_have_label_and_body(
    _workflow_layer,
) -> None:
    from lantern.mcp.validate import handle_validate

    result = handle_validate(
        workflow_layer=_workflow_layer,
        scope="workspace",
        workbench_id="upstream_intake_and_baselines",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    for entry in result.get("charter_layer_bodies", []):
        assert "label" in entry, f"charter_layer_bodies entry missing 'label': {entry}"
        assert "body" in entry, f"charter_layer_bodies entry missing 'body': {entry}"
        assert entry["body"], f"body is empty for label {entry.get('label')!r}"


def test_c09_validate_body_matches_charter_validation_layer(
    _workflow_layer,
) -> None:
    from lantern.mcp.validate import handle_validate

    result = handle_validate(
        workflow_layer=_workflow_layer,
        scope="workspace",
        workbench_id="upstream_intake_and_baselines",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    bodies = result.get("charter_layer_bodies", [])
    charter = _charter_for("upstream_intake_and_baselines")
    validation_layers = [lyr for lyr in charter.layers if lyr.transaction_moment == "validate"]
    assert len(bodies) == len(
        validation_layers
    ), f"expected {len(validation_layers)} validation layer(s), got {len(bodies)}"
    for entry, layer in zip(bodies, validation_layers):
        assert entry["label"] == layer.label
        assert entry["body"] == layer.body_section


# ── C10: FC-6 negative — charter_layer_bodies absent when no match ────────────


def test_c10_validate_without_workbench_id_omits_charter_layer_bodies(
    _workflow_layer,
) -> None:
    from lantern.mcp.validate import handle_validate

    result = handle_validate(
        workflow_layer=_workflow_layer,
        scope="workspace",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    assert (
        "charter_layer_bodies" not in result
    ), "charter_layer_bodies must be absent when workbench_id is not supplied to validate"


def test_c10_validate_with_no_validation_layer_workbench_omits_charter_layer_bodies(
    _workflow_layer,
) -> None:
    from lantern.mcp.validate import handle_validate

    # design_candidate_authoring has only an authoring layer — no validation layer.
    result = handle_validate(
        workflow_layer=_workflow_layer,
        scope="workspace",
        workbench_id="design_candidate_authoring",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    assert (
        "charter_layer_bodies" not in result
    ), "charter_layer_bodies must be absent when Charter has no validation layer"


def test_c10_commit_with_no_administrative_layer_workbench_omits_charter_layer_bodies(
    _workflow_layer,
) -> None:
    from lantern.mcp.commit import handle_commit

    # design_candidate_authoring has only an authoring layer — no administrative layer.
    result = handle_commit(
        workflow_layer=_workflow_layer,
        workbench_id="design_candidate_authoring",
        product_root=PRODUCT_ROOT,
        governance_root=None,
    )
    assert (
        "charter_layer_bodies" not in result
    ), "charter_layer_bodies must be absent when Charter has no administrative layer"
