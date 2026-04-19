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

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

from lantern.workflow.loader import (
    DEFAULT_WORKFLOW_ID,
    WorkflowLayerError,
    load_workflow_layer,
    render_generated_artifacts,
)


PRODUCT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DEFAULT_WORKBENCH_IDS = (
    "upstream_intake_and_baselines",
    "ch_and_td_readiness",
    "design_candidate_authoring",
    "design_selection",
    "ci_authoring",
    "ci_selection",
    "selected_ci_application",
    "verification_and_closure",
    "issue_operations",
    "governance_onboarding",
)

REPO_LOCAL_TRIAGE_WORKBENCH = {
    "workbench_id": "repo_local_triage",
    "display_name": "Repo Local Triage",
    "lifecycle_placement": {"kind": "lifecycle-independent"},
    "artifacts_in_scope": ["IS"],
    "intent_classes": ["repo_local_triage"],
    "posture_constraints": ["repo_local_only"],
    "workflow_surface": {
        "allowed_transaction_kinds": ["inspect", "draft", "validate"],
        "draftable_artifact_families": ["IS"],
        "contract_refs": ["contract.issue_operations.v1"],
        "inspect_views": ["catalog", "issues"],
        "response_surface_bindings": [
            {
                "transaction_kind": "inspect",
                "response_envelope": "catalog",
                "allowed_resource_roles": [
                    "instruction_resource",
                    "authoritative_guides",
                    "artifact_templates",
                ],
            },
            {
                "transaction_kind": "inspect",
                "response_envelope": "issues",
                "allowed_resource_roles": [
                    "instruction_resource",
                    "authoritative_guides",
                    "artifact_templates",
                ],
            },
            {
                "transaction_kind": "draft",
                "response_envelope": "default",
                "allowed_resource_roles": [
                    "instruction_resource",
                    "authoritative_guides",
                    "administration_guides",
                ],
            },
            {
                "transaction_kind": "validate",
                "response_envelope": "default",
                "allowed_resource_roles": ["instruction_resource", "authoritative_guides"],
            },
        ],
    },
    "instruction_resource": "lantern/resources/instructions/issue_operations.md",
    "authoritative_guides": ["lantern/resources/guides/issue_operations.md"],
    "administration_guides": ["lantern/administration_procedures/ISSUE__INTAKE_TRIAGE_RESOLUTION_v0.2.0.md"],
    "entry_conditions": ["repo local issue intake"],
    "exit_conditions": ["repo local issue resolved"],
}


def _write_yaml(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _copy_product_fixture(tmp_path: Path) -> Path:
    fixture_root = tmp_path / "product_fixture"
    shutil.copytree(PRODUCT_ROOT / "lantern", fixture_root / "lantern", dirs_exist_ok=True)
    return fixture_root


def _definitions_root(fixture_root: Path) -> Path:
    return fixture_root / "lantern" / "workflow" / "definitions"


def _generated_workflow_map_root(fixture_root: Path) -> Path:
    return fixture_root / "lantern" / "workflow" / "generated" / "workflow_maps"


def _load_fixture_layer(
    fixture_root: Path,
    *,
    governance_root: Path | None = None,
    workflow_id: str | None = None,
    workflow_folder: Path | None = None,
    workbench_folder: Path | None = None,
    enforce_generated_artifacts: bool = False,
):
    definitions_root = _definitions_root(fixture_root)
    return load_workflow_layer(
        governance_root=governance_root,
        workflow_id=workflow_id,
        workflow_folder=workflow_folder,
        workbench_folder=workbench_folder,
        workbench_catalog_root=definitions_root / "workbenches",
        workflow_catalog_root=definitions_root / "workflows",
        schema_path=definitions_root / "workbench_schema.yaml",
        workflow_schema_path=definitions_root / "workflow_schema.yaml",
        transaction_profiles_path=definitions_root / "transaction_profiles.yaml",
        registry_path=definitions_root / "workbench_registry.yaml",
        contract_catalog_path=definitions_root / "contract_catalog.json",
        resource_manifest_path=definitions_root / "resource_manifest.json",
        workflow_map_path=definitions_root / "workflow_map.md",
        workbench_resource_bindings_path=definitions_root / "workbench_resource_bindings.md",
        builtin_workflow_map_root=_generated_workflow_map_root(fixture_root),
        relocation_manifest_path=fixture_root / "lantern" / "preservation" / "relocation_manifest.yaml",
        enforce_generated_artifacts=enforce_generated_artifacts,
    )


def _refresh_fixture_projections(
    fixture_root: Path,
    *,
    governance_root: Path | None = None,
    workflow_id: str | None = None,
    workflow_folder: Path | None = None,
    workbench_folder: Path | None = None,
) -> None:
    definitions_root = _definitions_root(fixture_root)
    workflow_map_root = _generated_workflow_map_root(fixture_root)
    workflow_map_root.mkdir(parents=True, exist_ok=True)

    layer = _load_fixture_layer(
        fixture_root,
        governance_root=governance_root,
        workflow_id=workflow_id,
        workflow_folder=workflow_folder,
        workbench_folder=workbench_folder,
        enforce_generated_artifacts=False,
    )
    generated = render_generated_artifacts(
        workflow_id=layer.selected_workflow_id,
        workflow_display_name=layer.selected_workflow_display_name,
        runtime_surface_classification=layer.runtime_surface_classification,
        workbenches=layer.workbenches,
        transaction_profiles=layer.transaction_profiles,
        contract_catalog=layer.contract_catalog,
        resource_manifest=layer.resource_manifest,
    )
    (definitions_root / "workbench_registry.yaml").write_text(
        generated.compatibility_registry_text,
        encoding="utf-8",
    )
    (definitions_root / "contract_catalog.json").write_text(
        json.dumps(generated.contract_catalog_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (definitions_root / "resource_manifest.json").write_text(
        json.dumps(generated.resource_manifest_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (definitions_root / "workflow_map.md").write_text(generated.workflow_map_text, encoding="utf-8")
    (definitions_root / "workbench_resource_bindings.md").write_text(
        generated.workbench_resource_bindings_text,
        encoding="utf-8",
    )
    (workflow_map_root / f"{layer.selected_workflow_id}.md").write_text(
        generated.built_in_workflow_map_text,
        encoding="utf-8",
    )


def _write_repo_local_catalog(
    governance_root: Path,
    *,
    workflow_name: str,
    workbench_name: str = "repo_local_triage",
    display_name: str = "Repo Local Triage",
    workflow_ids: tuple[str, ...] | None = None,
    workflow_folder: Path | None = None,
    workbench_folder: Path | None = None,
) -> tuple[Path, Path]:
    workflow_root = workflow_folder or governance_root / "workflow" / "definitions" / "workflows"
    workbench_root = workbench_folder or governance_root / "workflow" / "definitions" / "workbenches"
    workbench_payload = dict(REPO_LOCAL_TRIAGE_WORKBENCH)
    workbench_payload["workbench_id"] = workbench_name
    workbench_payload["display_name"] = display_name
    workflow_payload = {
        "workflow_id": workflow_name,
        "display_name": workflow_name.replace("_", " ").title(),
        "runtime_surface_classification": "partial_governed_surface",
        "active_workbench_ids": list(workflow_ids or (workbench_name,)),
    }
    workbench_path = _write_yaml(workbench_root / f"{workbench_name}.yaml", workbench_payload)
    workflow_path = _write_yaml(workflow_root / f"{workflow_name}.yaml", workflow_payload)
    return workbench_path, workflow_path


def test_td0024_c01_built_in_catalog_loading_and_default_selection() -> None:
    layer = load_workflow_layer()

    assert layer.selected_workflow_id == DEFAULT_WORKFLOW_ID
    assert layer.runtime_surface_classification == "full_governed_surface"
    assert tuple(workbench.workbench_id for workbench in layer.workbenches) == EXPECTED_DEFAULT_WORKBENCH_IDS
    assert len(layer.catalog_workbenches) == 10
    assert len(layer.workflow_definitions) == 1
    assert all(
        workbench.source_path.startswith("lantern/workflow/definitions/workbenches/")
        for workbench in layer.catalog_workbenches
    )


def test_td0024_c01_repo_local_catalog_loading(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    governance_root = tmp_path / "governance"
    governance_root.mkdir()
    _write_repo_local_catalog(governance_root, workflow_name="repo_local_triage_flow")

    layer = _load_fixture_layer(
        fixture_root,
        governance_root=governance_root,
        workflow_id="repo_local_triage_flow",
    )

    assert len(layer.catalog_workbenches) == 11
    assert tuple(workbench.workbench_id for workbench in layer.workbenches) == ("repo_local_triage",)
    assert any(workbench.workbench_id == "repo_local_triage" for workbench in layer.catalog_workbenches)
    assert any(workflow.workflow_id == "repo_local_triage_flow" for workflow in layer.workflow_definitions)


def test_td0024_c03_workflow_selection_and_folder_overrides(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    governance_root = tmp_path / "governance"
    governance_root.mkdir()

    _write_repo_local_catalog(governance_root, workflow_name="default_repo_local_flow")
    alt_workflow_root = governance_root / "alt" / "workflows"
    alt_workbench_root = governance_root / "alt" / "workbenches"
    _write_repo_local_catalog(
        governance_root,
        workflow_name="override_repo_local_flow",
        workbench_name="override_repo_local_triage",
        display_name="Override Repo Local Triage",
        workflow_folder=alt_workflow_root,
        workbench_folder=alt_workbench_root,
    )

    default_layer = _load_fixture_layer(
        fixture_root,
        governance_root=governance_root,
        workflow_id="default_repo_local_flow",
    )
    override_layer = _load_fixture_layer(
        fixture_root,
        governance_root=governance_root,
        workflow_id="override_repo_local_flow",
        workflow_folder=alt_workflow_root,
        workbench_folder=alt_workbench_root,
    )

    assert default_layer.selected_workflow_id == "default_repo_local_flow"
    assert override_layer.selected_workflow_id == "override_repo_local_flow"
    assert tuple(workbench.workbench_id for workbench in override_layer.workbenches) == ("override_repo_local_triage",)
    assert any(workflow.workflow_id == DEFAULT_WORKFLOW_ID for workflow in override_layer.workflow_definitions)


@pytest.mark.parametrize(
    ("workbench_payload", "workflow_payload", "message_fragment"),
    [
        (
            {"workbench_id": "issue_operations", "display_name": "Repo Local Duplicate Id"},
            None,
            "collides with built-in definition",
        ),
        (
            {"workbench_id": "repo_local_duplicate_name", "display_name": "Issue Operations"},
            None,
            "collides with built-in definition",
        ),
        (
            None,
            {
                "workflow_id": DEFAULT_WORKFLOW_ID,
                "display_name": "Duplicate Workflow Id",
                "runtime_surface_classification": "partial_governed_surface",
                "active_workbench_ids": ["issue_operations"],
            },
            "collides with built-in definition",
        ),
    ],
)
def test_td0024_c04_collision_rejection(
    tmp_path: Path,
    workbench_payload: dict[str, object] | None,
    workflow_payload: dict[str, object] | None,
    message_fragment: str,
) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    governance_root = tmp_path / "governance"
    governance_root.mkdir()

    if workbench_payload is not None:
        payload = dict(REPO_LOCAL_TRIAGE_WORKBENCH)
        payload.update(workbench_payload)
        _write_yaml(
            governance_root / "workflow" / "definitions" / "workbenches" / f"{payload['workbench_id']}.yaml",
            payload,
        )
    if workflow_payload is not None:
        _write_yaml(
            governance_root / "workflow" / "definitions" / "workflows" / f"{workflow_payload['workflow_id']}.yaml",
            workflow_payload,
        )

    with pytest.raises(WorkflowLayerError, match=message_fragment):
        _load_fixture_layer(fixture_root, governance_root=governance_root)


def test_td0024_c05_missing_active_workbench_reference_is_fatal(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    governance_root = tmp_path / "governance"
    governance_root.mkdir()
    _write_yaml(
        governance_root / "workflow" / "definitions" / "workflows" / "missing_reference.yaml",
        {
            "workflow_id": "missing_reference",
            "display_name": "Missing Reference",
            "runtime_surface_classification": "partial_governed_surface",
            "active_workbench_ids": ["does_not_exist"],
        },
    )

    with pytest.raises(WorkflowLayerError, match="unknown active_workbench_id"):
        _load_fixture_layer(
            fixture_root,
            governance_root=governance_root,
            workflow_id="missing_reference",
        )


def test_td0024_c06_removed_authority_fields_are_rejected(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    workbench_path = _definitions_root(fixture_root) / "workbenches" / "issue_operations.yaml"
    payload = yaml.safe_load(workbench_path.read_text(encoding="utf-8"))
    payload["governance_mode"] = "intervention"
    _write_yaml(workbench_path, payload)

    with pytest.raises(WorkflowLayerError, match="removed authority field"):
        _load_fixture_layer(fixture_root)


def test_td0024_c09_workbench_file_presence_does_not_activate_it(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    governance_root = tmp_path / "governance"
    governance_root.mkdir()
    _write_yaml(
        governance_root / "workflow" / "definitions" / "workbenches" / "repo_local_triage.yaml",
        REPO_LOCAL_TRIAGE_WORKBENCH,
    )

    layer = _load_fixture_layer(fixture_root, governance_root=governance_root)

    assert "repo_local_triage" not in {workbench.workbench_id for workbench in layer.workbenches}
    assert "repo_local_triage" in {workbench.workbench_id for workbench in layer.catalog_workbenches}


def test_generated_projections_are_optional_by_default_and_enforceable_explicitly(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    _refresh_fixture_projections(fixture_root)
    definitions_root = _definitions_root(fixture_root)
    workflow_map_path = definitions_root / "workflow_map.md"
    workflow_map_path.write_text(workflow_map_path.read_text(encoding="utf-8") + "\nSTALE\n", encoding="utf-8")

    layer = _load_fixture_layer(fixture_root, enforce_generated_artifacts=False)
    assert layer.workbenches

    with pytest.raises(WorkflowLayerError, match="workflow_map.md"):
        _load_fixture_layer(fixture_root, enforce_generated_artifacts=True)
