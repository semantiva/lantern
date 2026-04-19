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

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from lantern.workflow.merger import (
    ConfigurationMerger,
    PostureValidationError,
    PostureValidator,
    _INTERVENTION_FORBIDDEN_TRANSACTION_KINDS,
    _REQUIRED_FULL_GOVERNED_GATES,
)


@dataclass(frozen=True)
class FakeWorkbench:
    workbench_id: str
    lifecycle_placement: object
    artifacts_in_scope: tuple[str, ...]


def _workbench(
    *, workbench_id: str, kind: str, gates: tuple[str, ...] = (), families: tuple[str, ...] = ()
) -> FakeWorkbench:
    if kind == "covered_gates":
        placement = SimpleNamespace(kind=kind, covered_gates=gates)
    elif kind == "lifecycle_span":
        placement = SimpleNamespace(kind=kind, start_gate=gates[0], end_gate=gates[1])
    else:
        placement = SimpleNamespace(kind=kind)
    return FakeWorkbench(workbench_id=workbench_id, lifecycle_placement=placement, artifacts_in_scope=families)


def _workflow_layer(*workbenches: FakeWorkbench):
    return SimpleNamespace(workbenches=tuple(workbenches), runtime_surface_classification="full_governed_surface")


def _status_contract() -> dict:
    return {
        "families": {
            family: {} for family in ["ARCH", "CH", "CI", "DB", "DC", "DEC", "DIP", "EV", "INI", "IS", "SPEC", "TD"]
        }
    }


def _effective_layer(classification: str, active_workbench_ids: tuple[str, ...]):
    merger = ConfigurationMerger()
    return merger.merge(
        baseline_surface_classification=classification,
        baseline_version="0.5.0",
        configuration_surface=None,
        selected_workflow_id=f"{classification}_workflow",
        selected_workflow_display_name=classification,
        selected_workflow_source_path=f"workflow/definitions/workflows/{classification}.yaml",
        active_workbench_ids=active_workbench_ids,
        workflow_root="workflow/definitions/workflows",
        workbench_root="workflow/definitions/workbenches",
    )


def test_full_governed_surface_passes_when_required_gates_and_families_are_covered() -> None:
    all_gates = tuple(sorted(_REQUIRED_FULL_GOVERNED_GATES))
    layer = _workflow_layer(
        _workbench(
            workbench_id="full_governed",
            kind="covered_gates",
            gates=all_gates,
            families=("ARCH", "CH", "CI", "DB", "DC", "DEC", "DIP", "EV", "INI", "IS", "SPEC", "TD"),
        )
    )

    result = PostureValidator().validate(
        effective_layer=_effective_layer("full_governed_surface", ("full_governed",)),
        workflow_layer=layer,
        status_contract=_status_contract(),
    )

    assert result.classification == "full_governed_surface"
    assert result.bounded_scope_markers == ()
    assert result.restricted_capabilities == ()


def test_full_governed_surface_fails_when_required_gates_are_missing() -> None:
    layer = _workflow_layer(
        _workbench(workbench_id="partial", kind="covered_gates", gates=("GT-110", "GT-115"), families=("CH",))
    )

    with pytest.raises(PostureValidationError, match="full_governed_surface claim is INVALID"):
        PostureValidator().validate(
            effective_layer=_effective_layer("full_governed_surface", ("partial",)),
            workflow_layer=layer,
            status_contract=_status_contract(),
        )


def test_full_governed_surface_fails_when_family_is_absent_from_status_contract() -> None:
    all_gates = tuple(sorted(_REQUIRED_FULL_GOVERNED_GATES))
    layer = _workflow_layer(
        _workbench(
            workbench_id="unknown_family",
            kind="covered_gates",
            gates=all_gates,
            families=("UNKNOWN",),
        )
    )

    with pytest.raises(PostureValidationError, match="absent from the packaged status contract"):
        PostureValidator().validate(
            effective_layer=_effective_layer("full_governed_surface", ("unknown_family",)),
            workflow_layer=layer,
            status_contract=_status_contract(),
        )


def test_partial_governed_surface_uses_active_workbench_ids_as_bounded_scope_markers() -> None:
    result = PostureValidator().validate(
        effective_layer=_effective_layer("partial_governed_surface", ("ci_authoring", "issue_operations")),
        workflow_layer=_workflow_layer(),
        status_contract=_status_contract(),
    )

    assert result.classification == "partial_governed_surface"
    assert result.bounded_scope_markers == ("ci_authoring", "issue_operations")
    assert result.restricted_capabilities == ()


def test_intervention_surface_restricts_mutation_capabilities() -> None:
    result = PostureValidator().validate(
        effective_layer=_effective_layer("intervention_surface", ("issue_operations",)),
        workflow_layer=_workflow_layer(
            _workbench(workbench_id="issue_operations", kind="lifecycle-independent", families=("IS",))
        ),
        status_contract=_status_contract(),
    )

    assert result.classification == "intervention_surface"
    assert set(result.restricted_capabilities) == _INTERVENTION_FORBIDDEN_TRANSACTION_KINDS


def test_intervention_surface_rejects_workflows_that_cover_closure_gates() -> None:
    layer = _workflow_layer(
        _workbench(
            workbench_id="verification_and_closure", kind="covered_gates", gates=("GT-130",), families=("EV", "DEC")
        )
    )

    with pytest.raises(PostureValidationError, match="covers governed-closure gates"):
        PostureValidator().validate(
            effective_layer=_effective_layer("intervention_surface", ("verification_and_closure",)),
            workflow_layer=layer,
            status_contract=_status_contract(),
        )
