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

"""Validate handler for CH-0004 scope-driven verification."""

from __future__ import annotations

from pathlib import Path

from lantern.mcp.transactions import TransactionEngine
from lantern.workflow.charter import CharterLoadError, get_layer_bodies, load_charter
from lantern.workflow.loader import WorkflowLayer

_REPO_ROOT = Path(__file__).resolve().parents[2]


def handle_validate(
    *,
    workflow_layer: WorkflowLayer,
    scope: str,
    product_root: Path,
    governance_root: Path | None,
    draft_id: str | None = None,
    artifact_path: str | None = None,
    transaction_id: str | None = None,
    workbench_id: str | None = None,
) -> dict[str, object]:
    engine = TransactionEngine(
        workflow_layer=workflow_layer,
        product_root=product_root,
        governance_root=governance_root,
    )
    result = engine.validate(
        scope=scope,
        draft_id=draft_id,
        artifact_path=artifact_path,
        transaction_id=transaction_id,
    )
    if workbench_id:
        workbench = workflow_layer.get_workbench(workbench_id)
        bodies = _load_charter_layer_bodies(workbench.charter_ref, "validate")
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
