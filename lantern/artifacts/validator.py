"""Validation helpers for CH-0004 requests and CH-0009 MVP-hardening checks."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lantern.artifacts.renderers import parse_header_block
from lantern.workflow.loader import WorkflowWorkbench


ValidationFinding = dict[str, str]
_GOVERNED_FAMILY_DIRS = ("arch", "ch", "ci", "db", "dc", "dec", "dip", "ev", "ini", "is", "spec", "td")
_HEADER_ID_KEYS = {
    "arch": "arch_id",
    "ch": "ch_id",
    "ci": "ci_id",
    "db": "db_id",
    "dc": "dc_id",
    "dec": "dec_id",
    "dip": "dip_id",
    "ev": "ev_id",
    "ini": "initiative_id",
    "is": "is_id",
    "spec": "spec_id",
    "td": "td_id",
}


def _finding(path: str, message: str, *, anchor: str, artifact_id: str | None = None) -> ValidationFinding:
    finding: ValidationFinding = {"path": path, "message": message, "anchor": anchor}
    if artifact_id:
        finding["artifact_id"] = artifact_id
    return finding


def validate_draft_request(
    *,
    workbench: WorkflowWorkbench,
    artifact_family: str,
    payload: Mapping[str, Any] | None,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if artifact_family not in workbench.draftable_artifact_families:
        findings.append(
            _finding(
                "artifact_family",
                f"artifact family {artifact_family!r} is not draftable in workbench {workbench.workbench_id!r}",
                anchor="workflow_owned_contract.family_binding",
            )
        )
    if not isinstance(payload, Mapping):
        findings.append(
            _finding(
                "payload",
                "payload must be an object with header, title, and sections",
                anchor="server_owned_contract.request_schemas.draft.properties.payload",
            )
        )
        return findings
    header = payload.get("header")
    if not isinstance(header, Mapping):
        findings.append(
            _finding(
                "payload.header",
                "header must be a mapping",
                anchor="server_owned_contract.request_schemas.draft.properties.payload.properties.header",
            )
        )
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        findings.append(
            _finding(
                "payload.title",
                "title must be a non-empty string",
                anchor="server_owned_contract.request_schemas.draft.properties.payload.properties.title",
            )
        )
    sections = payload.get("sections")
    if not isinstance(sections, list) or not sections:
        findings.append(
            _finding(
                "payload.sections",
                "sections must be a non-empty list",
                anchor="server_owned_contract.request_schemas.draft.properties.payload.properties.sections",
            )
        )
        return findings
    for index, section in enumerate(sections):
        path = f"payload.sections[{index}]"
        if not isinstance(section, Mapping):
            findings.append(
                _finding(
                    path,
                    "section must be an object with heading and body",
                    anchor="server_owned_contract.request_schemas.draft.properties.payload.properties.sections.items",
                )
            )
            continue
        heading = section.get("heading")
        body = section.get("body")
        if not isinstance(heading, str) or not heading.strip():
            findings.append(
                _finding(
                    f"{path}.heading",
                    "heading must be a non-empty string",
                    anchor="server_owned_contract.request_schemas.draft.properties.payload.properties.sections.items.properties.heading",
                )
            )
        if not isinstance(body, str):
            findings.append(
                _finding(
                    f"{path}.body",
                    "body must be a string",
                    anchor="server_owned_contract.request_schemas.draft.properties.payload.properties.sections.items.properties.body",
                )
            )
    return findings



def validate_selected_ci_commit_request(payload: Mapping[str, Any] | None) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    if not isinstance(payload, Mapping):
        return [
            _finding(
                "payload",
                "payload must be an object with ci_path and operations",
                anchor="server_owned_contract.request_schemas.commit",
            )
        ]
    ci_path = payload.get("ci_path")
    if not isinstance(ci_path, str) or not ci_path.strip():
        findings.append(
            _finding(
                "payload.ci_path",
                "ci_path must be a non-empty string",
                anchor="server_owned_contract.request_schemas.commit.properties.ci_path",
            )
        )
    operations = payload.get("operations")
    if not isinstance(operations, list) or not operations:
        findings.append(
            _finding(
                "payload.operations",
                "operations must be a non-empty list",
                anchor="server_owned_contract.request_schemas.commit.properties.operations",
            )
        )
        return findings
    for index, operation in enumerate(operations):
        path = f"payload.operations[{index}]"
        if not isinstance(operation, Mapping):
            findings.append(
                _finding(path, "operation must be an object", anchor="server_owned_contract.request_schemas.commit.properties.operations.items")
            )
            continue
        if not isinstance(operation.get("path"), str) or not str(operation.get("path")).strip():
            findings.append(
                _finding(
                    f"{path}.path",
                    "path must be a non-empty string",
                    anchor="server_owned_contract.request_schemas.commit.properties.operations.items.properties.path",
                )
            )
        if not isinstance(operation.get("content"), str):
            findings.append(
                _finding(
                    f"{path}.content",
                    "content must be a string",
                    anchor="server_owned_contract.request_schemas.commit.properties.operations.items.properties.content",
                )
            )
    return findings



def validate_commit_request(draft_id: str | None) -> list[ValidationFinding]:
    if isinstance(draft_id, str) and draft_id.strip():
        return []
    return [
        _finding(
            "draft_id",
            "draft_id must be a non-empty string",
            anchor="server_owned_contract.request_schemas.commit.properties.draft_id",
        )
    ]



def validate_artifact_file(path: Path) -> list[ValidationFinding]:
    if not path.exists():
        return [_finding("artifact_path", f"artifact does not exist: {path}", anchor="artifact")]
    text = path.read_text(encoding="utf-8")
    findings: list[ValidationFinding] = []
    try:
        header = parse_header_block(text)
    except ValueError as exc:
        return [_finding("artifact_path", str(exc), anchor="artifact.header")]
    title = header.get("title")
    if not isinstance(title, str) or not title.strip():
        findings.append(_finding("header.title", "header title must be a non-empty string", anchor="artifact.header"))
    if "# " not in text:
        findings.append(_finding("body", "artifact body must contain a level-1 title", anchor="artifact.body"))
    return findings



def validate_workspace_readiness(*, product_root: Path, governance_root: Path | None = None) -> list[ValidationFinding]:
    from lantern.workflow.loader import WorkflowLayerError, load_workflow_layer

    findings: list[ValidationFinding] = []
    product_root = Path(product_root).resolve()
    if not product_root.is_dir():
        return [_finding("workspace.product_root", f"product root not found: {product_root}", anchor="workspace")]

    loader_kwargs = {
        "registry_path": product_root / "lantern" / "workflow" / "definitions" / "workbench_registry.yaml",
        "schema_path": product_root / "lantern" / "workflow" / "definitions" / "workbench_schema.yaml",
        "transaction_profiles_path": product_root / "lantern" / "workflow" / "definitions" / "transaction_profiles.yaml",
        "contract_catalog_path": product_root / "lantern" / "workflow" / "definitions" / "contract_catalog.json",
        "resource_manifest_path": product_root / "lantern" / "workflow" / "definitions" / "resource_manifest.json",
        "workflow_map_path": product_root / "lantern" / "workflow" / "definitions" / "workflow_map.md",
        "workbench_resource_bindings_path": product_root / "lantern" / "workflow" / "definitions" / "workbench_resource_bindings.md",
        "relocation_manifest_path": product_root / "lantern" / "preservation" / "relocation_manifest.yaml",
    }
    try:
        load_workflow_layer(**loader_kwargs)
    except WorkflowLayerError as exc:
        findings.extend(_map_workflow_layer_error(exc, product_root=product_root))

    if governance_root is not None:
        governance_root = Path(governance_root).resolve()
        if not governance_root.is_dir():
            findings.append(
                _finding(
                    "workspace.governance_root",
                    f"governance root not found: {governance_root}",
                    anchor="workspace",
                )
            )
        else:
            findings.extend(validate_governance_corpus(governance_root))
    return findings



def validate_governance_corpus(governance_root: Path) -> list[ValidationFinding]:
    governance_root = Path(governance_root).resolve()
    findings: list[ValidationFinding] = []
    for family_dir in _GOVERNED_FAMILY_DIRS:
        base = governance_root / family_dir
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.md")):
            findings.extend(_validate_governed_artifact(path))
    return findings



def _validate_governed_artifact(path: Path) -> list[ValidationFinding]:
    family = path.parent.name
    artifact_id = path.stem
    if family == "is":
        return _validate_issue_record(path, artifact_id)

    text = path.read_text(encoding="utf-8")
    try:
        header = parse_header_block(text)
    except ValueError as exc:
        return [_finding(f"{artifact_id}.header", str(exc), anchor="governance_corpus.header", artifact_id=artifact_id)]

    findings: list[ValidationFinding] = []
    header_key = _HEADER_ID_KEYS.get(family)
    header_id = str(header.get(header_key, "")).strip()
    if header_key and header_id and header_id != artifact_id:
        findings.append(
            _finding(
                f"{artifact_id}.{header_key}",
                f"header {header_key} must match filename stem {artifact_id!r}",
                anchor="governance_corpus.identity",
                artifact_id=artifact_id,
            )
        )
    title = str(header.get("title", "")).strip() or _extract_h1(text)
    if not title:
        findings.append(
            _finding(
                f"{artifact_id}.title",
                "artifact must declare a non-empty title in the header or level-1 heading",
                anchor="governance_corpus.title",
                artifact_id=artifact_id,
            )
        )
    h1 = _extract_h1(text)
    if not h1:
        findings.append(
            _finding(
                f"{artifact_id}.body",
                "artifact body must contain a level-1 title",
                anchor="governance_corpus.body",
                artifact_id=artifact_id,
            )
        )
    elif artifact_id not in h1:
        findings.append(
            _finding(
                f"{artifact_id}.body",
                f"level-1 title must include artifact id {artifact_id}",
                anchor="governance_corpus.body",
                artifact_id=artifact_id,
            )
        )
    return findings



def _validate_issue_record(path: Path, artifact_id: str) -> list[ValidationFinding]:
    text = path.read_text(encoding="utf-8")
    findings: list[ValidationFinding] = []
    h1 = _extract_h1(text)
    if not h1:
        findings.append(
            _finding(
                f"{artifact_id}.body",
                "issue record must contain a level-1 title",
                anchor="governance_corpus.issue_record",
                artifact_id=artifact_id,
            )
        )
    elif artifact_id not in h1:
        findings.append(
            _finding(
                f"{artifact_id}.body",
                f"issue record title must include artifact id {artifact_id}",
                anchor="governance_corpus.issue_record",
                artifact_id=artifact_id,
            )
        )
    for required_heading in ("## Summary", "## Observation", "## Impact / Risk", "## Evidence", "## Change log"):
        if required_heading not in text:
            findings.append(
                _finding(
                    f"{artifact_id}.sections",
                    f"issue record is missing required section {required_heading!r}",
                    anchor="governance_corpus.issue_record",
                    artifact_id=artifact_id,
                )
            )
    if text.startswith("```yaml\n"):
        try:
            header = parse_header_block(text)
        except ValueError as exc:
            findings.append(
                _finding(
                    f"{artifact_id}.header",
                    str(exc),
                    anchor="governance_corpus.issue_record",
                    artifact_id=artifact_id,
                )
            )
        else:
            header_id = str(header.get("is_id", "")).strip()
            if header_id and header_id != artifact_id:
                findings.append(
                    _finding(
                        f"{artifact_id}.is_id",
                        f"header is_id must match filename stem {artifact_id!r}",
                        anchor="governance_corpus.issue_record",
                        artifact_id=artifact_id,
                    )
                )
    return findings



def _extract_h1(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""



def _map_workflow_layer_error(exc: Exception, *, product_root: Path) -> list[ValidationFinding]:
    message = str(exc)
    if message.startswith("lantern_grammar"):
        return [_finding("workspace.grammar", message, anchor="workspace.readiness")]
    if message.startswith("Missing generated artifact ") or message.startswith("Committed "):
        _, _, raw_path = message.partition(": ")
        target = raw_path.strip() if raw_path else "lantern/workflow/definitions"
        return [_finding(_relative_path(target, product_root), message, anchor="workspace.generated_artifacts")]
    if message.startswith("Missing workflow registry") or message.startswith("Missing workflow schema"):
        _, _, raw_path = message.partition(": ")
        return [_finding(_relative_path(raw_path.strip(), product_root), message, anchor="workspace.readiness")]
    return [_finding("workspace.readiness", message, anchor="workspace.readiness")]



def _relative_path(raw_path: str, product_root: Path) -> str:
    try:
        return str(Path(raw_path).resolve().relative_to(product_root))
    except Exception:
        return raw_path
