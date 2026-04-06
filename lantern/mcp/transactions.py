"""Shared transaction engine for CH-0004 mutation flows."""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from lantern.artifacts.allocator import allocate_artifact_id, artifact_path
from lantern.artifacts.renderers import canonical_render_markdown, parse_header_block
from lantern.artifacts.validator import (
    validate_artifact_file,
    validate_commit_request,
    validate_draft_request,
    validate_selected_ci_commit_request,
)
from lantern.mcp.journal import (
    ensure_runtime_dirs,
    load_journal_record,
    load_validation_snapshot,
    write_journal_record,
    write_validation_snapshot,
)
from lantern.mcp.topology import resolve_topology
from lantern.workflow.loader import WorkflowLayer

_TRANSACTION_LOCK = threading.Lock()


class TransactionError(RuntimeError):
    """Raised when a transaction cannot be completed safely."""


@dataclass(frozen=True)
class ChangeSurface:
    workbench_id: str
    contract_ref: str
    ci_path: str
    product_root: str
    governance_root: str | None
    allowed_change_surface: tuple[str, ...]
    change_surface_hash: str


class TransactionEngine:
    def __init__(
        self,
        *,
        workflow_layer: WorkflowLayer,
        product_root: Path,
        governance_root: Path | None,
    ) -> None:
        self.workflow_layer = workflow_layer
        self.product_root = Path(product_root).resolve()
        self.governance_root = Path(governance_root).resolve() if governance_root is not None else None
        self.runtime_root = ensure_runtime_dirs(
            product_root=self.product_root,
            governance_root=self.governance_root,
        )

    def inspect_change_surface(self, *, workbench_id: str, ci_path: str) -> ChangeSurface:
        workbench = self.workflow_layer.get_workbench(workbench_id)
        if workbench.workbench_id != "selected_ci_application":
            raise TransactionError("change_surface inspection is only supported for selected_ci_application in CH-0004")
        header = parse_header_block(Path(ci_path).read_text(encoding="utf-8"))
        allowed = header.get("allowed_change_surface")
        if isinstance(allowed, str):
            allowed_paths = tuple(part.strip() for part in allowed.split(",") if part.strip())
        elif isinstance(allowed, list):
            allowed_paths = tuple(str(item).strip() for item in allowed if str(item).strip())
        else:
            raise TransactionError("selected CI artifact is missing allowed_change_surface")
        token_payload = {
            "workbench_id": workbench_id,
            "contract_ref": workbench.contract_refs[0],
            "ci_path": str(Path(ci_path).resolve()),
            "product_root": str(self.product_root),
            "governance_root": str(self.governance_root) if self.governance_root else None,
            "allowed_change_surface": list(allowed_paths),
        }
        digest = sha256(json.dumps(token_payload, sort_keys=True).encode("utf-8")).hexdigest()
        return ChangeSurface(
            workbench_id=workbench_id,
            contract_ref=workbench.contract_refs[0],
            ci_path=token_payload["ci_path"],
            product_root=token_payload["product_root"],
            governance_root=token_payload["governance_root"],
            allowed_change_surface=allowed_paths,
            change_surface_hash=digest,
        )

    def create_draft(
        self,
        *,
        workbench_id: str,
        artifact_family: str,
        payload: Mapping[str, Any] | None,
        contract_ref: str,
        actor: str,
    ) -> dict[str, Any]:
        workbench = self.workflow_layer.get_workbench(workbench_id)
        findings = validate_draft_request(
            workbench=workbench,
            artifact_family=artifact_family,
            payload=payload,
        )
        if findings:
            return {
                "status": "invalid",
                "contract_ref": contract_ref,
                "findings": findings,
            }
        assert payload is not None
        header = dict(payload["header"])
        ch_id = str(header.get("ch_id", "")).strip() or None
        artifact_id_key = f"{artifact_family.lower()}_id"
        artifact_id = str(header.get(artifact_id_key, "")).strip()
        if not artifact_id:
            artifact_id = allocate_artifact_id(artifact_family, self.governance_root or self.product_root, ch_id=ch_id)
            header[artifact_id_key] = artifact_id
        if not header.get("title"):
            header["title"] = str(payload["title"]).strip()
        artifact_file = artifact_path(self.governance_root or self.product_root, artifact_id)
        preview = canonical_render_markdown(
            header=header,
            artifact_id=artifact_id,
            title=str(payload["title"]).strip(),
            sections=payload["sections"],
        )
        draft_id = f"draft-{uuid4()}"
        draft_record = {
            "draft_id": draft_id,
            "actor": actor,
            "workbench_id": workbench_id,
            "contract_ref": contract_ref,
            "artifact_family": artifact_family,
            "artifact_id": artifact_id,
            "artifact_path": str(artifact_file),
            "header": header,
            "title": str(payload["title"]).strip(),
            "sections": list(payload["sections"]),
            "preview": preview,
        }
        (self.runtime_root / "drafts" / f"{draft_id}.json").write_text(
            json.dumps(draft_record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {
            "status": "ok",
            "draft_id": draft_id,
            "contract_ref": contract_ref,
            "artifact_family": artifact_family,
            "derived_fields": {
                "artifact_id": artifact_id,
                "artifact_path": str(artifact_file),
            },
            "preview": preview,
            "validation": {"valid": True, "findings": []},
        }

    def commit_governance(
        self,
        *,
        workbench_id: str,
        draft_id: str | None,
        actor: str,
        hold_lock_seconds: float = 0.0,
    ) -> dict[str, Any]:
        findings = validate_commit_request(draft_id)
        if findings:
            return {"status": "invalid", "findings": findings}
        draft_path = self.runtime_root / "drafts" / f"{draft_id}.json"
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        acquired = _TRANSACTION_LOCK.acquire(blocking=False)
        if not acquired:
            return {
                "status": "lock_conflict",
                "detail": "another commit already owns the internal transaction lock",
            }
        try:
            if hold_lock_seconds > 0:
                time.sleep(hold_lock_seconds)
            artifact_file = Path(draft["artifact_path"])
            artifact_file.parent.mkdir(parents=True, exist_ok=True)
            existed_before = artifact_file.exists()
            artifact_file.write_text(draft["preview"], encoding="utf-8")
            transaction_id = self._new_transaction_id()
            validation_findings = validate_artifact_file(artifact_file)
            validation_snapshot = {
                "scope": "transaction",
                "transaction_id": transaction_id,
                "valid": not validation_findings,
                "findings": validation_findings,
                "affected_paths": [str(artifact_file)],
            }
            journal_record = {
                "tx_id": transaction_id,
                "name": "commit_governance_artifact",
                "status": "COMMITTED",
                "updated_utc": _utc_now(),
                "metadata": {
                    "actor": actor,
                    "workbench_id": workbench_id,
                    "contract_ref": draft["contract_ref"],
                    "artifact_id": draft["artifact_id"],
                    "validation_scope": "transaction",
                },
                "touched_paths": [str(artifact_file)],
                "created_paths": [] if existed_before else [str(artifact_file)],
                "validation_snapshot": str((self.runtime_root / "validation" / f"{transaction_id}.json").resolve()),
            }
            journal_path = write_journal_record(
                runtime_root=self.runtime_root,
                transaction_id=transaction_id,
                record=journal_record,
            )
            validation_path = write_validation_snapshot(
                runtime_root=self.runtime_root,
                transaction_id=transaction_id,
                snapshot=validation_snapshot,
            )
            return {
                "status": "committed",
                "transaction_id": transaction_id,
                "artifact_id": draft["artifact_id"],
                "artifact_path": str(artifact_file),
                "affected_paths": [str(artifact_file)],
                "journal_path": str(journal_path),
                "validation": {
                    "scope": "transaction",
                    "path": str(validation_path),
                    "valid": not validation_findings,
                    "findings": validation_findings,
                },
                "correlation": {
                    "transaction_id": transaction_id,
                    "contract_ref": draft["contract_ref"],
                    "actor": actor,
                    "artifact_id": draft["artifact_id"],
                    "journal_path": str(journal_path),
                },
            }
        finally:
            _TRANSACTION_LOCK.release()

    def commit_selected_ci_application(
        self,
        *,
        workbench_id: str,
        payload: Mapping[str, Any] | None,
        actor: str,
    ) -> dict[str, Any]:
        findings = validate_selected_ci_commit_request(payload)
        if findings:
            return {"status": "invalid", "findings": findings}
        assert payload is not None
        change_surface = self.inspect_change_surface(
            workbench_id=workbench_id,
            ci_path=str(payload["ci_path"]),
        )
        operations = list(payload["operations"])
        acquired = _TRANSACTION_LOCK.acquire(blocking=False)
        if not acquired:
            return {
                "status": "lock_conflict",
                "detail": "another commit already owns the internal transaction lock",
            }
        try:
            hold_seconds = max(float(op.get("hold_lock_seconds", 0.0)) for op in operations)
            if hold_seconds > 0:
                time.sleep(hold_seconds)
            affected_paths: list[str] = []
            for operation in operations:
                rel_path = str(operation["path"])
                if not _is_path_allowed(rel_path, change_surface.allowed_change_surface):
                    return {
                        "status": "invalid",
                        "findings": [
                            {
                                "path": f"payload.operations[{operations.index(operation)}].path",
                                "message": f"path {rel_path!r} is outside the inspected change surface",
                                "anchor": "inspect.change_surface.allowed_change_surface",
                            }
                        ],
                    }
                target = self.product_root / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(str(operation["content"]), encoding="utf-8")
                affected_paths.append(str(target))
            transaction_id = self._new_transaction_id()
            validation_findings = self._post_commit_product_validation(affected_paths)
            validation_snapshot = {
                "scope": "transaction",
                "transaction_id": transaction_id,
                "valid": not validation_findings,
                "findings": validation_findings,
                "affected_paths": affected_paths,
                "change_surface_hash": change_surface.change_surface_hash,
            }
            journal_record = {
                "tx_id": transaction_id,
                "name": "selected_ci_application_commit",
                "status": "COMMITTED",
                "updated_utc": _utc_now(),
                "metadata": {
                    "actor": actor,
                    "workbench_id": workbench_id,
                    "contract_ref": change_surface.contract_ref,
                    "change_surface_hash": change_surface.change_surface_hash,
                    "validation_scope": "transaction",
                },
                "touched_paths": affected_paths,
                "created_paths": affected_paths,
                "validation_snapshot": str((self.runtime_root / "validation" / f"{transaction_id}.json").resolve()),
            }
            journal_path = write_journal_record(
                runtime_root=self.runtime_root,
                transaction_id=transaction_id,
                record=journal_record,
            )
            validation_path = write_validation_snapshot(
                runtime_root=self.runtime_root,
                transaction_id=transaction_id,
                snapshot=validation_snapshot,
            )
            return {
                "status": "committed",
                "transaction_id": transaction_id,
                "affected_paths": affected_paths,
                "journal_path": str(journal_path),
                "change_surface": {
                    "allowed_change_surface": list(change_surface.allowed_change_surface),
                    "change_surface_hash": change_surface.change_surface_hash,
                },
                "validation": {
                    "scope": "transaction",
                    "path": str(validation_path),
                    "valid": not validation_findings,
                    "findings": validation_findings,
                },
                "correlation": {
                    "transaction_id": transaction_id,
                    "contract_ref": change_surface.contract_ref,
                    "actor": actor,
                    "affected_paths": affected_paths,
                    "journal_path": str(journal_path),
                },
            }
        finally:
            _TRANSACTION_LOCK.release()

    def validate(
        self,
        *,
        scope: str,
        draft_id: str | None = None,
        artifact_path: str | None = None,
        transaction_id: str | None = None,
    ) -> dict[str, Any]:
        if scope == "workspace":
            posture = resolve_topology(product_root=self.product_root, governance_root=self.governance_root)
            findings = [
                {"path": "workspace", "message": issue, "anchor": "topology"}
                for issue in posture.startup_issues
            ]
            return {
                "scope": "workspace",
                "valid": not findings,
                "findings": findings,
                "workspace": {
                    "product_root": str(self.product_root),
                    "governance_root": str(self.governance_root) if self.governance_root else None,
                },
            }
        if scope == "draft":
            if not draft_id:
                return {
                    "scope": "draft",
                    "valid": False,
                    "findings": [{"path": "draft_id", "message": "draft_id is required", "anchor": "validate.scope"}],
                }
            draft = json.loads((self.runtime_root / "drafts" / f"{draft_id}.json").read_text(encoding="utf-8"))
            findings = []
            if not draft.get("preview"):
                findings.append({"path": "preview", "message": "draft preview missing", "anchor": "draft.preview"})
            return {
                "scope": "draft",
                "draft_id": draft_id,
                "valid": not findings,
                "findings": findings,
            }
        if scope == "artifact":
            if not artifact_path:
                return {
                    "scope": "artifact",
                    "valid": False,
                    "findings": [{"path": "artifact_path", "message": "artifact_path is required", "anchor": "validate.scope"}],
                }
            findings = validate_artifact_file(Path(artifact_path))
            return {
                "scope": "artifact",
                "artifact_path": artifact_path,
                "valid": not findings,
                "findings": findings,
            }
        if scope == "transaction":
            if not transaction_id:
                return {
                    "scope": "transaction",
                    "valid": False,
                    "findings": [{"path": "transaction_id", "message": "transaction_id is required", "anchor": "validate.scope"}],
                }
            journal = load_journal_record(runtime_root=self.runtime_root, transaction_id=transaction_id)
            snapshot = load_validation_snapshot(runtime_root=self.runtime_root, transaction_id=transaction_id)
            return {
                "scope": "transaction",
                "transaction_id": transaction_id,
                "valid": bool(snapshot.get("valid")),
                "findings": list(snapshot.get("findings", [])),
                "journal_path": str((self.runtime_root / "journal" / transaction_id / "journal.json").resolve()),
                "affected_paths": journal.get("touched_paths", []),
            }
        return {
            "scope": scope,
            "valid": False,
            "findings": [{"path": "scope", "message": f"unsupported validate scope: {scope}", "anchor": "validate.scope"}],
        }

    def _post_commit_product_validation(self, affected_paths: list[str]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        for path_str in affected_paths:
            text = Path(path_str).read_text(encoding="utf-8")
            if "FAIL_VALIDATION" in text:
                findings.append(
                    {
                        "path": path_str,
                        "message": "FAIL_VALIDATION marker present in committed product file",
                        "anchor": "post_commit_validation",
                    }
                )
        return findings

    @staticmethod
    def _new_transaction_id() -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        return f"{stamp}-{uuid4().hex[:12]}"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_path_allowed(relative_path: str, allowed_entries: tuple[str, ...]) -> bool:
    clean = relative_path.strip().lstrip("./")
    for entry in allowed_entries:
        allowed = entry.strip().lstrip("./")
        if allowed.endswith("/") and clean.startswith(allowed):
            return True
        if clean == allowed:
            return True
    return False
