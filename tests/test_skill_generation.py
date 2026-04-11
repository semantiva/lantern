"""TD-0006 packaged thin-skill and discovery-manifest tests."""
from __future__ import annotations

import json
from typing import Any

from lantern.skills.generator import (
    PACKAGED_SKILL_MANIFEST_PATH,
    PACKAGED_SKILL_MD_PATH,
    assert_packaged_skill_surface_current,
    build_packaged_skill_manifest,
    build_packaged_skill_md,
)
from lantern.workflow.loader import load_workflow_layer


def _contains_forbidden_path_key(value: Any) -> bool:
    if isinstance(value, dict):
        if "path" in value:
            return True
        return any(_contains_forbidden_path_key(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_path_key(item) for item in value)
    return False


def test_td0006_c01_packaged_skill_has_mandatory_header_and_routing_content() -> None:
    layer = load_workflow_layer()
    skill = build_packaged_skill_md(layer)

    assert skill.startswith("---\nname: lantern\ndescription: Use this skill when the task involves Lantern-governed workflow work.")
    assert "---\n\n# Lantern Operator Skill\n" in skill
    assert "## Use Lantern when" in skill
    assert "## Do not use Lantern as" in skill
    assert "## What Lantern gives you" in skill
    assert "## First MCP move" in skill
    assert "`inspect(kind=\"catalog\")`" in skill
    assert "`inspect(kind=\"workspace\")`" in skill
    assert "## Universal discovery sequence" in skill
    assert "## Workflow modes currently exposed" in skill
    assert "## Minimal routing hints" in skill
    assert "## Immutable safety rules" in skill
    assert "## Operating posture" in skill

    for mode_id in [item["mode_id"] for item in build_packaged_skill_manifest(layer)["workflow_modes"]]:
        assert f"- `{mode_id}`" in skill

    for forbidden in (
        "Operator instruction resource for workbench",
        "GT-120__CI_SELECTION_ADMINISTRATION",
        "TEMPLATE__CI",
        "lantern/resources/",
        "lantern/templates/",
    ):
        assert forbidden not in skill


def test_td0006_c02_manifest_is_mode_first_and_path_free() -> None:
    layer = load_workflow_layer()
    manifest = build_packaged_skill_manifest(layer)

    assert manifest["skill_schema_version"] == "1"
    assert manifest["workflow_release"]["workflow_layer_hash"]
    assert manifest["workflow_release"]["contract_catalog_hash"]
    assert manifest["workflow_release"]["resource_manifest_hash"]
    assert manifest["workflow_modes"]
    assert not _contains_forbidden_path_key(manifest)

    for item in manifest["workflow_modes"]:
        assert item["mode_id"]
        assert item["entry_workbench_id"]
        assert item["entry_contract_refs"]
        assert item["resource_refs"]


def test_td0006_c02_manifest_carries_template_refs_for_draftable_modes() -> None:
    manifest = build_packaged_skill_manifest(load_workflow_layer())
    assert any(
        ref.startswith("resource.template.")
        for item in manifest["workflow_modes"]
        for ref in item["resource_refs"]
    )
    selected_ci_mode = next(
        item
        for item in manifest["workflow_modes"]
        if item["entry_workbench_id"] == "selected_ci_application"
    )
    assert all(
        not ref.startswith("resource.template.")
        for ref in selected_ci_mode["resource_refs"]
    )


def test_td0006_c03_packaged_first_touch_route_is_mechanically_derivable() -> None:
    layer = load_workflow_layer()
    manifest = build_packaged_skill_manifest(layer)
    workbench_ids = {workbench.workbench_id for workbench in layer.workbenches}
    contract_lookup = {
        workbench.workbench_id: set(workbench.contract_refs) for workbench in layer.workbenches
    }

    assert "inspect(kind=\"catalog\")" in build_packaged_skill_md(layer)
    assert "inspect(kind=\"workspace\")" in build_packaged_skill_md(layer)

    for mode in manifest["workflow_modes"]:
        assert mode["entry_workbench_id"] in workbench_ids
        assert set(mode["entry_contract_refs"]) == contract_lookup[mode["entry_workbench_id"]]


def test_td0006_c06_committed_packaged_surface_matches_packaged_truth() -> None:
    assert_packaged_skill_surface_current()


def test_td0006_c07_packaged_manifest_matches_source_tree_routing() -> None:
    layer = load_workflow_layer()
    committed = json.loads(PACKAGED_SKILL_MANIFEST_PATH.read_text(encoding="utf-8"))
    built = build_packaged_skill_manifest(layer)

    assert committed == built
    assert PACKAGED_SKILL_MD_PATH.read_text(encoding="utf-8") == build_packaged_skill_md(layer)