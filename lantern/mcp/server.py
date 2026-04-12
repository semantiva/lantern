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

"""MCP server registration and routing for Lantern."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover

    class _Tool:
        def __init__(self, func):
            self.func = func
            self.name = func.__name__

    class FastMCP:  # type: ignore[no-redef]
        def __init__(self, name: str):
            self.name = name
            self._tools: list[_Tool] = []

        def tool(self):
            def decorator(func):
                self._tools.append(_Tool(func))
                return func

            return decorator

        async def list_tools(self):
            return tuple(self._tools)

        def run(self):
            raise RuntimeError("mcp package not installed")


from lantern.mcp.commit import handle_commit
from lantern.mcp.draft import handle_draft
from lantern.mcp.inspect import handle_inspect
from lantern.mcp.orient import handle_orient
from lantern.mcp.validate import handle_validate
from lantern.mcp.transactions import configure_posture_result as _configure_posture_result
from lantern.workflow.loader import WorkflowLayer, load_effective_layer, load_workflow_layer
from lantern.workflow.merger import (
    ConfigurationMerger,
    EffectiveLayer,
    PostureResult,
    PostureValidator,
)

mcp = FastMCP("lantern")
_workflow_layer: Optional[WorkflowLayer] = None
_effective_layer: Optional[EffectiveLayer] = None
_posture_result: Optional[PostureResult] = None
_product_root: Optional[Path] = None
_governance_root: Optional[Path] = None


def configure_server_paths(
    *,
    product_root: Path,
    governance_root: Optional[Path] = None,
) -> None:
    global _product_root, _governance_root, _workflow_layer, _effective_layer, _posture_result
    _product_root = Path(product_root).resolve()
    _governance_root = Path(governance_root).resolve() if governance_root is not None else None
    _workflow_layer = None
    _effective_layer = None
    _posture_result = None


def _get_workflow_layer() -> WorkflowLayer:
    global _workflow_layer, _effective_layer, _posture_result
    if _workflow_layer is None:
        _workflow_layer = load_workflow_layer()
        _effective_layer, _posture_result = _run_startup_sequence(_workflow_layer)
        _configure_posture_result(_posture_result)
    return _workflow_layer


def _run_startup_sequence(
    workflow_layer: WorkflowLayer,
) -> tuple[EffectiveLayer, PostureResult]:
    """Execute the ordered startup validation sequence before any MCP tool responds."""
    from lantern.artifacts.validator import load_status_contract

    effective_layer = load_effective_layer(
        workflow_layer=workflow_layer,
        configuration_root=_governance_root,
    )

    status_contract = load_status_contract()
    validator = PostureValidator()
    posture_result = validator.validate(
        effective_layer=effective_layer,
        workflow_layer=workflow_layer,
        status_contract=status_contract,
    )

    merger = ConfigurationMerger()
    merger.validate_guide_consistency(
        effective_layer=effective_layer,
        workflow_layer=workflow_layer,
    )

    return effective_layer, posture_result


def _get_posture_result() -> PostureResult:
    """Return the current session PostureResult; triggers startup sequence if not yet run."""
    _get_workflow_layer()
    assert _posture_result is not None
    return _posture_result


def _require_product_root() -> Path:
    if _product_root is None:
        raise RuntimeError("server paths not configured")
    return _product_root


@mcp.tool()
def inspect(
    kind: str,
    contract_ref: str = "",
    workbench_id: str = "",
    ci_path: str = "",
) -> dict[str, Any]:
    result = handle_inspect(
        kind=kind,
        workflow_layer=_get_workflow_layer(),
        workbench_id=workbench_id or None,
        contract_ref=contract_ref or None,
        product_root=_product_root,
        governance_root=_governance_root,
        ci_path=ci_path or None,
        posture_result=_get_posture_result(),
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
        posture_result=_get_posture_result(),
    )
    return _to_dict(result)


@mcp.tool()
def draft(
    workbench_id: str,
    artifact_family: str,
    payload: str = "{}",
    contract_ref: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    result = handle_draft(
        workflow_layer=_get_workflow_layer(),
        workbench_id=workbench_id,
        artifact_family=artifact_family,
        payload=_parse_payload(payload),
        product_root=_require_product_root(),
        governance_root=_governance_root,
        contract_ref=contract_ref or None,
        actor=actor,
    )
    return _to_dict(result)


@mcp.tool()
def commit(
    workbench_id: str,
    draft_id: str = "",
    payload: str = "{}",
    actor: str = "operator",
) -> dict[str, Any]:
    result = handle_commit(
        workflow_layer=_get_workflow_layer(),
        workbench_id=workbench_id,
        draft_id=draft_id or None,
        payload=_parse_payload(payload),
        product_root=_require_product_root(),
        governance_root=_governance_root,
        actor=actor,
    )
    return _to_dict(result)


@mcp.tool()
def validate(
    scope: str,
    draft_id: str = "",
    artifact_path: str = "",
    transaction_id: str = "",
) -> dict[str, Any]:
    result = handle_validate(
        workflow_layer=_get_workflow_layer(),
        scope=scope,
        draft_id=draft_id or None,
        artifact_path=artifact_path or None,
        transaction_id=transaction_id or None,
        product_root=_require_product_root(),
        governance_root=_governance_root,
    )
    return _to_dict(result)


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


def _parse_payload(raw: str) -> Mapping[str, Any] | None:
    if not raw.strip():
        return {}
    payload = json.loads(raw)
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ValueError("payload must decode to a JSON object")
    return payload


def _to_dict(obj: Any) -> dict[str, Any]:
    if is_dataclass(obj) and not isinstance(obj, type):
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
        parser.error(f"--governance-root does not exist or is not a directory: {args.governance_root}")
    configure_server_paths(
        product_root=args.product_root,
        governance_root=args.governance_root,
    )
    mcp.run()


if __name__ == "__main__":
    main()
