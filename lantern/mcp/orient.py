"""Orient tool handler for the Lantern MCP surface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from lantern.mcp.catalog import (
    filter_resources_for_workbench,
    get_allowed_roles_for_transaction,
)
from lantern.workflow.loader import WorkflowLayer
from lantern.workflow.resolver import (
    ResolvedWorkbenchSet,
    ResolverAmbiguityError,
    resolve_active_workbenches,
)

_ORIENT_TRANSACTION_KIND = "orient"


@dataclass(frozen=True)
class OrientResponse:
    active_workbench_ids: tuple[str, ...]
    preferred_workbench_id: Optional[str]
    surface_classification: str
    blockers: tuple[str, ...]
    preconditions: tuple[str, ...]
    runtime_exposure_posture: dict[str, Any]
    next_valid_actions: tuple[str, ...]
    ambiguity: Optional[dict[str, Any]]


def handle_orient(
    *,
    workflow_layer: WorkflowLayer,
    governance_state: dict[str, Any],
    intent: Optional[str] = None,
    ch_id: Optional[str] = None,
) -> OrientResponse:
    try:
        resolved: ResolvedWorkbenchSet = resolve_active_workbenches(
            workflow_layer=workflow_layer,
            governance_state=governance_state,
            intent=intent,
            ch_id=ch_id,
        )
    except ResolverAmbiguityError as exc:
        return OrientResponse(
            active_workbench_ids=(),
            preferred_workbench_id=None,
            surface_classification=workflow_layer.runtime_surface_classification,
            blockers=(),
            preconditions=(),
            runtime_exposure_posture={"status": "ambiguous"},
            next_valid_actions=(),
            ambiguity={
                "error": "multi_ch_ambiguity",
                "detail": str(exc),
                "resolution": "provide explicit ch_id to orient",
            },
        )

    runtime_exposure = _build_runtime_exposure(
        workflow_layer=workflow_layer,
        resolved=resolved,
    )

    return OrientResponse(
        active_workbench_ids=resolved.active_workbench_ids,
        preferred_workbench_id=resolved.preferred_workbench_id,
        surface_classification=resolved.runtime_surface_classification,
        blockers=resolved.blockers,
        preconditions=resolved.preconditions,
        runtime_exposure_posture=runtime_exposure,
        next_valid_actions=resolved.next_valid_actions,
        ambiguity=None,
    )


def _build_runtime_exposure(
    *,
    workflow_layer: WorkflowLayer,
    resolved: ResolvedWorkbenchSet,
) -> dict[str, Any]:
    exposure: dict[str, Any] = {
        "surface_classification": resolved.runtime_surface_classification,
        "workbenches": [],
    }
    for workbench_id in resolved.active_workbench_ids:
        try:
            workbench = workflow_layer.get_workbench(workbench_id)
        except KeyError:
            continue
        allowed_roles = get_allowed_roles_for_transaction(workbench, _ORIENT_TRANSACTION_KIND)
        resources = filter_resources_for_workbench(
            workflow_layer, workbench_id, allowed_roles
        )
        exposure["workbenches"].append(
            {
                "workbench_id": workbench_id,
                "allowed_roles": list(allowed_roles),
                "resources": resources,
                "contract_refs": list(workbench.contract_refs),
                "inspect_views": list(workbench.inspect_views),
            }
        )
    return exposure
