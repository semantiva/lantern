"""Logical-ref-first contract and resource discovery for Lantern inspect and orient responses."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from lantern.workflow.loader import WorkflowLayer, WorkflowWorkbench

FIXED_TOOL_SURFACE: tuple[str, ...] = (
    "inspect",
    "orient",
    "draft",
    "commit",
    "validate",
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


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


def build_contract_response(workflow_layer: WorkflowLayer, contract_ref: str) -> ContractResponse:
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


def get_allowed_roles_for_transaction(workbench: WorkflowWorkbench, transaction_kind: str) -> tuple[str, ...]:
    for binding in workbench.response_surface_bindings:
        if binding.transaction_kind == transaction_kind:
            return binding.allowed_resource_roles
    return ()


def _sanitize_identifier(value: str) -> str:
    value = value.lower().replace("-", "_")
    value = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)
    while "__" in value:
        value = value.replace("__", "_")
    return value.strip("_")


def _content_format(rel_path: str) -> str:
    suffix = Path(rel_path).suffix.lower()
    if suffix == ".md":
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    return "text"


def _load_text(rel_path: str) -> str:
    return (_REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _resource_title(body: str, rel_path: str) -> str:
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return Path(rel_path).stem


def _template_rel_path(family: str) -> str:
    return f"lantern/templates/TEMPLATE__{family}.md"


def _template_resource_id(workbench_id: str, family: str) -> str:
    name = _sanitize_identifier(f"{workbench_id}_artifact_templates_TEMPLATE__{family}")
    return f"resource.template.{name}"


def _template_summaries(workbench: WorkflowWorkbench) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for family in workbench.draftable_artifact_families:
        rel_path = _template_rel_path(family)
        if not (_REPO_ROOT / rel_path).exists():
            continue
        result.append(
            {
                "resource_id": _template_resource_id(workbench.workbench_id, family),
                "kind": "template",
                "roles": ["artifact_templates"],
            }
        )
    return result


def _template_packets(workbench: WorkflowWorkbench) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for family in workbench.draftable_artifact_families:
        rel_path = _template_rel_path(family)
        abs_path = _REPO_ROOT / rel_path
        if not abs_path.exists():
            continue
        body = abs_path.read_text(encoding="utf-8")
        packets.append(
            {
                "resource_id": _template_resource_id(workbench.workbench_id, family),
                "kind": "template",
                "roles": ["artifact_templates"],
                "content_format": _content_format(rel_path),
                "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "title": _resource_title(body, rel_path),
                "body": body,
            }
        )
    return packets


def filter_resources_for_workbench(
    workflow_layer: WorkflowLayer,
    workbench_id: str,
    allowed_roles: tuple[str, ...],
) -> list[dict[str, Any]]:
    allowed_set = set(allowed_roles)
    result: list[dict[str, Any]] = []
    workbench = workflow_layer.get_workbench(workbench_id)
    for entry in workflow_layer.resource_manifest:
        if entry.workbench_id != workbench_id:
            continue
        filtered = [role for role in entry.roles if role in allowed_set]
        if not filtered:
            continue
        result.append(
            {
                "resource_id": entry.resource_id,
                "kind": entry.kind,
                "roles": filtered,
            }
        )
    if "artifact_templates" in allowed_set:
        result.extend(_template_summaries(workbench))
    return sorted(result, key=lambda item: item["resource_id"])


def build_resource_packets_for_workbench(
    workflow_layer: WorkflowLayer,
    workbench_id: str,
    allowed_roles: tuple[str, ...],
) -> list[dict[str, Any]]:
    allowed_set = set(allowed_roles)
    packets: list[dict[str, Any]] = []
    workbench = workflow_layer.get_workbench(workbench_id)
    for entry in workflow_layer.resource_manifest:
        if entry.workbench_id != workbench_id:
            continue
        filtered = [role for role in entry.roles if role in allowed_set]
        if not filtered:
            continue
        body = _load_text(entry.path)
        packets.append(
            {
                "resource_id": entry.resource_id,
                "kind": entry.kind,
                "roles": filtered,
                "content_format": _content_format(entry.path),
                "content_sha256": entry.content_hash,
                "title": _resource_title(body, entry.path),
                "body": body,
            }
        )
    if "artifact_templates" in allowed_set:
        packets.extend(_template_packets(workbench))
    return sorted(packets, key=lambda item: item["resource_id"])
