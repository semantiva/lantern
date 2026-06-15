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

"""Configuration surface loader, merger, and posture validator for CH-0005.

This module owns the three-phase merge chain, declared-posture validation,
intervention restriction enforcement, and runtime-posture audit labeling.
It does not touch the static skill surface (SKILL.md is hand-maintained, CH-0034).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigurationLoadError(RuntimeError):
    """Raised when a product-governance configuration surface cannot be loaded."""


class PostureValidationError(RuntimeError):
    """Raised when the declared posture cannot be validated against the merged surface."""


class InterventionRestrictionError(RuntimeError):
    """Raised when a forbidden operation is attempted under intervention_surface posture."""


# Three valid posture values sourced from workbench_schema.yaml runtime_surface_classification_values
_VALID_POSTURES = frozenset({"full_governed_surface", "partial_governed_surface", "intervention_surface"})

# Required gates for full_governed_surface sourced from workbench_schema.yaml required_full_governed_gates
_REQUIRED_FULL_GOVERNED_GATES = frozenset({"GT-030", "GT-050", "GT-060", "GT-110", "GT-115", "GT-120", "GT-130"})

# Transaction kinds forbidden under intervention_surface posture (from DC-A design commitment)
_INTERVENTION_FORBIDDEN_TRANSACTION_KINDS = frozenset(
    {"claim_governed_closure", "advance_status_to_terminal", "write_binding_record", "emit_gate_evidence"}
)


@dataclass(frozen=True)
class WorkflowMode:
    mode_id: str
    entry_workbench: str


@dataclass(frozen=True)
class ConfigurationSurface:
    folder: Path
    configuration_version: str
    declared_posture: str
    workflow_modes: tuple[WorkflowMode, ...]
    main_yaml_hash: str
    authoritative_refs: dict[str, str]


@dataclass(frozen=True)
class MergeProvenance:
    baseline_version: str
    configuration_folder: str | None
    main_yaml_hash: str | None
    launcher_overlay_folder: str | None
    launcher_overlay_hash: str | None
    selected_workflow_id: str | None = None
    selected_workflow_source_path: str | None = None
    workflow_root: str | None = None
    workbench_root: str | None = None


@dataclass(frozen=True)
class PostureResult:
    classification: str
    bounded_scope_markers: tuple[str, ...]
    restricted_capabilities: tuple[str, ...]
    provenance: MergeProvenance


@dataclass(frozen=True)
class FreshnessResult:
    fresh: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EffectiveLayer:
    """Merged runtime surface: packaged baseline + optional product-governance config + optional launcher overlay."""

    baseline_surface_classification: str
    effective_surface_classification: str
    posture_result: PostureResult
    merged_modes: tuple[WorkflowMode, ...]
    configuration_surface: ConfigurationSurface | None
    selected_workflow_id: str | None = None
    selected_workflow_display_name: str | None = None
    selected_workflow_source_path: str | None = None
    active_workbench_ids: tuple[str, ...] = ()
    workflow_root: str | None = None
    workbench_root: str | None = None


class ConfigurationLoader:
    """Load and schema-validate a product-governance configuration folder."""

    def load_and_validate(self, folder: Path) -> ConfigurationSurface:
        """Load main.yaml and validate the configuration folder tree.

        Raises ConfigurationLoadError on any structural, schema, or path-resolution failure.
        """
        main_yaml_path = folder / "main.yaml"
        if not main_yaml_path.exists():
            raise ConfigurationLoadError(f"main.yaml not found at {main_yaml_path}")
        try:
            raw: dict[str, Any] = yaml.safe_load(main_yaml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigurationLoadError(f"main.yaml parse error at {main_yaml_path}: {exc}") from exc

        # Required top-level fields
        for required_field in ("configuration_version", "declared_posture"):
            if required_field not in raw:
                raise ConfigurationLoadError(
                    f"main.yaml at {main_yaml_path} is missing required field: {required_field!r}"
                )

        declared_posture = str(raw["declared_posture"]).strip()
        if declared_posture not in _VALID_POSTURES:
            raise ConfigurationLoadError(
                f"main.yaml declared_posture must be one of {sorted(_VALID_POSTURES)}; "
                f"got {declared_posture!r} at {main_yaml_path}"
            )

        # Workflow modes
        modes_raw = raw.get("workflow_modes") or []
        modes: list[WorkflowMode] = []
        seen_mode_ids: set[str] = set()
        for item in modes_raw:
            mode_id = str(item.get("mode_id", "")).strip()
            entry_workbench = str(item.get("entry_workbench", "")).strip()
            if not mode_id:
                raise ConfigurationLoadError(f"workflow_modes entry in {main_yaml_path} is missing mode_id")
            if mode_id in seen_mode_ids:
                raise ConfigurationLoadError(f"Duplicate mode_id {mode_id!r} in workflow_modes at {main_yaml_path}")
            seen_mode_ids.add(mode_id)
            if not entry_workbench:
                raise ConfigurationLoadError(
                    f"workflow_modes {mode_id!r} in {main_yaml_path} is missing entry_workbench"
                )
            modes.append(WorkflowMode(mode_id=mode_id, entry_workbench=entry_workbench))

        main_yaml_hash = _sha256_path(main_yaml_path)
        authoritative_refs = {str(k): str(v) for k, v in (raw.get("authoritative_refs") or {}).items()}

        return ConfigurationSurface(
            folder=folder,
            configuration_version=str(raw.get("configuration_version", "1")),
            declared_posture=declared_posture,
            workflow_modes=tuple(modes),
            main_yaml_hash=main_yaml_hash,
            authoritative_refs=authoritative_refs,
        )


class ConfigurationMerger:
    """Compose packaged baseline, product-governance configuration, and optional launcher overlay."""

    def merge(
        self,
        *,
        baseline_surface_classification: str,
        baseline_version: str,
        configuration_surface: ConfigurationSurface | None = None,
        launcher_overlay_surface: ConfigurationSurface | None = None,
        selected_workflow_id: str | None = None,
        selected_workflow_display_name: str | None = None,
        selected_workflow_source_path: str | None = None,
        active_workbench_ids: tuple[str, ...] = (),
        workflow_root: str | None = None,
        workbench_root: str | None = None,
    ) -> EffectiveLayer:
        """Apply the three-phase deterministic merge and return an EffectiveLayer.

        Phase 1: packaged Lantern workflow baseline (immutable, always present).
        Phase 2: product-governance configuration folder (optional; determines effective posture).
        Phase 3: launcher overlay using the same declaration model (optional; startup-only).

        The launcher overlay may NOT declare a different posture from Phase 2 when both are present.
        The launcher overlay may NOT add workbench override IDs not already in the Phase 2 surface.
        """
        if selected_workflow_id is not None:
            provenance = MergeProvenance(
                baseline_version=baseline_version,
                configuration_folder=None,
                main_yaml_hash=None,
                launcher_overlay_folder=None,
                launcher_overlay_hash=None,
                selected_workflow_id=selected_workflow_id,
                selected_workflow_source_path=selected_workflow_source_path,
                workflow_root=workflow_root,
                workbench_root=workbench_root,
            )
            effective_classification = baseline_surface_classification
            posture_result = PostureResult(
                classification=effective_classification,
                bounded_scope_markers=(
                    tuple(active_workbench_ids) if effective_classification == "partial_governed_surface" else ()
                ),
                restricted_capabilities=(
                    tuple(sorted(_INTERVENTION_FORBIDDEN_TRANSACTION_KINDS))
                    if effective_classification == "intervention_surface"
                    else ()
                ),
                provenance=provenance,
            )
            return EffectiveLayer(
                baseline_surface_classification=baseline_surface_classification,
                effective_surface_classification=effective_classification,
                posture_result=posture_result,
                merged_modes=(),
                configuration_surface=None,
                selected_workflow_id=selected_workflow_id,
                selected_workflow_display_name=selected_workflow_display_name,
                selected_workflow_source_path=selected_workflow_source_path,
                active_workbench_ids=tuple(active_workbench_ids),
                workflow_root=workflow_root,
                workbench_root=workbench_root,
            )

        merged_modes: list[WorkflowMode] = []

        # Phase 2
        if configuration_surface is not None:
            merged_modes = list(configuration_surface.workflow_modes)

        # Phase 3
        launcher_overlay_folder: str | None = None
        launcher_overlay_hash: str | None = None
        if launcher_overlay_surface is not None:
            if (
                configuration_surface is not None
                and launcher_overlay_surface.declared_posture != configuration_surface.declared_posture
            ):
                raise PostureValidationError(
                    f"Launcher overlay declared_posture {launcher_overlay_surface.declared_posture!r} "
                    f"differs from product-governance configuration declared_posture "
                    f"{configuration_surface.declared_posture!r}; they must match when both are present."
                )
            if launcher_overlay_surface.workflow_modes:
                merged_modes = list(launcher_overlay_surface.workflow_modes)
            launcher_overlay_folder = str(launcher_overlay_surface.folder)
            launcher_overlay_hash = launcher_overlay_surface.main_yaml_hash

        # Effective surface classification
        effective_classification = (
            configuration_surface.declared_posture
            if configuration_surface is not None
            else baseline_surface_classification
        )

        provenance = MergeProvenance(
            baseline_version=baseline_version,
            configuration_folder=(str(configuration_surface.folder) if configuration_surface else None),
            main_yaml_hash=(configuration_surface.main_yaml_hash if configuration_surface else None),
            launcher_overlay_folder=launcher_overlay_folder,
            launcher_overlay_hash=launcher_overlay_hash,
        )

        posture_result = PostureResult(
            classification=effective_classification,
            bounded_scope_markers=(),
            restricted_capabilities=(),
            provenance=provenance,
        )

        return EffectiveLayer(
            baseline_surface_classification=baseline_surface_classification,
            effective_surface_classification=effective_classification,
            posture_result=posture_result,
            merged_modes=tuple(merged_modes),
            configuration_surface=configuration_surface,
        )


class PostureValidator:
    """Validate the effective posture claim against the merged surface and status contract."""

    def validate(
        self,
        *,
        effective_layer: EffectiveLayer,
        workflow_layer: Any,
        status_contract: dict[str, Any],
    ) -> PostureResult:
        """Validate and return a final PostureResult with fully resolved restricted_capabilities.

        Raises PostureValidationError (always fatal) when full_governed_surface is claimed
        but the merged surface cannot satisfy the required gate or family coverage.
        """
        classification = effective_layer.effective_surface_classification
        provenance = effective_layer.posture_result.provenance

        if classification == "full_governed_surface":
            return self._validate_full_governed(effective_layer, workflow_layer, status_contract, provenance)
        if classification == "partial_governed_surface":
            return self._validate_partial_governed(effective_layer, provenance)
        if classification == "intervention_surface":
            return self._validate_intervention(effective_layer, workflow_layer, provenance)

        raise PostureValidationError(f"Unknown posture classification: {classification!r}")

    def _validate_full_governed(
        self,
        effective_layer: EffectiveLayer,
        workflow_layer: Any,
        status_contract: dict[str, Any],
        provenance: MergeProvenance,
    ) -> PostureResult:
        # Gate coverage: collect gates from all active workbenches in the selected workflow.
        covered_gates: set[str] = set()
        for workbench in workflow_layer.workbenches:
            placement = workbench.lifecycle_placement
            if placement.kind == "covered_gates":
                covered_gates.update(placement.covered_gates)
            elif placement.kind == "lifecycle_span":
                covered_gates.add(placement.start_gate)
                covered_gates.add(placement.end_gate)

        missing_gates = sorted(_REQUIRED_FULL_GOVERNED_GATES - covered_gates)
        if missing_gates:
            raise PostureValidationError(
                f"full_governed_surface claim is INVALID: the merged workbench set does not cover "
                f"required gates {missing_gates}. "
                f"A product-governance configuration must not remove workbenches that cover required "
                f"governed gates. Remediation: restore the missing workbench declarations or "
                f"change declared_posture to partial_governed_surface."
            )

        # Family admissibility: every artifact family in scope must exist in the status contract
        known_families = set(status_contract.get("families", {}).keys())
        for workbench in workflow_layer.workbenches:
            for family in workbench.artifacts_in_scope:
                if family not in known_families:
                    raise PostureValidationError(
                        f"full_governed_surface claim is INVALID: workbench {workbench.workbench_id!r} "
                        f"references artifact family {family!r} which is absent from the packaged "
                        f"status contract. "
                        f"Remediation: add the family to the status contract or remove the workbench."
                    )

        return PostureResult(
            classification="full_governed_surface",
            bounded_scope_markers=(),
            restricted_capabilities=(),
            provenance=provenance,
        )

    def _validate_partial_governed(
        self,
        effective_layer: EffectiveLayer,
        provenance: MergeProvenance,
    ) -> PostureResult:
        return PostureResult(
            classification="partial_governed_surface",
            bounded_scope_markers=effective_layer.active_workbench_ids,
            restricted_capabilities=(),
            provenance=provenance,
        )

    def _validate_intervention(
        self,
        effective_layer: EffectiveLayer,
        workflow_layer: Any,
        provenance: MergeProvenance,
    ) -> PostureResult:
        # Verify no intervention workbench claims governed-closure gates (GT-120, GT-130)
        _governed_closure_gates = frozenset({"GT-120", "GT-130"})
        for workbench in workflow_layer.workbenches:
            placement = workbench.lifecycle_placement
            gates: list[str] = []
            if placement.kind == "covered_gates":
                gates = list(placement.covered_gates)
            elif placement.kind == "lifecycle_span":
                gates = [placement.start_gate, placement.end_gate]
            overlap = set(gates) & _governed_closure_gates
            if overlap:
                raise PostureValidationError(
                    f"intervention_surface claim is INVALID: workbench {workbench.workbench_id!r} "
                    f"covers governed-closure gates {sorted(overlap)}. "
                    f"Intervention workbenches may not claim governed closure. "
                    f"Remediation: remove the closure gate coverage from the intervention workbench."
                )
        return PostureResult(
            classification="intervention_surface",
            bounded_scope_markers=(),
            restricted_capabilities=tuple(sorted(_INTERVENTION_FORBIDDEN_TRANSACTION_KINDS)),
            provenance=provenance,
        )


class InterventionRestrictionGuard:
    """Enforce intervention-surface restrictions at the transaction-engine chokepoint.

    This guard is the single enforcement point for all mutation-capable flows.
    Individual MCP handlers must NOT implement per-handler intervention checks.
    """

    def check(self, *, posture_result: PostureResult | None, transaction_kind: str) -> None:
        """Raise InterventionRestrictionError if the transaction is forbidden under the active posture.

        Safe to call with posture_result=None (no-op; used when effective layer is not yet loaded).
        """
        if posture_result is None:
            return
        if posture_result.classification != "intervention_surface":
            return
        if transaction_kind in _INTERVENTION_FORBIDDEN_TRANSACTION_KINDS:
            raise InterventionRestrictionError(
                f"Transaction kind {transaction_kind!r} is forbidden under intervention_surface posture. "
                f"Intervention workbenches cannot claim governed closure, advance artifact status to "
                f"terminal values, write binding records, or emit gate evidence. "
                f"Restricted capabilities for this session: "
                f"{sorted(posture_result.restricted_capabilities)}"
            )


def build_runtime_posture_label(posture_result: PostureResult) -> dict[str, Any]:
    """Return the runtime_posture block for inclusion in inspect/orient/journal output.

    This block is present in ALL responses, including the default full_governed_surface case
    (with empty bounded_scope_markers and empty restricted_capabilities), so that tests can
    assert the block universally without branching on session type.
    """
    provenance = posture_result.provenance
    merge_sources: list[dict[str, Any]] = [
        {"phase": 1, "label": "packaged_baseline", "version": provenance.baseline_version},
    ]
    if provenance.configuration_folder is not None:
        merge_sources.append(
            {
                "phase": 2,
                "label": "product_governance_configuration",
                "folder": provenance.configuration_folder,
                "hash": provenance.main_yaml_hash,
            }
        )
    if provenance.launcher_overlay_folder is not None:
        merge_sources.append(
            {
                "phase": 3,
                "label": "launcher_overlay",
                "folder": provenance.launcher_overlay_folder,
                "hash": provenance.launcher_overlay_hash,
            }
        )
    return {
        "classification": posture_result.classification,
        "selected_workflow": {
            "workflow_id": provenance.selected_workflow_id,
            "source_path": provenance.selected_workflow_source_path,
        },
        "catalog_roots": {
            "workflow_root": provenance.workflow_root,
            "workbench_root": provenance.workbench_root,
        },
        "bounded_scope_markers": list(posture_result.bounded_scope_markers),
        "configuration_provenance": {
            "folder": provenance.configuration_folder,
            "main_yaml_hash": provenance.main_yaml_hash,
            "merge_sources": merge_sources,
        },
        "restricted_capabilities": list(posture_result.restricted_capabilities),
    }


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
