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

"""Tests for the Lantern workflow resolver.

TD-0003 coverage:
  C01 - Governance-state resolution: active workbench set matches governance state
  C02 - Intent-first resolution: preferred workbench matches intent without
        contradicting governance state
  C03 - Multi-workbench resolution: all concurrent active workbench IDs appear
        exactly once
  C10 - Multi-CH ambiguity: ResolverAmbiguityError raised without ch_id; resolves
        successfully with explicit ch_id
  C12 - Determinism and no stage map: repeated resolution yields identical output;
        AST scan of resolver.py finds no authoritative stage-map dict literals
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
import yaml

import lantern.workflow.resolver as resolver_module
from lantern.workflow.loader import load_workflow_layer
from lantern.workflow.resolver import (
    ResolvedWorkbenchSet,
    ResolverAmbiguityError,
    resolve_active_workbenches,
)


@pytest.fixture(scope="module")
def workflow_layer():
    return load_workflow_layer()


_GT110_ACTIVE = {
    "ch_statuses": {"CH-0003": "Ready"},
    "active_gates": ["GT-110"],
    "passed_gates": [],
}

_GT115_SPAN = {
    "ch_statuses": {"CH-0003": "Ready"},
    "active_gates": [],
    "passed_gates": ["GT-110"],
}

_EMPTY_GATES = {
    "ch_statuses": {"CH-0003": "Ready"},
    "active_gates": [],
    "passed_gates": [],
}


def test_c01_gt110_active_includes_ch_and_td_readiness(workflow_layer) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    assert isinstance(result, ResolvedWorkbenchSet)
    assert "ch_and_td_readiness" in result.active_workbench_ids


def test_c01_lifecycle_independent_workbenches_always_active(workflow_layer) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_EMPTY_GATES,
        ch_id="CH-0003",
    )
    assert "issue_operations" in result.active_workbench_ids
    assert "governance_onboarding" in result.active_workbench_ids


def test_c01_gt110_inactive_excludes_ch_and_td_readiness(workflow_layer) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_EMPTY_GATES,
        ch_id="CH-0003",
    )
    assert "ch_and_td_readiness" not in result.active_workbench_ids


def test_c02_intent_selects_ch_and_td_readiness_when_gt110_active(
    workflow_layer,
) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        intent="change readiness review for CH-0003",
        ch_id="CH-0003",
    )
    assert result.preferred_workbench_id == "ch_and_td_readiness"
    assert result.preferred_workbench_id in result.active_workbench_ids


def test_c02_no_intent_match_returns_none_preferred(workflow_layer) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_EMPTY_GATES,
        intent="xyzzy unmatched intent string that matches nothing",
        ch_id="CH-0003",
    )
    if len(result.active_workbench_ids) > 1:
        assert result.preferred_workbench_id is None


def test_c03_all_concurrent_ids_appear_exactly_once(workflow_layer) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    assert len(result.active_workbench_ids) == len(set(result.active_workbench_ids))
    for always_active in ("issue_operations", "governance_onboarding"):
        assert always_active in result.active_workbench_ids


def test_c03_lifecycle_span_workbench_active_between_gates(workflow_layer) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT115_SPAN,
        ch_id="CH-0003",
    )
    assert "design_candidate_authoring" in result.active_workbench_ids


def test_c10_raises_without_ch_id_when_multiple_non_terminal_chs(
    workflow_layer,
) -> None:
    multi_ch_state = {
        "ch_statuses": {"CH-0003": "Ready", "CH-0004": "Ready"},
        "active_gates": ["GT-110"],
        "passed_gates": [],
    }
    with pytest.raises(ResolverAmbiguityError) as exc_info:
        resolve_active_workbenches(
            workflow_layer=workflow_layer,
            governance_state=multi_ch_state,
        )
    msg = str(exc_info.value)
    assert "CH-0003" in msg
    assert "CH-0004" in msg


def test_c10_resolves_successfully_with_explicit_ch_id(workflow_layer) -> None:
    multi_ch_state = {
        "ch_statuses": {"CH-0003": "Ready", "CH-0004": "Ready"},
        "active_gates": ["GT-110"],
        "passed_gates": [],
    }
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=multi_ch_state,
        ch_id="CH-0003",
    )
    assert isinstance(result, ResolvedWorkbenchSet)


def test_c10_single_non_terminal_ch_does_not_raise(workflow_layer) -> None:
    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
    )
    assert isinstance(result, ResolvedWorkbenchSet)


def test_c10_inprogress_alias_does_not_create_second_non_terminal_ch(workflow_layer) -> None:
    mixed_state = {
        "ch_statuses": {"CH-0003": "Ready", "CH-0004": "InProgress"},
        "active_gates": ["GT-110"],
        "passed_gates": [],
    }

    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=mixed_state,
    )

    assert isinstance(result, ResolvedWorkbenchSet)


def test_c12_repeated_resolution_produces_identical_output(workflow_layer) -> None:
    first = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    second = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )
    assert first == second


def test_c12_resolver_source_has_no_authoritative_stage_map_dict_literals() -> None:
    resolver_path = Path(resolver_module.__file__)
    source = resolver_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    gate_pattern = re.compile(r"^GT-\d{3}$")

    class StageMappingVisitor(ast.NodeVisitor):
        violations: list[str] = []

        def visit_Dict(self, node: ast.Dict) -> None:
            for key, value in zip(node.keys, node.values):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and gate_pattern.match(key.value)
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    self.violations.append(
                        f"Stage-map literal at line {key.lineno}: " f"{key.value!r} -> {value.value!r}"
                    )
            self.generic_visit(node)

    visitor = StageMappingVisitor()
    visitor.visit(tree)

    assert not visitor.violations


def test_c12_resolver_source_does_not_hardcode_legacy_ch_aliases() -> None:
    resolver_path = Path(resolver_module.__file__)
    source = resolver_path.read_text(encoding="utf-8")

    assert '{"Draft", "Ready", "InProgress", "Selected"}' not in source
    assert "InProgress" not in source
    assert "Selected" not in source


def _write_repo_local_workflow(governance_root: Path, *, workflow_id: str = "change_readiness_only") -> None:
    workflow_root = governance_root / "workflow" / "definitions" / "workflows"
    workflow_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "workflow_id": workflow_id,
        "display_name": "Change Readiness Only",
        "runtime_surface_classification": "partial_governed_surface",
        "active_workbench_ids": [
            "ch_and_td_readiness",
            "issue_operations",
            "governance_onboarding",
        ],
    }
    (workflow_root / f"{workflow_id}.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_td0024_repo_local_subset_excludes_omitted_builtins(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    _write_repo_local_workflow(governance_root)
    workflow_layer = load_workflow_layer(
        governance_root=governance_root,
        workflow_id="change_readiness_only",
        enforce_generated_artifacts=False,
    )

    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT110_ACTIVE,
        ch_id="CH-0003",
    )

    assert set(result.active_workbench_ids) == {
        "ch_and_td_readiness",
        "issue_operations",
        "governance_onboarding",
    }
    assert "design_candidate_authoring" not in result.active_workbench_ids
    assert (
        workflow_layer.get_catalog_workbench("design_candidate_authoring").display_name == "Design Candidate Authoring"
    )


def test_td0024_subset_keeps_omitted_builtins_inactive_between_gates(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance"
    _write_repo_local_workflow(governance_root)
    workflow_layer = load_workflow_layer(
        governance_root=governance_root,
        workflow_id="change_readiness_only",
        enforce_generated_artifacts=False,
    )

    result = resolve_active_workbenches(
        workflow_layer=workflow_layer,
        governance_state=_GT115_SPAN,
        ch_id="CH-0003",
    )

    assert set(result.active_workbench_ids) == {"issue_operations", "governance_onboarding"}
    assert "design_candidate_authoring" not in result.active_workbench_ids
