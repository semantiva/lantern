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
from lantern.workflow.merger import InterventionRestrictionGuard, PostureResult
from lantern.artifacts.renderers import canonical_render_markdown, parse_header_block
from lantern.artifacts.validator import (
    validate_artifact_file,
    validate_commit_request,
    validate_draft_request,
    validate_selected_ci_commit_request,
    validate_workspace_readiness,
)
from lantern.mcp.journal import (
    ensure_runtime_dirs,
    load_application_handoff,
    load_journal_record,
    load_validation_snapshot,
    write_application_handoff,
    write_journal_record,
    write_validation_snapshot,
)
from lantern.mcp.topology import resolve_topology
from lantern.workflow.loader import WorkflowLayer

_TRANSACTION_LOCK = threading.Lock()
_active_posture_result: PostureResult | None = None
_intervention_guard = InterventionRestrictionGuard()


def configure_posture_result(posture_result: PostureResult | None) -> None:
    """Set the session-scoped PostureResult for all subsequent transaction-engine operations.

    Called by server.py during the startup sequence after posture validation completes.
    Must be called before any MCP tool handles a request.
    """
    global _active_posture_result
    _active_posture_result = posture_result


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
    runtime_managed_change_surface: tuple[str, ...]
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
        runtime_managed = (".gitignore",) if _gitignore_needs_hygiene_block(self.product_root) else ()
        token_payload = {
            "workbench_id": workbench_id,
            "contract_ref": workbench.contract_refs[0],
            "ci_path": str(Path(ci_path).resolve()),
            "product_root": str(self.product_root),
            "governance_root": str(self.governance_root) if self.governance_root else None,
            "allowed_change_surface": list(allowed_paths),
            "runtime_managed_change_surface": list(runtime_managed),
        }
        digest = sha256(json.dumps(token_payload, sort_keys=True).encode("utf-8")).hexdigest()
        return ChangeSurface(
            workbench_id=workbench_id,
            contract_ref=workbench.contract_refs[0],
            ci_path=token_payload["ci_path"],
            product_root=token_payload["product_root"],
            governance_root=token_payload["governance_root"],
            allowed_change_surface=allowed_paths,
            runtime_managed_change_surface=runtime_managed,
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
        _intervention_guard.check(
            posture_result=_active_posture_result,
            transaction_kind="write_binding_record",
        )
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
        _intervention_guard.check(
            posture_result=_active_posture_result,
            transaction_kind="write_binding_record",
        )
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
            for index, operation in enumerate(operations):
                rel_path = str(operation["path"]).strip()
                if rel_path == ".gitignore":
                    return {
                        "status": "invalid",
                        "findings": [
                            {
                                "path": f"payload.operations[{index}].path",
                                "message": ".gitignore is runtime-managed during selected CI application and cannot be supplied by the operator payload",
                                "anchor": "selected_ci_application.runtime_managed_hygiene",
                            }
                        ],
                    }
                if not _is_path_allowed(rel_path, change_surface.allowed_change_surface):
                    return {
                        "status": "invalid",
                        "findings": [
                            {
                                "path": f"payload.operations[{index}].path",
                                "message": f"path {rel_path!r} is outside the inspected change surface",
                                "anchor": "inspect.change_surface.allowed_change_surface",
                            }
                        ],
                    }
                target = self.product_root / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(str(operation["content"]), encoding="utf-8")
                affected_paths.append(str(target.resolve()))
            managed_hygiene_path = self._ensure_runtime_managed_gitignore_hygiene(change_surface)
            if managed_hygiene_path is not None:
                affected_paths.append(managed_hygiene_path)
            transaction_id = self._new_transaction_id()
            validation_findings = self._post_commit_product_validation(affected_paths)
            handoff = self._build_application_handoff(
                workbench_id=workbench_id,
                actor=actor,
                ci_path=Path(str(payload["ci_path"])),
                change_surface=change_surface,
                affected_paths=affected_paths,
            )
            validation_snapshot = {
                "scope": "transaction",
                "transaction_id": transaction_id,
                "valid": not validation_findings,
                "findings": validation_findings,
                "affected_paths": affected_paths,
                "change_surface_hash": change_surface.change_surface_hash,
                "application_handoff": handoff,
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
                    "post_application_state": "awaiting_gt130",
                },
                "touched_paths": affected_paths,
                "created_paths": affected_paths,
                "validation_snapshot": str((self.runtime_root / "validation" / f"{transaction_id}.json").resolve()),
                "application_handoff": str((self.runtime_root / "journal" / transaction_id / "application_handoff.json").resolve()),
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
            handoff_path = write_application_handoff(
                runtime_root=self.runtime_root,
                transaction_id=transaction_id,
                handoff=handoff,
            )
            return {
                "status": "committed",
                "transaction_id": transaction_id,
                "affected_paths": affected_paths,
                "journal_path": str(journal_path),
                "change_surface": {
                    "allowed_change_surface": list(change_surface.allowed_change_surface),
                    "runtime_managed_change_surface": list(change_surface.runtime_managed_change_surface),
                    "change_surface_hash": change_surface.change_surface_hash,
                },
                "application_handoff": {
                    **handoff,
                    "path": str(handoff_path),
                },
                "validation": {
                    "scope": "transaction",
                    "path": str(validation_path),
                    "valid": not validation_findings,
                    "findings": validation_findings,
                    "application_handoff": handoff,
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
            findings = validate_workspace_readiness(
                product_root=self.product_root,
                governance_root=self.governance_root if self.governance_root and self.governance_root.is_dir() else None,
            )
            if self.governance_root is None:
                findings = [
                    {"path": "workspace.governance_root", "message": "governance root not configured", "anchor": "topology"},
                    *findings,
                ]
            elif not self.governance_root.is_dir():
                findings = [
                    {"path": "workspace.governance_root", "message": f"governance root not found: {self.governance_root}", "anchor": "topology"},
                    *findings,
                ]
            return {
                "scope": "workspace",
                "valid": not findings,
                "findings": findings,
                "workspace": {
                    "product_root": str(self.product_root),
                    "governance_root": str(self.governance_root) if self.governance_root else None,
                    "runtime_surface_classification": posture.runtime_surface_classification,
                    "consistency_state": posture.consistency_state,
                    "startup_issues": list(posture.startup_issues),
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
            handoff = load_application_handoff(runtime_root=self.runtime_root, transaction_id=transaction_id)
            return {
                "scope": "transaction",
                "transaction_id": transaction_id,
                "valid": bool(snapshot.get("valid")),
                "findings": list(snapshot.get("findings", [])),
                "journal_path": str((self.runtime_root / "journal" / transaction_id / "journal.json").resolve()),
                "affected_paths": journal.get("touched_paths", []),
                "application_handoff": handoff,
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

    def _ensure_runtime_managed_gitignore_hygiene(self, change_surface: ChangeSurface) -> str | None:
        if ".gitignore" not in change_surface.runtime_managed_change_surface:
            return None
        gitignore_path = self.product_root / ".gitignore"
        existing_lines = []
        if gitignore_path.exists():
            existing_lines = gitignore_path.read_text(encoding="utf-8").splitlines()
        existing_entries = {line.strip() for line in existing_lines if line.strip() and not line.strip().startswith("#")}
        missing_entries = [entry for entry in _MANAGED_GITIGNORE_ENTRIES if entry not in existing_entries]
        if not missing_entries:
            return None
        managed_block = [
            _MANAGED_GITIGNORE_START,
            *missing_entries,
            _MANAGED_GITIGNORE_END,
        ]
        if existing_lines and existing_lines[-1].strip():
            existing_lines.append("")
        existing_lines.extend(managed_block)
        gitignore_path.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")
        return str(gitignore_path.resolve())

    def _build_application_handoff(
        self,
        *,
        workbench_id: str,
        actor: str,
        ci_path: Path,
        change_surface: ChangeSurface,
        affected_paths: list[str],
    ) -> dict[str, Any]:
        workbench = self.workflow_layer.get_workbench("verification_and_closure")
        ci_header = parse_header_block(ci_path.read_text(encoding="utf-8"))
        return {
            "ci_id": str(ci_header.get("ci_id", ci_path.stem)),
            "contract_ref": change_surface.contract_ref,
            "effective_change_surface": list(change_surface.allowed_change_surface + change_surface.runtime_managed_change_surface),
            "change_surface_hash": change_surface.change_surface_hash,
            "affected_product_paths": affected_paths,
            "applied_at_utc": _utc_now(),
            "actor": actor,
            "post_application_state": "awaiting_gt130",
            "next_step": {
                "workbench_id": workbench.workbench_id,
                "instruction_resource": workbench.instruction_resource,
                "guide_refs": list(workbench.authoritative_guides + workbench.administration_guides),
            },
        }

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


_MANAGED_GITIGNORE_START = "# BEGIN LANTERN MANAGED PYTHON HYGIENE"
_MANAGED_GITIGNORE_END = "# END LANTERN MANAGED PYTHON HYGIENE"
_MANAGED_GITIGNORE_ENTRIES = (
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".venv/",
    "venv/",
)


def _gitignore_needs_hygiene_block(product_root: Path) -> bool:
    gitignore_path = product_root / ".gitignore"
    if not gitignore_path.exists():
        return True
    existing_entries = {line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")}
    return any(entry not in existing_entries for entry in _MANAGED_GITIGNORE_ENTRIES)
