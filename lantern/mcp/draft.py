"""Draft handler for CH-0004 structured mutation flows."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from lantern.mcp.transactions import TransactionEngine
from lantern.workflow.loader import WorkflowLayer


def handle_draft(
    *,
    workflow_layer: WorkflowLayer,
    workbench_id: str,
    artifact_family: str,
    payload: Mapping[str, Any] | None,
    product_root: Path,
    governance_root: Path | None,
    contract_ref: str | None = None,
    actor: str = "operator",
) -> dict[str, Any]:
    workbench = workflow_layer.get_workbench(workbench_id)
    resolved_contract_ref = contract_ref or workbench.contract_refs[0]
    engine = TransactionEngine(
        workflow_layer=workflow_layer,
        product_root=product_root,
        governance_root=governance_root,
    )
    return engine.create_draft(
        workbench_id=workbench_id,
        artifact_family=artifact_family,
        payload=payload,
        contract_ref=resolved_contract_ref,
        actor=actor,
    )
