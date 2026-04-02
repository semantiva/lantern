from __future__ import annotations

import copy
import re
from pathlib import Path

import yaml

from lantern.registry.loader import (
    DEFAULT_REGISTRY_PATH,
    DEFAULT_SCHEMA_JSON_PATH,
    DEFAULT_SCHEMA_YAML_PATH,
    load_workbench_registry,
)

EXPECTED_WORKBENCH_IDS = (
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


def _write_registry(tmp_dir: Path, payload: dict) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / "workbench_registry.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_registry_loads_and_contains_all_built_in_workbenches() -> None:
    registry = load_workbench_registry()
    assert registry.runtime_surface_classification == "full_governed_surface"
    assert registry.ids() == EXPECTED_WORKBENCH_IDS
    assert len(registry.workbenches) == 10


def test_missing_required_gate_is_fatal() -> None:
    payload = copy.deepcopy(yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8")))
    for workbench in payload["workbenches"]:
        if workbench["workbench_id"] == "design_selection":
            workbench["lifecycle_placement"]["covered_gates"] = ["GT-999"]
    registry_path = _write_registry(Path.cwd() / ".pytest_cache" / "ch0001_gt115_missing", payload)
    try:
        load_workbench_registry(
            registry_path=registry_path,
            schema_yaml_path=DEFAULT_SCHEMA_YAML_PATH,
            schema_json_path=DEFAULT_SCHEMA_JSON_PATH,
        )
    except ValueError as exc:
        message = str(exc)
        assert "GT-115" in message
        assert "uncovered" in message
    else:
        raise AssertionError("Expected uncovered GT-115 validation failure")


def test_content_hashes_are_sha256_hex_strings() -> None:
    registry = load_workbench_registry()
    for workbench in registry.workbenches:
        assert re.fullmatch(r"[0-9a-f]{64}", workbench.content_hash)


def test_content_hashes_are_deterministic_across_loads() -> None:
    first = load_workbench_registry()
    second = load_workbench_registry()
    assert [item.content_hash for item in first.workbenches] == [item.content_hash for item in second.workbenches]


def test_missing_required_field_is_fatal() -> None:
    payload = copy.deepcopy(yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8")))
    del payload["workbenches"][0]["workbench_id"]
    registry_path = _write_registry(Path.cwd() / ".pytest_cache" / "ch0001_missing_field", payload)
    try:
        load_workbench_registry(
            registry_path=registry_path,
            schema_yaml_path=DEFAULT_SCHEMA_YAML_PATH,
            schema_json_path=DEFAULT_SCHEMA_JSON_PATH,
        )
    except ValueError as exc:
        message = str(exc)
        assert "workbench_id" in message
        assert "required" in message.lower()
    else:
        raise AssertionError("Expected required-field validation failure")


def test_lifecycle_placement_variants_parse_correctly() -> None:
    registry = load_workbench_registry()
    assert registry.get("upstream_intake_and_baselines").lifecycle_placement.kind == "covered_gates"
    assert registry.get("design_candidate_authoring").lifecycle_placement.kind == "lifecycle_span"
