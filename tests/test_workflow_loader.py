from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml
from lantern_grammar import Grammar

from lantern.artifacts.validator import validate_governance_corpus, validate_workspace_readiness
from lantern.workflow.loader import (
    DEFAULT_CONTRACT_CATALOG_PATH,
    DEFAULT_REGISTRY_PATH,
    DEFAULT_RESOURCE_MANIFEST_PATH,
    DEFAULT_WORKBENCH_BINDINGS_PATH,
    DEFAULT_WORKFLOW_MAP_PATH,
    WorkflowLayerError,
    load_workflow_layer,
    render_generated_artifacts,
)


def _load_registry_payload() -> dict:
    return copy.deepcopy(yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8")))


def _write_yaml(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _write_registry_fixture(tmp_path: Path, payload: dict) -> Path:
    fixture_root = tmp_path / "fixture_repo"
    source_lantern = Path(__file__).resolve().parents[1] / "lantern"
    fixture_lantern = fixture_root / "lantern"
    fixture_lantern.mkdir(parents=True, exist_ok=True)
    for name in ("resources", "administration_procedures", "authoring_contracts", "preservation"):
        target = fixture_lantern / name
        if not target.exists():
            target.symlink_to(source_lantern / name, target_is_directory=True)
    return _write_yaml(fixture_lantern / "workflow" / "definitions" / "workbench_registry.yaml", payload)


def test_workflow_layer_loads_typed_immutable_objects() -> None:
    layer = load_workflow_layer()

    assert layer.runtime_surface_classification == "full_governed_surface"
    assert len(layer.workbenches) == 10
    assert len(layer.contract_catalog) == 10
    assert layer.grammar_version
    assert layer.grammar_package_version

    first_workbench = layer.workbenches[0]
    first_binding = first_workbench.response_surface_bindings[0]
    first_profile = layer.transaction_profiles[0]
    first_contract = layer.contract_catalog[0]
    first_resource = layer.resource_manifest[0]

    with pytest.raises(dataclasses.FrozenInstanceError):
        first_binding.response_envelope = "mutated"
    with pytest.raises(dataclasses.FrozenInstanceError):
        first_profile.side_effect_class = "mutated"
    with pytest.raises(dataclasses.FrozenInstanceError):
        first_contract.transaction_kind = "mutated"
    with pytest.raises(dataclasses.FrozenInstanceError):
        first_resource.kind = "mutated"
    with pytest.raises(dataclasses.FrozenInstanceError):
        first_workbench.display_name = "mutated"


def test_td0002_c02_built_in_inventory_and_loader_derived_content_hashes() -> None:
    payload = _load_registry_payload()
    layer = load_workflow_layer()

    expected_ids = (
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

    assert tuple(workbench.workbench_id for workbench in layer.workbenches) == expected_ids

    for raw_entry, workbench in zip(payload["workbenches"], layer.workbenches, strict=True):
        assert "content_hash" not in raw_entry
        assert raw_entry["workflow_surface"]["response_surface_bindings"]
        normalized = json.dumps(raw_entry, sort_keys=True, separators=(",", ":"))
        assert workbench.content_hash == hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def test_generated_artifacts_are_deterministic_and_match_committed_outputs() -> None:
    layer = load_workflow_layer()
    first = render_generated_artifacts(
        runtime_surface_classification=layer.runtime_surface_classification,
        workbenches=layer.workbenches,
        transaction_profiles=layer.transaction_profiles,
        contract_catalog=layer.contract_catalog,
        resource_manifest=layer.resource_manifest,
    )
    second = render_generated_artifacts(
        runtime_surface_classification=layer.runtime_surface_classification,
        workbenches=layer.workbenches,
        transaction_profiles=layer.transaction_profiles,
        contract_catalog=layer.contract_catalog,
        resource_manifest=layer.resource_manifest,
    )

    assert first.contract_catalog_payload == second.contract_catalog_payload
    assert first.resource_manifest_payload == second.resource_manifest_payload
    assert first.workflow_map_text == second.workflow_map_text
    assert first.workbench_resource_bindings_text == second.workbench_resource_bindings_text

    assert json.loads(DEFAULT_CONTRACT_CATALOG_PATH.read_text(encoding="utf-8")) == first.contract_catalog_payload
    assert json.loads(DEFAULT_RESOURCE_MANIFEST_PATH.read_text(encoding="utf-8")) == first.resource_manifest_payload
    assert DEFAULT_WORKFLOW_MAP_PATH.read_text(encoding="utf-8") == first.workflow_map_text
    assert DEFAULT_WORKBENCH_BINDINGS_PATH.read_text(encoding="utf-8") == first.workbench_resource_bindings_text


def test_grammar_metadata_flows_into_contract_catalog_compatibility() -> None:
    layer = load_workflow_layer()
    grammar = Grammar.load()
    manifest = dict(grammar.manifest())

    expected_grammar_version = str(manifest["model_version"])
    expected_package_version = str(grammar.package_version())

    assert layer.grammar_version == expected_grammar_version
    assert layer.grammar_package_version == expected_package_version
    for entry in layer.contract_catalog:
        assert entry.compatibility["grammar_version"] == expected_grammar_version
        assert entry.compatibility["grammar_package_version"] == expected_package_version
        assert entry.compatibility["runtime_surface_classification"] == layer.runtime_surface_classification
        if entry.gate_binding:
            assert entry.compatibility["gate_dependencies"]
        else:
            assert entry.compatibility["gate_dependencies"] == {}


def test_td0002_c10_grammar_gate_incompatibility_is_descriptive(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeGrammar:
        def manifest(self) -> dict[str, str]:
            return {"model_version": "broken-grammar"}

        def package_version(self) -> str:
            return "0.test"

        def validate_integrity(self) -> dict[str, object]:
            return {"ok": True}

        def get_entity(self, entity_id: str):
            if entity_id.endswith("gt_115"):
                return None
            return object()

        def gate_dependencies(self, entity_id: str) -> dict[str, object]:
            return {"entity_id": entity_id}

    monkeypatch.setattr("lantern.workflow.loader._load_grammar", lambda: FakeGrammar())

    with pytest.raises(WorkflowLayerError) as excinfo:
        load_workflow_layer()

    message = str(excinfo.value)
    assert "design_candidate_authoring" in message
    assert "GT-115" in message
    assert "not present in lantern_grammar" in message


def test_td0002_c12_collective_artifact_family_union_covers_all_governed_families() -> None:
    layer = load_workflow_layer()
    observed = {family for workbench in layer.workbenches for family in workbench.artifacts_in_scope}

    assert observed == {"ARCH", "CH", "CI", "DB", "DC", "DEC", "DIP", "EV", "INI", "IS", "SPEC", "TD"}


def test_td0002_c13_runtime_surface_and_gate_coverage_are_enforced(tmp_path: Path) -> None:
    layer = load_workflow_layer()
    covered_gates: set[str] = set()
    for workbench in layer.workbenches:
        placement = workbench.lifecycle_placement
        if placement.kind == "covered_gates":
            covered_gates.update(placement.covered_gates)
        elif placement.kind == "lifecycle_span":
            covered_gates.update((placement.start_gate, placement.end_gate))

    assert layer.runtime_surface_classification == "full_governed_surface"
    assert {"GT-030", "GT-050", "GT-060", "GT-110", "GT-115", "GT-120", "GT-130"} <= covered_gates

    payload = _load_registry_payload()
    for workbench in payload["workbenches"]:
        if workbench["workbench_id"] == "design_selection":
            workbench["lifecycle_placement"]["covered_gates"] = ["GT-999"]
    registry_path = _write_registry_fixture(tmp_path, payload)

    with pytest.raises(ValueError) as excinfo:
        load_workflow_layer(registry_path=registry_path)

    message = str(excinfo.value)
    assert "GT-115" in message
    assert "uncovered" in message


def test_missing_response_surface_binding_is_fatal(tmp_path: Path) -> None:
    payload = _load_registry_payload()
    payload["workbenches"][0]["workflow_surface"]["response_surface_bindings"] = []
    registry_path = _write_registry_fixture(tmp_path, payload)

    with pytest.raises(WorkflowLayerError) as excinfo:
        load_workflow_layer(registry_path=registry_path)

    message = str(excinfo.value)
    assert "upstream_intake_and_baselines" in message
    assert "response_surface_bindings" in message


def test_td0002_c17_schema_invalid_workbench_reports_workbench_context(tmp_path: Path) -> None:
    payload = _load_registry_payload()
    del payload["workbenches"][0]["workflow_surface"]["response_surface_bindings"]
    registry_path = _write_registry_fixture(tmp_path, payload)

    with pytest.raises(WorkflowLayerError) as excinfo:
        load_workflow_layer(registry_path=registry_path)

    message = str(excinfo.value)
    assert "upstream_intake_and_baselines" in message
    assert "response_surface_bindings" in message


def test_unresolved_authoritative_guide_path_is_fatal(tmp_path: Path) -> None:
    payload = _load_registry_payload()
    payload["workbenches"][0]["authoritative_guides"] = [
        "lantern/resources/guides/does_not_exist.md"
    ]
    registry_path = _write_registry_fixture(tmp_path, payload)

    with pytest.raises(WorkflowLayerError) as excinfo:
        load_workflow_layer(registry_path=registry_path)

    message = str(excinfo.value)
    assert "upstream_intake_and_baselines" in message
    assert "authoritative_guides" in message
    assert "does_not_exist.md" in message
    assert "resource.authoritative_guide.upstream_intake_and_baselines_authoritative_guides_does_not_exist" in message
    assert "affected_response_surface_bindings" in message
    assert "inspect:catalog" in message


GOVERNANCE_ROOT = Path(__file__).resolve().parents[2] / "lantern-governance"


def _copy_product_fixture(tmp_path: Path) -> Path:
    fixture_root = tmp_path / "product_fixture"
    shutil.copytree(Path(__file__).resolve().parents[1] / "lantern", fixture_root / "lantern", dirs_exist_ok=True)
    return fixture_root


def test_td0009_c01_missing_lantern_grammar_failure_names_manual_install_step(monkeypatch: pytest.MonkeyPatch) -> None:
    from lantern.workflow.loader import WorkflowLayerError

    def _raise_missing_grammar():
        raise WorkflowLayerError(
            "lantern_grammar public API import failed; install lantern_grammar before loading the workflow layer (for example from a sibling checkout: pip install -e ../lantern-grammar)"
        )

    monkeypatch.setattr("lantern.workflow.loader._load_grammar", _raise_missing_grammar)
    findings = validate_workspace_readiness(product_root=Path(__file__).resolve().parents[1])
    assert findings
    assert findings[0]["path"] == "workspace.grammar"
    assert "pip install -e ../lantern-grammar" in findings[0]["message"]


def test_td0009_c02_stale_generated_artifact_is_reported_with_path(tmp_path: Path) -> None:
    fixture_root = _copy_product_fixture(tmp_path)
    definitions_root = fixture_root / "lantern" / "workflow" / "definitions"
    workflow_map = definitions_root / "workflow_map.md"
    workflow_map.write_text(workflow_map.read_text(encoding="utf-8") + "\nSTALE\n", encoding="utf-8")

    with pytest.raises(WorkflowLayerError) as excinfo:
        load_workflow_layer(
            registry_path=definitions_root / "workbench_registry.yaml",
            schema_path=definitions_root / "workbench_schema.yaml",
            transaction_profiles_path=definitions_root / "transaction_profiles.yaml",
            contract_catalog_path=definitions_root / "contract_catalog.json",
            resource_manifest_path=definitions_root / "resource_manifest.json",
            workflow_map_path=workflow_map,
            workbench_resource_bindings_path=definitions_root / "workbench_resource_bindings.md",
            relocation_manifest_path=fixture_root / "lantern" / "preservation" / "relocation_manifest.yaml",
        )

    message = str(excinfo.value)
    assert "stale" in message
    assert str(workflow_map) in message


def test_td0009_c03_governance_conformance_reports_artifact_id_and_path(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    artifact_path = governance_root / "ch" / "CH-9999.md"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        "```yaml\nch_id: CH-9999\n```\n\n## Missing title\n",
        encoding="utf-8",
    )

    findings = validate_governance_corpus(governance_root)
    assert findings
    assert findings[0]["artifact_id"] == "CH-9999"
    assert findings[0]["path"].startswith("CH-9999.")


def test_td0009_c04_active_governance_corpus_passes_conformance() -> None:
    assert validate_governance_corpus(GOVERNANCE_ROOT) == []


def test_td0011_c02_external_workspace_readiness_uses_runtime_release_surface(tmp_path: Path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    findings = validate_workspace_readiness(product_root=product_root, governance_root=governance_root)

    assert findings == []
    assert not (product_root / "lantern").exists()


def test_td0011_c04_runtime_install_failures_do_not_point_at_product_local_lantern_tree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from lantern.workflow.loader import WorkflowLayerError

    def _raise_missing_grammar():
        raise WorkflowLayerError(
            "lantern_grammar public API import failed; install lantern_grammar before loading the workflow layer (for example from a sibling checkout: pip install -e ../lantern-grammar)"
        )

    monkeypatch.setattr("lantern.workflow.loader._load_grammar", _raise_missing_grammar)
    product_root = tmp_path / "product"
    product_root.mkdir()

    findings = validate_workspace_readiness(product_root=product_root)

    assert findings
    assert findings[0]["path"] == "workspace.grammar"
    assert "product_root/lantern" not in findings[0]["message"]
    assert "pip install -e ../lantern-grammar" in findings[0]["message"]
