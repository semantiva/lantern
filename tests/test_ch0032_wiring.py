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

"""TD-0032: delivery-topology wiring of deferred authoring guides (CH-0032)."""

from __future__ import annotations

from pathlib import Path

from lantern.mcp.catalog import build_resource_packets_for_workbench, get_allowed_roles_for_transaction
from lantern.workflow.loader import load_workflow_layer

PRODUCT_ROOT = Path(__file__).resolve().parents[1]

# Expected wiring: guide path → target workbench (from INI-0004 decomposition).
EXPECTED_WIRING = {
    "lantern/authoring_contracts/dip_authoring_guide.md": "upstream_intake_and_baselines",
    "lantern/authoring_contracts/spec_authoring_guide.md": "upstream_intake_and_baselines",
    "lantern/authoring_contracts/arch_authoring_guide.md": "upstream_intake_and_baselines",
    "lantern/authoring_contracts/test_definition_authoring_guide.md": "ch_and_td_readiness",
    "lantern/authoring_contracts/design_baseline_authoring_guide.md": "design_selection",
}


def test_td0032_c01_guides_in_manifest_on_correct_workbench() -> None:
    """Each of the five guides has exactly one manifest entry bound to the stated workbench
    with kind 'authoring_contract'."""
    layer = load_workflow_layer(enforce_generated_artifacts=True)
    manifest_by_path = {entry.path: entry for entry in layer.resource_manifest}
    for path, expected_workbench in EXPECTED_WIRING.items():
        assert path in manifest_by_path, f"guide absent from manifest: {path}"
        entry = manifest_by_path[path]
        assert (
            entry.workbench_id == expected_workbench
        ), f"{path}: expected workbench {expected_workbench!r}, got {entry.workbench_id!r}"
        assert entry.kind == "authoring_contract", f"{path}: expected kind 'authoring_contract', got {entry.kind!r}"


def test_td0032_c02_guides_constructible_in_draft_moment_packet() -> None:
    """Each guide appears in the packet built by build_resource_packets_for_workbench
    when called with the draft-moment allowed roles.

    NOTE: The current MCP surface does not surface administration_guides resources
    to operators through any verb (orient filters them out; inspect uses inspect roles;
    draft returns no resource packets). Runtime operator delivery of administration_guides
    is CH-0033 scope. This test verifies structural constructibility: that the packet
    builder, called with the draft binding's allowed roles, includes each guide.
    """
    layer = load_workflow_layer()
    workbench_map = {wb.workbench_id: wb for wb in layer.workbenches}
    for guide_path, workbench_id in EXPECTED_WIRING.items():
        workbench = workbench_map[workbench_id]
        draft_roles = get_allowed_roles_for_transaction(workbench, "draft")
        assert (
            "administration_guides" in draft_roles
        ), f"{workbench_id} draft binding does not include administration_guides"
        packets = build_resource_packets_for_workbench(layer, workbench_id, draft_roles)
        packet_paths = {p["resource_id"] for p in packets}
        guide_resource_ids = {entry.resource_id for entry in layer.resource_manifest if entry.path == guide_path}
        assert guide_resource_ids, f"no manifest entry found for {guide_path}"
        for rid in guide_resource_ids:
            assert (
                rid in packet_paths
            ), f"{guide_path} (resource_id={rid}) not in draft-moment packet for {workbench_id}"


def test_td0032_c03_no_allowlist_membrane_check_passes() -> None:
    """The DEFERRED_MEMBRANE_GAP allowlist is gone and every guidance file is manifest-reachable."""
    static_checks = PRODUCT_ROOT / "tests" / "test_arch0002_static_checks.py"
    assert "DEFERRED_MEMBRANE_GAP" not in static_checks.read_text(
        encoding="utf-8"
    ), "DEFERRED_MEMBRANE_GAP allowlist must be removed from test_arch0002_static_checks.py"
    # All guidance files must be in the manifest — verified by load_workflow_layer succeeding
    # and by the membrane test (test_membrane_check_all_guidance_files_are_reachable).
    layer = load_workflow_layer(enforce_generated_artifacts=True)
    manifest_paths = {entry.path for entry in layer.resource_manifest}
    guidance_dirs = (
        "lantern/authoring_contracts",
        "lantern/administration_procedures",
        "lantern/resources/instructions",
    )
    for directory in guidance_dirs:
        for path in (PRODUCT_ROOT / directory).glob("*.md"):
            rel = f"lantern/{path.relative_to(PRODUCT_ROOT / 'lantern').as_posix()}"
            assert rel in manifest_paths, f"guidance file not manifest-reachable: {rel}"


def test_td0032_c04_no_new_resource_kind_or_role() -> None:
    """CH-0032 introduces no new resource kind, class, or role relative to the pre-CH-0032 taxonomy."""
    layer = load_workflow_layer()
    kinds = {entry.kind for entry in layer.resource_manifest}
    roles = {role for entry in layer.resource_manifest for role in entry.roles}
    pre_ch0032_kinds = {"instruction", "authoring_contract", "administration_guide"}
    pre_ch0032_roles = {"instruction_resource", "administration_guides", "authoritative_guides"}
    assert kinds <= pre_ch0032_kinds, f"unexpected new kinds: {kinds - pre_ch0032_kinds}"
    assert roles <= pre_ch0032_roles, f"unexpected new roles: {roles - pre_ch0032_roles}"
