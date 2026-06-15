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

"""TD-0031: governed regeneration entrypoint for committed projections (CH-0031)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from lantern.workflow.loader import (
    WorkflowLayerError,
    load_workflow_layer,
    render_generated_artifacts,
)
from lantern.workflow.regenerate import write_committed_projections


PRODUCT_ROOT = Path(__file__).resolve().parents[1]


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _copy_product_fixture(tmp_path: Path) -> Path:
    fixture_root = tmp_path / "product_fixture"
    shutil.copytree(PRODUCT_ROOT / "lantern", fixture_root / "lantern", dirs_exist_ok=True)
    return fixture_root


def _definitions_root(fixture_root: Path) -> Path:
    return fixture_root / "lantern" / "workflow" / "definitions"


def _generated_workflow_map_root(fixture_root: Path) -> Path:
    return fixture_root / "lantern" / "workflow" / "generated" / "workflow_maps"


def _load_fixture_layer(fixture_root: Path, *, enforce_generated_artifacts: bool = False):
    defs = _definitions_root(fixture_root)
    return load_workflow_layer(
        workbench_catalog_root=defs / "workbenches",
        workflow_catalog_root=defs / "workflows",
        schema_path=defs / "workbench_schema.yaml",
        workflow_schema_path=defs / "workflow_schema.yaml",
        transaction_profiles_path=defs / "transaction_profiles.yaml",
        registry_path=defs / "workbench_registry.yaml",
        contract_catalog_path=defs / "contract_catalog.json",
        resource_manifest_path=defs / "resource_manifest.json",
        workflow_map_path=defs / "workflow_map.md",
        workbench_resource_bindings_path=defs / "workbench_resource_bindings.md",
        builtin_workflow_map_root=_generated_workflow_map_root(fixture_root),
        enforce_generated_artifacts=enforce_generated_artifacts,
    )


def _regenerate_in_fixture(fixture_root: Path) -> None:
    defs = _definitions_root(fixture_root)
    wm_root = _generated_workflow_map_root(fixture_root)
    layer = _load_fixture_layer(fixture_root)
    write_committed_projections(
        workflow_layer=layer,
        registry_path=defs / "workbench_registry.yaml",
        contract_catalog_path=defs / "contract_catalog.json",
        resource_manifest_path=defs / "resource_manifest.json",
        workflow_map_path=defs / "workflow_map.md",
        workbench_resource_bindings_path=defs / "workbench_resource_bindings.md",
        builtin_workflow_map_root=wm_root,
    )


def test_documented_command_runs_successfully() -> None:
    """The documented developer command (python -m scripts.regenerate_committed_projections)
    exits 0 and makes no changes on an already-in-sync product tree.

    Snapshotting before/after catches two failure modes: command errors (non-zero exit)
    and silent staleness (command runs but rewrites committed files that should already match).
    """
    layer = load_workflow_layer()
    defs = PRODUCT_ROOT / "lantern" / "workflow" / "definitions"
    wm_root = PRODUCT_ROOT / "lantern" / "workflow" / "generated" / "workflow_maps"
    snapshot_paths = [
        defs / "workbench_registry.yaml",
        defs / "contract_catalog.json",
        defs / "resource_manifest.json",
        defs / "workflow_map.md",
        defs / "workbench_resource_bindings.md",
        wm_root / f"{layer.selected_workflow_id}.md",
    ]
    before = {p: p.read_bytes() for p in snapshot_paths}

    result = subprocess.run(
        [sys.executable, "-m", "scripts.regenerate_committed_projections"],
        cwd=PRODUCT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Documented command failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    after = {p: p.read_bytes() for p in snapshot_paths}
    for path in snapshot_paths:
        assert (
            before[path] == after[path]
        ), f"Documented command changed a committed projection on an already-in-sync tree: {path.name}"


def test_td0031_c01_regeneration_satisfies_committed_equals_derived(tmp_path: Path) -> None:
    """Regeneration target set is complete; each output satisfies the loader's
    committed-equals-derived assertions after the command runs."""
    fixture_root = _copy_product_fixture(tmp_path)
    _regenerate_in_fixture(fixture_root)
    _load_fixture_layer(fixture_root, enforce_generated_artifacts=True)


def test_td0031_c02_regeneration_is_idempotent_on_unchanged_tree(tmp_path: Path) -> None:
    """Running the command on a tree already in committed-equals-derived agreement
    produces an empty diff across all projection targets including the skill surface."""
    fixture_root = _copy_product_fixture(tmp_path)
    defs = _definitions_root(fixture_root)
    wm_root = _generated_workflow_map_root(fixture_root)

    target_paths = [
        defs / "workbench_registry.yaml",
        defs / "contract_catalog.json",
        defs / "resource_manifest.json",
        defs / "workflow_map.md",
        defs / "workbench_resource_bindings.md",
        wm_root / "default_full_governed_surface.md",
    ]
    before = {p: p.read_bytes() for p in target_paths}
    _regenerate_in_fixture(fixture_root)
    after = {p: p.read_bytes() for p in target_paths}

    for path in target_paths:
        assert before[path] == after[path], f"unexpected diff after idempotent regeneration: {path.name}"


def test_td0031_c03_stale_projections_are_recovered(tmp_path: Path) -> None:
    """After a workflow input renders committed projections stale, the command
    brings them back into committed-equals-derived agreement."""
    fixture_root = _copy_product_fixture(tmp_path)
    defs = _definitions_root(fixture_root)

    wm_path = defs / "workflow_map.md"
    wm_path.write_text(wm_path.read_text(encoding="utf-8") + "\nSTALE\n", encoding="utf-8")

    with pytest.raises(WorkflowLayerError, match="stale"):
        _load_fixture_layer(fixture_root, enforce_generated_artifacts=True)

    _regenerate_in_fixture(fixture_root)

    _load_fixture_layer(fixture_root, enforce_generated_artifacts=True)


def test_td0031_c04_regeneration_output_equals_loader_derivation(tmp_path: Path) -> None:
    """The command only writes; its output is byte-identical to the loader's
    in-memory derivation for the same inputs."""
    fixture_root = _copy_product_fixture(tmp_path)
    defs = _definitions_root(fixture_root)
    wm_root = _generated_workflow_map_root(fixture_root)

    layer = _load_fixture_layer(fixture_root)
    generated = render_generated_artifacts(
        workflow_id=layer.selected_workflow_id,
        workflow_display_name=layer.selected_workflow_display_name,
        runtime_surface_classification=layer.runtime_surface_classification,
        workbenches=layer.workbenches,
        transaction_profiles=layer.transaction_profiles,
        contract_catalog=layer.contract_catalog,
        resource_manifest=layer.resource_manifest,
    )

    write_committed_projections(
        workflow_layer=layer,
        registry_path=defs / "workbench_registry.yaml",
        contract_catalog_path=defs / "contract_catalog.json",
        resource_manifest_path=defs / "resource_manifest.json",
        workflow_map_path=defs / "workflow_map.md",
        workbench_resource_bindings_path=defs / "workbench_resource_bindings.md",
        builtin_workflow_map_root=wm_root,
    )

    assert (defs / "workbench_registry.yaml").read_text(encoding="utf-8") == generated.compatibility_registry_text
    assert (defs / "contract_catalog.json").read_text(encoding="utf-8") == _canonical_json(
        generated.contract_catalog_payload
    )
    assert (defs / "resource_manifest.json").read_text(encoding="utf-8") == _canonical_json(
        generated.resource_manifest_payload
    )
    assert (defs / "workflow_map.md").read_text(encoding="utf-8") == generated.workflow_map_text
    assert (defs / "workbench_resource_bindings.md").read_text(
        encoding="utf-8"
    ) == generated.workbench_resource_bindings_text
    assert (wm_root / f"{layer.selected_workflow_id}.md").read_text(
        encoding="utf-8"
    ) == generated.built_in_workflow_map_text
