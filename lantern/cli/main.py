"""Human-first operational CLI for CH-0021."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence, TextIO

from lantern.bootstrap.manager import apply_bootstrap_plan, plan_bootstrap
from lantern.cli.context import ContextResolutionError, resolve_operational_context
from lantern.cli.doctor import gather_doctor_report
from lantern.discovery.registry import build_discovery_registry, list_records, show_record
from lantern.mcp.server import configure_server_paths, mcp as mcp_server


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    prog="lantern",
    description="Lantern operational CLI",
  )
  subparsers = parser.add_subparsers(dest="command", required=True)

  serve = subparsers.add_parser("serve", help="Start the bounded Lantern MCP server")
  serve.add_argument("--governance-root", type=Path, required=True)
  serve.add_argument("--product-root", type=Path)

  doctor = subparsers.add_parser("doctor", help="Report bounded diagnostics")
  doctor.add_argument("--governance-root", type=Path, required=True)
  doctor.add_argument("--product-root", type=Path)
  doctor.add_argument("--json", action="store_true", dest="json_output")

  bootstrap = subparsers.add_parser("bootstrap-product", help="Preview or apply bootstrap")
  bootstrap.add_argument("--governance-root", type=Path, required=True)
  bootstrap.add_argument("--product-root", type=Path, required=True)
  bootstrap.add_argument("--apply", action="store_true")
  bootstrap.add_argument("--json", action="store_true", dest="json_output")

  list_parser = subparsers.add_parser("list", help="List governed discovery records")
  list_parser.add_argument("--governance-root", type=Path, required=True)
  list_parser.add_argument("--product-root", type=Path)
  list_parser.add_argument("--id")
  list_parser.add_argument("--family")
  list_parser.add_argument("--title")
  list_parser.add_argument("--status")
  list_parser.add_argument("--gate")
  list_parser.add_argument("--mode")
  list_parser.add_argument("--workbench")
  list_parser.add_argument("--logical-ref")
  list_parser.add_argument("--heading")
  list_parser.add_argument("--json", action="store_true", dest="json_output")

  show = subparsers.add_parser("show", help="Show one exact governed discovery record")
  show.add_argument("token")
  show.add_argument("--governance-root", type=Path, required=True)
  show.add_argument("--product-root", type=Path)
  show.add_argument("--entity-kind")
  show.add_argument("--json", action="store_true", dest="json_output")

  return parser


def run_cli(
  argv: Sequence[str] | None = None,
  *,
  stdout: TextIO | None = None,
  stderr: TextIO | None = None,
  run_server: bool = True,
) -> int:
  stdout = stdout or sys.stdout
  stderr = stderr or sys.stderr
  parser = build_parser()
  args = parser.parse_args(list(argv) if argv is not None else None)

  try:
    if args.command == "serve":
      context = resolve_operational_context(
        governance_root=args.governance_root,
        supplied_product_root=args.product_root,
        allow_supplied_product_root=args.product_root is not None,
      )
      configure_server_paths(
        product_root=context.product_root,
        governance_root=context.governance_root,
      )
      if run_server:
        mcp_server.run()
      else:
        stdout.write(
          f"configured server roots: product={context.product_root} governance={context.governance_root}\n"
        )
      return 0

    if args.command == "doctor":
      context = resolve_operational_context(
        governance_root=args.governance_root,
        supplied_product_root=args.product_root,
        allow_supplied_product_root=True,
      )
      payload = gather_doctor_report(
        governance_root=context.governance_root,
        product_root=context.product_root,
      )
      _write_payload(payload, stdout=stdout, json_output=args.json_output)
      return 0

    if args.command == "bootstrap-product":
      plan = plan_bootstrap(
        product_root=args.product_root,
        governance_root=args.governance_root,
      )
      if args.apply:
        apply_bootstrap_plan(plan)
      payload = {
        "kind": "bootstrap_plan",
        "preview_only": plan.preview_only,
        "applied": bool(args.apply),
        "operations": [
          {
            "path": str(operation.path),
            "action": operation.action,
          }
          for operation in plan.operations
        ],
      }
      _write_payload(payload, stdout=stdout, json_output=args.json_output)
      return 0

    if args.command == "list":
      context = resolve_operational_context(
        governance_root=args.governance_root,
        supplied_product_root=args.product_root,
        allow_supplied_product_root=True,
      )
      registry = build_discovery_registry(
        product_root=context.product_root,
        governance_root=context.governance_root,
      )
      filters = {
        "id": args.id,
        "family": args.family,
        "title": args.title,
        "status": args.status,
        "gate": args.gate,
        "mode": args.mode,
        "workbench": args.workbench,
        "logical_ref": args.logical_ref,
        "heading": args.heading,
      }
      payload = {
        "kind": "discovery_list",
        "records": list_records(
          registry,
          **{key: value for key, value in filters.items() if value is not None},
        ),
      }
      _write_payload(payload, stdout=stdout, json_output=args.json_output)
      return 0

    if args.command == "show":
      context = resolve_operational_context(
        governance_root=args.governance_root,
        supplied_product_root=args.product_root,
        allow_supplied_product_root=True,
      )
      registry = build_discovery_registry(
        product_root=context.product_root,
        governance_root=context.governance_root,
      )
      payload = show_record(
        registry,
        args.token,
        entity_kind=args.entity_kind,
      )
      _write_payload(payload, stdout=stdout, json_output=args.json_output)
      return 0
  except ContextResolutionError as exc:
    stderr.write(f"{exc}\n")
    return 2

  parser.error(f"unsupported command: {args.command}")
  return 2


def main(argv: Sequence[str] | None = None) -> int:
  return run_cli(argv)


def _write_payload(payload: dict[str, Any], *, stdout: TextIO, json_output: bool) -> None:
  if json_output:
    stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return
  stdout.write(_render_human_payload(payload) + "\n")


def _render_human_payload(payload: dict[str, Any]) -> str:
  kind = payload.get("kind")
  if kind == "doctor_report":
    lines = ["Doctor Report"]
    for category in payload["categories"]:
      check = payload["checks"][category]
      status = check.get("status", check if isinstance(check, str) else "ok")
      lines.append(f"- {category}: {status}")
    for finding in payload["findings"]:
      lines.append(
        f"- {finding['classification']}: {finding['subject']} — {finding['message']}"
      )
    return "\n".join(lines)
  if kind == "discovery_list":
    return "\n".join(
      f"- {record['entity_kind']}: {record['token']} — {record.get('title', record['token'])}"
      for record in payload["records"]
    ) or "(no records)"
  if kind == "bootstrap_plan":
    lines = ["Bootstrap Plan"]
    lines.extend(f"- {op['action']}: {op['path']}" for op in payload["operations"])
    return "\n".join(lines)
  return json.dumps(payload, indent=2, sort_keys=True)