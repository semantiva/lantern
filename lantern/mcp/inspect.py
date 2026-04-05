"""Inspect tool handler for the Lantern MCP surface."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from lantern.mcp.catalog import build_catalog_response, build_contract_response
from lantern.mcp.topology import TopologyPosture, resolve_topology
from lantern.workflow.loader import WorkflowLayer


class InspectError(ValueError):
    """Raised when an inspect request cannot be satisfied within its contract."""


@dataclass(frozen=True)
class InspectCatalogResult:
    kind: str
    tools: tuple[str, ...]
    runtime_surface_classification: str
    workbench_count: int
    contract_refs: tuple[str, ...]


@dataclass(frozen=True)
class InspectContractResult:
    kind: str
    contract_ref: str
    transaction_kind: str
    workbench_refs: tuple[str, ...]
    family_binding: tuple[str, ...]
    gate_binding: tuple[str, ...]
    response_surface_bindings: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class InspectWorkspaceResult:
    kind: str
    product_root: str
    governance_root: Optional[str]
    runtime_surface_classification: str
    consistency_state: str
    startup_issues: tuple[str, ...]
    read_only: bool


def handle_inspect(
    *,
    kind: str,
    workflow_layer: WorkflowLayer,
    workbench_id: Optional[str] = None,
    contract_ref: Optional[str] = None,
    product_root: Optional[Path] = None,
    governance_root: Optional[Path] = None,
) -> InspectCatalogResult | InspectContractResult | InspectWorkspaceResult:
    del workbench_id
    if kind == "catalog":
        return _handle_catalog(workflow_layer)
    if kind == "contract":
        return _handle_contract(workflow_layer, contract_ref)
    if kind == "workspace":
        return _handle_workspace(product_root, governance_root)

    declared_views: set[str] = set()
    for workbench in workflow_layer.workbenches:
        declared_views.update(workbench.inspect_views)

    raise InspectError(
        f"inspect kind {kind!r} is not in any workbench's declared inspect_views "
        f"({sorted(declared_views)}). Only governed inspect kinds are permitted."
    )


def _handle_catalog(workflow_layer: WorkflowLayer) -> InspectCatalogResult:
    resp = build_catalog_response(workflow_layer)
    return InspectCatalogResult(
        kind="catalog",
        tools=resp.tools,
        runtime_surface_classification=resp.runtime_surface_classification,
        workbench_count=resp.workbench_count,
        contract_refs=resp.contract_refs,
    )


def _handle_contract(
    workflow_layer: WorkflowLayer,
    contract_ref: Optional[str],
) -> InspectContractResult:
    if not contract_ref:
        raise InspectError("inspect(kind='contract') requires a non-empty contract_ref")
    try:
        resp = build_contract_response(workflow_layer, contract_ref)
    except KeyError as exc:
        raise InspectError(str(exc)) from exc
    return InspectContractResult(
        kind="contract",
        contract_ref=resp.contract_ref,
        transaction_kind=resp.transaction_kind,
        workbench_refs=resp.workbench_refs,
        family_binding=resp.family_binding,
        gate_binding=resp.gate_binding,
        response_surface_bindings=resp.response_surface_bindings,
    )


def _handle_workspace(
    product_root: Optional[Path],
    governance_root: Optional[Path] = None,
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
    )
