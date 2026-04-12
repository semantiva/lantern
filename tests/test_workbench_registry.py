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


def _load_registry_payload() -> dict:
    return copy.deepcopy(yaml.safe_load(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8")))


def _write_registry(tmp_dir: Path, payload: dict) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / "workbench_registry.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _load_registry_from_payload(tmp_name: str, payload: dict):
    registry_path = _write_registry(Path.cwd() / ".pytest_cache" / tmp_name, payload)
    return load_workbench_registry(
        registry_path=registry_path,
        schema_yaml_path=DEFAULT_SCHEMA_YAML_PATH,
        schema_json_path=DEFAULT_SCHEMA_JSON_PATH,
    )


def _assert_payload_fails(payload: dict, tmp_name: str, *fragments: str) -> None:
    try:
        _load_registry_from_payload(tmp_name, payload)
    except ValueError as exc:
        message = str(exc)
        for fragment in fragments:
            assert fragment in message
    else:
        raise AssertionError("Expected validation failure")


def test_registry_loads_and_contains_all_built_in_workbenches() -> None:
    registry = load_workbench_registry()
    assert registry.runtime_surface_classification == "full_governed_surface"
    assert registry.ids() == EXPECTED_WORKBENCH_IDS
    assert len(registry.workbenches) == 10


def test_missing_required_gate_is_fatal() -> None:
    payload = _load_registry_payload()
    for workbench in payload["workbenches"]:
        if workbench["workbench_id"] == "design_selection":
            workbench["lifecycle_placement"]["covered_gates"] = ["GT-999"]
    _assert_payload_fails(payload, "ch0001_gt115_missing", "GT-115", "uncovered")


def test_content_hashes_are_sha256_hex_strings() -> None:
    registry = load_workbench_registry()
    for workbench in registry.workbenches:
        assert re.fullmatch(r"[0-9a-f]{64}", workbench.content_hash)


def test_content_hashes_are_deterministic_across_loads() -> None:
    first = load_workbench_registry()
    second = load_workbench_registry()
    assert [item.content_hash for item in first.workbenches] == [item.content_hash for item in second.workbenches]


def test_foundation_loader_projects_additive_workflow_surface_fields() -> None:
    payload = _load_registry_payload()
    payload["workbenches"][0]["workflow_surface"]["future_additive_projection_only"] = ["preview"]

    registry = _load_registry_from_payload("ch0002_projection_regression", payload)
    workbench = registry.get("upstream_intake_and_baselines")

    assert workbench.workflow_surface.allowed_transaction_kinds == ("inspect", "draft", "commit", "validate")
    assert not hasattr(workbench.workflow_surface, "response_surface_bindings")
    assert not hasattr(workbench.workflow_surface, "future_additive_projection_only")


def test_missing_required_field_is_fatal() -> None:
    payload = _load_registry_payload()
    del payload["workbenches"][0]["workbench_id"]
    _assert_payload_fails(payload, "ch0001_missing_field", "workbench_id", "required")


def test_invalid_instruction_resource_path_is_fatal() -> None:
    payload = _load_registry_payload()
    payload["workbenches"][0]["instruction_resource"] = "../outside.md"
    _assert_payload_fails(
        payload,
        "ch0008_invalid_instruction_resource",
        "instruction_resource",
        "upstream_intake_and_baselines",
    )


def test_invalid_authoritative_guide_path_is_fatal() -> None:
    payload = _load_registry_payload()
    payload["workbenches"][0]["authoritative_guides"] = ["guides/outside.md"]
    _assert_payload_fails(
        payload,
        "ch0008_invalid_authoritative_guide",
        "authoritative_guides[0]",
        "upstream_intake_and_baselines",
    )


def test_invalid_contract_ref_is_fatal() -> None:
    payload = _load_registry_payload()
    payload["workbenches"][0]["workflow_surface"]["contract_refs"] = ["bad-ref"]
    _assert_payload_fails(
        payload,
        "ch0008_invalid_contract_ref",
        "contract_refs[0]",
        "upstream_intake_and_baselines",
    )


def test_structurally_valid_nonexistent_guide_path_is_allowed() -> None:
    payload = _load_registry_payload()
    payload["workbenches"][0]["authoritative_guides"] = ["lantern/resources/guides/not-yet-delivered.md"]
    registry = _load_registry_from_payload("ch0008_valid_nonexistent_guide", payload)
    assert registry.ids() == EXPECTED_WORKBENCH_IDS


def test_lifecycle_placement_variants_parse_correctly() -> None:
    registry = load_workbench_registry()
    assert registry.get("upstream_intake_and_baselines").lifecycle_placement.kind == "covered_gates"
    assert registry.get("design_candidate_authoring").lifecycle_placement.kind == "lifecycle_span"
