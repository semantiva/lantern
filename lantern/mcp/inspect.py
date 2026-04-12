"""Inspect tool handler for the Lantern MCP surface."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional

from lantern.artifacts.validator import DEFAULT_STATUS_CONTRACT_PATH, load_status_contract
from lantern.artifacts.render_contracts import build_two_layer_contract
from lantern.mcp.catalog import (
    build_catalog_response,
    build_contract_response,
    build_resource_packets_for_workbench,
    filter_resources_for_workbench,
    get_allowed_roles_for_transaction,
)
from lantern.mcp.topology import TopologyPosture, resolve_topology
from lantern.mcp.transactions import ChangeSurface, TransactionEngine, TransactionError
from lantern.workflow.loader import WorkflowLayer
from lantern.workflow.merger import PostureResult, build_runtime_posture_label


class InspectError(ValueError):
    """Raised when an inspect request cannot be satisfied within its contract."""


@dataclass(frozen=True)
class InspectCatalogResult:
    kind: str
    tools: tuple[str, ...]
    runtime_surface_classification: str
    workbench_count: int
    contract_refs: tuple[str, ...]
    runtime_posture: dict[str, Any]


@dataclass(frozen=True)
class InspectContractResult:
    kind: str
    contract_ref: str
    request_schema_ref: str
    transaction_kind: str
    workbench_refs: tuple[str, ...]
    family_binding: tuple[str, ...]
    gate_binding: tuple[str, ...]
    resource_refs: tuple[str, ...]
    resource_packets: tuple[dict[str, Any], ...]
    response_surface_bindings: tuple[dict[str, Any], ...]
    server_owned_contract: dict[str, Any]
    workflow_owned_contract: dict[str, Any]
    runtime_posture: dict[str, Any]


@dataclass(frozen=True)
class InspectWorkspaceResult:
    kind: str
    product_root: str
    governance_root: Optional[str]
    runtime_surface_classification: str
    consistency_state: str
    startup_issues: tuple[str, ...]
    read_only: bool
    runtime_posture: dict[str, Any]


@dataclass(frozen=True)
class InspectStatusContractResult:
    kind: str
    projection_path: str
    authoritative_source_path: str
    projection_sha256: str
    families: dict[str, Any]
    runtime_posture: dict[str, Any]


@dataclass(frozen=True)
class InspectChangeSurfaceResult:
    kind: str
    workbench_id: str
    contract_ref: str
    ci_path: str
    product_root: str
    governance_root: Optional[str]
    allowed_change_surface: tuple[str, ...]
    runtime_managed_change_surface: tuple[str, ...]
    change_surface_hash: str
    runtime_posture: dict[str, Any]


def handle_inspect(
    *,
    kind: str,
    workflow_layer: WorkflowLayer,
    workbench_id: Optional[str] = None,
    contract_ref: Optional[str] = None,
    product_root: Optional[Path] = None,
    governance_root: Optional[Path] = None,
    ci_path: Optional[str] = None,
    posture_result: Optional[PostureResult] = None,
) -> (
    InspectCatalogResult
    | InspectContractResult
    | InspectWorkspaceResult
    | InspectStatusContractResult
    | InspectChangeSurfaceResult
):
    _rp = _default_runtime_posture_label(workflow_layer, posture_result)
    if kind == "catalog":
        return _handle_catalog(workflow_layer, _rp)
    if kind == "contract":
        return _handle_contract(workflow_layer, contract_ref, _rp)
    if kind == "workspace":
        return _handle_workspace(product_root, governance_root, _rp)
    if kind == "status_contract":
        return _handle_status_contract(_rp)
    if kind == "change_surface":
        return _handle_change_surface(
            workflow_layer=workflow_layer,
            workbench_id=workbench_id,
            product_root=product_root,
            governance_root=governance_root,
            ci_path=ci_path,
            runtime_posture=_rp,
        )

    declared_views: set[str] = set()
    for workbench in workflow_layer.workbenches:
        declared_views.update(workbench.inspect_views)

    raise InspectError(
        f"inspect kind {kind!r} is not in any workbench's declared inspect_views "
        f"({sorted(declared_views)}). Only governed inspect kinds are permitted."
    )


def _handle_catalog(workflow_layer: WorkflowLayer, runtime_posture: dict[str, Any]) -> InspectCatalogResult:
    resp = build_catalog_response(workflow_layer)
    return InspectCatalogResult(
        kind="catalog",
        tools=resp.tools,
        runtime_surface_classification=resp.runtime_surface_classification,
        workbench_count=resp.workbench_count,
        contract_refs=resp.contract_refs,
        runtime_posture=runtime_posture,
    )


def _handle_contract(
    workflow_layer: WorkflowLayer,
    contract_ref: Optional[str],
    runtime_posture: dict[str, Any],
) -> InspectContractResult:
    if not contract_ref:
        raise InspectError("inspect(kind='contract') requires a non-empty contract_ref")
    try:
        resp = build_contract_response(workflow_layer, contract_ref)
    except KeyError as exc:
        raise InspectError(str(exc)) from exc
    layers = build_two_layer_contract(
        next(entry for entry in workflow_layer.contract_catalog if entry.contract_ref == contract_ref)
    )
    workbench = workflow_layer.get_workbench(resp.workbench_refs[0])
    allowed_roles = get_allowed_roles_for_transaction(workbench, "inspect")
    resources = filter_resources_for_workbench(
        workflow_layer=workflow_layer,
        workbench_id=workbench.workbench_id,
        allowed_roles=allowed_roles,
    )
    resource_refs = tuple(item["resource_id"] for item in resources)
    resource_packets = tuple(
        build_resource_packets_for_workbench(
            workflow_layer=workflow_layer,
            workbench_id=workbench.workbench_id,
            allowed_roles=allowed_roles,
        )
    )
    workflow_owned_contract = dict(layers["workflow_owned_contract"])
    workflow_owned_contract.pop("guide_refs", None)
    workflow_owned_contract["resource_refs"] = list(resource_refs)
    return InspectContractResult(
        kind="contract",
        contract_ref=resp.contract_ref,
        request_schema_ref=resp.request_schema_ref,
        transaction_kind=resp.transaction_kind,
        workbench_refs=resp.workbench_refs,
        family_binding=resp.family_binding,
        gate_binding=resp.gate_binding,
        resource_refs=resource_refs,
        resource_packets=resource_packets,
        response_surface_bindings=resp.response_surface_bindings,
        server_owned_contract=layers["server_owned_contract"],
        workflow_owned_contract=workflow_owned_contract,
        runtime_posture=runtime_posture,
    )


def _handle_workspace(
    product_root: Optional[Path],
    governance_root: Optional[Path],
    runtime_posture: dict[str, Any],
) -> InspectWorkspaceResult:
    if product_root is None:
        raise InspectError(
            "inspect(kind='workspace') requires an explicit product_root; "
            "the MCP server must be started with --product-root and does not use a default path"
        )
    posture: TopologyPosture = resolve_topology(
        product_root=product_root,
        governance_root=governance_root,
    )
    return InspectWorkspaceResult(
        kind="workspace",
        product_root=str(posture.product_root),
        governance_root=str(posture.governance_root) if posture.governance_root else None,
        runtime_surface_classification=posture.runtime_surface_classification,
        consistency_state=posture.consistency_state,
        startup_issues=posture.startup_issues,
        read_only=posture.read_only,
        runtime_posture=runtime_posture,
    )


def _handle_status_contract(runtime_posture: dict[str, Any]) -> InspectStatusContractResult:
    payload = load_status_contract()
    raw = DEFAULT_STATUS_CONTRACT_PATH.read_text(encoding="utf-8")
    return InspectStatusContractResult(
        kind="status_contract",
        projection_path="lantern/workflow/definitions/artifact_status_contract.json",
        authoritative_source_path=str(payload["generated_from"]["authoritative_path"]),
        projection_sha256=sha256(raw.encode("utf-8")).hexdigest(),
        families=dict(payload["families"]),
        runtime_posture=runtime_posture,
    )


def _handle_change_surface(
    *,
    workflow_layer: WorkflowLayer,
    workbench_id: Optional[str],
    product_root: Optional[Path],
    governance_root: Optional[Path],
    ci_path: Optional[str],
    runtime_posture: dict[str, Any],
) -> InspectChangeSurfaceResult:
    if product_root is None:
        raise InspectError("inspect(kind='change_surface') requires an explicit product_root")
    if not workbench_id:
        raise InspectError("inspect(kind='change_surface') requires a non-empty workbench_id")
    if not ci_path:
        raise InspectError("inspect(kind='change_surface') requires a ci_path for selected_ci_application")
    engine = TransactionEngine(
        workflow_layer=workflow_layer,
        product_root=product_root,
        governance_root=governance_root,
    )
    try:
        posture: ChangeSurface = engine.inspect_change_surface(
            workbench_id=workbench_id,
            ci_path=ci_path,
        )
    except TransactionError as exc:
        raise InspectError(str(exc)) from exc
    return InspectChangeSurfaceResult(
        kind="change_surface",
        workbench_id=posture.workbench_id,
        contract_ref=posture.contract_ref,
        ci_path=posture.ci_path,
        product_root=posture.product_root,
        governance_root=posture.governance_root,
        allowed_change_surface=posture.allowed_change_surface,
        runtime_managed_change_surface=posture.runtime_managed_change_surface,
        change_surface_hash=posture.change_surface_hash,
        runtime_posture=runtime_posture,
    )


def _default_runtime_posture_label(
    workflow_layer: WorkflowLayer,
    posture_result: Optional[PostureResult],
) -> dict[str, Any]:
    """Return a runtime_posture block from posture_result, or a minimal default block."""
    if posture_result is not None:
        return build_runtime_posture_label(posture_result)
    from lantern.workflow.merger import MergeProvenance, PostureResult as _PostureResult

    default_pr = _PostureResult(
        classification=workflow_layer.runtime_surface_classification,
        bounded_scope_markers=(),
        restricted_capabilities=(),
        provenance=MergeProvenance(
            baseline_version=workflow_layer.grammar_version or "unknown",
            configuration_folder=None,
            main_yaml_hash=None,
            launcher_overlay_folder=None,
            launcher_overlay_hash=None,
        ),
    )
    return build_runtime_posture_label(default_pr)
