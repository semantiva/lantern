"""MCP server registration and routing for Lantern."""
from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    class _Tool:
        def __init__(self, func):
            self.func = func
            self.name = func.__name__

    class FastMCP:  # type: ignore[override]
        def __init__(self, name: str):
            self.name = name
            self._tools: list[_Tool] = []

        def tool(self):
            def decorator(func):
                self._tools.append(_Tool(func))
                return func
            return decorator

        def list_tools(self):
            return tuple(self._tools)

        def run(self):
            raise RuntimeError("mcp package not installed")

from lantern.mcp.inspect import handle_inspect
from lantern.mcp.orient import handle_orient
from lantern.workflow.loader import WorkflowLayer, load_workflow_layer

mcp = FastMCP("lantern")
_workflow_layer: Optional[WorkflowLayer] = None
_product_root: Optional[Path] = None
_governance_root: Optional[Path] = None


def configure_server_paths(
    *,
    product_root: Path,
    governance_root: Optional[Path] = None,
) -> None:
    global _product_root, _governance_root
    _product_root = Path(product_root).resolve()
    _governance_root = (
        Path(governance_root).resolve() if governance_root is not None else None
    )


def _get_workflow_layer() -> WorkflowLayer:
    global _workflow_layer
    if _workflow_layer is None:
        _workflow_layer = load_workflow_layer()
    return _workflow_layer


@mcp.tool()
def inspect(
    kind: str,
    contract_ref: str = "",
) -> dict[str, Any]:
    result = handle_inspect(
        kind=kind,
        workflow_layer=_get_workflow_layer(),
        contract_ref=contract_ref or None,
        product_root=_product_root,
        governance_root=_governance_root,
    )
    return _to_dict(result)


@mcp.tool()
def orient(
    intent: str = "",
    ch_id: str = "",
    active_gates: str = "",
    passed_gates: str = "",
    ch_statuses: str = "",
) -> dict[str, Any]:
    governance_state = _parse_governance_state(active_gates, passed_gates, ch_statuses)
    result = handle_orient(
        workflow_layer=_get_workflow_layer(),
        governance_state=governance_state,
        intent=intent or None,
        ch_id=ch_id or None,
    )
    return _to_dict(result)


@mcp.tool()
def draft(
    workbench_id: str,
    artifact_family: str,
    content: str = "",
) -> dict[str, Any]:
    del content
    return {
        "status": "not_implemented",
        "detail": "draft mutation behavior is delivered in CH-0004",
        "workbench_id": workbench_id,
        "artifact_family": artifact_family,
    }


@mcp.tool()
def commit(
    workbench_id: str,
    artifact_family: str,
    draft_id: str = "",
) -> dict[str, Any]:
    del draft_id
    return {
        "status": "not_implemented",
        "detail": "commit mutation behavior is delivered in CH-0004",
        "workbench_id": workbench_id,
        "artifact_family": artifact_family,
    }


@mcp.tool()
def validate(workbench_id: str) -> dict[str, Any]:
    return {
        "status": "not_implemented",
        "detail": "validate behavior is delivered in CH-0004",
        "workbench_id": workbench_id,
    }


def _parse_governance_state(
    active_gates_str: str,
    passed_gates_str: str,
    ch_statuses_str: str,
) -> dict[str, Any]:
    active_gates = [g.strip() for g in active_gates_str.split(",") if g.strip()]
    passed_gates = [g.strip() for g in passed_gates_str.split(",") if g.strip()]
    ch_statuses: dict[str, str] = {}
    for pair in ch_statuses_str.split(","):
        pair = pair.strip()
        if ":" in pair:
            ch, status = pair.split(":", 1)
            ch_statuses[ch.strip()] = status.strip()
    return {
        "ch_statuses": ch_statuses,
        "active_gates": active_gates,
        "passed_gates": passed_gates,
    }


def _to_dict(obj: Any) -> dict[str, Any]:
    if is_dataclass(obj):
        return asdict(obj)
    return dict(obj)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Lantern MCP server with explicit workspace paths. "
            "No default product or governance repository paths are assumed."
        )
    )
    parser.add_argument("--product-root", required=True, type=Path)
    parser.add_argument("--governance-root", type=Path)
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.product_root.is_dir():
        parser.error(f"--product-root does not exist or is not a directory: {args.product_root}")
    if args.governance_root is not None and not args.governance_root.is_dir():
        parser.error(
            f"--governance-root does not exist or is not a directory: {args.governance_root}"
        )
    configure_server_paths(
        product_root=args.product_root,
        governance_root=args.governance_root,
    )
    mcp.run()


if __name__ == "__main__":
    main()
