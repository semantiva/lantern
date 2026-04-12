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

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_TARGET_ROOTS = (
    Path("lantern/authoring_contracts"),
    Path("lantern/administration_procedures"),
    Path("lantern/templates"),
)


@dataclass(frozen=True)
class SyncResult:
    entry_id: str
    status: str
    target: str
    detail: str = ""


def plan_manifest(
    manifest_path: Path,
    source_locks_path: Path,
    bridge_root: Path,
    product_root: Path,
) -> list[SyncResult]:
    return _run_manifest(manifest_path, source_locks_path, bridge_root, product_root, mode="plan")


def apply_manifest(
    manifest_path: Path,
    source_locks_path: Path,
    bridge_root: Path,
    product_root: Path,
) -> list[SyncResult]:
    return _run_manifest(manifest_path, source_locks_path, bridge_root, product_root, mode="apply")


def _run_manifest(
    manifest_path: Path,
    source_locks_path: Path,
    bridge_root: Path,
    product_root: Path,
    *,
    mode: str,
) -> list[SyncResult]:
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    locks = yaml.safe_load(source_locks_path.read_text(encoding="utf-8"))
    source_locks = dict(locks.get("locks", {}))
    results: list[SyncResult] = []

    for entry in payload.get("entries", []):
        entry_id = entry["entry_id"]
        target = entry["target"]
        target_path = product_root / target
        entry_class = entry.get("entry_class")

        if entry_class != "bridge_copy":
            status = "unchanged" if target_path.exists() else "failed"
            detail = "product-owned entry present" if status == "unchanged" else "product-owned entry missing"
            results.append(SyncResult(entry_id=entry_id, status=status, target=target, detail=detail))
            continue

        if not _target_is_allowed(Path(target)):
            results.append(
                SyncResult(
                    entry_id=entry_id,
                    status="failed",
                    target=target,
                    detail="target escapes allowed bridge-copy roots",
                )
            )
            continue

        source = entry["source"]
        source_path = bridge_root / source
        if not source_path.exists():
            results.append(
                SyncResult(entry_id=entry_id, status="failed", target=target, detail=f"missing source: {source}")
            )
            continue

        expected_digest = source_locks.get(source)
        if expected_digest is None:
            results.append(
                SyncResult(entry_id=entry_id, status="failed", target=target, detail=f"missing source lock: {source}")
            )
            continue

        actual_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual_digest != expected_digest:
            results.append(
                SyncResult(
                    entry_id=entry_id,
                    status="failed",
                    target=target,
                    detail=f"source lock mismatch for {source}",
                )
            )
            continue

        rendered = _rewrite_bridge_text(source_path.read_text(encoding="utf-8"))
        if target_path.exists() and target_path.read_text(encoding="utf-8") == rendered:
            results.append(SyncResult(entry_id=entry_id, status="unchanged", target=target))
            continue

        if mode == "plan":
            results.append(SyncResult(entry_id=entry_id, status="planned", target=target))
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(rendered, encoding="utf-8")
        results.append(SyncResult(entry_id=entry_id, status="written", target=target))

    return results


def _target_is_allowed(target: Path) -> bool:
    return any(target == root or root in target.parents for root in _TARGET_ROOTS)


def _rewrite_bridge_text(text: str) -> str:
    lines = text.splitlines()
    rewritten_lines: list[str] = []
    skipping_banner = False

    for line in lines:
        if not skipping_banner and line.startswith("> **Lantern Ops Bridge adaptation note:**"):
            skipping_banner = True
            continue
        if skipping_banner:
            if line.startswith(">"):
                continue
            skipping_banner = False
        rewritten_lines.append(line)

    rewritten = "\n".join(rewritten_lines)
    for old, new in _exact_replacements():
        rewritten = rewritten.replace(old, new)
    rewritten = re.sub(r"(?i)\btier[-_ ]?h\b", _replace_legacy_name, rewritten)
    return rewritten + ("\n" if text.endswith("\n") else "")


def _exact_replacements() -> tuple[tuple[str, str], ...]:
    legacy_upper = "_".join(("TIER", "H"))
    legacy_snake = "_".join(("tier", "h"))
    legacy_root = f"_{legacy_upper}"
    bridge_root = "lantern-ops-bridge/"
    return (
        (f"{legacy_upper}_MODEL_BINDING.md", "LANTERN_MODEL_BINDING.md"),
        (f"allocate_{legacy_snake}_id.py", "allocate_lantern_id.py"),
        (f"validate_{legacy_snake}.py", "validate_lantern.py"),
        (f"validate_{legacy_snake}_ssot.py", "validate_lantern_workspace.py"),
        (f"bootstrap_{legacy_snake}_workspace.py", "bootstrap_lantern_workspace.py"),
        (f"{legacy_snake}_mcp_server.py", "lantern_ops_bridge_mcp_server.py"),
        (f"{legacy_snake}_", "lantern_"),
        (f"{bridge_root}authoring_contracts/", "lantern/authoring_contracts/"),
        (f"{bridge_root}administration_procedures/", "lantern/administration_procedures/"),
        (f"{bridge_root}templates/", "lantern/templates/"),
        (f"{bridge_root}preservation/", "lantern/preservation/"),
        (f"{bridge_root}runtime/", "lantern/workflow/"),
        (bridge_root, "lantern/"),
        (f"{legacy_root}/change/change_intents/", "ch/"),
        (f"{legacy_root}/change/change_increments/", "ci/"),
        (f"{legacy_root}/change/design_baselines/", "db/"),
        (f"{legacy_root}/change/design_candidates/", "dc/"),
        (f"{legacy_root}/change/evidence/", "ev/"),
        (f"{legacy_root}/change/decisions/", "dec/"),
        (f"{legacy_root}/change/initiatives/", "ini/"),
        (f"{legacy_root}/inputs/dips/", "dip/"),
        (f"{legacy_root}/inputs/specs/", "spec/"),
        (f"{legacy_root}/inputs/arch/", "arch/"),
        (f"{legacy_root}/inputs/test_definitions/", "td/"),
        (f"{legacy_root}/issues/", "is/"),
        (f"{legacy_root}/specs/", "lantern/preservation/"),
        (f"{legacy_root}/authoring_contracts/", "lantern/authoring_contracts/"),
        (f"{legacy_root}/administration_procedures/", "lantern/administration_procedures/"),
        (f"{legacy_root}/templates/", "lantern/templates/"),
        (legacy_root, "Lantern"),
        (f"{legacy_root}/", "lantern/"),
    )


def _replace_legacy_name(match: re.Match[str]) -> str:
    text = match.group(0)
    if text.isupper():
        return "LANTERN"
    if text.islower():
        return "lantern"
    return "Lantern"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronize bridge-derived Lantern corpus files.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-locks", required=True, type=Path)
    parser.add_argument("--bridge-root", required=True, type=Path)
    parser.add_argument("--product-root", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("plan", "apply"))
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if args.mode == "plan":
        results = plan_manifest(args.manifest, args.source_locks, args.bridge_root, args.product_root)
    else:
        results = apply_manifest(args.manifest, args.source_locks, args.bridge_root, args.product_root)

    failures = [result for result in results if result.status == "failed"]
    for result in results:
        detail = f" {result.detail}" if result.detail else ""
        print(f"{result.entry_id} {result.status} {result.target}{detail}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
