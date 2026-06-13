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
from lantern.workflow.charter import CharterLoadError, get_layer_bodies, load_charter
from lantern.workflow.loader import WorkflowLayer

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
        result = engine.commit_selected_ci_application(
            workbench_id=workbench_id,
            payload=payload,
            actor=actor,
        )
    else:
        hold_lock_seconds = 0.0
        if isinstance(payload, Mapping):
            hold_lock_seconds = float(payload.get("hold_lock_seconds", 0.0))
        result = engine.commit_governance(
            workbench_id=workbench_id,
            draft_id=draft_id,
            actor=actor,
            hold_lock_seconds=hold_lock_seconds,
        )
    workbench = workflow_layer.get_workbench(workbench_id)
    bodies = _load_charter_layer_bodies(workbench.charter_ref, "commit")
    if bodies:
        result["charter_layer_bodies"] = bodies
    return result


def _load_charter_layer_bodies(charter_ref: str, moment: str) -> list[dict[str, str]]:
    if not charter_ref:
        return []
    charter_path = _REPO_ROOT / charter_ref
    try:
        charter = load_charter(charter_path)
        return get_layer_bodies(charter, moment)
    except (CharterLoadError, OSError):
        return []
