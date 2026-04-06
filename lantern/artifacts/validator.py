"""Validation helpers for CH-0004 structured mutation requests and outputs."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lantern.artifacts.renderers import parse_header_block
from lantern.workflow.loader import WorkflowWorkbench


ValidationFinding = dict[str, str]


def _finding(path: str, message: str, *, anchor: str) -> ValidationFinding:
    return {"path": path, "message": message, "anchor": anchor}


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
