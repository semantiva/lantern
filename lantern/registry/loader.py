"""Workbench registry loader and validation helpers for Lantern."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

import yaml
from jsonschema import Draft7Validator

from .models import (
    LifecyclePlacement,
    NameViolation,
    WorkbenchDeclaration,
    WorkbenchRegistry,
    WorkflowSurface,
)

DEFAULT_DEFINITIONS_ROOT = Path(__file__).resolve().parents[1] / "workflow" / "definitions"
DEFAULT_REGISTRY_PATH = DEFAULT_DEFINITIONS_ROOT / "workbench_registry.yaml"
DEFAULT_SCHEMA_YAML_PATH = DEFAULT_DEFINITIONS_ROOT / "workbench_schema.yaml"
DEFAULT_SCHEMA_JSON_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "schemas" / "workbench_schema.json"

_TEXT_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".md", ".txt", ".toml", ".ini", ".cfg", ".rst", ".sh"}
_SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv"}
_FORBIDDEN_NAME_PATTERN = re.compile(
    "(?i)(?:" + "tier" + r"[-_ ]?" + "h|_" + "tier" + "_" + "h|" + "lantern" + "-" + "governance" + ")"
)
_CONTRACT_REF_PATTERN = re.compile(r"^contract\.[a-z0-9_]+(?:\.[a-z0-9_]+)*\.v\d+$")
_FOUNDATION_WORKFLOW_SURFACE_FIELDS = frozenset(
    {
        "allowed_transaction_kinds",
        "draftable_artifact_families",
        "contract_refs",
        "inspect_views",
    }
)


def load_workbench_registry(
    *,
    registry_path: str | Path | None = None,
    schema_yaml_path: str | Path | None = None,
    schema_json_path: str | Path | None = None,
) -> WorkbenchRegistry:
    registry_file = Path(registry_path or DEFAULT_REGISTRY_PATH)
    schema_yaml_file = Path(schema_yaml_path or DEFAULT_SCHEMA_YAML_PATH)
    schema_json_file = Path(schema_json_path or DEFAULT_SCHEMA_JSON_PATH)

    registry_payload = _load_yaml(registry_file)
    schema_metadata = _load_yaml(schema_yaml_file)
    schema_payload = json.loads(schema_json_file.read_text(encoding="utf-8"))

    return _build_projected_workbench_registry(
        registry_payload=registry_payload,
        schema_metadata=schema_metadata,
        schema_payload=schema_payload,
    )


def validate_gate_coverage(payload: Mapping[str, Any], *, required_gates: Sequence[str]) -> None:
    if payload.get("runtime_surface_classification") != "full_governed_surface":
        return
    covered: set[str] = set()
    for entry in payload.get("workbenches", []):
        if not entry.get("enabled", True):
            continue
        placement = entry.get("lifecycle_placement", {})
        if placement.get("kind") == "covered_gates":
            covered.update(str(item) for item in placement.get("covered_gates", []))
    missing = [gate for gate in required_gates if gate not in covered]
    if missing:
        raise ValueError("full_governed_surface has uncovered required gates: " + ", ".join(missing))


def _validate_workflow_references(payload: Mapping[str, Any]) -> None:
    errors: list[str] = []
    for entry in payload.get("workbenches", []):
        workbench_id = str(entry.get("workbench_id", "<unknown-workbench>"))
        _append_resource_ref_error(errors, workbench_id, "instruction_resource", entry.get("instruction_resource"))
        _append_resource_ref_list_errors(
            errors, workbench_id, "authoritative_guides", entry.get("authoritative_guides", [])
        )
        _append_resource_ref_list_errors(
            errors, workbench_id, "administration_guides", entry.get("administration_guides", [])
        )
        workflow_surface = entry.get("workflow_surface", {})
        _append_contract_ref_errors(errors, workbench_id, workflow_surface.get("contract_refs", []))
    if errors:
        raise ValueError("; ".join(errors))


def _append_resource_ref_list_errors(
    errors: list[str],
    workbench_id: str,
    field: str,
    values: Sequence[Any],
) -> None:
    for index, value in enumerate(values):
        _append_resource_ref_error(errors, workbench_id, f"{field}[{index}]", value)


def _append_resource_ref_error(
    errors: list[str],
    workbench_id: str,
    field: str,
    value: Any,
) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{workbench_id}.{field} must be a non-empty Lantern-local markdown path")
        return
    candidate = PurePosixPath(value.strip())
    if (
        candidate.is_absolute()
        or not candidate.parts
        or candidate.parts[0] != "lantern"
        or ".." in candidate.parts
        or candidate.suffix != ".md"
    ):
        errors.append(f"{workbench_id}.{field} must be a Lantern-local markdown path under 'lantern/': {value!r}")


def _append_contract_ref_errors(
    errors: list[str],
    workbench_id: str,
    values: Sequence[Any],
) -> None:
    for index, value in enumerate(values):
        if not isinstance(value, str) or not _CONTRACT_REF_PATTERN.match(value):
            errors.append(
                f"{workbench_id}.workflow_surface.contract_refs[{index}] must match 'contract.<name>.vN': {value!r}"
            )


def scan_forbidden_names(root: str | Path) -> list[NameViolation]:
    root_path = Path(root)
    violations: list[NameViolation] = []
    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix and path.suffix.lower() not in _TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if _FORBIDDEN_NAME_PATTERN.search(line):
                violations.append(
                    NameViolation(
                        path=str(path.relative_to(root_path)),
                        line_number=line_number,
                        line_text=line.strip(),
                    )
                )
    return violations


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _project_foundation_registry_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    projection = json.loads(json.dumps(payload))
    for workbench in projection.get("workbenches", []):
        workflow_surface = workbench.get("workflow_surface")
        if not isinstance(workflow_surface, dict):
            continue
        for field in tuple(workflow_surface.keys()):
            if field not in _FOUNDATION_WORKFLOW_SURFACE_FIELDS:
                workflow_surface.pop(field, None)
    return projection


def _build_projected_workbench_registry(
    *,
    registry_payload: Mapping[str, Any],
    schema_metadata: Mapping[str, Any],
    schema_payload: Mapping[str, Any],
) -> WorkbenchRegistry:
    projected_payload = _project_foundation_registry_payload(registry_payload)

    _validate_against_schema(projected_payload, schema_payload)
    _validate_schema_metadata(projected_payload, schema_metadata)
    _validate_workflow_references(projected_payload)
    validate_gate_coverage(projected_payload, required_gates=schema_metadata["required_full_governed_gates"])

    workbenches = tuple(_build_workbench(entry) for entry in projected_payload["workbenches"])
    return WorkbenchRegistry(
        runtime_surface_classification=projected_payload["runtime_surface_classification"],
        workbenches=workbenches,
    )


def _validate_against_schema(payload: Mapping[str, Any], schema_payload: Mapping[str, Any]) -> None:
    validator = Draft7Validator(schema_payload)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    if not errors:
        return
    first = errors[0]
    field_path = ".".join(str(token) for token in first.path) or "<root>"
    raise ValueError(f"Schema validation failed at {field_path}: {first.message}")


def _validate_schema_metadata(payload: Mapping[str, Any], metadata: Mapping[str, Any]) -> None:
    built_in_ids = metadata["built_in_workbench_ids"]
    actual_ids = [entry["workbench_id"] for entry in payload["workbenches"]]
    if actual_ids != built_in_ids:
        raise ValueError(
            "workbench_id set/order mismatch: expected " + ", ".join(built_in_ids) + "; got " + ", ".join(actual_ids)
        )


def _build_workbench(entry: Mapping[str, Any]) -> WorkbenchDeclaration:
    lifecycle = _build_lifecycle(entry["lifecycle_placement"])
    workflow_surface = WorkflowSurface(
        allowed_transaction_kinds=_as_tuple(entry["workflow_surface"]["allowed_transaction_kinds"]),
        draftable_artifact_families=_as_tuple(entry["workflow_surface"]["draftable_artifact_families"]),
        contract_refs=_as_tuple(entry["workflow_surface"]["contract_refs"]),
        inspect_views=_as_tuple(entry["workflow_surface"]["inspect_views"]),
    )
    return WorkbenchDeclaration(
        workbench_id=entry["workbench_id"],
        display_name=entry["display_name"],
        lifecycle_placement=lifecycle,
        artifacts_in_scope=_as_tuple(entry["artifacts_in_scope"]),
        intent_classes=_as_tuple(entry["intent_classes"]),
        posture_constraints=_as_tuple(entry["posture_constraints"]),
        workflow_surface=workflow_surface,
        instruction_resource=entry["instruction_resource"],
        authoritative_guides=_as_tuple(entry["authoritative_guides"]),
        administration_guides=_as_tuple(entry["administration_guides"]),
        entry_conditions=_as_tuple(entry["entry_conditions"]),
        exit_conditions=_as_tuple(entry["exit_conditions"]),
        source=entry["source"],
        enabled=bool(entry["enabled"]),
        governance_mode=entry["governance_mode"],
        content_hash=_compute_content_hash(entry),
    )


def _build_lifecycle(payload: Mapping[str, Any]) -> LifecyclePlacement:
    return LifecyclePlacement(
        kind=payload["kind"],
        covered_gates=_as_tuple(payload.get("covered_gates", [])),
        start_gate=payload.get("start_gate"),
        end_gate=payload.get("end_gate"),
    )


def _as_tuple(values: Iterable[Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in values)


def _compute_content_hash(entry: Mapping[str, Any]) -> str:
    normalized = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
