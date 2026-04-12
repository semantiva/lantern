"""Tests for Lantern MCP tool handlers and repo-local docs."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest

from lantern.artifacts.renderers import canonical_render_markdown
from lantern.mcp.catalog import FIXED_TOOL_SURFACE, get_allowed_roles_for_transaction
from lantern.mcp.inspect import (
    InspectCatalogResult,
    InspectChangeSurfaceResult,
    InspectContractResult,
    InspectError,
    InspectStatusContractResult,
    InspectWorkspaceResult,
    handle_inspect,
)
from lantern.mcp.orient import OrientResponse, handle_orient
from lantern.mcp.server import configure_server_paths, inspect as server_inspect, mcp as mcp_server
from lantern.workflow.loader import load_workflow_layer

PRODUCT_ROOT = Path(__file__).resolve().parents[1]

_REQUIRED_ORIENT_ANCHORS = frozenset(
    {
        "active_workbench_ids",
        "preferred_workbench_id",
        "surface_classification",
        "blockers",
        "preconditions",
        "runtime_exposure_posture",
        "next_valid_actions",
        "ambiguity",
    }
)

_REQUIRED_WORKSPACE_ANCHORS = frozenset(
    {
        "kind",
        "product_root",
        "governance_root",
        "runtime_surface_classification",
        "consistency_state",
        "startup_issues",
        "read_only",
    }
)

_GT110_ACTIVE = {
    "ch_statuses": {"CH-0003": "Ready"},
    "active_gates": ["GT-110"],
    "passed_gates": [],
}


@pytest.fixture(scope="module")
def workflow_layer():
    return load_workflow_layer()


def _write_selected_ci(governance_root: Path) -> Path:
    ci_path = governance_root / "ci" / "CI-0004-selected.md"
    ci_path.parent.mkdir(parents=True, exist_ok=True)
    content = canonical_render_markdown(
        header={
            "ch_id": "CH-0004",
            "ci_id": "CI-0004-selected",
            "status": "Selected",
            "title": "Selected CI for change-surface inspection",
            "allowed_change_surface": ["src/allowed.txt", "tests/"],
        },
        artifact_id="CI-0004-selected",
        title="Selected CI for change-surface inspection",
        sections=[
            {"heading": "Intent", "body": "Selected CI fixture."},
        ],
    )
    ci_path.write_text(content, encoding="utf-8")
    return ci_path


def test_c04_catalog_contains_exactly_five_tools(workflow_layer) -> None:
    result = handle_inspect(kind="catalog", workflow_layer=workflow_layer)
    assert isinstance(result, InspectCatalogResult)
    assert set(result.tools) == set(FIXED_TOOL_SURFACE)
    result_dict = vars(result)
    for forbidden in ("schema", "definitions", "properties", "allOf", "anyOf"):
        assert forbidden not in result_dict


def test_c04_catalog_contract_refs_are_lantern_local(workflow_layer) -> None:
    result = handle_inspect(kind="catalog", workflow_layer=workflow_layer)
    assert result.contract_refs
    for ref in result.contract_refs:
        assert ref.startswith("contract.")


def test_c04_catalog_workbench_count_matches_layer(workflow_layer) -> None:
    result = handle_inspect(kind="catalog", workflow_layer=workflow_layer)
    assert result.workbench_count == len(workflow_layer.workbenches)


def test_c01_contract_response_exposes_server_owned_mutation_surface(workflow_layer) -> None:
    result = handle_inspect(
        kind="contract",
        workflow_layer=workflow_layer,
        contract_ref="contract.ci_authoring.v1",
    )
    assert isinstance(result, InspectContractResult)
    assert result.server_owned_contract["structured_input_only"] is True
    assert result.server_owned_contract["raw_markdown_client_input_allowed"] is False
    assert "draft" in result.server_owned_contract["request_schemas"]


def test_c01_status_contract_inspect_is_machine_readable(workflow_layer) -> None:
    result = handle_inspect(kind="status_contract", workflow_layer=workflow_layer)

    assert isinstance(result, InspectStatusContractResult)
    assert result.authoritative_source_path == "workflow/artifact_status_contract.yaml"
    assert len(result.projection_sha256) == 64
    assert result.families["CH"]["canonical_statuses"] == ["Proposed", "Ready", "Addressed"]
    assert result.families["IS"]["canonical_statuses"] == ["NEW", "NEEDS_INFO", "ACCEPTED", "DEFERRED", "REJECTED", "RESOLVED"]
    assert result.families["EV"]["normal_path_policy"] == "statusless"


def test_c02_contract_response_keeps_server_and_workflow_layers_distinct(workflow_layer) -> None:
    result = handle_inspect(
        kind="contract",
        workflow_layer=workflow_layer,
        contract_ref="contract.selected_ci_application.v1",
    )
    assert isinstance(result, InspectContractResult)
    assert result.server_owned_contract["change_surface_preflight"] is True
    assert result.workflow_owned_contract["contract_ref"] == "contract.selected_ci_application.v1"
    assert result.workflow_owned_contract["resource_refs"]
    assert result.resource_packets
    assert result.server_owned_contract != result.workflow_owned_contract


def test_c05_contract_response_scoped_to_requested_ref(workflow_layer) -> None:
    first_ref = workflow_layer.contract_catalog[0].contract_ref
    result = handle_inspect(
        kind="contract", workflow_layer=workflow_layer, contract_ref=first_ref
    )
    assert isinstance(result, InspectContractResult)
    assert result.contract_ref == first_ref


def test_c05_contract_response_excludes_unrelated_contracts(workflow_layer) -> None:
    all_refs = list({entry.contract_ref for entry in workflow_layer.contract_catalog})
    assert len(all_refs) >= 2
    result = handle_inspect(
        kind="contract", workflow_layer=workflow_layer, contract_ref=all_refs[0]
    )
    body_str = str(vars(result))
    assert all_refs[1] not in body_str


def test_c05_change_surface_inspection_is_deterministic(workflow_layer, tmp_path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    ci_path = _write_selected_ci(governance_root)
    first = handle_inspect(
        kind="change_surface",
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        product_root=product_root,
        governance_root=governance_root,
        ci_path=str(ci_path),
    )
    second = handle_inspect(
        kind="change_surface",
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        product_root=product_root,
        governance_root=governance_root,
        ci_path=str(ci_path),
    )
    assert isinstance(first, InspectChangeSurfaceResult)
    assert first == second
    assert first.allowed_change_surface == ("src/allowed.txt", "tests/")


def test_c06_workspace_response_has_all_required_anchors(workflow_layer, tmp_path) -> None:
    result = handle_inspect(
        kind="workspace", workflow_layer=workflow_layer, product_root=tmp_path
    )
    assert isinstance(result, InspectWorkspaceResult)
    result_dict = vars(result)
    for anchor in _REQUIRED_WORKSPACE_ANCHORS:
        assert anchor in result_dict


def test_c06_workspace_without_governance_reports_missing_governance(
    workflow_layer,
    tmp_path,
) -> None:
    result = handle_inspect(
        kind="workspace", workflow_layer=workflow_layer, product_root=tmp_path
    )
    assert result.governance_root is None
    assert result.consistency_state == "missing_governance"

def test_td0011_c01_external_workspace_topology_is_valid_without_product_local_lantern_tree(
    workflow_layer,
    tmp_path,
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    result = handle_inspect(
        kind="workspace",
        workflow_layer=workflow_layer,
        product_root=product_root,
        governance_root=governance_root,
    )

    assert result.consistency_state == "valid"
    assert result.runtime_surface_classification == "full_governed_surface"
    assert not result.startup_issues
    assert not (product_root / "lantern").exists()



def test_c06_workspace_requires_explicit_product_root(workflow_layer) -> None:
    with pytest.raises(InspectError):
        handle_inspect(kind="workspace", workflow_layer=workflow_layer)


def test_c06_workspace_read_only_is_true_and_no_mutation_affordance(
    workflow_layer, tmp_path
) -> None:
    result = handle_inspect(
        kind="workspace", workflow_layer=workflow_layer, product_root=tmp_path
    )
    assert result.read_only is True
    result_dict = vars(result)
    for mutation_key in ("write", "delete", "create", "patch", "mutation_affordance", "mutate"):
        assert mutation_key not in result_dict


def test_c07_orient_contains_all_required_anchors(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    assert isinstance(result, OrientResponse)
    result_dict = vars(result)
    for anchor in _REQUIRED_ORIENT_ANCHORS:
        assert anchor in result_dict


def test_c07_orient_active_workbench_ids_is_non_empty_tuple(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    assert isinstance(result.active_workbench_ids, tuple)
    assert len(result.active_workbench_ids) >= 1


def test_c07_orient_next_valid_actions_non_empty_when_active(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    assert result.next_valid_actions


def test_c07_orient_runtime_exposure_posture_has_workbenches_key(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    assert "workbenches" in result.runtime_exposure_posture


def test_c08_orient_resources_limited_to_allowed_roles(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    for wb_entry in result.runtime_exposure_posture.get("workbenches", []):
        workbench = workflow_layer.get_workbench(wb_entry["workbench_id"])
        allowed = set(
            get_allowed_roles_for_transaction(workbench, "orient")
            or get_allowed_roles_for_transaction(workbench, "inspect")
        )
        allowed.discard("administration_guides")
        for resource in wb_entry.get("resources", []):
            for role in resource["roles"]:
                assert role in allowed


def test_c08_all_emitted_resource_ids_resolve_in_manifest_or_inline_packets(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    manifest_ids = {entry.resource_id for entry in workflow_layer.resource_manifest}
    for wb_entry in result.runtime_exposure_posture.get("workbenches", []):
        packet_ids = {packet["resource_id"] for packet in wb_entry.get("resource_packets", [])}
        for resource in wb_entry.get("resources", []):
            assert resource["resource_id"] in manifest_ids or resource["resource_id"] in packet_ids


def test_td0006_c04_contract_inspect_surfaces_logical_refs_and_inline_packets(workflow_layer) -> None:
    result = handle_inspect(
        kind="contract",
        workflow_layer=workflow_layer,
        contract_ref="contract.ch_td_readiness.v1",
    )

    assert result.resource_refs
    assert result.resource_packets
    assert any(ref.startswith("resource.template.") for ref in result.resource_refs)
    assert all(ref.startswith("resource.") for ref in result.resource_refs)
    assert all("path" not in packet for packet in result.resource_packets)
    assert any("artifact_templates" in packet["roles"] for packet in result.resource_packets)
    assert {packet["resource_id"] for packet in result.resource_packets}.issuperset(
        set(result.resource_refs)
    )


def test_td0006_c04_orient_surfaces_logical_refs_and_inline_packets(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )

    for wb_entry in result.runtime_exposure_posture.get("workbenches", []):
        packet_ids = {packet["resource_id"] for packet in wb_entry.get("resource_packets", [])}
        assert any("artifact_templates" in resource["roles"] for resource in wb_entry.get("resources", []))
        assert any(
            "artifact_templates" in packet["roles"]
            for packet in wb_entry.get("resource_packets", [])
        )
        for resource in wb_entry.get("resources", []):
            assert "path" not in resource
            assert resource["resource_id"] in packet_ids


def test_td0006_c05_source_tree_startup_does_not_require_generated_skill_folders(tmp_path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    config_root = governance_root / "workflow" / "configuration"

    product_root.mkdir()
    (config_root / "instructions").mkdir(parents=True)
    (config_root / "workbenches").mkdir()
    (config_root / "guides").mkdir()
    (config_root / "main.yaml").write_text(
        "configuration_version: '1'\ndeclared_posture: full_governed_surface\n",
        encoding="utf-8",
    )

    configure_server_paths(product_root=product_root, governance_root=governance_root)
    result = server_inspect(kind="catalog")

    assert result["kind"] == "catalog"
    assert not (config_root / "generated_skill").exists()
    assert not (config_root / "generated_artifact_templates").exists()


def test_c09_inspect_catalog_does_not_surface_administration_guides(
    workflow_layer,
) -> None:
    result = handle_inspect(kind="catalog", workflow_layer=workflow_layer)
    result_str = str(vars(result))
    assert "administration_guides" not in result_str


def test_c09_orient_does_not_surface_administration_guides_in_resources(
    workflow_layer,
) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    for wb_entry in result.runtime_exposure_posture.get("workbenches", []):
        for resource in wb_entry.get("resources", []):
            assert "administration_guides" not in resource["roles"]


def test_c11_readme_exists_at_product_repo_root() -> None:
    readme_path = PRODUCT_ROOT / "README.md"
    assert readme_path.exists()


def test_c11_readme_points_to_workflow_readme() -> None:
    readme_path = PRODUCT_ROOT / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text(encoding="utf-8")
    assert "lantern/workflow/README.md" in content


def test_c11_workflow_readme_exists() -> None:
    workflow_readme = PRODUCT_ROOT / "lantern" / "workflow" / "README.md"
    assert workflow_readme.exists()


def test_c11_workflow_readme_contains_all_required_anchors() -> None:
    workflow_readme = PRODUCT_ROOT / "lantern" / "workflow" / "README.md"
    assert workflow_readme.exists()
    content = workflow_readme.read_text(encoding="utf-8")
    for anchor in (
        "workbench_registry.yaml",
        "transaction_profiles.yaml",
        "workflow_map.md",
        "workbench_resource_bindings.md",
    ):
        assert anchor in content


def test_c11_workflow_readme_has_authored_generated_boundary_text() -> None:
    workflow_readme = PRODUCT_ROOT / "lantern" / "workflow" / "README.md"
    content = workflow_readme.read_text(encoding="utf-8").lower()
    assert "authored" in content
    assert "generated" in content


def test_server_registers_fixed_five_tool_names() -> None:
    names = {tool.name for tool in asyncio.run(mcp_server.list_tools())}
    assert names == set(FIXED_TOOL_SURFACE)


def test_td0009_c06_gt130_docs_require_expectation_to_delivery_review() -> None:
    guide = (PRODUCT_ROOT / "lantern" / "resources" / "guides" / "verification_and_closure.md").read_text(encoding="utf-8")
    admin = (PRODUCT_ROOT / "lantern" / "administration_procedures" / "GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION.md").read_text(encoding="utf-8")
    for anchor in (
        "initiative objective",
        "roadmap role",
        "requirements satisfaction",
        "architectural fit",
        "clean-state",
        "reproducibility",
    ):
        assert anchor in guide.lower() or anchor in admin.lower()


def test_td0009_c07_readme_documents_manual_install_and_native_smoke_path() -> None:
    content = (PRODUCT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "pip install lantern-grammar" in content
    assert "python -m lantern.mcp.server" in content
    assert 'validate(scope="workspace")' in content
    assert "without `lantern-ops-bridge`" in content


def test_td0011_c03_bootstrap_docs_forbid_runtime_vendoring_and_define_minimal_product_surface() -> None:
    readme = (PRODUCT_ROOT / "README.md").read_text(encoding="utf-8")
    template = (PRODUCT_ROOT / "lantern" / "templates" / "TEMPLATE__PRODUCT_REPO_AGENTS.md").read_text(encoding="utf-8")
    onboarding = (PRODUCT_ROOT / "lantern" / "resources" / "instructions" / "governance_onboarding.md").read_text(encoding="utf-8")

    assert "must **not** vendor or copy a `lantern/` runtime tree" in readme
    assert "Minimal tracked bootstrap surface" in readme
    assert "tools/run-lantern-mcp.sh" in readme
    assert ".vscode/mcp.json" in readme
    assert "Do **not** vendor or copy the Lantern runtime" in template
    assert "Do not instruct operators to vendor or copy the Lantern runtime" in onboarding
