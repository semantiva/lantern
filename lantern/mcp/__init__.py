"""Lantern MCP execution surface."""

from __future__ import annotations

from lantern.mcp.catalog import (
    FIXED_TOOL_SURFACE,
    build_catalog_response,
    build_contract_response,
    filter_resources_for_workbench,
    get_allowed_roles_for_transaction,
)
from lantern.mcp.inspect import (
    InspectCatalogResult,
    InspectContractResult,
    InspectError,
    InspectWorkspaceResult,
    handle_inspect,
)
from lantern.mcp.orient import OrientResponse, handle_orient
from lantern.mcp.topology import TopologyPosture, resolve_topology

__all__ = [
    "FIXED_TOOL_SURFACE",
    "InspectCatalogResult",
    "InspectContractResult",
    "InspectError",
    "InspectWorkspaceResult",
    "OrientResponse",
    "TopologyPosture",
    "build_catalog_response",
    "build_contract_response",
    "filter_resources_for_workbench",
    "get_allowed_roles_for_transaction",
    "handle_inspect",
    "handle_orient",
    "resolve_topology",
]
