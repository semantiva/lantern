"""Validate handler for CH-0004 scope-driven verification."""

from __future__ import annotations

from pathlib import Path

from lantern.mcp.transactions import TransactionEngine
from lantern.workflow.loader import WorkflowLayer


def handle_validate(
    *,
    workflow_layer: WorkflowLayer,
    scope: str,
    product_root: Path,
    governance_root: Path | None,
    draft_id: str | None = None,
    artifact_path: str | None = None,
    transaction_id: str | None = None,
) -> dict[str, object]:
    engine = TransactionEngine(
        workflow_layer=workflow_layer,
        product_root=product_root,
        governance_root=governance_root,
    )
    return engine.validate(
        scope=scope,
        draft_id=draft_id,
        artifact_path=artifact_path,
        transaction_id=transaction_id,
    )
