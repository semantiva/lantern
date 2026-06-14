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

from lantern.workflow.loader import (
    DEFAULT_RESOURCE_MANIFEST_PATH,
    WorkflowLayerError,
    _derive_resource_manifest,
    _load_yaml,
    _resource_entry_to_dict,
    load_workflow_layer,
    render_generated_artifacts,
)


PRODUCT_ROOT = Path(__file__).resolve().parents[1]


def _copy_product_fixture(tmp_path: Path) -> Path:
    fixture_root = tmp_path / "product_fixture"
    shutil.copytree(PRODUCT_ROOT / "lantern", fixture_root / "lantern", dirs_exist_ok=True)
    return fixture_root


def _definitions_root(fixture_root: Path) -> Path:
    return fixture_root / "lantern" / "workflow" / "definitions"


def _generated_workflow_map_root(fixture_root: Path) -> Path:
    return fixture_root / "lantern" / "workflow" / "generated" / "workflow_maps"


def _load_fixture_layer(fixture_root: Path, *, enforce_generated_artifacts: bool = False):
    definitions_root = _definitions_root(fixture_root)
    return load_workflow_layer(
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


def _refresh_fixture_projections(fixture_root: Path) -> None:
    definitions_root = _definitions_root(fixture_root)
    workflow_map_root = _generated_workflow_map_root(fixture_root)
    workflow_map_root.mkdir(parents=True, exist_ok=True)
    layer = _load_fixture_layer(fixture_root, enforce_generated_artifacts=False)
    generated = render_generated_artifacts(
        workflow_id=layer.selected_workflow_id,
        workflow_display_name=layer.selected_workflow_display_name,
        runtime_surface_classification=layer.runtime_surface_classification,
        workbenches=layer.workbenches,
        transaction_profiles=layer.transaction_profiles,
        contract_catalog=layer.contract_catalog,
        resource_manifest=layer.resource_manifest,
    )
    (definitions_root / "workbench_registry.yaml").write_text(generated.compatibility_registry_text, encoding="utf-8")
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


def test_contract_catalog_and_resource_manifest_cover_selected_workflow() -> None:
    layer = load_workflow_layer()

    workbench_ids = {workbench.workbench_id for workbench in layer.workbenches}
    contract_refs = {workbench.contract_refs[0] for workbench in layer.workbenches}

    assert {entry.contract_ref for entry in layer.contract_catalog} == contract_refs
    assert {entry.workbench_refs[0] for entry in layer.contract_catalog} == workbench_ids
    for entry in layer.contract_catalog:
        assert entry.request_schema_ref == f"schema.request.{entry.workbench_refs[0]}.v1"
        assert entry.response_surface_bindings
        assert entry.compatibility["runtime_surface_classification"] == layer.runtime_surface_classification
        assert entry.compatibility["selected_workflow_id"] == layer.selected_workflow_id


def test_resource_manifest_is_empty_after_authority_field_retirement() -> None:
    layer = load_workflow_layer()
    assert layer.resource_manifest == (), (
        "resource_manifest must be empty: all legacy authority role fields retired in CH-0034"
    )


def test_recomputed_resource_manifest_matches_committed_projection() -> None:
    layer = load_workflow_layer()
    relocation_manifest = _load_yaml(
        PRODUCT_ROOT / "lantern" / "preservation" / "relocation_manifest.yaml", "relocation manifest"
    )
    recomputed = _derive_resource_manifest(
        relocation_manifest=relocation_manifest,
        workbenches=layer.workbenches,
        product_root=PRODUCT_ROOT,
    )

    assert [_resource_entry_to_dict(entry) for entry in recomputed] == json.loads(
        DEFAULT_RESOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )


def test_projection_files_include_default_workflow_map_named_by_workflow_id() -> None:
    workflow_map_path = (
        PRODUCT_ROOT / "lantern" / "workflow" / "generated" / "workflow_maps" / "default_full_governed_surface.md"
    )
    legacy_registry_path = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "workbench_registry.yaml"

    assert workflow_map_path.exists()
    assert "default_full_governed_surface" in workflow_map_path.read_text(encoding="utf-8")
    assert legacy_registry_path.exists()
    assert "Generated compatibility projection" in legacy_registry_path.read_text(encoding="utf-8")


def test_projection_enforcement_is_explicit_for_fixture_copies(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    _refresh_fixture_projections(fixture_root)
    definitions_root = _definitions_root(fixture_root)
    registry_path = definitions_root / "workbench_registry.yaml"
    registry_path.write_text(registry_path.read_text(encoding="utf-8") + "\n# stale\n", encoding="utf-8")

    assert _load_fixture_layer(fixture_root, enforce_generated_artifacts=False).workbenches

    with pytest.raises(WorkflowLayerError, match="workbench_registry.yaml"):
        _load_fixture_layer(fixture_root, enforce_generated_artifacts=True)


def test_relocation_manifest_no_longer_consulted_by_derive_resource_manifest() -> None:
    layer = load_workflow_layer()
    relocation_manifest = _load_yaml(
        PRODUCT_ROOT / "lantern" / "preservation" / "relocation_manifest.yaml", "relocation manifest"
    )
    recomputed = _derive_resource_manifest(
        relocation_manifest=relocation_manifest,
        workbenches=layer.workbenches,
        product_root=PRODUCT_ROOT,
    )
    assert recomputed == (), "resource manifest must be empty: legacy role entries retired in CH-0034"
