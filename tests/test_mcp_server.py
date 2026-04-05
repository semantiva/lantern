"""Tests for Lantern MCP tool handlers and repo-local docs."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest

from lantern.mcp.catalog import FIXED_TOOL_SURFACE, get_allowed_roles_for_transaction
from lantern.mcp.inspect import (
    InspectCatalogResult,
    InspectContractResult,
    InspectError,
    InspectWorkspaceResult,
    handle_inspect,
)
from lantern.mcp.orient import OrientResponse, handle_orient
from lantern.mcp.server import mcp as mcp_server
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
        allowed = set(get_allowed_roles_for_transaction(workbench, "orient"))
        for resource in wb_entry.get("resources", []):
            for role in resource["roles"]:
                assert role in allowed


def test_c08_all_emitted_resource_ids_resolve_in_manifest(workflow_layer) -> None:
    result = handle_orient(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    manifest_ids = {entry.resource_id for entry in workflow_layer.resource_manifest}
    for wb_entry in result.runtime_exposure_posture.get("workbenches", []):
        for resource in wb_entry.get("resources", []):
            assert resource["resource_id"] in manifest_ids


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


def test_c11_workflow_readme_has_validation_guidance() -> None:
    workflow_readme = PRODUCT_ROOT / "lantern" / "workflow" / "README.md"
    content = workflow_readme.read_text(encoding="utf-8").lower()
    assert "valid" in content


def test_c11_workflow_readme_does_not_link_back_to_ssot_container() -> None:
    workflow_readme = PRODUCT_ROOT / "lantern" / "workflow" / "README.md"
    content = workflow_readme.read_text(encoding="utf-8")
    ssot_link_pattern = re.compile(r"\[.*?\]\(.*?lantern-governance.*?\)")
    matches = ssot_link_pattern.findall(content)
    assert not matches


def test_server_registers_exactly_five_tools() -> None:
    registered_tools = {tool.name for tool in asyncio.run(mcp_server.list_tools())}
    expected = {"inspect", "orient", "draft", "commit", "validate"}
    assert registered_tools == expected
