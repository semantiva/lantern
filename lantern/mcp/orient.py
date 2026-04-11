"""Orient tool handler for the Lantern MCP surface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from lantern.mcp.catalog import (
    build_resource_packets_for_workbench,
    filter_resources_for_workbench,
    get_allowed_roles_for_transaction,
)
from lantern.workflow.loader import WorkflowLayer
from lantern.workflow.merger import PostureResult, build_runtime_posture_label
from lantern.workflow.resolver import (
    ResolvedWorkbenchSet,
    ResolverAmbiguityError,
    resolve_active_workbenches,
)

_ORIENT_TRANSACTION_KIND = "orient"
_ORIENT_DISCOVERY_SAFE_ROLES = frozenset(
    {"instruction_resource", "authoritative_guides", "artifact_templates"}
)


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
    runtime_posture: dict[str, Any]


def handle_orient(
    *,
    workflow_layer: WorkflowLayer,
    governance_state: dict[str, Any],
    intent: Optional[str] = None,
    ch_id: Optional[str] = None,
    posture_result: Optional[PostureResult] = None,
) -> OrientResponse:
    rp = _orient_runtime_posture_label(workflow_layer, posture_result)
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
            runtime_posture=rp,
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
        runtime_posture=rp,
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
        if not allowed_roles:
            allowed_roles = get_allowed_roles_for_transaction(workbench, "inspect")
        allowed_roles = tuple(
            role for role in allowed_roles if role in _ORIENT_DISCOVERY_SAFE_ROLES
        )
        resources = filter_resources_for_workbench(
            workflow_layer, workbench_id, allowed_roles
        )
        resource_packets = build_resource_packets_for_workbench(
            workflow_layer=workflow_layer,
            workbench_id=workbench_id,
            allowed_roles=allowed_roles,
        )
        exposure["workbenches"].append(
            {
                "workbench_id": workbench_id,
                "allowed_roles": list(allowed_roles),
                "resources": resources,
                "resource_packets": resource_packets,
                "contract_refs": list(workbench.contract_refs),
                "inspect_views": list(workbench.inspect_views),
            }
        )
    return exposure


def _orient_runtime_posture_label(
    workflow_layer: WorkflowLayer,
    posture_result: Optional[PostureResult],
) -> dict[str, Any]:
    if posture_result is not None:
        return build_runtime_posture_label(posture_result)
    from lantern.workflow.merger import MergeProvenance, PostureResult as _PostureResult
    default_pr = _PostureResult(
        classification=workflow_layer.runtime_surface_classification,
        bounded_scope_markers=(),
        restricted_capabilities=(),
        provenance=MergeProvenance(
            baseline_version="unknown",
            configuration_folder=None,
            main_yaml_hash=None,
            launcher_overlay_folder=None,
            launcher_overlay_hash=None,
        ),
    )
    return build_runtime_posture_label(default_pr)
