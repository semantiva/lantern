from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .ref_resolver import collect_emitted_refs, resolve_guide_refs

_LEGACY_NAME_PATTERN = re.compile(r"(?i)tier[-_ ]?h")


@dataclass(frozen=True)
class PreservationFinding:
    entry_id: str
    target: str
    check: str
    detail: str
    severity: str

    def __str__(self) -> str:
        return f"[{self.severity}] [{self.entry_id}] {self.target}: {self.check}: {self.detail}"


def validate_manifest(
    manifest_path: Path,
    product_root: Path,
    *,
    source_locks_path: Path | None = None,
    bridge_root: Path | None = None,
) -> list[PreservationFinding]:
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    source_locks = _load_source_locks(source_locks_path)
    findings: list[PreservationFinding] = []

    for entry in payload.get("entries", []):
        findings.extend(_validate_entry(entry, product_root, source_locks, bridge_root))

    registry_path = product_root / "lantern/workflow/definitions/workbench_registry.yaml"
    instructions_root = product_root / "lantern/resources/instructions"
    if registry_path.exists() and instructions_root.exists():
        emitted_refs = collect_emitted_refs(registry_path, instructions_root)
        unresolved = resolve_guide_refs(manifest_path, emitted_refs, product_root)
        for ref in unresolved:
            findings.append(
                PreservationFinding(
                    entry_id="GLOBAL",
                    target=ref,
                    check="UNRESOLVED_REF",
                    detail=f"Emitted Lantern-local reference does not resolve: {ref}",
                    severity="FATAL",
                )
            )

    return findings


def _validate_entry(
    entry: dict[str, Any],
    product_root: Path,
    source_locks: dict[str, str],
    bridge_root: Path | None,
) -> list[PreservationFinding]:
    findings: list[PreservationFinding] = []
    entry_id = entry["entry_id"]
    target = entry["target"]
    target_path = product_root / target

    if not target_path.exists():
        findings.append(
            PreservationFinding(
                entry_id=entry_id,
                target=target,
                check="MISSING_FILE",
                detail="Target file does not exist",
                severity="FATAL",
            )
        )
        return findings

    content = target_path.read_text(encoding="utf-8")
    signature = entry.get("preservation_signature", {})

    for heading in signature.get("required_headings", []):
        pattern = rf"^{re.escape(heading)}\s*$"
        if not re.search(pattern, content, re.MULTILINE):
            findings.append(
                PreservationFinding(
                    entry_id=entry_id,
                    target=target,
                    check="MISSING_HEADING",
                    detail=f"Required heading missing: {heading}",
                    severity="FATAL",
                )
            )

    header_keys = signature.get("required_header_keys", [])
    if header_keys:
        header_text = _extract_header_text(content)
        for key in header_keys:
            if not re.search(rf"^{re.escape(key)}\s*:", header_text, re.MULTILINE):
                findings.append(
                    PreservationFinding(
                        entry_id=entry_id,
                        target=target,
                        check="MISSING_HEADER_KEY",
                        detail=f"Required header key missing: {key}",
                        severity="FATAL",
                    )
                )

    for pattern in signature.get("forbidden_patterns", []):
        if pattern and pattern in content:
            findings.append(
                PreservationFinding(
                    entry_id=entry_id,
                    target=target,
                    check="FORBIDDEN_PATTERN",
                    detail=f"Forbidden pattern present: {pattern}",
                    severity="FATAL",
                )
            )

    if _LEGACY_NAME_PATTERN.search(content):
        findings.append(
            PreservationFinding(
                entry_id=entry_id,
                target=target,
                check="FORBIDDEN_PATTERN",
                detail="Legacy prior-product marker remains in file content",
                severity="FATAL",
            )
        )

    if "lantern-ops-bridge/" in content:
        findings.append(
            PreservationFinding(
                entry_id=entry_id,
                target=target,
                check="FORBIDDEN_PATTERN",
                detail="Bridge-local path remains in file content",
                severity="FATAL",
            )
        )

    if entry.get("entry_class") == "bridge_copy":
        source = entry.get("source", "")
        if source not in source_locks:
            findings.append(
                PreservationFinding(
                    entry_id=entry_id,
                    target=target,
                    check="MISSING_SOURCE_LOCK",
                    detail=f"No source lock recorded for {source}",
                    severity="FATAL",
                )
            )
        elif bridge_root is not None:
            source_path = bridge_root / source
            if not source_path.exists():
                findings.append(
                    PreservationFinding(
                        entry_id=entry_id,
                        target=target,
                        check="MISSING_SOURCE",
                        detail=f"Locked bridge source missing: {source}",
                        severity="FATAL",
                    )
                )
            else:
                actual_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
                if actual_digest != source_locks[source]:
                    findings.append(
                        PreservationFinding(
                            entry_id=entry_id,
                            target=target,
                            check="SOURCE_LOCK_MISMATCH",
                            detail=f"Expected {source_locks[source]}, got {actual_digest}",
                            severity="FATAL",
                        )
                    )

    return findings


def _extract_header_text(content: str) -> str:
    fenced_match = re.match(r"^```yaml\s*\n(.*?)\n```", content, re.DOTALL)
    if fenced_match:
        return fenced_match.group(1)
    front_matter_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if front_matter_match:
        return front_matter_match.group(1)
    return ""


def _load_source_locks(source_locks_path: Path | None) -> dict[str, str]:
    if source_locks_path is None or not source_locks_path.exists():
        return {}
    payload = yaml.safe_load(source_locks_path.read_text(encoding="utf-8"))
    return dict(payload.get("locks", {}))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the Lantern relocation manifest.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--product-root", required=True, type=Path)
    parser.add_argument("--source-locks", type=Path)
    parser.add_argument("--bridge-root", type=Path)
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    findings = validate_manifest(
        args.manifest,
        args.product_root,
        source_locks_path=args.source_locks,
        bridge_root=args.bridge_root,
    )
    fatals = [finding for finding in findings if finding.severity == "FATAL"]
    for finding in findings:
        print(finding)
    if fatals:
        return 1
    print("PRESERVATION OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())