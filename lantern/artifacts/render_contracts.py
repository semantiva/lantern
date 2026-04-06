"""Server-owned mutation contract surfaces for CH-0004."""
from __future__ import annotations

from typing import Any

from lantern.workflow.loader import ContractCatalogEntry

_VALIDATION_SCOPES = ("workspace", "draft", "artifact", "transaction")


def _draft_request_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["artifact_family", "payload"],
        "properties": {
            "artifact_family": {"type": "string"},
            "payload": {
                "type": "object",
                "required": ["header", "title", "sections"],
                "properties": {
                    "header": {"type": "object"},
                    "title": {"type": "string"},
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["heading", "body"],
                            "properties": {
                                "heading": {"type": "string"},
                                "body": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    }


def _selected_ci_commit_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["ci_path", "operations"],
        "properties": {
            "ci_path": {"type": "string"},
            "operations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["path", "content"],
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "hold_lock_seconds": {"type": "number"},
                    },
                },
            },
        },
    }


def _generic_commit_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["draft_id"],
        "properties": {
            "draft_id": {"type": "string"},
            "hold_lock_seconds": {"type": "number"},
        },
    }


def _validate_request_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["scope"],
        "properties": {
            "scope": {"enum": list(_VALIDATION_SCOPES)},
            "draft_id": {"type": "string"},
            "artifact_path": {"type": "string"},
            "transaction_id": {"type": "string"},
        },
    }


def build_server_owned_contract(entry: ContractCatalogEntry) -> dict[str, Any]:
    mutation_kinds = {binding.transaction_kind for binding in entry.response_surface_bindings}
    request_schemas: dict[str, Any] = {}
    if "draft" in mutation_kinds:
        request_schemas["draft"] = _draft_request_schema()
    if "commit" in mutation_kinds:
        if entry.contract_ref == "contract.selected_ci_application.v1":
            request_schemas["commit"] = _selected_ci_commit_schema()
        else:
            request_schemas["commit"] = _generic_commit_schema()
    if "validate" in mutation_kinds:
        request_schemas["validate"] = _validate_request_schema()

    return {
        "structured_input_only": True,
        "raw_markdown_client_input_allowed": False,
        "request_schemas": request_schemas,
        "preview_surface": "canonical_markdown",
        "canonical_persistence": "governed_markdown_only",
        "lock_policy": "internal_transaction_lock",
        "journal_policy": "one_entry_per_successful_commit",
        "validation_scopes": list(_VALIDATION_SCOPES),
        "change_surface_preflight": entry.contract_ref == "contract.selected_ci_application.v1",
    }


def build_two_layer_contract(entry: ContractCatalogEntry) -> dict[str, Any]:
    return {
        "server_owned_contract": build_server_owned_contract(entry),
        "workflow_owned_contract": {
            "contract_ref": entry.contract_ref,
            "request_schema_ref": entry.request_schema_ref,
            "transaction_kind": entry.transaction_kind,
            "family_binding": list(entry.family_binding),
            "gate_binding": list(entry.gate_binding),
            "workbench_refs": list(entry.workbench_refs),
            "guide_refs": list(entry.guide_refs),
            "response_surface_bindings": [
                {
                    "transaction_kind": binding.transaction_kind,
                    "response_envelope": binding.response_envelope,
                    "allowed_resource_roles": list(binding.allowed_resource_roles),
                }
                for binding in entry.response_surface_bindings
            ],
        },
    }
