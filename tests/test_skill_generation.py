"""Tests for TD-0005-C10 (AI-agent projection consistency) and TD-0005-C11 (freshness checks).

C10: SkillGenerator.generate() produces skill_manifest.json with mode/guide agreement.
C11: SkillGenerator.check_freshness() is fatal for full_governed_surface when stale.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from lantern.workflow.merger import (
    ConfigurationLoader,
    FreshnessResult,
)
from lantern.skills.generator import SkillGenerator, compute_workflow_layer_hash


def _make_config_folder_with_modes(tmp_path: Path) -> Path:
    cfg = tmp_path / "workflow" / "configuration"
    for sub in ("instructions", "workbenches", "guides"):
        (cfg / sub).mkdir(parents=True, exist_ok=True)
    (cfg / "instructions" / "onboarding.md").write_text("# onboarding", encoding="utf-8")
    (cfg / "guides" / "README.md").write_text("# guide README", encoding="utf-8")
    (cfg / "guides" / "feature_delivery.md").write_text("# feature_delivery guide", encoding="utf-8")
    main_yaml = {
        "configuration_version": "1",
        "declared_posture": "full_governed_surface",
        "workflow_modes": [
            {
                "mode_id": "feature_delivery",
                "entry_workbench": "ch_and_td_readiness",
                "guide_refs": ["guides/README.md", "guides/feature_delivery.md"],
            },
            {
                "mode_id": "bug_fix",
                "entry_workbench": "issue_operations",
                "guide_refs": ["guides/README.md"],
            },
        ],
    }
    (cfg / "main.yaml").write_text(yaml.safe_dump(main_yaml), encoding="utf-8")
    return cfg


# ---------------------------------------------------------------------------
# C10 — AI-agent projection consistency
# ---------------------------------------------------------------------------

def test_c10_generate_produces_skill_manifest_with_correct_modes(tmp_path: Path) -> None:
    cfg = _make_config_folder_with_modes(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)

    generator = SkillGenerator()
    generator.generate(
        product_governance_root=tmp_path,
        configuration_surface=surface,
        workflow_layer_hash="deadbeef0123456789",
    )

    manifest_path = cfg / "generated_skill" / "skill_manifest.json"
    assert manifest_path.exists(), "skill_manifest.json must exist after generation"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["configuration_hash"] == surface.main_yaml_hash
    assert manifest["workflow_layer_hash"] == "deadbeef0123456789"
    assert "generation_timestamp" in manifest

    mode_ids = {m["mode_id"] for m in manifest["modes"]}
    assert mode_ids == {"feature_delivery", "bug_fix"}

    feature_mode = next(m for m in manifest["modes"] if m["mode_id"] == "feature_delivery")
    assert "guides/README.md" in feature_mode["guide_refs"]
    assert "guides/feature_delivery.md" in feature_mode["guide_refs"]


def test_c10_generated_skill_md_exists_after_generation(tmp_path: Path) -> None:
    cfg = _make_config_folder_with_modes(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    generator = SkillGenerator()
    generator.generate(
        product_governance_root=tmp_path,
        configuration_surface=surface,
        workflow_layer_hash="hash_abc",
    )
    assert (cfg / "generated_skill" / "SKILL.md").exists()


def test_c10_manifest_modes_match_main_yaml(tmp_path: Path) -> None:
    cfg = _make_config_folder_with_modes(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    generator = SkillGenerator()
    generator.generate(
        product_governance_root=tmp_path,
        configuration_surface=surface,
        workflow_layer_hash="hash_abc",
    )
    manifest = json.loads(
        (cfg / "generated_skill" / "skill_manifest.json").read_text(encoding="utf-8")
    )
    # Every mode in main.yaml must appear in the manifest
    main_mode_ids = {m.mode_id for m in surface.workflow_modes}
    manifest_mode_ids = {m["mode_id"] for m in manifest["modes"]}
    assert main_mode_ids == manifest_mode_ids
    for mode in surface.workflow_modes:
        manifest_mode = next(m for m in manifest["modes"] if m["mode_id"] == mode.mode_id)
        assert set(manifest_mode["guide_refs"]) == set(mode.guide_refs)


# ---------------------------------------------------------------------------
# C11 — freshness checks
# ---------------------------------------------------------------------------

def test_c11_fresh_manifest_returns_fresh_true(tmp_path: Path) -> None:
    cfg = _make_config_folder_with_modes(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    generator = SkillGenerator()
    workflow_hash = "abc123"
    generator.generate(
        product_governance_root=tmp_path,
        configuration_surface=surface,
        workflow_layer_hash=workflow_hash,
    )
    result = generator.check_freshness(
        configuration_surface=surface,
        workflow_layer_hash=workflow_hash,
    )
    assert result.fresh is True
    assert result.reasons == ()


def test_c11_stale_configuration_hash_returns_not_fresh(tmp_path: Path) -> None:
    cfg = _make_config_folder_with_modes(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    generator = SkillGenerator()
    generator.generate(
        product_governance_root=tmp_path,
        configuration_surface=surface,
        workflow_layer_hash="original_hash",
    )
    # Mutate main.yaml to change its hash
    raw = yaml.safe_load((cfg / "main.yaml").read_text())
    raw["configuration_version"] = "2"
    (cfg / "main.yaml").write_text(yaml.safe_dump(raw), encoding="utf-8")
    # Reload surface to get updated hash
    surface2 = loader.load_and_validate(cfg)
    result = generator.check_freshness(
        configuration_surface=surface2,
        workflow_layer_hash="original_hash",
    )
    assert result.fresh is False
    assert any("configuration_hash" in r for r in result.reasons)


def test_c11_stale_workflow_layer_hash_returns_not_fresh(tmp_path: Path) -> None:
    cfg = _make_config_folder_with_modes(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    generator = SkillGenerator()
    generator.generate(
        product_governance_root=tmp_path,
        configuration_surface=surface,
        workflow_layer_hash="original_hash",
    )
    result = generator.check_freshness(
        configuration_surface=surface,
        workflow_layer_hash="different_hash",  # workflow layer changed
    )
    assert result.fresh is False
    assert any("workflow_layer_hash" in r for r in result.reasons)


def test_c11_missing_manifest_returns_not_fresh(tmp_path: Path) -> None:
    cfg = _make_config_folder_with_modes(tmp_path)
    loader = ConfigurationLoader()
    surface = loader.load_and_validate(cfg)
    generator = SkillGenerator()
    # Do not generate — manifest is absent
    result = generator.check_freshness(
        configuration_surface=surface,
        workflow_layer_hash="any_hash",
    )
    assert result.fresh is False
    assert any("missing" in r.lower() for r in result.reasons)


def test_c11_compute_workflow_layer_hash_is_deterministic() -> None:
    from lantern.workflow.loader import load_workflow_layer

    layer = load_workflow_layer()
    h1 = compute_workflow_layer_hash(layer)
    h2 = compute_workflow_layer_hash(layer)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest