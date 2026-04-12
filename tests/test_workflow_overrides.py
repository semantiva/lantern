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

"""Tests for TD-0005-C01 (configuration-folder contract) and TD-0005-C02 (merge precedence).

C01: ConfigurationLoader validates the required folder tree and fails descriptively on violations.
C02: ConfigurationMerger applies baseline < product-governance < launcher-overlay precedence.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from lantern.workflow.merger import (
    ConfigurationLoadError,
    ConfigurationLoader,
    ConfigurationMerger,
    PostureValidationError,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_valid_config_folder(root: Path, declared_posture: str = "full_governed_surface") -> Path:
    """Create a minimal valid configuration folder at root/workflow/configuration/."""
    cfg = root / "workflow" / "configuration"
    for sub in ("instructions", "workbenches", "guides"):
        (cfg / sub).mkdir(parents=True, exist_ok=True)
    (cfg / "instructions" / "onboarding.md").write_text("# onboarding", encoding="utf-8")
    (cfg / "workbenches" / "ch_and_td_readiness.yaml").write_text(
        textwrap.dedent(
            """\
            workbench_id: ch_and_td_readiness
            instruction_resource: instructions/onboarding.md
            authoritative_guides: []
        """
        ),
        encoding="utf-8",
    )
    main_yaml = {
        "configuration_version": "1",
        "declared_posture": declared_posture,
        "workflow_modes": [
            {
                "mode_id": "feature_delivery",
                "entry_workbench": "ch_and_td_readiness",
                "guide_refs": [],
            }
        ],
        "workbench_overrides": [
            {
                "workbench_id": "ch_and_td_readiness",
                "file": "workbenches/ch_and_td_readiness.yaml",
            }
        ],
    }
    (cfg / "main.yaml").write_text(yaml.safe_dump(main_yaml), encoding="utf-8")
    return cfg


# ---------------------------------------------------------------------------
# C01 — configuration-folder contract
# ---------------------------------------------------------------------------


def test_c01_valid_folder_loads_successfully(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    assert surface.declared_posture == "full_governed_surface"
    assert surface.configuration_version == "1"
    assert len(surface.workflow_modes) == 1
    assert surface.workflow_modes[0].mode_id == "feature_delivery"
    assert len(surface.workbench_overrides) == 1
    assert surface.workbench_overrides[0].workbench_id == "ch_and_td_readiness"
    assert surface.main_yaml_hash


def test_c01_missing_main_yaml_raises(tmp_path: Path) -> None:
    cfg = tmp_path / "workflow" / "configuration"
    cfg.mkdir(parents=True)
    loader = ConfigurationLoader()
    with pytest.raises(ConfigurationLoadError, match="main.yaml not found"):
        loader.load_and_validate(cfg)


def test_c01_missing_declared_posture_raises(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path)
    raw = yaml.safe_load((cfg / "main.yaml").read_text())
    del raw["declared_posture"]
    (cfg / "main.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    loader = ConfigurationLoader()
    with pytest.raises(ConfigurationLoadError, match="missing required field.*declared_posture"):
        loader.load_and_validate(cfg)


def test_c01_invalid_declared_posture_raises(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path)
    raw = yaml.safe_load((cfg / "main.yaml").read_text())
    raw["declared_posture"] = "super_governed_surface"
    (cfg / "main.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    loader = ConfigurationLoader()
    with pytest.raises(ConfigurationLoadError, match="declared_posture must be one of"):
        loader.load_and_validate(cfg)


def test_c01_missing_required_subfolder_raises(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path)
    import shutil

    shutil.rmtree(cfg / "instructions")
    loader = ConfigurationLoader()
    with pytest.raises(ConfigurationLoadError, match="missing required subfolder.*instructions"):
        loader.load_and_validate(cfg)


def test_c01_workbench_override_missing_instruction_resource_raises(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path)
    bad_wb = {"workbench_id": "ch_and_td_readiness"}  # no instruction_resource
    (cfg / "workbenches" / "ch_and_td_readiness.yaml").write_text(yaml.safe_dump(bad_wb), encoding="utf-8")
    loader = ConfigurationLoader()
    with pytest.raises(ConfigurationLoadError, match="missing instruction_resource"):
        loader.load_and_validate(cfg)


def test_c01_workbench_override_unresolvable_instruction_resource_raises(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path)
    bad_wb = {"workbench_id": "ch_and_td_readiness", "instruction_resource": "instructions/nonexistent.md"}
    (cfg / "workbenches" / "ch_and_td_readiness.yaml").write_text(yaml.safe_dump(bad_wb), encoding="utf-8")
    loader = ConfigurationLoader()
    with pytest.raises(ConfigurationLoadError, match="does not exist"):
        loader.load_and_validate(cfg)


def test_c01_duplicate_workbench_id_raises(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path)
    raw = yaml.safe_load((cfg / "main.yaml").read_text())
    raw["workbench_overrides"].append(
        {
            "workbench_id": "ch_and_td_readiness",
            "file": "workbenches/ch_and_td_readiness.yaml",
        }
    )
    (cfg / "main.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    loader = ConfigurationLoader()
    with pytest.raises(ConfigurationLoadError, match="Duplicate workbench_id"):
        loader.load_and_validate(cfg)


# ---------------------------------------------------------------------------
# C02 — deterministic merge precedence
# ---------------------------------------------------------------------------


def test_c02_baseline_only_uses_baseline_classification(tmp_path: Path) -> None:
    merger = ConfigurationMerger()
    layer = merger.merge(
        baseline_surface_classification="full_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=None,
    )
    assert layer.effective_surface_classification == "full_governed_surface"
    assert layer.baseline_surface_classification == "full_governed_surface"
    assert layer.configuration_surface is None
    assert layer.posture_result.provenance.configuration_folder is None


def test_c02_phase2_overrides_baseline_classification(tmp_path: Path) -> None:
    cfg = _make_valid_config_folder(tmp_path, declared_posture="partial_governed_surface")
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    merger = ConfigurationMerger()
    layer = merger.merge(
        baseline_surface_classification="full_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=surface,
    )
    assert layer.effective_surface_classification == "partial_governed_surface"
    assert "ch_and_td_readiness" in layer.merged_workbench_overrides


def test_c02_phase3_overlay_overrides_phase2_workbench(tmp_path: Path) -> None:
    # Phase 2: partial; launcher overlay overrides the same workbench with different content
    cfg2 = _make_valid_config_folder(tmp_path / "p2", declared_posture="partial_governed_surface")
    (cfg2 / "instructions" / "onboarding_overlay.md").write_text("# overlay", encoding="utf-8")
    overlay_wb = {
        "workbench_id": "ch_and_td_readiness",
        "instruction_resource": "instructions/onboarding_overlay.md",
        "authoritative_guides": [],
        "_source": "overlay",
    }
    (cfg2 / "workbenches" / "ch_and_td_readiness.yaml").write_text(yaml.safe_dump(overlay_wb), encoding="utf-8")
    main_overlay = {
        "configuration_version": "1",
        "declared_posture": "partial_governed_surface",
        "workbench_overrides": [
            {"workbench_id": "ch_and_td_readiness", "file": "workbenches/ch_and_td_readiness.yaml"}
        ],
    }
    cfg3 = _make_valid_config_folder(tmp_path / "p3", declared_posture="partial_governed_surface")
    (cfg3 / "instructions" / "onboarding_overlay.md").write_text("# overlay", encoding="utf-8")
    (cfg3 / "workbenches" / "ch_and_td_readiness.yaml").write_text(yaml.safe_dump(overlay_wb), encoding="utf-8")
    (cfg3 / "main.yaml").write_text(yaml.safe_dump(main_overlay), encoding="utf-8")

    loader = ConfigurationLoader()
    surface2 = loader.load_and_validate(cfg2)
    surface3 = loader.load_and_validate(cfg3)

    merger = ConfigurationMerger()
    layer = merger.merge(
        baseline_surface_classification="full_governed_surface",
        baseline_version="0.5.0",
        configuration_surface=surface2,
        launcher_overlay_surface=surface3,
    )
    # Phase 3 overlay wins for this workbench
    merged_wb = layer.merged_workbench_overrides.get("ch_and_td_readiness", {})
    assert merged_wb.get("_source") == "overlay"
    assert layer.posture_result.provenance.launcher_overlay_folder is not None


def test_c02_launcher_overlay_mismatched_posture_raises(tmp_path: Path) -> None:
    cfg2 = _make_valid_config_folder(tmp_path / "p2", declared_posture="partial_governed_surface")
    cfg3 = _make_valid_config_folder(tmp_path / "p3", declared_posture="full_governed_surface")
    loader = ConfigurationLoader()
    surface2 = loader.load_and_validate(cfg2)
    surface3 = loader.load_and_validate(cfg3)
    merger = ConfigurationMerger()
    with pytest.raises(PostureValidationError, match="differs from product-governance configuration"):
        merger.merge(
            baseline_surface_classification="full_governed_surface",
            baseline_version="0.5.0",
            configuration_surface=surface2,
            launcher_overlay_surface=surface3,
        )


def test_c02_launcher_overlay_new_workbench_id_raises(tmp_path: Path) -> None:
    cfg2 = _make_valid_config_folder(tmp_path / "p2", declared_posture="partial_governed_surface")
    # Phase 3 tries to add a workbench not in Phase 2
    (cfg2.parent.parent / "p3" / "workflow" / "configuration" / "instructions").mkdir(parents=True, exist_ok=True)
    (cfg2.parent.parent / "p3" / "workflow" / "configuration" / "workbenches").mkdir(parents=True, exist_ok=True)
    (cfg2.parent.parent / "p3" / "workflow" / "configuration" / "guides").mkdir(parents=True, exist_ok=True)
    instr = cfg2.parent.parent / "p3" / "workflow" / "configuration" / "instructions" / "new.md"
    instr.write_text("# new", encoding="utf-8")
    new_wb = {
        "workbench_id": "new_workbench",
        "instruction_resource": "instructions/new.md",
        "authoritative_guides": [],
    }
    wb_path = cfg2.parent.parent / "p3" / "workflow" / "configuration" / "workbenches" / "new_workbench.yaml"
    wb_path.write_text(yaml.safe_dump(new_wb), encoding="utf-8")
    main3 = {
        "configuration_version": "1",
        "declared_posture": "partial_governed_surface",
        "workbench_overrides": [{"workbench_id": "new_workbench", "file": "workbenches/new_workbench.yaml"}],
    }
    cfg3 = cfg2.parent.parent / "p3" / "workflow" / "configuration"
    (cfg3 / "main.yaml").write_text(yaml.safe_dump(main3), encoding="utf-8")
    loader = ConfigurationLoader()
    surface2 = loader.load_and_validate(cfg2)
    surface3 = loader.load_and_validate(cfg3)
    merger = ConfigurationMerger()
    with pytest.raises(PostureValidationError, match="may not widen the governed workbench scope"):
        merger.merge(
            baseline_surface_classification="full_governed_surface",
            baseline_version="0.5.0",
            configuration_surface=surface2,
            launcher_overlay_surface=surface3,
        )
