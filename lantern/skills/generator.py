"""Authoritative generated-projection generator for product-governance configuration folders.

SkillGenerator writes generated_skill/SKILL.md and generated_skill/skill_manifest.json
into a product's governance repository configuration folder.  It also writes
generated_artifact_templates/ entries sourced from the packaged Lantern templates.

Generation is an explicit maintainer action, not an automatic startup side-effect.
At runtime startup, only SkillGenerator.check_freshness() is called to verify that
the committed projections are current relative to the authored configuration inputs.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from lantern.workflow.merger import (
    ConfigurationSurface,
    FreshnessResult,
)

# Packaged Lantern template directory (source for generated_artifact_templates/)
_LANTERN_TEMPLATES_ROOT = Path(__file__).resolve().parents[1] / "templates"

# Template filenames to include in generated_artifact_templates/
_TEMPLATE_FILENAMES = (
    "TEMPLATE__DIP.md",
    "TEMPLATE__SPEC.md",
    "TEMPLATE__ARCH.md",
    "TEMPLATE__INI.md",
    "TEMPLATE__CH.md",
    "TEMPLATE__TD.md",
    "TEMPLATE__DC.md",
    "TEMPLATE__DB.md",
    "TEMPLATE__CI.md",
    "TEMPLATE__EV.md",
    "TEMPLATE__DEC.md",
    "TEMPLATE__IS.md",
)

_SKILL_MD_TEMPLATE = """\
# Lantern Governed Workflow Runtime — AI Operator Skill

**Configuration:** {configuration_id}  
**Declared posture:** {declared_posture}  
**Generated:** {generation_timestamp}

## Discovery sequence

Always follow inspect → orient → transaction to operate safely:

1. `inspect(kind="catalog")` — list available tools and contracts.
2. `inspect(kind="workspace")` — confirm product and governance roots and posture.
3. `orient(intent="...", ch_statuses="...", active_gates="...", passed_gates="...")` — resolve active workbench and next valid actions.
4. `inspect(kind="contract", contract_ref="...")` — load the active workbench contract.
5. Execute the appropriate transaction (`draft`, `commit`, or `validate`).

## Workflow modes

{modes_section}

## Generated projection provenance

- configuration_hash: {configuration_hash}
- workflow_layer_hash: {workflow_layer_hash}
- generation_timestamp: {generation_timestamp}

Do not hand-edit this file. Regenerate by running `SkillGenerator.generate()` after
updating main.yaml or workbench declarations.
"""


class SkillGenerator:
    """Generate and freshness-check authoritative AI-facing projections for a product-governance folder."""

    def generate(
        self,
        *,
        product_governance_root: Path,
        configuration_surface: ConfigurationSurface,
        workflow_layer_hash: str,
    ) -> None:
        """Write generated_skill/ and generated_artifact_templates/ into the configuration folder.

        product_governance_root: the governed product's governance repository root.
        configuration_surface: loaded ConfigurationSurface for this product.
        workflow_layer_hash: SHA-256 of the merged workflow layer (caller computes this).

        The generated files are committed to governance by the maintainer after generation.
        They are never auto-regenerated at runtime startup.
        """
        config_folder = configuration_surface.folder
        configuration_hash = configuration_surface.main_yaml_hash
        generation_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        # Build modes section for SKILL.md
        modes_lines: list[str] = []
        for mode in configuration_surface.workflow_modes:
            modes_lines.append(f"### {mode.mode_id}")
            modes_lines.append(f"- Entry workbench: `{mode.entry_workbench}`")
            if mode.guide_refs:
                modes_lines.append("- Guides: " + ", ".join(f"`{g}`" for g in mode.guide_refs))
            modes_lines.append("")
        modes_section = "\n".join(modes_lines).rstrip()

        configuration_id = str(config_folder.relative_to(product_governance_root))

        skill_md = _SKILL_MD_TEMPLATE.format(
            configuration_id=configuration_id,
            declared_posture=configuration_surface.declared_posture,
            generation_timestamp=generation_timestamp,
            modes_section=modes_section or "(no workflow modes declared)",
            configuration_hash=configuration_hash,
            workflow_layer_hash=workflow_layer_hash,
        )

        modes_payload = [
            {
                "mode_id": mode.mode_id,
                "entry_workbench": mode.entry_workbench,
                "guide_refs": list(mode.guide_refs),
            }
            for mode in configuration_surface.workflow_modes
        ]

        manifest = {
            "generation_timestamp": generation_timestamp,
            "configuration_hash": configuration_hash,
            "workflow_layer_hash": workflow_layer_hash,
            "declared_posture": configuration_surface.declared_posture,
            "modes": modes_payload,
        }

        # Write generated_skill/
        skill_dir = config_folder / "generated_skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
        (skill_dir / "skill_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # Write generated_artifact_templates/
        templates_dir = config_folder / "generated_artifact_templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        for filename in _TEMPLATE_FILENAMES:
            source = _LANTERN_TEMPLATES_ROOT / filename
            if source.exists():
                dest = templates_dir / filename
                dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    def check_freshness(
        self,
        *,
        configuration_surface: ConfigurationSurface,
        workflow_layer_hash: str,
    ) -> FreshnessResult:
        """Check whether the committed generated projections are current.

        Returns a FreshnessResult.  Callers apply the fatal/warning distinction:
        - full_governed_surface: stale projections are a fatal startup error.
        - partial_governed_surface / intervention_surface: stale projections are a warning only.
        """
        config_folder = configuration_surface.folder
        reasons: list[str] = []

        skill_manifest_path = config_folder / "generated_skill" / "skill_manifest.json"
        skill_md_path = config_folder / "generated_skill" / "SKILL.md"

        if not skill_manifest_path.exists():
            reasons.append(
                f"generated_skill/skill_manifest.json is missing at {skill_manifest_path}. "
                f"Run SkillGenerator.generate() to produce authoritative projections."
            )
        else:
            try:
                manifest = json.loads(skill_manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                reasons.append(f"generated_skill/skill_manifest.json is unreadable: {exc}")
            else:
                committed_config_hash = manifest.get("configuration_hash", "")
                committed_wl_hash = manifest.get("workflow_layer_hash", "")
                if committed_config_hash != configuration_surface.main_yaml_hash:
                    reasons.append(
                        f"generated_skill/skill_manifest.json configuration_hash "
                        f"{committed_config_hash!r} does not match current main.yaml hash "
                        f"{configuration_surface.main_yaml_hash!r}. "
                        f"main.yaml has changed since the last generation run."
                    )
                if committed_wl_hash != workflow_layer_hash:
                    reasons.append(
                        f"generated_skill/skill_manifest.json workflow_layer_hash "
                        f"{committed_wl_hash!r} does not match current workflow layer hash "
                        f"{workflow_layer_hash!r}. "
                        f"The packaged workflow layer has changed since the last generation run."
                    )

        if not skill_md_path.exists():
            reasons.append(
                f"generated_skill/SKILL.md is missing at {skill_md_path}. "
                f"Run SkillGenerator.generate() to produce authoritative projections."
            )

        return FreshnessResult(fresh=not reasons, reasons=tuple(reasons))


def compute_workflow_layer_hash(workflow_layer: object) -> str:
    """Compute a deterministic hash of the workflow layer for freshness tracking.

    Uses grammar_version + grammar_package_version + sorted workbench_id list as the
    hash input.  This is stable across runs as long as the workflow layer inputs are unchanged.
    """
    payload = {
        "grammar_version": getattr(workflow_layer, "grammar_version", ""),
        "grammar_package_version": getattr(workflow_layer, "grammar_package_version", ""),
        "workbench_ids": sorted(
            w.workbench_id for w in getattr(workflow_layer, "workbenches", [])
        ),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()