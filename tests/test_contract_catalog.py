from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
import yaml

from lantern.workflow.loader import (
    DEFAULT_REGISTRY_PATH,
    DEFAULT_RELOCATION_MANIFEST_PATH,
    DEFAULT_RESOURCE_MANIFEST_PATH,
    WorkflowLayerError,
    _derive_resource_manifest,
    _load_yaml,
    _resource_entry_to_dict,
    load_workflow_layer,
)

_CONTRACT_RE = re.compile(r"^contract\.[a-z0-9_]+\.v1$")
_RESOURCE_RE = re.compile(r"^resource\.[a-z_]+\.[a-z0-9_]+$")


def _load_registry_payload() -> dict:
    return copy.deepcopy(yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8")))


def _load_relocation_manifest_payload() -> dict:
    return copy.deepcopy(yaml.safe_load(DEFAULT_RELOCATION_MANIFEST_PATH.read_text(encoding="utf-8")))


def _write_yaml(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _write_fixture_repo(
    tmp_path: Path,
    *,
    registry_payload: dict | None = None,
    relocation_manifest_payload: dict | None = None,
) -> tuple[Path, Path | None]:
    fixture_root = tmp_path / "fixture_repo"
    source_lantern = Path(__file__).resolve().parents[1] / "lantern"
    fixture_lantern = fixture_root / "lantern"
    fixture_lantern.mkdir(parents=True, exist_ok=True)

    for name in ("resources", "administration_procedures", "authoring_contracts"):
        target = fixture_lantern / name
        if not target.exists():
            target.symlink_to(source_lantern / name, target_is_directory=True)

    if relocation_manifest_payload is None:
        preservation_target = fixture_lantern / "preservation"
        if not preservation_target.exists():
            preservation_target.symlink_to(source_lantern / "preservation", target_is_directory=True)
        relocation_manifest_path = None
    else:
        relocation_manifest_path = _write_yaml(
            fixture_lantern / "preservation" / "relocation_manifest.yaml",
            relocation_manifest_payload,
        )

    registry_path = _write_yaml(
        fixture_lantern / "workflow" / "definitions" / "workbench_registry.yaml",
        registry_payload or _load_registry_payload(),
    )
    return registry_path, relocation_manifest_path


def test_contract_catalog_and_resource_manifest_naming_and_completeness() -> None:
    layer = load_workflow_layer()

    workbench_ids = {workbench.workbench_id for workbench in layer.workbenches}
    contract_refs = {workbench.contract_refs[0] for workbench in layer.workbenches}

    assert {entry.contract_ref for entry in layer.contract_catalog} == contract_refs
    for entry in layer.contract_catalog:
        assert _CONTRACT_RE.fullmatch(entry.contract_ref)
        assert entry.workbench_refs[0] in workbench_ids
        assert entry.request_schema_ref == f"schema.request.{entry.workbench_refs[0]}.v1"
        assert entry.guide_refs
        assert entry.response_surface_bindings
        assert entry.family_binding
        if entry.gate_binding:
            assert entry.compatibility["gate_dependencies"]
        else:
            assert entry.compatibility["gate_dependencies"] == {}


def test_resource_manifest_entries_are_reviewed_and_cover_all_workflow_resources() -> None:
    layer = load_workflow_layer()

    expected_pairs: set[tuple[str, str]] = set()
    for workbench in layer.workbenches:
        expected_pairs.add((workbench.workbench_id, workbench.instruction_resource))
        expected_pairs.update((workbench.workbench_id, path) for path in workbench.authoritative_guides)
        expected_pairs.update((workbench.workbench_id, path) for path in workbench.administration_guides)

    actual_pairs = {(entry.workbench_id, entry.path) for entry in layer.resource_manifest}
    assert actual_pairs == expected_pairs

    for entry in layer.resource_manifest:
        assert _RESOURCE_RE.fullmatch(entry.resource_id)
        assert entry.review_status in {"reviewed", "lantern_authored"}
        assert entry.provenance_type
        assert entry.provenance_refs
        assert entry.roles
        assert entry.path.startswith("lantern/")


def test_td0002_c07_workflow_resources_are_manifested_and_traceable() -> None:
    layer = load_workflow_layer()
    manifest_by_key = {(entry.workbench_id, entry.path): entry for entry in layer.resource_manifest}

    for workbench in layer.workbenches:
        referenced_paths = (
            [workbench.instruction_resource]
            + list(workbench.authoritative_guides)
            + list(workbench.administration_guides)
        )
        for path in referenced_paths:
            entry = manifest_by_key[(workbench.workbench_id, path)]
            assert path.startswith("lantern/")
            if path.startswith("lantern/resources/guides/"):
                assert entry.review_status == "lantern_authored"
                assert entry.projection_trace == {
                    "derivation": "lantern_authored_guide_surface",
                    "source": "guide_header",
                }
            else:
                assert entry.review_status == "reviewed"
                assert entry.projection_trace["derivation"] == "relocation_manifest_projection"
                assert entry.projection_trace["relocation_entry_id"]


def test_td0002_c18_recomputed_resource_projection_matches_committed_manifest() -> None:
    layer = load_workflow_layer()
    relocation_manifest = _load_yaml(DEFAULT_RELOCATION_MANIFEST_PATH, "relocation manifest")
    product_root = Path(__file__).resolve().parents[1]

    recomputed = _derive_resource_manifest(
        relocation_manifest=relocation_manifest,
        workbenches=layer.workbenches,
        product_root=product_root,
    )

    assert [_resource_entry_to_dict(entry) for entry in recomputed] == json.loads(
        DEFAULT_RESOURCE_MANIFEST_PATH.read_text(encoding="utf-8")
    )


def test_generated_markdown_aids_reference_every_workbench() -> None:
    layer = load_workflow_layer()
    workflow_map_path = layer.workbenches[0].__class__.__module__.rsplit(".", 1)[0]
    # The loader already validates committed generated files for exact concordance.
    # This test asserts the maintainer-facing markdown artifacts enumerate the full workbench set.
    from lantern.workflow.loader import DEFAULT_WORKBENCH_BINDINGS_PATH, DEFAULT_WORKFLOW_MAP_PATH

    workflow_map = DEFAULT_WORKFLOW_MAP_PATH.read_text(encoding="utf-8")
    bindings = DEFAULT_WORKBENCH_BINDINGS_PATH.read_text(encoding="utf-8")

    for workbench in layer.workbenches:
        assert workbench.workbench_id in workflow_map
        assert workbench.workbench_id in bindings
        assert workbench.instruction_resource in bindings


def test_td0002_c23_legacy_copy_without_review_is_rejected(tmp_path: Path) -> None:
    registry_payload = _load_registry_payload()
    relocation_manifest_payload = _load_relocation_manifest_payload()
    target_path = registry_payload["workbenches"][1]["administration_guides"][0]

    for entry in relocation_manifest_payload["entries"]:
        if entry["target"] == target_path:
            entry["entry_class"] = "legacy_copy"
            break
    else:  # pragma: no cover - defensive fixture guard
        raise AssertionError(f"Expected relocation manifest entry for {target_path}")

    registry_path, relocation_manifest_path = _write_fixture_repo(
        tmp_path,
        registry_payload=registry_payload,
        relocation_manifest_payload=relocation_manifest_payload,
    )

    with pytest.raises(WorkflowLayerError) as excinfo:
        load_workflow_layer(
            registry_path=registry_path,
            relocation_manifest_path=relocation_manifest_path,
        )

    message = str(excinfo.value)
    assert target_path in message
    assert "legacy_copy" in message
    assert "reviewed" in message
