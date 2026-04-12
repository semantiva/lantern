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
