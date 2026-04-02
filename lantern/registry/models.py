"""Immutable workbench registry models for Lantern."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

RuntimeSurfaceClassification = str
GovernanceMode = str
LifecyclePlacementKind = str


@dataclass(frozen=True)
class LifecyclePlacement:
    kind: LifecyclePlacementKind
    covered_gates: Tuple[str, ...] = ()
    start_gate: Optional[str] = None
    end_gate: Optional[str] = None


@dataclass(frozen=True)
class WorkflowSurface:
    allowed_transaction_kinds: Tuple[str, ...]
    draftable_artifact_families: Tuple[str, ...]
    contract_refs: Tuple[str, ...]
    inspect_views: Tuple[str, ...]


@dataclass(frozen=True)
class WorkbenchDeclaration:
    workbench_id: str
    display_name: str
    lifecycle_placement: LifecyclePlacement
    artifacts_in_scope: Tuple[str, ...]
    intent_classes: Tuple[str, ...]
    posture_constraints: Tuple[str, ...]
    workflow_surface: WorkflowSurface
    instruction_resource: str
    authoritative_guides: Tuple[str, ...]
    administration_guides: Tuple[str, ...]
    entry_conditions: Tuple[str, ...]
    exit_conditions: Tuple[str, ...]
    source: str
    enabled: bool
    governance_mode: GovernanceMode
    content_hash: str


@dataclass(frozen=True)
class WorkbenchRegistry:
    runtime_surface_classification: RuntimeSurfaceClassification
    workbenches: Tuple[WorkbenchDeclaration, ...]

    def ids(self) -> Tuple[str, ...]:
        return tuple(workbench.workbench_id for workbench in self.workbenches)

    def get(self, workbench_id: str) -> WorkbenchDeclaration:
        for workbench in self.workbenches:
            if workbench.workbench_id == workbench_id:
                return workbench
        raise KeyError(workbench_id)


@dataclass(frozen=True)
class NameViolation:
    path: str
    line_number: int
    line_text: str
