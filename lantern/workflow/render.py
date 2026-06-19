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

"""Human-readable workflow map rendering for user documentation."""

from __future__ import annotations

from lantern.workflow.loader import LifecyclePlacement, WorkflowLayer


def render_workflow_map(layer: WorkflowLayer) -> str:
    """Return a markdown workflow map for the given WorkflowLayer."""
    lines = [
        f"# Workflow map: {layer.selected_workflow_id}",
        "",
        f"Workflow ID: `{layer.selected_workflow_id}`",
        f"Display name: `{layer.selected_workflow_display_name}`",
        f"Runtime surface classification: `{layer.runtime_surface_classification}`",
        "",
        "| Workbench | Lifecycle placement | Transactions | Inspect views | Artifact families |",
        "|---|---|---|---|---|",
    ]
    for workbench in layer.workbenches:
        lines.append(
            "| {wb} | {placement} | {tx} | {views} | {families} |".format(
                wb=workbench.workbench_id,
                placement=_format_lifecycle(workbench.lifecycle_placement),
                tx=", ".join(workbench.allowed_transaction_kinds),
                views=", ".join(workbench.inspect_views) or "-",
                families=", ".join(workbench.artifacts_in_scope),
            )
        )
    return "\n".join(lines) + "\n"


def _format_lifecycle(placement: LifecyclePlacement) -> str:
    if placement.kind == "covered_gates":
        return f"covered_gates: {', '.join(placement.covered_gates)}"
    if placement.kind == "lifecycle_span":
        return f"lifecycle_span: {placement.start_gate} -> {placement.end_gate}"
    return placement.kind
