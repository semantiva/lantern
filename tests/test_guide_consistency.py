"""Tests for TD-0005-C07 (mode/workbench guide consistency), C08 (inspect), C09 (orient).

C07: ConfigurationMerger.validate_guide_consistency raises on diverging guide refs.
C08: handle_inspect adds a runtime_posture block to all response kinds.
C09: handle_orient adds a runtime_posture block to OrientResponse.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from lantern.workflow.merger import (
    ConfigurationLoadError,
    ConfigurationLoader,
    ConfigurationMerger,
    MergeProvenance,
    PostureResult,
    WorkflowMode,
    build_runtime_posture_label,
)


def _make_posture_result(classification: str = "full_governed_surface") -> PostureResult:
    return PostureResult(
        classification=classification,
        bounded_scope_markers=(),
        restricted_capabilities=(),
        provenance=MergeProvenance(
            baseline_version="0.5.0",
            configuration_folder=None,
            main_yaml_hash=None,
            launcher_overlay_folder=None,
            launcher_overlay_hash=None,
        ),
    )


def _make_workflow_layer_with_guides(wb_id: str, guide_refs: list[str]) -> MagicMock:
    wb = MagicMock()
    wb.workbench_id = wb_id
    wb.authoritative_guides = tuple(guide_refs)
    layer = MagicMock()
    layer.workbenches = [wb]

    def _get_workbench(wid: str) -> MagicMock:
        if wid == wb_id:
            return wb
        raise KeyError(wid)

    layer.get_workbench.side_effect = _get_workbench
    return layer


# ---------------------------------------------------------------------------
# C07 — mode/workbench guide consistency
# ---------------------------------------------------------------------------


def test_c07_consistent_guides_passes() -> None:
    from lantern.workflow.merger import EffectiveLayer, MergeProvenance, PostureResult

    mode = WorkflowMode(
        mode_id="feature_delivery",
        entry_workbench="ch_and_td_readiness",
        guide_refs=("guides/README.md", "guides/feature_delivery.md"),
    )
    layer = _make_workflow_layer_with_guides(
        "ch_and_td_readiness",
        ["guides/README.md", "guides/feature_delivery.md"],
    )
    provenance = MergeProvenance("0.5.0", None, None, None, None)
    effective = EffectiveLayer(
        baseline_surface_classification="full_governed_surface",
        effective_surface_classification="full_governed_surface",
        posture_result=PostureResult("full_governed_surface", (), (), provenance),
        merged_workbench_overrides={},
        merged_modes=(mode,),
        configuration_surface=None,
    )
    merger = ConfigurationMerger()
    merger.validate_guide_consistency(effective_layer=effective, workflow_layer=layer)  # must not raise


def test_c07_diverging_guide_refs_raises() -> None:
    from lantern.workflow.merger import EffectiveLayer, MergeProvenance, PostureResult

    mode = WorkflowMode(
        mode_id="feature_delivery",
        entry_workbench="ch_and_td_readiness",
        guide_refs=("guides/README.md", "guides/feature_delivery.md"),
    )
    layer = _make_workflow_layer_with_guides(
        "ch_and_td_readiness",
        ["guides/README.md", "guides/different_guide.md"],  # diverges
    )
    provenance = MergeProvenance("0.5.0", None, None, None, None)
    effective = EffectiveLayer(
        baseline_surface_classification="full_governed_surface",
        effective_surface_classification="full_governed_surface",
        posture_result=PostureResult("full_governed_surface", (), (), provenance),
        merged_workbench_overrides={},
        merged_modes=(mode,),
        configuration_surface=None,
    )
    merger = ConfigurationMerger()
    with pytest.raises(ConfigurationLoadError, match="Guide consistency failure"):
        merger.validate_guide_consistency(effective_layer=effective, workflow_layer=layer)


def test_c07_unknown_entry_workbench_not_in_overrides_raises() -> None:
    from lantern.workflow.merger import EffectiveLayer, MergeProvenance, PostureResult

    mode = WorkflowMode(
        mode_id="feature_delivery",
        entry_workbench="nonexistent_workbench",
        guide_refs=("guides/README.md",),
    )
    layer = MagicMock()
    layer.get_workbench.side_effect = KeyError("nonexistent_workbench")
    provenance = MergeProvenance("0.5.0", None, None, None, None)
    effective = EffectiveLayer(
        baseline_surface_classification="full_governed_surface",
        effective_surface_classification="full_governed_surface",
        posture_result=PostureResult("full_governed_surface", (), (), provenance),
        merged_workbench_overrides={},
        merged_modes=(mode,),
        configuration_surface=None,
    )
    merger = ConfigurationMerger()
    with pytest.raises(ConfigurationLoadError, match="not present in the built-in workbench set"):
        merger.validate_guide_consistency(effective_layer=effective, workflow_layer=layer)


def test_c07_overridden_workbench_skips_guide_cross_check() -> None:
    """Mode's entry_workbench is in merged_workbench_overrides — no consistency check needed."""
    from lantern.workflow.merger import EffectiveLayer, MergeProvenance, PostureResult

    mode = WorkflowMode(
        mode_id="feature_delivery",
        entry_workbench="ch_and_td_readiness",
        guide_refs=("guides/README.md",),
    )
    layer = MagicMock()
    layer.get_workbench.side_effect = KeyError  # should never be called for overridden wb
    provenance = MergeProvenance("0.5.0", None, None, None, None)
    effective = EffectiveLayer(
        baseline_surface_classification="full_governed_surface",
        effective_surface_classification="full_governed_surface",
        posture_result=PostureResult("full_governed_surface", (), (), provenance),
        merged_workbench_overrides={"ch_and_td_readiness": {}},
        merged_modes=(mode,),
        configuration_surface=None,
    )
    merger = ConfigurationMerger()
    merger.validate_guide_consistency(effective_layer=effective, workflow_layer=layer)  # must not raise


# ---------------------------------------------------------------------------
# C08 — inspect runtime_posture block
# ---------------------------------------------------------------------------


def test_c08_inspect_catalog_includes_runtime_posture() -> None:
    from lantern.mcp.inspect import handle_inspect
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    posture = _make_posture_result()
    result = handle_inspect(kind="catalog", workflow_layer=layer, posture_result=posture)
    assert hasattr(result, "runtime_posture")
    rp = result.runtime_posture
    assert rp["classification"] == "full_governed_surface"
    assert "configuration_provenance" in rp
    assert "restricted_capabilities" in rp


def test_c08_inspect_workspace_includes_runtime_posture(tmp_path: Path) -> None:
    from lantern.mcp.inspect import handle_inspect
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    posture = _make_posture_result("partial_governed_surface")
    result = handle_inspect(
        kind="workspace",
        workflow_layer=layer,
        product_root=tmp_path,
        posture_result=posture,
    )
    assert result.runtime_posture["classification"] == "partial_governed_surface"


def test_c08_inspect_status_contract_includes_runtime_posture() -> None:
    from lantern.mcp.inspect import handle_inspect
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    posture = _make_posture_result()
    result = handle_inspect(kind="status_contract", workflow_layer=layer, posture_result=posture)
    assert result.runtime_posture["classification"] == "full_governed_surface"


# ---------------------------------------------------------------------------
# C09 — orient runtime_posture block
# ---------------------------------------------------------------------------


def test_c09_orient_includes_runtime_posture_block() -> None:
    from lantern.mcp.orient import handle_orient
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    posture = _make_posture_result("intervention_surface")
    result = handle_orient(
        workflow_layer=layer,
        governance_state={"ch_statuses": {}, "active_gates": [], "passed_gates": []},
        posture_result=posture,
    )
    assert hasattr(result, "runtime_posture")
    assert result.runtime_posture["classification"] == "intervention_surface"


def test_c09_orient_default_posture_block_present_on_full_governed() -> None:
    from lantern.mcp.orient import handle_orient
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    posture = _make_posture_result("full_governed_surface")
    result = handle_orient(
        workflow_layer=layer,
        governance_state={"ch_statuses": {}, "active_gates": [], "passed_gates": []},
        posture_result=posture,
    )
    rp = result.runtime_posture
    assert rp["classification"] == "full_governed_surface"
    assert rp["bounded_scope_markers"] == []
    assert rp["restricted_capabilities"] == []
