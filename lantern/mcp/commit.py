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

"""Commit handler for CH-0004 structured mutation flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from lantern.mcp.transactions import TransactionEngine
from lantern.workflow.loader import WorkflowLayer


def handle_commit(
    *,
    workflow_layer: WorkflowLayer,
    workbench_id: str,
    product_root: Path,
    governance_root: Path | None,
    draft_id: str | None = None,
    payload: Mapping[str, Any] | None = None,
    actor: str = "operator",
) -> dict[str, Any]:
    engine = TransactionEngine(
        workflow_layer=workflow_layer,
        product_root=product_root,
        governance_root=governance_root,
    )
    if workbench_id == "selected_ci_application":
        return engine.commit_selected_ci_application(
            workbench_id=workbench_id,
            payload=payload,
            actor=actor,
        )
    hold_lock_seconds = 0.0
    if isinstance(payload, Mapping):
        hold_lock_seconds = float(payload.get("hold_lock_seconds", 0.0))
    return engine.commit_governance(
        workbench_id=workbench_id,
        draft_id=draft_id,
        actor=actor,
        hold_lock_seconds=hold_lock_seconds,
    )
