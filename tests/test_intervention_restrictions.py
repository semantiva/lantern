"""Tests for TD-0005-C05 (intervention activation) and TD-0005-C06 (restriction enforcement).

C05: Configuration declared intervention_surface is resolved to intervention_surface classification.
C06: InterventionRestrictionGuard raises InterventionRestrictionError for forbidden transaction kinds.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from lantern.workflow.merger import (
    ConfigurationLoader,
    ConfigurationMerger,
    InterventionRestrictionError,
    InterventionRestrictionGuard,
    PostureResult,
    PostureValidationError,
    PostureValidator,
    MergeProvenance,
    _INTERVENTION_FORBIDDEN_TRANSACTION_KINDS,
)


def _make_intervention_provenance() -> MergeProvenance:
    return MergeProvenance(
        baseline_version="0.5.0",
        configuration_folder="/some/path",
        main_yaml_hash="abc",
        launcher_overlay_folder=None,
        launcher_overlay_hash=None,
    )


def _make_intervention_posture_result() -> PostureResult:
    return PostureResult(
        classification="intervention_surface",
        bounded_scope_markers=(),
        restricted_capabilities=tuple(sorted(_INTERVENTION_FORBIDDEN_TRANSACTION_KINDS)),
        provenance=_make_intervention_provenance(),
    )


# ---------------------------------------------------------------------------
# C05 — intervention_surface activation
# ---------------------------------------------------------------------------

def test_c05_intervention_declared_posture_resolved_correctly(tmp_path: Path) -> None:
    cfg = tmp_path / "workflow" / "configuration"
    for sub in ("instructions", "workbenches", "guides"):
        (cfg / sub).mkdir(parents=True, exist_ok=True)
    (cfg / "instructions" / "onboarding.md").write_text("# onboarding", encoding="utf-8")
    main_yaml = {"configuration_version": "1", "declared_posture": "intervention_surface"}
    (cfg / "main.yaml").write_text(yaml.safe_dump(main_yaml), encoding="utf-8")

    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    assert surface.declared_posture == "intervention_surface"

    merger = ConfigurationMerger()
    layer = merger.merge(
        baseline_surface_classification="full_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=surface,
    )
    assert layer.effective_surface_classification == "intervention_surface"

    # PostureValidator must classify as intervention_surface
    wb = MagicMock()
    wb.workbench_id = "governance_onboarding"
    wb.enabled = True
    wb.governance_mode = "intervention"
    placement = MagicMock()
    placement.kind = "lifecycle-independent"
    wb.lifecycle_placement = placement
    wb.artifacts_in_scope = []
    workflow_layer = MagicMock()
    workflow_layer.workbenches = [wb]

    validator = PostureValidator()
    result = validator.validate(
        effective_layer=layer,
        workflow_layer=workflow_layer,
        status_contract={"families": {}},
    )
    assert result.classification == "intervention_surface"
    assert set(result.restricted_capabilities) == _INTERVENTION_FORBIDDEN_TRANSACTION_KINDS


def test_c05_intervention_workbench_with_closure_gate_raises(tmp_path: Path) -> None:
    cfg = tmp_path / "workflow" / "configuration"
    for sub in ("instructions", "workbenches", "guides"):
        (cfg / sub).mkdir(parents=True, exist_ok=True)
    (cfg / "instructions" / "onboarding.md").write_text("# onboarding", encoding="utf-8")
    main_yaml = {"configuration_version": "1", "declared_posture": "intervention_surface"}
    (cfg / "main.yaml").write_text(yaml.safe_dump(main_yaml), encoding="utf-8")

    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    merger = ConfigurationMerger()
    effective = merger.merge(
        baseline_surface_classification="full_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=surface,
    )

    # Intervention workbench claims GT-130 (governed closure) — this must fail
    wb = MagicMock()
    wb.workbench_id = "bad_intervention"
    wb.enabled = True
    wb.governance_mode = "intervention"
    placement = MagicMock()
    placement.kind = "covered_gates"
    placement.covered_gates = ["GT-130"]
    wb.lifecycle_placement = placement
    wb.artifacts_in_scope = []
    workflow_layer = MagicMock()
    workflow_layer.workbenches = [wb]

    validator = PostureValidator()
    with pytest.raises(PostureValidationError, match="governed-closure gates"):
        validator.validate(
            effective_layer=effective,
            workflow_layer=workflow_layer,
            status_contract={"families": {}},
        )


# ---------------------------------------------------------------------------
# C06 — intervention restriction enforcement
# ---------------------------------------------------------------------------

def test_c06_guard_blocks_write_binding_record_under_intervention() -> None:
    posture = _make_intervention_posture_result()
    guard = InterventionRestrictionGuard()
    with pytest.raises(InterventionRestrictionError, match="write_binding_record"):
        guard.check(posture_result=posture, transaction_kind="write_binding_record")


def test_c06_guard_blocks_claim_governed_closure_under_intervention() -> None:
    posture = _make_intervention_posture_result()
    guard = InterventionRestrictionGuard()
    with pytest.raises(InterventionRestrictionError, match="intervention_surface posture"):
        guard.check(posture_result=posture, transaction_kind="claim_governed_closure")


def test_c06_guard_blocks_advance_status_to_terminal_under_intervention() -> None:
    posture = _make_intervention_posture_result()
    guard = InterventionRestrictionGuard()
    with pytest.raises(InterventionRestrictionError):
        guard.check(posture_result=posture, transaction_kind="advance_status_to_terminal")


def test_c06_guard_blocks_emit_gate_evidence_under_intervention() -> None:
    posture = _make_intervention_posture_result()
    guard = InterventionRestrictionGuard()
    with pytest.raises(InterventionRestrictionError):
        guard.check(posture_result=posture, transaction_kind="emit_gate_evidence")


def test_c06_guard_allows_inspect_under_intervention() -> None:
    posture = _make_intervention_posture_result()
    guard = InterventionRestrictionGuard()
    guard.check(posture_result=posture, transaction_kind="inspect")  # must not raise


def test_c06_guard_allows_orient_under_intervention() -> None:
    posture = _make_intervention_posture_result()
    guard = InterventionRestrictionGuard()
    guard.check(posture_result=posture, transaction_kind="orient")  # must not raise


def test_c06_guard_is_noop_under_full_governed() -> None:
    posture = PostureResult(
        classification="full_governed_surface",
        bounded_scope_markers=(),
        restricted_capabilities=(),
        provenance=_make_intervention_provenance(),
    )
    guard = InterventionRestrictionGuard()
    for kind in _INTERVENTION_FORBIDDEN_TRANSACTION_KINDS:
        guard.check(posture_result=posture, transaction_kind=kind)  # must not raise


def test_c06_guard_is_noop_when_posture_result_is_none() -> None:
    guard = InterventionRestrictionGuard()
    guard.check(posture_result=None, transaction_kind="write_binding_record")  # must not raise