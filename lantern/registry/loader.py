"""Workbench registry loader and validation helpers for Lantern."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
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

_TEXT_EXTENSIONS = {
    ".py", ".yaml", ".yml", ".json", ".md", ".txt", ".toml", ".ini", ".cfg", ".rst", ".sh"
}
_SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", ".venv", "venv"}
_FORBIDDEN_NAME_PATTERN = re.compile("(?i)(?:" + "tier" + r"[-_ ]?" + "h|_" + "tier" + "_" + "h)")


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

    _validate_against_schema(registry_payload, schema_payload)
    _validate_schema_metadata(registry_payload, schema_metadata)
    validate_gate_coverage(registry_payload, required_gates=schema_metadata["required_full_governed_gates"])

    workbenches = tuple(_build_workbench(entry) for entry in registry_payload["workbenches"])
    return WorkbenchRegistry(
        runtime_surface_classification=registry_payload["runtime_surface_classification"],
        workbenches=workbenches,
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
            "workbench_id set/order mismatch: expected "
            + ", ".join(built_in_ids)
            + "; got "
            + ", ".join(actual_ids)
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
