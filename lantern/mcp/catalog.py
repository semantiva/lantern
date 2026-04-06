"""Narrow contract and resource discovery for Lantern inspect and orient responses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from lantern.workflow.loader import WorkflowLayer, WorkflowWorkbench

FIXED_TOOL_SURFACE: tuple[str, ...] = (
    "inspect",
    "orient",
    "draft",
    "commit",
    "validate",
)


@dataclass(frozen=True)
class CatalogResponse:
    tools: tuple[str, ...]
    runtime_surface_classification: str
    workbench_count: int
    contract_refs: tuple[str, ...]


@dataclass(frozen=True)
class ContractResponse:
    contract_ref: str
    request_schema_ref: str
    transaction_kind: str
    workbench_refs: tuple[str, ...]
    family_binding: tuple[str, ...]
    gate_binding: tuple[str, ...]
    guide_refs: tuple[str, ...]
    response_surface_bindings: tuple[dict[str, Any], ...]
    compatibility: Mapping[str, Any]
    provenance: Mapping[str, Any]


def build_catalog_response(workflow_layer: WorkflowLayer) -> CatalogResponse:
    refs = tuple(sorted({entry.contract_ref for entry in workflow_layer.contract_catalog}))
    return CatalogResponse(
        tools=FIXED_TOOL_SURFACE,
        runtime_surface_classification=workflow_layer.runtime_surface_classification,
        workbench_count=len(workflow_layer.workbenches),
        contract_refs=refs,
    )


def build_contract_response(
    workflow_layer: WorkflowLayer, contract_ref: str
) -> ContractResponse:
    for entry in workflow_layer.contract_catalog:
        if entry.contract_ref == contract_ref:
            return ContractResponse(
                contract_ref=entry.contract_ref,
                request_schema_ref=entry.request_schema_ref,
                transaction_kind=entry.transaction_kind,
                workbench_refs=entry.workbench_refs,
                family_binding=entry.family_binding,
                gate_binding=entry.gate_binding,
                guide_refs=entry.guide_refs,
                response_surface_bindings=tuple(
                    {
                        "transaction_kind": b.transaction_kind,
                        "response_envelope": b.response_envelope,
                        "allowed_resource_roles": list(b.allowed_resource_roles),
                    }
                    for b in entry.response_surface_bindings
                ),
                compatibility=entry.compatibility,
                provenance=entry.provenance,
            )
    raise KeyError(f"contract ref not found in catalog: {contract_ref!r}")


def get_allowed_roles_for_transaction(
    workbench: WorkflowWorkbench, transaction_kind: str
) -> tuple[str, ...]:
    for binding in workbench.response_surface_bindings:
        if binding.transaction_kind == transaction_kind:
            return binding.allowed_resource_roles
    return ()


def filter_resources_for_workbench(
    workflow_layer: WorkflowLayer,
    workbench_id: str,
    allowed_roles: tuple[str, ...],
) -> list[dict[str, Any]]:
    allowed_set = set(allowed_roles)
    result: list[dict[str, Any]] = []
    for entry in workflow_layer.resource_manifest:
        if entry.workbench_id != workbench_id:
            continue
        filtered = [r for r in entry.roles if r in allowed_set]
        if not filtered:
            continue
        result.append(
            {
                "resource_id": entry.resource_id,
                "kind": entry.kind,
                "path": entry.path,
                "roles": filtered,
            }
        )
    return result
