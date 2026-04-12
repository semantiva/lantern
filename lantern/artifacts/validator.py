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

"""Validation helpers for CH-0004 requests and CH-0009 MVP-hardening checks."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from lantern.artifacts.renderers import parse_header_block
from lantern.workflow.loader import (
    DEFAULT_CONTRACT_CATALOG_PATH,
    DEFAULT_REGISTRY_PATH,
    DEFAULT_RELOCATION_MANIFEST_PATH,
    DEFAULT_RESOURCE_MANIFEST_PATH,
    DEFAULT_SCHEMA_PATH,
    DEFAULT_TRANSACTION_PROFILES_PATH,
    DEFAULT_WORKBENCH_BINDINGS_PATH,
    DEFAULT_WORKFLOW_MAP_PATH,
    WorkflowWorkbench,
)


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
DEFAULT_STATUS_CONTRACT_PATH = (
    Path(__file__).resolve().parents[1] / "workflow" / "definitions" / "artifact_status_contract.json"
)
_ISSUE_STATUS_RE = re.compile(r"^Status:\s*(?P<status>[A-Za-z_][A-Za-z_ ]*)\s*$", re.MULTILINE)
_ACTIVE_CI_STATUSES = {"Draft", "Candidate", "Selected"}
_GT130_EXTENSION_REQUIRED_FLAGS = (
    "discovered_during_gt130",
    "bounded_integration_gap",
    "no_spec_changes",
    "no_test_changes",
    "no_design_baseline_changes",
    "no_architectural_baseline_changes",
)


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
    extension_evidence_path = payload.get("extension_evidence_path")
    extension_decision_path = payload.get("extension_decision_path")
    if bool(extension_evidence_path) != bool(extension_decision_path):
        findings.append(
            _finding(
                "payload.extension_evidence_path",
                "extension_evidence_path and extension_decision_path must be supplied together",
                anchor="selected_ci_application.gt130_extension",
            )
        )
    for field_name in ("extension_evidence_path", "extension_decision_path"):
        value = payload.get(field_name)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            findings.append(
                _finding(
                    f"payload.{field_name}",
                    f"{field_name} must be a non-empty string when supplied",
                    anchor="selected_ci_application.gt130_extension",
                )
            )
    for index, operation in enumerate(operations):
        path = f"payload.operations[{index}]"
        if not isinstance(operation, Mapping):
            findings.append(
                _finding(
                    path,
                    "operation must be an object",
                    anchor="server_owned_contract.request_schemas.commit.properties.operations.items",
                )
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


def extract_allowed_change_surface(header: Mapping[str, Any]) -> tuple[str, ...]:
    allowed = header.get("allowed_change_surface")
    if isinstance(allowed, str):
        return tuple(part.strip() for part in allowed.split(",") if part.strip())
    if isinstance(allowed, list):
        return tuple(str(item).strip() for item in allowed if str(item).strip())
    raise ValueError("selected CI artifact is missing allowed_change_surface")


def resolve_gt130_extension_surface(
    *,
    evidence_path: Path,
    decision_path: Path,
    expected_ci_id: str | None = None,
) -> tuple[str, ...]:
    evidence_header = parse_header_block(Path(evidence_path).read_text(encoding="utf-8"))
    evidence_id = str(evidence_header.get("ev_id") or Path(evidence_path).stem)
    evidence_findings = _validate_gt130_extension_evidence(evidence_header, evidence_id)
    if evidence_findings:
        raise ValueError("; ".join(finding["message"] for finding in evidence_findings))

    decision_header = parse_header_block(Path(decision_path).read_text(encoding="utf-8"))
    decision_id = str(decision_header.get("dec_id") or Path(decision_path).stem)
    decision_findings = _validate_gt130_extension_decision(decision_header, decision_id)
    if decision_findings:
        raise ValueError("; ".join(finding["message"] for finding in decision_findings))

    allowed_paths = _normalize_string_list(evidence_header["gt130_extension"].get("allowed_paths"))
    if expected_ci_id is not None:
        ci_refs = _extract_reference_values(evidence_header.get("references"), "ci", "cis")
        if expected_ci_id not in ci_refs:
            raise ValueError(
                f"GT-130 extension evidence {evidence_id!r} does not reference selected CI {expected_ci_id!r}"
            )
        decision_ci_refs = _extract_reference_values(decision_header.get("references"), "ci", "cis")
        if decision_ci_refs and expected_ci_id not in decision_ci_refs:
            raise ValueError(
                f"GT-130 extension decision {decision_id!r} does not reference selected CI {expected_ci_id!r}"
            )

    decision_evidence_refs = _extract_reference_values(decision_header.get("references"), "evidence")
    if evidence_id not in decision_evidence_refs:
        raise ValueError(f"GT-130 extension decision {decision_id!r} does not reference evidence {evidence_id!r}")

    decision_extension = decision_header.get("gt130_extension")
    if isinstance(decision_extension, Mapping):
        approved_paths = _normalize_string_list(decision_extension.get("approved_paths"))
        evidence_ref = str(decision_extension.get("evidence_ref", "")).strip()
        if evidence_ref and evidence_ref != evidence_id:
            raise ValueError(
                f"GT-130 extension decision {decision_id!r} points to evidence {evidence_ref!r}, expected {evidence_id!r}"
            )
        if approved_paths and approved_paths != allowed_paths:
            raise ValueError(
                f"GT-130 extension decision {decision_id!r} approved paths do not match evidence {evidence_id!r}"
            )
    return allowed_paths


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


@lru_cache(maxsize=8)
def load_status_contract(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path or DEFAULT_STATUS_CONTRACT_PATH)
    if not target.exists():
        raise FileNotFoundError(f"Missing generated artifact artifact_status_contract.json: {target}")
    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get("projection_kind") != "artifact_status_contract":
        raise ValueError(f"invalid status-contract projection: {target}")
    families = payload.get("families")
    if not isinstance(families, dict) or not families:
        raise ValueError(f"status-contract projection has no family map: {target}")
    return payload


def validate_status_transition(family: str, from_status: str, to_status: str) -> list[ValidationFinding]:
    contract = load_status_contract()
    rule = _family_contract(family, contract)
    from_findings = _validate_family_status(family, from_status, artifact_id=family, contract=contract)
    to_findings = _validate_family_status(family, to_status, artifact_id=family, contract=contract)
    if from_findings or to_findings:
        return [
            _finding(
                f"{family}.transition",
                f"{family} transition {from_status!r} -> {to_status!r} is not allowed by the authoritative status contract",
                anchor="status_contract.transition",
                artifact_id=family,
            )
        ]
    allowed = {(item["from"], item["to"]) for item in rule["transitions"]}
    if (from_status, to_status) in allowed:
        return []
    return [
        _finding(
            f"{family}.transition",
            f"{family} transition {from_status!r} -> {to_status!r} is not allowed by the authoritative status contract",
            anchor="status_contract.transition",
            artifact_id=family,
        )
    ]


def audit_legacy_status_values(governance_root: Path) -> list[dict[str, str]]:
    governance_root = Path(governance_root).resolve()
    contract = load_status_contract()
    results: list[dict[str, str]] = []
    for family_dir in _GOVERNED_FAMILY_DIRS:
        family = family_dir.upper()
        base = governance_root / family_dir
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.md")):
            artifact_id = path.stem
            text = path.read_text(encoding="utf-8")
            if family == "IS":
                current = _extract_issue_status(text)
            elif text.startswith("```yaml\n"):
                try:
                    current = parse_header_block(text).get("status")
                except ValueError:
                    current = None
            else:
                current = None
            if current is None:
                continue
            alias = _normalization_target(family, str(current).strip(), contract)
            if alias is None:
                continue
            results.append(
                {
                    "artifact_id": artifact_id,
                    "family": family,
                    "path": f"{artifact_id}.status",
                    "current": str(current).strip(),
                    "normalized": alias,
                }
            )
    return results


def _family_contract(family: str, contract: Mapping[str, Any]) -> Mapping[str, Any]:
    return contract["families"][family]


def _normalization_target(family: str, value: str, contract: Mapping[str, Any]) -> str | None:
    rule = _family_contract(family, contract)
    aliases = dict(rule["aliases"])
    if value in aliases:
        if family == "IS":
            issue_rewrites = {"Open": "NEW", "Resolved": "RESOLVED", "Closed": "RESOLVED"}
            if value in issue_rewrites:
                return issue_rewrites[value]
        replacement = aliases[value]
        return replacement if replacement is not None else "<remove status>"
    if rule["normal_path_policy"] == "statusless" and value:
        return "<remove status>"
    return None


def _validate_family_status(
    family: str,
    status_value: str | None,
    *,
    artifact_id: str,
    contract: Mapping[str, Any],
) -> list[ValidationFinding]:
    rule = _family_contract(family, contract)
    policy = rule["normal_path_policy"]
    canonical = tuple(rule["canonical_statuses"])
    aliases = dict(rule["aliases"])

    if policy == "statusless":
        if status_value is None:
            return []
        return [
            _finding(
                f"{artifact_id}.status",
                f"{family} is statusless on the normal path; remove status {status_value!r}",
                anchor="status_contract.lifecycle_exempt",
                artifact_id=artifact_id,
            )
        ]

    if status_value is None or not str(status_value).strip():
        if policy == "allow_record_local_status":
            return []
        return [
            _finding(
                f"{artifact_id}.status",
                f"{family} requires an admissible status from {list(canonical)}",
                anchor="status_contract.status",
                artifact_id=artifact_id,
            )
        ]

    value = str(status_value).strip()
    if value in canonical:
        return []
    if value in aliases:
        replacement = aliases[value]
        action = f"use {replacement!r}" if replacement is not None else "remove the status field"
        return [
            _finding(
                f"{artifact_id}.status",
                f"{family} status {value!r} is legacy-only on the normal path; {action}",
                anchor="status_contract.alias",
                artifact_id=artifact_id,
            )
        ]
    return [
        _finding(
            f"{artifact_id}.status",
            f"{family} status {value!r} is not admissible; expected one of {list(canonical)}",
            anchor="status_contract.status",
            artifact_id=artifact_id,
        )
    ]


def _extract_issue_status(text: str) -> str | None:
    match = _ISSUE_STATUS_RE.search(text)
    return match.group("status").strip() if match else None


def validate_workspace_readiness(
    *,
    product_root: Path,
    governance_root: Path | None = None,
    status_contract_path: Path | None = None,
) -> list[ValidationFinding]:
    """Validate only product-owned runtime readiness.

    Product-repository readiness must not descend into governance-corpus validation.
    A supplied governance_root is treated strictly as a topology/configuration input:
    its presence may be checked, but governance-corpus conformance is owned by the
    governance repository and its own test suite.
    """
    from lantern.workflow.loader import WorkflowLayerError, load_workflow_layer

    findings: list[ValidationFinding] = []
    product_root = Path(product_root).resolve()
    if not product_root.is_dir():
        return [_finding("workspace.product_root", f"product root not found: {product_root}", anchor="workspace")]

    try:
        load_status_contract(status_contract_path)
    except (FileNotFoundError, ValueError) as exc:
        target = Path(status_contract_path or DEFAULT_STATUS_CONTRACT_PATH)
        findings.append(
            _finding(
                _runtime_relative_path(str(target)),
                str(exc),
                anchor="workspace.status_contract",
            )
        )

    loader_kwargs = {
        "registry_path": DEFAULT_REGISTRY_PATH,
        "schema_path": DEFAULT_SCHEMA_PATH,
        "transaction_profiles_path": DEFAULT_TRANSACTION_PROFILES_PATH,
        "contract_catalog_path": DEFAULT_CONTRACT_CATALOG_PATH,
        "resource_manifest_path": DEFAULT_RESOURCE_MANIFEST_PATH,
        "workflow_map_path": DEFAULT_WORKFLOW_MAP_PATH,
        "workbench_resource_bindings_path": DEFAULT_WORKBENCH_BINDINGS_PATH,
        "relocation_manifest_path": DEFAULT_RELOCATION_MANIFEST_PATH,
    }
    try:
        load_workflow_layer(**loader_kwargs)
    except WorkflowLayerError as exc:
        findings.extend(_map_workflow_layer_error(exc))

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
    return findings


def validate_governance_corpus(governance_root: Path) -> list[ValidationFinding]:
    governance_root = Path(governance_root).resolve()
    contract = load_status_contract()
    findings: list[ValidationFinding] = []
    for family_dir in _GOVERNED_FAMILY_DIRS:
        base = governance_root / family_dir
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.md")):
            findings.extend(_validate_governed_artifact(path, contract))
    return findings


def _validate_governed_artifact(path: Path, contract: Mapping[str, Any]) -> list[ValidationFinding]:
    family = path.parent.name
    artifact_id = path.stem
    if family == "is":
        return _validate_issue_record(path, artifact_id, contract)

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
    findings.extend(
        _validate_family_status(
            family.upper(),
            header.get("status"),
            artifact_id=artifact_id,
            contract=contract,
        )
    )
    if family == "ci":
        findings.extend(_validate_ci_change_surface_justifications(header, artifact_id))
    elif family == "ev":
        findings.extend(_validate_gt130_extension_evidence(header, artifact_id))
    elif family == "dec":
        findings.extend(_validate_gt130_extension_decision(header, artifact_id))
    return findings


def _validate_issue_record(path: Path, artifact_id: str, contract: Mapping[str, Any]) -> list[ValidationFinding]:
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
    findings.extend(
        _validate_family_status(
            "IS",
            _extract_issue_status(text),
            artifact_id=artifact_id,
            contract=contract,
        )
    )
    return findings


def _extract_h1(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def _validate_ci_change_surface_justifications(
    header: Mapping[str, Any],
    artifact_id: str,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    try:
        allowed_paths = extract_allowed_change_surface(header)
    except ValueError as exc:
        return [
            _finding(
                f"{artifact_id}.allowed_change_surface",
                str(exc),
                anchor="governance_corpus.ci_change_surface",
                artifact_id=artifact_id,
            )
        ]
    init_paths = tuple(path for path in allowed_paths if path.endswith("__init__.py"))
    if not init_paths:
        return findings
    if str(header.get("status", "")).strip() not in _ACTIVE_CI_STATUSES:
        return findings

    justifications = header.get("change_surface_justifications")
    if not isinstance(justifications, list) or not justifications:
        return [
            _finding(
                f"{artifact_id}.change_surface_justifications",
                "active CI records that include __init__.py in allowed_change_surface must declare change_surface_justifications",
                anchor="governance_corpus.ci_change_surface",
                artifact_id=artifact_id,
            )
        ]

    covered_paths: set[str] = set()
    for index, justification in enumerate(justifications):
        if not isinstance(justification, Mapping):
            findings.append(
                _finding(
                    f"{artifact_id}.change_surface_justifications[{index}]",
                    "change-surface justification entries must be mappings with path and rationale",
                    anchor="governance_corpus.ci_change_surface",
                    artifact_id=artifact_id,
                )
            )
            continue
        path = str(justification.get("path", "")).strip()
        rationale = str(justification.get("rationale", "")).strip()
        if not path:
            findings.append(
                _finding(
                    f"{artifact_id}.change_surface_justifications[{index}].path",
                    "change-surface justification path must be a non-empty string",
                    anchor="governance_corpus.ci_change_surface",
                    artifact_id=artifact_id,
                )
            )
        if not rationale:
            findings.append(
                _finding(
                    f"{artifact_id}.change_surface_justifications[{index}].rationale",
                    "change-surface justification rationale must be a non-empty string",
                    anchor="governance_corpus.ci_change_surface",
                    artifact_id=artifact_id,
                )
            )
        if path and rationale:
            covered_paths.add(path)

    for init_path in init_paths:
        if init_path not in covered_paths:
            findings.append(
                _finding(
                    f"{artifact_id}.change_surface_justifications",
                    f"active CI records must justify __init__.py surface entry {init_path!r}",
                    anchor="governance_corpus.ci_change_surface",
                    artifact_id=artifact_id,
                )
            )
    return findings


def _validate_gt130_extension_evidence(
    header: Mapping[str, Any],
    artifact_id: str,
) -> list[ValidationFinding]:
    extension = header.get("gt130_extension")
    if extension is None:
        return []
    if not isinstance(extension, Mapping):
        return [
            _finding(
                f"{artifact_id}.gt130_extension",
                "gt130_extension must be a mapping when present",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        ]

    findings: list[ValidationFinding] = []
    if str(header.get("gate_id", "")).strip() != "GT-130":
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension",
                "gt130_extension is only valid on GT-130 evidence records",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    if str(header.get("evidence_type", "")).strip() != "verification_report":
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension",
                "gt130_extension requires evidence_type 'verification_report'",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    allowed_paths = _normalize_string_list(extension.get("allowed_paths"))
    if not allowed_paths:
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension.allowed_paths",
                "gt130_extension.allowed_paths must declare at least one bounded product path",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    rationale = str(extension.get("rationale", "")).strip()
    if not rationale:
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension.rationale",
                "gt130_extension.rationale must be a non-empty string",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    for flag_name in _GT130_EXTENSION_REQUIRED_FLAGS:
        if extension.get(flag_name) is not True:
            findings.append(
                _finding(
                    f"{artifact_id}.gt130_extension.{flag_name}",
                    f"gt130_extension.{flag_name} must be true",
                    anchor="governance_corpus.gt130_extension",
                    artifact_id=artifact_id,
                )
            )
    return findings


def _validate_gt130_extension_decision(
    header: Mapping[str, Any],
    artifact_id: str,
) -> list[ValidationFinding]:
    extension = header.get("gt130_extension")
    if extension is None:
        return []
    if not isinstance(extension, Mapping):
        return [
            _finding(
                f"{artifact_id}.gt130_extension",
                "gt130_extension must be a mapping when present",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        ]

    findings: list[ValidationFinding] = []
    if str(header.get("gate_id", "")).strip() != "GT-130":
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension",
                "gt130_extension is only valid on GT-130 decision records",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    if str(header.get("decision_type", "")).strip() != "gate":
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension",
                "gt130_extension requires decision_type 'gate'",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    if str(header.get("outcome", "")).strip() != "PASS":
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension",
                "gt130_extension approval requires outcome 'PASS'",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    evidence_ref = str(extension.get("evidence_ref", "")).strip()
    if not evidence_ref:
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension.evidence_ref",
                "gt130_extension.evidence_ref must point to the approving EV record",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    approved_paths = _normalize_string_list(extension.get("approved_paths"))
    if not approved_paths:
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension.approved_paths",
                "gt130_extension.approved_paths must declare at least one bounded product path",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    referenced_evidence = _extract_reference_values(header.get("references"), "evidence")
    if evidence_ref and evidence_ref not in referenced_evidence:
        findings.append(
            _finding(
                f"{artifact_id}.gt130_extension.evidence_ref",
                f"gt130_extension.evidence_ref {evidence_ref!r} must appear in references.evidence",
                anchor="governance_corpus.gt130_extension",
                artifact_id=artifact_id,
            )
        )
    return findings


def _normalize_string_list(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def _extract_reference_values(references: Any, *keys: str) -> tuple[str, ...]:
    if not isinstance(references, Mapping):
        return ()
    values: list[str] = []
    for key in keys:
        values.extend(_normalize_string_list(references.get(key)))
    return tuple(dict.fromkeys(values))


def _map_workflow_layer_error(exc: Exception) -> list[ValidationFinding]:
    message = str(exc)
    if message.startswith("lantern_grammar"):
        return [_finding("workspace.grammar", message, anchor="workspace.readiness")]
    if message.startswith("Missing generated artifact ") or message.startswith("Committed "):
        _, _, raw_path = message.partition(": ")
        target = raw_path.strip() if raw_path else "lantern/workflow/definitions"
        return [_finding(_runtime_relative_path(target), message, anchor="workspace.generated_artifacts")]
    if message.startswith("Missing workflow registry") or message.startswith("Missing workflow schema"):
        _, _, raw_path = message.partition(": ")
        return [_finding(_runtime_relative_path(raw_path.strip()), message, anchor="workspace.readiness")]
    return [_finding("workspace.readiness", message, anchor="workspace.readiness")]


def _runtime_relative_path(raw_path: str) -> str:
    runtime_package_root = Path(__file__).resolve().parents[1]
    runtime_repo_root = runtime_package_root.parent
    candidate = Path(raw_path)
    try:
        resolved = candidate.resolve()
    except Exception:
        return raw_path
    try:
        return str(resolved.relative_to(runtime_repo_root))
    except Exception:
        return raw_path
