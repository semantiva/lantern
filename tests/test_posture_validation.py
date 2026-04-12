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

"""Tests for TD-0005-C03 (full_governed fail-closed) and TD-0005-C04 (partial_governed acceptance).

C03: PostureValidator raises PostureValidationError when full_governed_surface claim is invalid.
C04: PostureValidator returns PostureResult with bounded_scope_markers for partial_governed_surface.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from lantern.workflow.merger import (
    ConfigurationLoader,
    ConfigurationMerger,
    MergeProvenance,
    PostureResult,
    PostureValidationError,
    PostureValidator,
)


# ---------------------------------------------------------------------------
# Helpers: minimal workflow_layer mock and status_contract fixture
# ---------------------------------------------------------------------------


def _make_workflow_layer(
    *,
    governance_modes: dict[str, str] | None = None,
    covered_gates: dict[str, list[str]] | None = None,
    artifact_families: dict[str, list[str]] | None = None,
) -> MagicMock:
    """Build a minimal mock WorkflowLayer suitable for PostureValidator calls."""
    governance_modes = governance_modes or {}
    covered_gates = covered_gates or {}
    artifact_families = artifact_families or {}

    workbenches = []
    for wb_id, gmode in governance_modes.items():
        wb = MagicMock()
        wb.workbench_id = wb_id
        wb.enabled = True
        wb.governance_mode = gmode
        placement = MagicMock()
        gates = covered_gates.get(wb_id, [])
        if gates:
            placement.kind = "covered_gates"
            placement.covered_gates = gates
        else:
            placement.kind = "lifecycle-independent"
        wb.lifecycle_placement = placement
        wb.artifacts_in_scope = artifact_families.get(wb_id, [])
        workbenches.append(wb)

    layer = MagicMock()
    layer.workbenches = workbenches
    layer.runtime_surface_classification = "full_governed_surface"
    layer.grammar_version = "1.0"
    layer.grammar_package_version = "0.1"

    def _get_workbench(wid: str) -> MagicMock:
        for wb in workbenches:
            if wb.workbench_id == wid:
                return wb
        raise KeyError(wid)

    layer.get_workbench.side_effect = _get_workbench
    return layer


def _full_status_contract() -> dict:
    """Minimal status contract with all families present (so family check passes)."""
    families = {f: {} for f in ["CH", "CI", "DC", "DB", "DEC", "DIP", "EV", "INI", "IS", "SPEC", "ARCH", "TD"]}
    return {"families": families}


def _make_provenance() -> MergeProvenance:
    return MergeProvenance(
        baseline_version="0.5.0",
        configuration_folder=None,
        main_yaml_hash=None,
        launcher_overlay_folder=None,
        launcher_overlay_hash=None,
    )


def _make_effective_layer_from_merger(
    tmp_path: Path,
    declared_posture: str,
    governance_modes: dict[str, str] | None = None,
    covered_gates: dict[str, list[str]] | None = None,
) -> object:
    import textwrap
    import yaml as _yaml
    from lantern.workflow.merger import ConfigurationLoader, ConfigurationMerger

    cfg = tmp_path / "workflow" / "configuration"
    for sub in ("instructions", "workbenches", "guides"):
        (cfg / sub).mkdir(parents=True, exist_ok=True)
    (cfg / "instructions" / "onboarding.md").write_text("# onboarding", encoding="utf-8")
    main_yaml = {"configuration_version": "1", "declared_posture": declared_posture}
    (cfg / "main.yaml").write_text(_yaml.safe_dump(main_yaml), encoding="utf-8")
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    merger = ConfigurationMerger()
    return merger.merge(
        baseline_surface_classification="full_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=surface,
    )


# ---------------------------------------------------------------------------
# C03 — fail-closed full_governed_surface
# ---------------------------------------------------------------------------


def test_c03_full_governed_passes_when_gates_covered(tmp_path: Path) -> None:
    from lantern.workflow.merger import _REQUIRED_FULL_GOVERNED_GATES

    all_gates = list(_REQUIRED_FULL_GOVERNED_GATES)
    layer = _make_workflow_layer(
        governance_modes={"wb_all": "full"},
        covered_gates={"wb_all": all_gates},
        artifact_families={"wb_all": []},
    )
    effective = _make_effective_layer_from_merger(tmp_path, "full_governed_surface")
    validator = PostureValidator()
    result = validator.validate(
        effective_layer=effective,
        workflow_layer=layer,
        status_contract=_full_status_contract(),
    )
    assert result.classification == "full_governed_surface"
    assert result.bounded_scope_markers == ()
    assert result.restricted_capabilities == ()


def test_c03_missing_required_gate_raises_fatal_error(tmp_path: Path) -> None:
    # Only covers a subset of required gates
    layer = _make_workflow_layer(
        governance_modes={"wb_partial": "full"},
        covered_gates={"wb_partial": ["GT-110", "GT-115"]},
        artifact_families={"wb_partial": []},
    )
    effective = _make_effective_layer_from_merger(tmp_path, "full_governed_surface")
    validator = PostureValidator()
    with pytest.raises(PostureValidationError, match="full_governed_surface claim is INVALID"):
        validator.validate(
            effective_layer=effective,
            workflow_layer=layer,
            status_contract=_full_status_contract(),
        )


def test_c03_family_not_in_status_contract_raises_fatal_error(tmp_path: Path) -> None:
    from lantern.workflow.merger import _REQUIRED_FULL_GOVERNED_GATES

    all_gates = list(_REQUIRED_FULL_GOVERNED_GATES)
    layer = _make_workflow_layer(
        governance_modes={"wb_all": "full"},
        covered_gates={"wb_all": all_gates},
        artifact_families={"wb_all": ["UNKNOWN_FAMILY"]},
    )
    effective = _make_effective_layer_from_merger(tmp_path, "full_governed_surface")
    validator = PostureValidator()
    with pytest.raises(PostureValidationError, match="artifact family.*absent from the packaged status contract"):
        validator.validate(
            effective_layer=effective,
            workflow_layer=layer,
            status_contract=_full_status_contract(),
        )


def test_c03_intervention_workbench_not_counted_toward_gate_coverage(tmp_path: Path) -> None:
    from lantern.workflow.merger import _REQUIRED_FULL_GOVERNED_GATES

    all_gates = list(_REQUIRED_FULL_GOVERNED_GATES)
    # Only the intervention workbench covers gates — this must NOT satisfy full_governed
    layer = _make_workflow_layer(
        governance_modes={"intervention_wb": "intervention"},
        covered_gates={"intervention_wb": all_gates},
        artifact_families={"intervention_wb": []},
    )
    effective = _make_effective_layer_from_merger(tmp_path, "full_governed_surface")
    validator = PostureValidator()
    with pytest.raises(PostureValidationError, match="full_governed_surface claim is INVALID"):
        validator.validate(
            effective_layer=effective,
            workflow_layer=layer,
            status_contract=_full_status_contract(),
        )


# ---------------------------------------------------------------------------
# C04 — partial_governed_surface acceptance
# ---------------------------------------------------------------------------


def test_c04_partial_governed_accepted_with_bounded_scope_markers(tmp_path: Path) -> None:
    import textwrap
    import yaml as _yaml

    cfg = tmp_path / "workflow" / "configuration"
    for sub in ("instructions", "workbenches", "guides"):
        (cfg / sub).mkdir(parents=True, exist_ok=True)
    (cfg / "instructions" / "onboarding.md").write_text("# onboarding", encoding="utf-8")
    wb_yaml = {
        "workbench_id": "ci_authoring",
        "instruction_resource": "instructions/onboarding.md",
        "authoritative_guides": [],
    }
    (cfg / "workbenches" / "ci_authoring.yaml").write_text(_yaml.safe_dump(wb_yaml), encoding="utf-8")
    main_yaml = {
        "configuration_version": "1",
        "declared_posture": "partial_governed_surface",
        "workbench_overrides": [{"workbench_id": "ci_authoring", "file": "workbenches/ci_authoring.yaml"}],
    }
    (cfg / "main.yaml").write_text(_yaml.safe_dump(main_yaml), encoding="utf-8")

    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    merger = ConfigurationMerger()
    effective = merger.merge(
        baseline_surface_classification="full_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=surface,
    )

    layer = _make_workflow_layer(governance_modes={}, covered_gates={})
    validator = PostureValidator()
    result = validator.validate(
        effective_layer=effective,
        workflow_layer=layer,
        status_contract=_full_status_contract(),
    )
    assert result.classification == "partial_governed_surface"
    assert "ci_authoring" in result.bounded_scope_markers
    assert result.restricted_capabilities == ()


def test_c04_partial_governed_baseline_only_returns_correct_classification() -> None:
    merger = ConfigurationMerger()
    effective = merger.merge(
        baseline_surface_classification="partial_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=None,
    )
    layer = _make_workflow_layer(governance_modes={})
    validator = PostureValidator()
    result = validator.validate(
        effective_layer=effective,
        workflow_layer=layer,
        status_contract=_full_status_contract(),
    )
    assert result.classification == "partial_governed_surface"
    assert result.bounded_scope_markers == ()
