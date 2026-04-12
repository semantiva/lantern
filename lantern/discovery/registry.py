"""Mechanically derived flat discovery registry for the CH-0021 CLI."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from lantern.artifacts.renderers import parse_header_block
from lantern.workflow.merger import ConfigurationLoader, ConfigurationSurface

_ARTIFACT_DIRS = ("arch", "ch", "ci", "db", "dc", "dec", "dip", "ev", "ini", "is", "q", "spec", "td")
_ARTIFACT_ID_RE = re.compile(r"\b(?:INI|DIP|SPEC|ARCH|CH|TD|DC|DB|CI|EV|DEC|IS|Q)-\d{4}(?:-[0-9a-fA-F-]{36})?\b")
_INDEX_LINK_RE = re.compile(r"\((?P<path>(?:arch|ch|ci|db|dc|dec|dip|ev|ini|is|q|spec|td)/[^)]+\.md)\)")
_ENTITY_ORDER = {
    "artifact": 0,
    "status": 1,
    "gate": 2,
    "mode": 3,
    "workbench": 4,
    "guide": 5,
    "template": 6,
}


def build_discovery_registry(
    *,
    product_root: Path,
    governance_root: Path,
) -> dict[str, Any]:
    product_root = Path(product_root).resolve()
    governance_root = Path(governance_root).resolve()
    runtime_root = _runtime_root(product_root)
    workbenches = _load_workbenches(runtime_root)
    config_surface = _load_configuration_surface(governance_root)

    records: list[dict[str, Any]] = []
    records.extend(_artifact_records(governance_root))
    records.extend(_status_records(governance_root))
    records.extend(_gate_records(governance_root))
    records.extend(_mode_records(runtime_root, config_surface))
    records.extend(_workbench_records(workbenches, config_surface, governance_root))
    records.extend(_guide_records(runtime_root, workbenches))
    records.extend(_template_records(runtime_root, workbenches))

    return {
        "kind": "discovery_registry",
        "records": sorted(records, key=_record_sort_key),
    }


def list_records(registry: dict[str, Any], **filters: str) -> list[dict[str, Any]]:
    supported = {"id", "family", "title", "status", "gate", "mode", "workbench", "logical_ref", "heading"}
    unknown = set(filters) - supported
    if unknown:
        raise ValueError(f"unsupported discovery filter(s): {sorted(unknown)}")

    result: list[dict[str, Any]] = []
    for record in registry["records"]:
        if "id" in filters and record["token"] != filters["id"]:
            continue
        if "family" in filters and record.get("family") != filters["family"]:
            continue
        if "title" in filters and filters["title"].lower() not in str(record.get("title", "")).lower():
            continue
        if "status" in filters and record.get("status") != filters["status"]:
            continue
        if "gate" in filters and filters["gate"] not in set(record.get("gate_names", ())):
            continue
        if "mode" in filters and filters["mode"] not in {record.get("mode_id"), record.get("token")}:
            continue
        if "workbench" in filters and filters["workbench"] not in {
            record.get("workbench_id"),
            record.get("token"),
        }:
            continue
        if "logical_ref" in filters and filters["logical_ref"] != record.get("logical_ref"):
            continue
        if "heading" in filters:
            headings = [heading.lower() for heading in record.get("heading_labels", ())]
            if filters["heading"].lower() not in headings:
                continue
        result.append(record)
    return result


def show_record(
    registry: dict[str, Any],
    token: str,
    *,
    entity_kind: str | None = None,
    doctor_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    matches = [record for record in registry["records"] if record["token"] == token]
    if entity_kind is not None:
        matches = [record for record in matches if record["entity_kind"] == entity_kind]
    if not matches:
        return {
            "entity_kind": "not_found",
            "token": token,
            "doctor_findings": list((doctor_report or {}).get("findings", [])),
        }
    if len(matches) > 1:
        return {
            "entity_kind": "ambiguity",
            "token": token,
            "candidates": [
                {
                    "entity_kind": record["entity_kind"],
                    "token": record["token"],
                    "title": record.get("title", record["token"]),
                }
                for record in matches
            ],
            "doctor_findings": list((doctor_report or {}).get("findings", [])),
        }
    payload = dict(matches[0])
    payload["doctor_findings"] = list((doctor_report or {}).get("findings", []))
    return payload


def diff_index_inventory(governance_root: Path) -> dict[str, list[str]]:
    governance_root = Path(governance_root).resolve()
    expected = sorted(_expected_index_paths(governance_root))
    actual = sorted(_actual_index_paths(governance_root))
    expected_set = set(expected)
    actual_set = set(actual)
    return {
        "expected": expected,
        "actual": actual,
        "missing": sorted(expected_set - actual_set),
        "stale": sorted(actual_set - expected_set),
    }


def _artifact_records(governance_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family_dir in _ARTIFACT_DIRS:
        base = governance_root / family_dir
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            artifact_id = path.stem
            header, status = _artifact_header_and_status(path, text)
            title = str(header.get("title") or _extract_h1(text) or artifact_id).strip()
            records.append(
                {
                    "entity_kind": "artifact",
                    "token": artifact_id,
                    "logical_ref": artifact_id,
                    "family": family_dir.upper(),
                    "title": title,
                    "status": status,
                    "heading_labels": tuple(_extract_headings(text)),
                    "source_path": path.relative_to(governance_root).as_posix(),
                    "fields": dict(header),
                    "direct_refs": tuple(sorted(_extract_declared_refs(header))),
                    "gate_names": tuple(sorted(_extract_gate_names(text))),
                }
            )
    return records


def _status_records(governance_root: Path) -> list[dict[str, Any]]:
    path = governance_root / "workflow" / "artifact_status_contract.yaml"
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    grouped: dict[str, dict[str, Any]] = {}
    for item in payload.get("families", []):
        family = item["family"]
        for status in item.get("canonical_statuses", []):
            record = grouped.setdefault(
                status,
                {
                    "entity_kind": "status",
                    "token": status,
                    "logical_ref": status,
                    "family": "MULTI",
                    "title": status,
                    "status": status,
                    "heading_labels": (),
                    "source_path": path.relative_to(governance_root).as_posix(),
                    "fields": {
                        "families": [],
                        "grammar_mappings": {},
                    },
                    "direct_refs": (),
                    "gate_names": (),
                },
            )
            record["fields"]["families"].append(family)
            mapping = item.get("grammar_mapping", {}).get(status)
            if mapping is not None:
                record["fields"]["grammar_mappings"][family] = mapping
    return list(grouped.values())


def _gate_records(governance_root: Path) -> list[dict[str, Any]]:
    path = governance_root / "workflow" / "gate_post_conditions.yaml"
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    records: list[dict[str, Any]] = []
    for item in payload.get("gates", []):
        token = item["gate"]
        records.append(
            {
                "entity_kind": "gate",
                "token": token,
                "logical_ref": token,
                "title": token,
                "status": None,
                "heading_labels": (),
                "source_path": path.relative_to(governance_root).as_posix(),
                "fields": dict(item),
                "direct_refs": (),
                "gate_names": (token,),
            }
        )
    return records


def _mode_records(product_root: Path, config_surface: ConfigurationSurface | None) -> list[dict[str, Any]]:
    if config_surface is not None and config_surface.workflow_modes:
        return [
            {
                "entity_kind": "mode",
                "token": mode.mode_id,
                "logical_ref": mode.mode_id,
                "title": mode.mode_id,
                "status": None,
                "heading_labels": (),
                "source_path": (config_surface.folder / "main.yaml")
                .relative_to(config_surface.folder.parent.parent)
                .as_posix(),
                "fields": {
                    "mode_id": mode.mode_id,
                    "entry_workbench": mode.entry_workbench,
                    "guide_refs": list(mode.guide_refs),
                },
                "entry_workbench": mode.entry_workbench,
                "guide_refs": list(mode.guide_refs),
                "mode_id": mode.mode_id,
                "direct_refs": (),
                "gate_names": (),
            }
            for mode in config_surface.workflow_modes
        ]

    from lantern._compat import get_package_resource_path

    manifest_path = get_package_resource_path("skills/packaged_default/skill-manifest.json")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [
        {
            "entity_kind": "mode",
            "token": item["mode_id"],
            "logical_ref": item["mode_id"],
            "title": item["mode_id"],
            "status": None,
            "heading_labels": (),
            "source_path": manifest_path.relative_to(product_root).as_posix(),
            "fields": dict(item),
            "entry_workbench": item["entry_workbench_id"],
            "guide_refs": list(item.get("resource_refs", [])),
            "mode_id": item["mode_id"],
            "direct_refs": (),
            "gate_names": (),
        }
        for item in payload.get("workflow_modes", [])
    ]


def _workbench_records(
    workbenches: list[dict[str, Any]],
    config_surface: ConfigurationSurface | None,
    governance_root: Path,
) -> list[dict[str, Any]]:
    overrides = _load_workbench_overrides(config_surface)
    records: list[dict[str, Any]] = []
    for workbench in workbenches:
        workbench_id = workbench["workbench_id"]
        override = overrides.get(workbench_id, {})
        instruction_resource = override.get("instruction_resource", workbench["instruction_resource"])
        authoritative_guides = tuple(override.get("authoritative_guides", workbench["authoritative_guides"]))
        records.append(
            {
                "entity_kind": "workbench",
                "token": workbench_id,
                "logical_ref": workbench_id,
                "title": workbench["display_name"],
                "status": None,
                "heading_labels": (),
                "source_path": _override_source_path(config_surface, workbench_id, governance_root),
                "fields": {
                    "display_name": workbench["display_name"],
                    "instruction_resource": instruction_resource,
                    "authoritative_guides": list(authoritative_guides),
                    "administration_guides": list(workbench["administration_guides"]),
                    "contract_refs": list(workbench["contract_refs"]),
                    "inspect_views": list(workbench["inspect_views"]),
                },
                "workbench_id": workbench_id,
                "instruction_resource": instruction_resource,
                "authoritative_guides": list(authoritative_guides),
                "mode_id": None,
                "direct_refs": (),
                "gate_names": tuple(sorted(_workbench_gate_names(workbench["lifecycle_placement"]))),
            }
        )
    return records


def _guide_records(product_root: Path, workbenches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_path = product_root / "lantern" / "workflow" / "definitions" / "resource_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    workbench_by_id = {workbench["workbench_id"]: workbench for workbench in workbenches}

    records: list[dict[str, Any]] = []
    for item in payload:
        roles = set(item.get("roles", ()))
        if not roles & {"authoritative_guides", "administration_guides"}:
            continue
        rel_path = item["path"]
        body = (product_root / rel_path).read_text(encoding="utf-8")
        workbench = workbench_by_id.get(item["workbench_id"])
        records.append(
            {
                "entity_kind": "guide",
                "token": item["resource_id"],
                "logical_ref": item["resource_id"],
                "title": _resource_title(body, rel_path),
                "status": None,
                "heading_labels": tuple(_extract_headings(body)),
                "source_path": rel_path,
                "fields": {
                    "kind": item["kind"],
                    "roles": list(item["roles"]),
                    "content_hash": item["content_hash"],
                    "provenance_refs": list(item.get("provenance_refs", [])),
                },
                "workbench_id": item["workbench_id"],
                "mode_id": None,
                "direct_refs": (),
                "gate_names": (
                    tuple(sorted(_workbench_gate_names(workbench["lifecycle_placement"]))) if workbench else ()
                ),
            }
        )
    return records


def _template_records(product_root: Path, workbenches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for workbench in workbenches:
        for family in workbench["draftable_artifact_families"]:
            rel_path = f"lantern/templates/TEMPLATE__{family}.md"
            abs_path = product_root / rel_path
            if not abs_path.exists():
                continue
            body = abs_path.read_text(encoding="utf-8")
            records.append(
                {
                    "entity_kind": "template",
                    "token": _template_resource_id(workbench["workbench_id"], family),
                    "logical_ref": _template_resource_id(workbench["workbench_id"], family),
                    "title": _resource_title(body, rel_path),
                    "status": None,
                    "heading_labels": tuple(_extract_headings(body)),
                    "source_path": rel_path,
                    "fields": {
                        "kind": "template",
                        "roles": ["artifact_templates"],
                        "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    },
                    "workbench_id": workbench["workbench_id"],
                    "mode_id": None,
                    "direct_refs": (),
                    "gate_names": tuple(sorted(_workbench_gate_names(workbench["lifecycle_placement"]))),
                }
            )
    return records


def _load_configuration_surface(governance_root: Path) -> ConfigurationSurface | None:
    config_root = governance_root / "workflow" / "configuration"
    if not config_root.exists():
        return None
    loader = ConfigurationLoader()
    return loader.load_and_validate(config_root)


def _load_workbench_overrides(
    config_surface: ConfigurationSurface | None,
) -> dict[str, dict[str, Any]]:
    if config_surface is None:
        return {}
    overrides: dict[str, dict[str, Any]] = {}
    for override in config_surface.workbench_overrides:
        override_path = config_surface.folder / override.file
        overrides[override.workbench_id] = yaml.safe_load(override_path.read_text(encoding="utf-8")) or {}
    return overrides


def _override_source_path(
    config_surface: ConfigurationSurface | None,
    workbench_id: str,
    governance_root: Path,
) -> str:
    if config_surface is None:
        return "lantern/workflow/definitions/workbench_registry.yaml"
    for override in config_surface.workbench_overrides:
        if override.workbench_id == workbench_id:
            return (config_surface.folder / override.file).relative_to(governance_root).as_posix()
    return "lantern/workflow/definitions/workbench_registry.yaml"


def _load_workbenches(product_root: Path) -> list[dict[str, Any]]:
    registry_path = product_root / "lantern" / "workflow" / "definitions" / "workbench_registry.yaml"
    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    records: list[dict[str, Any]] = []
    for item in payload.get("workbenches", []):
        workflow_surface = item.get("workflow_surface") or {}
        records.append(
            {
                "workbench_id": item["workbench_id"],
                "display_name": item["display_name"],
                "lifecycle_placement": item.get("lifecycle_placement") or {},
                "instruction_resource": item.get("instruction_resource", ""),
                "authoritative_guides": tuple(item.get("authoritative_guides", [])),
                "administration_guides": tuple(item.get("administration_guides", [])),
                "contract_refs": tuple(workflow_surface.get("contract_refs", [])),
                "inspect_views": tuple(workflow_surface.get("inspect_views", [])),
                "draftable_artifact_families": tuple(workflow_surface.get("draftable_artifact_families", [])),
            }
        )
    return records


def _workbench_gate_names(placement: dict[str, Any]) -> set[str]:
    if placement.get("kind") == "covered_gates":
        return set(placement.get("covered_gates", []))
    gates: set[str] = set()
    if placement.get("start_gate"):
        gates.add(placement["start_gate"])
    if placement.get("end_gate"):
        gates.add(placement["end_gate"])
    return gates


def _template_resource_id(workbench_id: str, family: str) -> str:
    identifier = _sanitize_identifier(f"{workbench_id}_artifact_templates_TEMPLATE__{family}")
    return f"resource.template.{identifier}"


def _sanitize_identifier(value: str) -> str:
    value = value.lower().replace("-", "_")
    value = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)
    while "__" in value:
        value = value.replace("__", "_")
    return value.strip("_")


def _resource_title(text: str, rel_path: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return Path(rel_path).stem


def _extract_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def _extract_h1(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _extract_declared_refs(header: Any) -> set[str]:
    refs: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                walk(nested)
            return
        if isinstance(value, str):
            refs.update(_ARTIFACT_ID_RE.findall(value))

    walk(header)
    return refs


def _extract_gate_names(text: str) -> set[str]:
    return set(re.findall(r"\bGT-\d{3}\b", text))


def _expected_index_paths(governance_root: Path) -> set[str]:
    expected: set[str] = set()
    for family_dir in _ARTIFACT_DIRS:
        base = governance_root / family_dir
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.md")):
            expected.add(path.relative_to(governance_root).as_posix())
    return expected


def _actual_index_paths(governance_root: Path) -> set[str]:
    index_path = governance_root / "INDEX.md"
    if not index_path.exists():
        return set()
    content = index_path.read_text(encoding="utf-8")
    return {match.group("path") for match in _INDEX_LINK_RE.finditer(content)}


def _record_sort_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _ENTITY_ORDER.get(record["entity_kind"], 999),
        record["token"],
        record.get("title", ""),
    )


def _artifact_header_and_status(path: Path, text: str) -> tuple[dict[str, Any], str | None]:
    if path.parent.name == "is":
        status_match = re.search(r"^Status:\s*(?P<status>[A-Z_]+)\s*$", text, re.MULTILINE)
        return {}, status_match.group("status") if status_match else None
    header = parse_header_block(text)
    status = header.get("status")
    return dict(header), status if isinstance(status, str) else status


def _runtime_root(product_root: Path) -> Path:
    candidate = product_root / "lantern" / "workflow" / "definitions" / "workbench_registry.yaml"
    if candidate.exists():
        return product_root
    return Path(__file__).resolve().parents[2]
