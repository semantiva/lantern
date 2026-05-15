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

"""Grammar-backed workflow layer loader for Lantern."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Mapping

if TYPE_CHECKING:
    from lantern.workflow.merger import EffectiveLayer

import yaml

from lantern._compat import GrammarCompatibilityError, require_supported_grammar

_GRAMMAR_IMPORT_ERROR: Exception | None = None
Grammar: Any = None
Lifecycle: Any = None
LanternGrammarLoadError: type[Exception] = RuntimeError

try:
    from lantern_grammar import (
        Grammar as ImportedGrammar,
        Lifecycle as ImportedLifecycle,
        LanternGrammarLoadError as ImportedLoadError,
    )
except Exception as exc:  # pragma: no cover - exercised in runtime environments missing the package
    _GRAMMAR_IMPORT_ERROR = exc
else:
    Grammar = ImportedGrammar
    Lifecycle = ImportedLifecycle
    LanternGrammarLoadError = ImportedLoadError
    _GRAMMAR_IMPORT_ERROR = None

DEFAULT_DEFINITIONS_ROOT = Path(__file__).resolve().parent / "definitions"
DEFAULT_REGISTRY_PATH = DEFAULT_DEFINITIONS_ROOT / "workbench_registry.yaml"
DEFAULT_SCHEMA_PATH = DEFAULT_DEFINITIONS_ROOT / "workbench_schema.yaml"
DEFAULT_TRANSACTION_PROFILES_PATH = DEFAULT_DEFINITIONS_ROOT / "transaction_profiles.yaml"
DEFAULT_CONTRACT_CATALOG_PATH = DEFAULT_DEFINITIONS_ROOT / "contract_catalog.json"
DEFAULT_RESOURCE_MANIFEST_PATH = DEFAULT_DEFINITIONS_ROOT / "resource_manifest.json"
DEFAULT_WORKFLOW_MAP_PATH = DEFAULT_DEFINITIONS_ROOT / "workflow_map.md"
DEFAULT_WORKBENCH_BINDINGS_PATH = DEFAULT_DEFINITIONS_ROOT / "workbench_resource_bindings.md"
DEFAULT_RELOCATION_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "preservation" / "relocation_manifest.yaml"

_ALLOWED_RESOURCE_ROLES = {
    "instruction_resource",
    "authoritative_guides",
    "administration_guides",
    "artifact_templates",
}
_REQUIRED_ARTIFACT_FAMILIES = {"DIP", "SPEC", "ARCH", "INI", "CH", "TD", "DC", "DB", "CI", "EV", "DEC", "IS"}
_PRIMARY_TRANSACTION_KIND = {
    "upstream_intake_and_baselines": "draft",
    "ch_and_td_readiness": "draft",
    "design_candidate_authoring": "draft",
    "design_selection": "commit",
    "ci_authoring": "draft",
    "ci_selection": "commit",
    "selected_ci_application": "commit",
    "verification_and_closure": "commit",
    "issue_operations": "commit",
    "governance_onboarding": "draft",
}
_RESOURCE_KIND_BY_PREFIX = {
    "lantern/resources/instructions/": "instruction",
    "lantern/resources/guides/": "authoritative_guide",
    "lantern/administration_procedures/": "administration_guide",
    "lantern/authoring_contracts/": "authoring_contract",
    "lantern/templates/": "template",
    "lantern/preservation/": "preservation_doc",
}


class WorkflowLayerError(RuntimeError):
    """Raised when authored or generated workflow artifacts are invalid."""


@dataclass(frozen=True)
class ResponseSurfaceBinding:
    transaction_kind: str
    response_envelope: str
    allowed_resource_roles: tuple[str, ...]


@dataclass(frozen=True)
class TransactionProfile:
    transaction_kind: str
    required_refs: tuple[str, ...]
    bounded_families: tuple[str, ...]
    allowed_contract_refs: tuple[str, ...]
    side_effect_class: str


@dataclass(frozen=True)
class ContractCatalogEntry:
    contract_ref: str
    request_schema_ref: str
    transaction_kind: str
    family_binding: tuple[str, ...]
    gate_binding: tuple[str, ...]
    workbench_refs: tuple[str, ...]
    guide_refs: tuple[str, ...]
    response_surface_bindings: tuple[ResponseSurfaceBinding, ...]
    compatibility: Mapping[str, Any]
    provenance: Mapping[str, Any]


@dataclass(frozen=True)
class ResourceManifestEntry:
    resource_id: str
    kind: str
    workbench_id: str
    path: str
    content_hash: str
    review_status: str
    provenance_type: str
    provenance_refs: tuple[Mapping[str, Any], ...]
    roles: tuple[str, ...]
    projection_trace: Mapping[str, Any]


def _load_grammar():
    if Grammar is None:
        error_detail = f": {_GRAMMAR_IMPORT_ERROR}" if _GRAMMAR_IMPORT_ERROR else ""
        raise WorkflowLayerError(
            f"lantern_grammar public API import failed{error_detail}. Install lantern-grammar into the active Python environment before loading the workflow layer (for example: pip install lantern-grammar)."
        ) from _GRAMMAR_IMPORT_ERROR
    try:
        grammar = Grammar.load()
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise WorkflowLayerError(f"lantern_grammar model bundle not found: {exc}") from exc
    except LanternGrammarLoadError as exc:  # pragma: no cover - defensive
        raise WorkflowLayerError(f"lantern_grammar failed to load: {exc}") from exc
    report = grammar.validate_integrity()
    if not report.get("ok", False):
        raise WorkflowLayerError(f"lantern_grammar integrity validation failed: {report.get('errors', [])}")
    try:
        require_supported_grammar(grammar)
    except GrammarCompatibilityError as exc:
        raise WorkflowLayerError(str(exc)) from exc
    return grammar


_DEFAULT_STATUS_CONTRACT_PATH = DEFAULT_DEFINITIONS_ROOT / "artifact_status_contract.json"

_LIFECYCLE_TO_PROJECTION_FAMILY: dict[str, str] = {
    "lg:artifacts/initiative": "INI",
    "lg:artifacts/dip": "DIP",
    "lg:artifacts/spec": "SPEC",
    "lg:artifacts/arch": "ARCH",
    "lg:artifacts/td": "TD",
    "lg:artifacts/ch": "CH",
    "lg:artifacts/dc": "DC",
    "lg:artifacts/db": "DB",
    "lg:artifacts/ci": "CI",
}


def _validate_lifecycle_bundle(grammar: Any, manifest_path: Path | None = None) -> None:
    if Lifecycle is None:
        return
    path = manifest_path or DEFAULT_LIFECYCLE_POLICY_MANIFEST_PATH
    if not path.exists():
        raise WorkflowLayerError(f"Lifecycle declaration bundle manifest not found: {path}")
    try:
        lc = Lifecycle.from_manifest(grammar, path)
    except Exception as exc:
        raise WorkflowLayerError(f"Lifecycle declaration bundle could not be loaded: {exc}") from exc
    result = lc.validate()
    if not result.ok:
        messages = "; ".join(f"{issue.path}: {issue.message}" for issue in result.issues)
        raise WorkflowLayerError(f"Lifecycle declaration bundle validation failed: {messages}")
    _verify_lifecycle_projection_consistency(path)


def _verify_lifecycle_projection_consistency(manifest_path: Path, status_contract_path: Path | None = None) -> None:
    """Mechanically verify that lifecycle-declared family statuses and transitions match the retained status projection.

    Detects divergence between the lifecycle bundle (authoritative) and artifact_status_contract.json
    (compatibility projection) for lifecycle-declared grammar-semantic families. Reads the bundle's
    family YAML files directly to get declared status IDs and transitions, then compares them against
    the grammar_mapping and transitions in the status projection.
    """
    contract_path = status_contract_path if status_contract_path is not None else _DEFAULT_STATUS_CONTRACT_PATH
    if not contract_path.exists():
        raise WorkflowLayerError(
            f"Lifecycle projection consistency check requires artifact_status_contract.json: {contract_path}"
        )
    projection = json.loads(contract_path.read_text(encoding="utf-8"))
    projection_families = projection.get("families", {})

    if not manifest_path.exists():
        raise WorkflowLayerError(
            f"Lifecycle declaration bundle manifest not found for consistency check: {manifest_path}"
        )
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise WorkflowLayerError(f"Lifecycle declaration bundle manifest is not a mapping: {manifest_path}")
    family_files = manifest.get("families", [])

    bundle_dir = manifest_path.parent
    for family_file in family_files:
        family_yaml_path = bundle_dir / family_file
        if not family_yaml_path.exists():
            raise WorkflowLayerError(
                f"Lifecycle bundle family file declared in manifest but not found: {family_yaml_path}"
            )
        family_data = yaml.safe_load(family_yaml_path.read_text(encoding="utf-8"))
        if not isinstance(family_data, dict):
            raise WorkflowLayerError(f"Lifecycle bundle family file is not a mapping: {family_yaml_path}")

        family_id = str(family_data.get("id", ""))
        short = _LIFECYCLE_TO_PROJECTION_FAMILY.get(family_id)
        if short is None:
            continue
        if short not in projection_families:
            raise WorkflowLayerError(
                f"Lifecycle bundle declares family {family_id!r} (projection key {short!r}) "
                f"but that family is absent from artifact_status_contract.json. "
                f"Regenerate artifact_status_contract.json from the lifecycle bundle."
            )
        grammar_mapping = projection_families[short].get("grammar_mapping", {})
        if not grammar_mapping:
            raise WorkflowLayerError(
                f"Lifecycle projection for {short!r} has absent or empty grammar_mapping in artifact_status_contract.json. "
                f"Regenerate artifact_status_contract.json from the lifecycle bundle."
            )

        # normal_path_policy must not be permissive for lifecycle-declared families
        _lc_policy = projection_families[short].get("normal_path_policy", "")
        _LIFECYCLE_ADMISSIBLE_POLICIES = {"reject_alias", "reject_unknown"}
        if _lc_policy not in _LIFECYCLE_ADMISSIBLE_POLICIES:
            raise WorkflowLayerError(
                f"Lifecycle projection policy broadening detected for {short}: "
                f"normal_path_policy {_lc_policy!r} is not permitted for lifecycle-declared families "
                f"(expected one of {sorted(_LIFECYCLE_ADMISSIBLE_POLICIES)}). "
                f"Regenerate artifact_status_contract.json from the lifecycle bundle."
            )

        # canonical_statuses parity: bundle status labels must exactly match projection canonical_statuses
        bundle_status_labels = {
            s["label"] for s in family_data.get("statuses", []) if isinstance(s, dict) and "label" in s
        }
        projection_canonical = set(projection_families[short].get("canonical_statuses") or [])
        canonical_divergent = bundle_status_labels.symmetric_difference(projection_canonical)
        if canonical_divergent:
            raise WorkflowLayerError(
                f"Lifecycle projection canonical_statuses divergence for {short}: "
                f"lifecycle bundle declares status labels {sorted(bundle_status_labels)} "
                f"but artifact_status_contract.json canonical_statuses is {sorted(projection_canonical)}. "
                f"Divergent: {sorted(canonical_divergent)}. "
                f"Regenerate artifact_status_contract.json from the lifecycle bundle."
            )

        # canonical_statuses ↔ grammar_mapping internal consistency: display key sets must agree
        grammar_mapping_keys = set(grammar_mapping.keys())
        if projection_canonical != grammar_mapping_keys:
            raise WorkflowLayerError(
                f"Lifecycle projection internal inconsistency for {short}: "
                f"canonical_statuses {sorted(projection_canonical)} and grammar_mapping keys "
                f"{sorted(grammar_mapping_keys)} disagree. "
                f"Regenerate artifact_status_contract.json from the lifecycle bundle."
            )

        # Association parity: exact label→grammar-ID mapping from bundle must equal projection grammar_mapping
        expected_mapping = {
            s["label"]: s["id"]
            for s in family_data.get("statuses", [])
            if isinstance(s, dict) and "label" in s and "id" in s
        }
        if expected_mapping != grammar_mapping:
            divergent_labels = {
                k
                for k in set(expected_mapping) | set(grammar_mapping)
                if expected_mapping.get(k) != grammar_mapping.get(k)
            }
            raise WorkflowLayerError(
                f"Lifecycle projection grammar_mapping association divergence for {short}: "
                f"lifecycle bundle declares {sorted((k, v) for k, v in expected_mapping.items())} "
                f"but artifact_status_contract.json grammar_mapping is "
                f"{sorted((k, v) for k, v in grammar_mapping.items())}. "
                f"Divergent label(s): {sorted(divergent_labels)}. "
                f"Regenerate artifact_status_contract.json from the lifecycle bundle."
            )

        # Transition parity: compare bundle transitions vs projection transitions (via grammar_mapping)
        bundle_transitions_raw = [
            t for t in family_data.get("transitions", []) if isinstance(t, dict) and t.get("from") and t.get("to")
        ]
        projection_transitions_raw = projection_families[short].get("transitions", [])
        if bundle_transitions_raw:
            if not isinstance(projection_transitions_raw, list) or not projection_transitions_raw:
                raise WorkflowLayerError(
                    f"Lifecycle projection transition divergence for {short}: "
                    f"lifecycle bundle declares {len(bundle_transitions_raw)} transition(s) but "
                    f"artifact_status_contract.json has no transitions for this family. "
                    f"Regenerate artifact_status_contract.json from the lifecycle bundle."
                )
            bundle_id_to_label = {
                s["id"]: s["label"]
                for s in family_data.get("statuses", [])
                if isinstance(s, dict) and "id" in s and "label" in s
            }
            bundle_transitions_display: set[tuple[str, str]] = set()
            for t in bundle_transitions_raw:
                from_display = bundle_id_to_label.get(t["from"])
                to_display = bundle_id_to_label.get(t["to"])
                if from_display and to_display:
                    bundle_transitions_display.add((from_display, to_display))
            projection_transitions_display: set[tuple[str, str]] = {
                (str(t["from"]), str(t["to"]))
                for t in projection_transitions_raw
                if isinstance(t, dict) and t.get("from") and t.get("to")
            }
            divergent_transitions = bundle_transitions_display.symmetric_difference(projection_transitions_display)
            if divergent_transitions:
                raise WorkflowLayerError(
                    f"Lifecycle projection transition divergence for {short}: "
                    f"divergent transitions: {sorted(str(p) for p in divergent_transitions)}. "
                    f"Regenerate artifact_status_contract.json from the lifecycle bundle."
                )


def _load_yaml(path: Path, label: str) -> Any:
    if not path.exists():
        raise WorkflowLayerError(f"Missing {label}: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_transaction_profiles(profiles_payload: Mapping[str, Any]) -> tuple[TransactionProfile, ...]:
    profiles = []
    seen_kinds: set[str] = set()
    for item in profiles_payload.get("transaction_profiles", []):
        required = {
            "transaction_kind",
            "required_refs",
            "bounded_families",
            "allowed_contract_refs",
            "side_effect_class",
        }
        missing = sorted(required - set(item.keys()))
        if missing:
            raise WorkflowLayerError(f"transaction_profiles entry missing fields: {missing}")
        transaction_kind = str(item["transaction_kind"])
        if transaction_kind in seen_kinds:
            raise WorkflowLayerError(f"transaction_profiles contains duplicate transaction kind {transaction_kind!r}")
        seen_kinds.add(transaction_kind)
        profiles.append(
            TransactionProfile(
                transaction_kind=transaction_kind,
                required_refs=tuple(str(v) for v in item["required_refs"]),
                bounded_families=tuple(str(v) for v in item["bounded_families"]),
                allowed_contract_refs=tuple(str(v) for v in item["allowed_contract_refs"]),
                side_effect_class=str(item["side_effect_class"]),
            )
        )
    if not profiles:
        raise WorkflowLayerError("transaction_profiles.yaml must declare at least one transaction profile")
    return tuple(profiles)


def _validate_grammar_gate_compatibility(
    grammar: Any, workbenches: Iterable[WorkflowWorkbench], grammar_version: str
) -> None:
    for workbench in workbenches:
        gate_ids: list[str] = []
        placement = workbench.lifecycle_placement
        if placement.kind == "covered_gates":
            gate_ids.extend(placement.covered_gates)
        elif placement.kind == "lifecycle_span":
            if placement.start_gate is not None:
                gate_ids.append(placement.start_gate)
            if placement.end_gate is not None:
                gate_ids.append(placement.end_gate)
        for gate_id in gate_ids:
            entity_id = _grammar_gate_entity_id(gate_id)
            entity = grammar.get_entity(entity_id)
            if entity is None:
                raise WorkflowLayerError(
                    f"{workbench.workbench_id} references gate {gate_id!r}, which is not present in lantern_grammar {grammar_version}"
                )
            grammar.gate_dependencies(entity_id)


def _derive_resource_manifest(
    *,
    relocation_manifest: Mapping[str, Any],
    workbenches: tuple[WorkflowWorkbench, ...],
    product_root: Path,
) -> tuple[ResourceManifestEntry, ...]:
    relocation_targets = {entry["target"]: entry for entry in relocation_manifest.get("entries", [])}
    entries: list[ResourceManifestEntry] = []
    for workbench in workbenches:
        refs = [
            ("instruction_resource", workbench.instruction_resource),
            *[("administration_guides", path) for path in workbench.administration_guides],
            *[("authoritative_guides", path) for path in workbench.authoritative_guides],
        ]
        for role, rel_path in refs:
            path = product_root / rel_path
            kind = _resource_kind_for_path(rel_path)
            resource_id = _resource_id(kind, workbench.workbench_id, role, rel_path)
            if not path.exists():
                affected_bindings = [
                    f"{binding.transaction_kind}:{binding.response_envelope}"
                    for binding in workbench.response_surface_bindings
                    if role in binding.allowed_resource_roles
                ]
                raise WorkflowLayerError(
                    f"{workbench.workbench_id} has unresolved resource role {role!r} at path {rel_path!r} "
                    f"(resource_id={resource_id}, affected_response_surface_bindings={affected_bindings})"
                )
            payload = path.read_text(encoding="utf-8")
            if rel_path.startswith("lantern/resources/guides/"):
                guide_meta = _extract_markdown_yaml_header(payload, rel_path)
                provenance_type = str(guide_meta.get("provenance_type", ""))
                if not provenance_type:
                    raise WorkflowLayerError(
                        f"{workbench.workbench_id} authoritative guide {rel_path!r} is missing provenance_type"
                    )
                provenance_refs = tuple(dict(item) for item in guide_meta.get("provenance_refs", []))
                if not provenance_refs:
                    raise WorkflowLayerError(
                        f"{workbench.workbench_id} authoritative guide {rel_path!r} is missing provenance_refs"
                    )
                review_status = "lantern_authored"
                projection_trace = {
                    "derivation": "lantern_authored_guide_surface",
                    "source": "guide_header",
                }
            else:
                if rel_path not in relocation_targets:
                    raise WorkflowLayerError(
                        f"{workbench.workbench_id} references {rel_path!r} for role {role!r}, but it is not traceable to lantern/preservation/relocation_manifest.yaml"
                    )
                relocation_entry = relocation_targets[rel_path]
                provenance_type = str(relocation_entry.get("entry_class", "bridge_copy"))
                if provenance_type not in {"bridge_copy", "product_owned"}:
                    raise WorkflowLayerError(
                        f"{workbench.workbench_id} references {rel_path!r} with unsupported provenance_type {provenance_type!r}; workflow resources must remain reviewed bridge_copy or product_owned surfaces"
                    )
                provenance_refs = (
                    {
                        "path": relocation_entry.get("source", ""),
                        "relocation_entry_id": relocation_entry.get("entry_id", ""),
                    },
                )
                review_status = "reviewed"
                projection_trace = {
                    "derivation": "relocation_manifest_projection",
                    "relocation_entry_id": relocation_entry.get("entry_id", ""),
                }
            resource_id = _resource_id(kind, workbench.workbench_id, role, rel_path)
            entries.append(
                ResourceManifestEntry(
                    resource_id=resource_id,
                    kind=kind,
                    workbench_id=workbench.workbench_id,
                    path=rel_path,
                    content_hash=_sha256_text(payload),
                    review_status=review_status,
                    provenance_type=provenance_type,
                    provenance_refs=provenance_refs,
                    roles=(role,),
                    projection_trace=projection_trace,
                )
            )
    return tuple(sorted(entries, key=lambda item: (item.workbench_id, item.path, item.roles[0])))


def _assert_committed_json_matches(path: Path, expected_payload: Any, label: str) -> None:
    expected_text = _canonical_json(expected_payload)
    if not path.exists():
        raise WorkflowLayerError(f"Missing generated artifact {label}: {path}")
    actual_payload = json.loads(path.read_text(encoding="utf-8"))
    actual_text = _canonical_json(actual_payload)
    if actual_text != expected_text:
        raise WorkflowLayerError(f"Committed {label} is stale relative to authored workflow inputs: {path}")


def _assert_committed_text_matches(path: Path, expected_text: str, label: str) -> None:
    if not path.exists():
        raise WorkflowLayerError(f"Missing generated artifact {label}: {path}")
    actual = path.read_text(encoding="utf-8")
    if actual != expected_text:
        raise WorkflowLayerError(f"Committed {label} is stale relative to authored workflow inputs: {path}")


def _resource_kind_for_path(rel_path: str) -> str:
    for prefix, kind in _RESOURCE_KIND_BY_PREFIX.items():
        if rel_path.startswith(prefix):
            return kind
    raise WorkflowLayerError(f"Unsupported workflow resource path: {rel_path!r}")


def _resource_id(kind: str, workbench_id: str, role: str, rel_path: str) -> str:
    name = _sanitize_identifier(f"{workbench_id}_{role}_{Path(rel_path).stem}")
    return f"resource.{kind}.{name}"


def _workbench_gate_binding(workbench: WorkflowWorkbench) -> list[str]:
    placement = workbench.lifecycle_placement
    if placement.kind == "covered_gates":
        return list(placement.covered_gates)
    if placement.kind == "lifecycle_span":
        return [gate_id for gate_id in (placement.start_gate, placement.end_gate) if gate_id is not None]
    return []


def _grammar_gate_entity_id(gate_id: str) -> str:
    return f"lg:gates/{gate_id.lower().replace('-', '_')}"


def _product_root(registry_file: Path) -> Path:
    return registry_file.resolve().parents[3]


def _format_lifecycle(placement: Any) -> str:
    if placement.kind == "covered_gates":
        return f"covered_gates: {', '.join(placement.covered_gates)}"
    if placement.kind == "lifecycle_span":
        return f"lifecycle_span: {placement.start_gate} -> {placement.end_gate}"
    return placement.kind


def _extract_markdown_yaml_header(content: str, rel_path: str) -> Mapping[str, Any]:
    if not content.startswith("```yaml\n"):
        raise WorkflowLayerError(f"Guide {rel_path!r} must start with a fenced yaml provenance block")
    _, _, remainder = content.partition("```yaml\n")
    header_text, sep, _ = remainder.partition("\n```")
    if not sep:
        raise WorkflowLayerError(f"Guide {rel_path!r} has an unterminated fenced yaml provenance block")
    return yaml.safe_load(header_text) or {}


def _contract_entry_to_dict(entry: ContractCatalogEntry) -> dict[str, Any]:
    return {
        "contract_ref": entry.contract_ref,
        "request_schema_ref": entry.request_schema_ref,
        "transaction_kind": entry.transaction_kind,
        "family_binding": list(entry.family_binding),
        "gate_binding": list(entry.gate_binding),
        "workbench_refs": list(entry.workbench_refs),
        "guide_refs": list(entry.guide_refs),
        "response_surface_bindings": [
            {
                "transaction_kind": binding.transaction_kind,
                "response_envelope": binding.response_envelope,
                "allowed_resource_roles": list(binding.allowed_resource_roles),
            }
            for binding in entry.response_surface_bindings
        ],
        "compatibility": dict(entry.compatibility),
        "provenance": dict(entry.provenance),
    }


def _resource_entry_to_dict(entry: ResourceManifestEntry) -> dict[str, Any]:
    return {
        "resource_id": entry.resource_id,
        "kind": entry.kind,
        "workbench_id": entry.workbench_id,
        "path": entry.path,
        "content_hash": entry.content_hash,
        "review_status": entry.review_status,
        "provenance_type": entry.provenance_type,
        "provenance_refs": [dict(item) for item in entry.provenance_refs],
        "roles": list(entry.roles),
        "projection_trace": dict(entry.projection_trace),
    }


def _to_plain_data(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _to_plain_data(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_plain_data(v) for v in value]
    return value


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sanitize_identifier(value: str) -> str:
    value = value.lower().replace("-", "_")
    value = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)
    value = re_sub_multi_underscore(value)
    return value.strip("_")


def re_sub_multi_underscore(value: str) -> str:
    while "__" in value:
        value = value.replace("__", "_")
    return value


DEFAULT_LIFECYCLE_POLICY_MANIFEST_PATH = DEFAULT_DEFINITIONS_ROOT / "lifecycle-policy" / "manifest.yaml"

DEFAULT_WORKFLOW_ID = "default_full_governed_surface"
DEFAULT_WORKBENCH_CATALOG_ROOT = DEFAULT_DEFINITIONS_ROOT / "workbenches"
DEFAULT_WORKFLOW_CATALOG_ROOT = DEFAULT_DEFINITIONS_ROOT / "workflows"
DEFAULT_WORKFLOW_SCHEMA_PATH = DEFAULT_DEFINITIONS_ROOT / "workflow_schema.yaml"
DEFAULT_BUILTIN_WORKFLOW_MAP_ROOT = Path(__file__).resolve().parent / "generated" / "workflow_maps"


@dataclass(frozen=True)
class LifecyclePlacement:
    kind: str
    covered_gates: tuple[str, ...] = ()
    start_gate: str | None = None
    end_gate: str | None = None


@dataclass(frozen=True)
class WorkflowDefinition:
    workflow_id: str
    display_name: str
    runtime_surface_classification: str
    active_workbench_ids: tuple[str, ...]
    source_path: str
    catalog_source: str
    content_hash: str


@dataclass(frozen=True)
class WorkflowWorkbench:
    workbench_id: str
    display_name: str
    lifecycle_placement: LifecyclePlacement
    artifacts_in_scope: tuple[str, ...]
    intent_classes: tuple[str, ...]
    posture_constraints: tuple[str, ...]
    allowed_transaction_kinds: tuple[str, ...]
    draftable_artifact_families: tuple[str, ...]
    contract_refs: tuple[str, ...]
    inspect_views: tuple[str, ...]
    response_surface_bindings: tuple[ResponseSurfaceBinding, ...]
    instruction_resource: str
    authoritative_guides: tuple[str, ...]
    administration_guides: tuple[str, ...]
    entry_conditions: tuple[str, ...]
    exit_conditions: tuple[str, ...]
    source_path: str
    catalog_source: str
    content_hash: str


@dataclass(frozen=True)
class WorkflowLayer:
    runtime_surface_classification: str
    selected_workflow_id: str
    selected_workflow_display_name: str
    selected_workflow_source_path: str
    built_in_workbench_catalog_root: str
    repo_workbench_catalog_root: str | None
    built_in_workflow_catalog_root: str
    repo_workflow_catalog_root: str | None
    workbenches: tuple[WorkflowWorkbench, ...]
    catalog_workbenches: tuple[WorkflowWorkbench, ...]
    workflow_definitions: tuple[WorkflowDefinition, ...]
    transaction_profiles: tuple[TransactionProfile, ...]
    contract_catalog: tuple[ContractCatalogEntry, ...]
    resource_manifest: tuple[ResourceManifestEntry, ...]
    grammar_version: str
    grammar_package_version: str

    @property
    def workbench_catalog_root(self) -> str:
        return self.repo_workbench_catalog_root or self.built_in_workbench_catalog_root

    @property
    def workflow_catalog_root(self) -> str:
        return self.repo_workflow_catalog_root or self.built_in_workflow_catalog_root

    def get_workbench(self, workbench_id: str) -> WorkflowWorkbench:
        for workbench in self.workbenches:
            if workbench.workbench_id == workbench_id:
                return workbench
        raise KeyError(workbench_id)

    def get_catalog_workbench(self, workbench_id: str) -> WorkflowWorkbench:
        for workbench in self.catalog_workbenches:
            if workbench.workbench_id == workbench_id:
                return workbench
        raise KeyError(workbench_id)

    def get_workflow_definition(self, workflow_id: str) -> WorkflowDefinition:
        for workflow in self.workflow_definitions:
            if workflow.workflow_id == workflow_id:
                return workflow
        raise KeyError(workflow_id)


@dataclass(frozen=True)
class GeneratedArtifacts:
    compatibility_registry_text: str
    contract_catalog_payload: list[dict[str, Any]]
    resource_manifest_payload: list[dict[str, Any]]
    workflow_map_text: str
    workbench_resource_bindings_text: str
    built_in_workflow_map_text: str


def load_workflow_layer(
    *,
    governance_root: str | Path | None = None,
    workflow_id: str | None = None,
    workflow_folder: str | Path | None = None,
    workbench_folder: str | Path | None = None,
    workbench_catalog_root: str | Path | None = None,
    workflow_catalog_root: str | Path | None = None,
    schema_path: str | Path | None = None,
    workflow_schema_path: str | Path | None = None,
    transaction_profiles_path: str | Path | None = None,
    registry_path: str | Path | None = None,
    contract_catalog_path: str | Path | None = None,
    resource_manifest_path: str | Path | None = None,
    workflow_map_path: str | Path | None = None,
    workbench_resource_bindings_path: str | Path | None = None,
    builtin_workflow_map_root: str | Path | None = None,
    relocation_manifest_path: str | Path | None = None,
    lifecycle_policy_manifest_path: str | Path | None = None,
    enforce_generated_artifacts: bool = False,
) -> WorkflowLayer:
    grammar = _load_grammar()
    _validate_lifecycle_bundle(
        grammar,
        Path(lifecycle_policy_manifest_path).resolve() if lifecycle_policy_manifest_path is not None else None,
    )
    grammar_manifest = dict(grammar.manifest())
    grammar_version = str(grammar_manifest.get("model_version", ""))
    grammar_package_version = str(grammar.package_version())

    built_in_workbench_root = Path(workbench_catalog_root or DEFAULT_WORKBENCH_CATALOG_ROOT).resolve()
    built_in_workflow_root = Path(workflow_catalog_root or DEFAULT_WORKFLOW_CATALOG_ROOT).resolve()
    if not built_in_workbench_root.is_dir():
        raise WorkflowLayerError(f"Missing built-in workbench catalog root: {built_in_workbench_root}")
    if not built_in_workflow_root.is_dir():
        raise WorkflowLayerError(f"Missing built-in workflow catalog root: {built_in_workflow_root}")

    governance_root_path = Path(governance_root).resolve() if governance_root is not None else None
    repo_workbench_root = _resolve_repo_catalog_root(
        governance_root=governance_root_path,
        override_root=workbench_folder,
        folder_name="workbenches",
    )
    repo_workflow_root = _resolve_repo_catalog_root(
        governance_root=governance_root_path,
        override_root=workflow_folder,
        folder_name="workflows",
    )

    product_root = _product_root_from_catalog_root(built_in_workbench_root)
    workbench_schema_file = Path(schema_path or built_in_workbench_root.parent / "workbench_schema.yaml").resolve()
    workflow_schema_file = Path(
        workflow_schema_path or built_in_workflow_root.parent / "workflow_schema.yaml"
    ).resolve()
    transaction_profiles_file = Path(
        transaction_profiles_path or built_in_workbench_root.parent / "transaction_profiles.yaml"
    ).resolve()
    relocation_manifest_file = Path(relocation_manifest_path or DEFAULT_RELOCATION_MANIFEST_PATH).resolve()
    registry_file = Path(registry_path or built_in_workbench_root.parent / "workbench_registry.yaml").resolve()
    contract_catalog_file = Path(
        contract_catalog_path or built_in_workbench_root.parent / "contract_catalog.json"
    ).resolve()
    resource_manifest_file = Path(
        resource_manifest_path or built_in_workbench_root.parent / "resource_manifest.json"
    ).resolve()
    workflow_map_file = Path(workflow_map_path or built_in_workbench_root.parent / "workflow_map.md").resolve()
    workbench_bindings_file = Path(
        workbench_resource_bindings_path or built_in_workbench_root.parent / "workbench_resource_bindings.md"
    ).resolve()
    builtin_workflow_map_root_path = Path(
        builtin_workflow_map_root or built_in_workflow_root.parents[1] / "generated" / "workflow_maps"
    ).resolve()

    workbench_schema_payload = _load_yaml(workbench_schema_file, "workbench schema")
    workflow_schema_payload = _load_yaml(workflow_schema_file, "workflow schema")
    transaction_profiles_payload = _load_yaml(transaction_profiles_file, "transaction profiles")
    relocation_manifest = _load_yaml(relocation_manifest_file, "relocation manifest")

    transaction_profiles = _load_transaction_profiles(transaction_profiles_payload)
    transaction_profile_map = {profile.transaction_kind: profile for profile in transaction_profiles}
    built_in_workbench_ids = tuple(workbench_schema_payload.get("built_in_workbench_ids", ()))
    built_in_workbenches = _load_workbench_catalog(
        catalog_root=built_in_workbench_root,
        schema_payload=workbench_schema_payload,
        catalog_source="built_in",
        anchor_root=product_root,
        expected_ids=built_in_workbench_ids,
    )
    repo_workbenches = _load_workbench_catalog(
        catalog_root=repo_workbench_root,
        schema_payload=workbench_schema_payload,
        catalog_source="repo_local",
        anchor_root=governance_root_path,
    )
    catalog_workbenches = _merge_workbench_catalogs(built_in_workbenches, repo_workbenches)
    workbench_by_id = {workbench.workbench_id: workbench for workbench in catalog_workbenches}

    built_in_workflows = _load_workflow_catalog(
        catalog_root=built_in_workflow_root,
        schema_payload=workflow_schema_payload,
        catalog_source="built_in",
        anchor_root=product_root,
    )
    repo_workflows = _load_workflow_catalog(
        catalog_root=repo_workflow_root,
        schema_payload=workflow_schema_payload,
        catalog_source="repo_local",
        anchor_root=governance_root_path,
    )
    workflow_definitions = _merge_workflow_catalogs(built_in_workflows, repo_workflows)
    _validate_workflow_references(workflow_definitions, workbench_by_id)

    target_workflow_id = workflow_id or DEFAULT_WORKFLOW_ID
    try:
        selected_workflow = next(item for item in workflow_definitions if item.workflow_id == target_workflow_id)
    except StopIteration as exc:
        raise WorkflowLayerError(f"Unknown workflow_id {target_workflow_id!r}") from exc

    active_workbenches = tuple(workbench_by_id[workbench_id] for workbench_id in selected_workflow.active_workbench_ids)
    if selected_workflow.runtime_surface_classification == "full_governed_surface":
        _validate_required_artifact_family_coverage(active_workbenches)
    _validate_grammar_gate_compatibility(grammar, active_workbenches, grammar_version)

    resource_manifest = _derive_resource_manifest(
        relocation_manifest=relocation_manifest,
        workbenches=active_workbenches,
        product_root=product_root,
    )
    contract_catalog = _build_contract_catalog(
        workbenches=active_workbenches,
        transaction_profiles=transaction_profile_map,
        grammar=grammar,
        grammar_version=grammar_version,
        grammar_package_version=grammar_package_version,
        selected_workflow=selected_workflow,
    )

    generated = render_generated_artifacts(
        workflow_id=selected_workflow.workflow_id,
        workflow_display_name=selected_workflow.display_name,
        runtime_surface_classification=selected_workflow.runtime_surface_classification,
        workbenches=active_workbenches,
        transaction_profiles=transaction_profiles,
        contract_catalog=contract_catalog,
        resource_manifest=resource_manifest,
    )

    if enforce_generated_artifacts and selected_workflow.workflow_id == DEFAULT_WORKFLOW_ID:
        _assert_committed_text_matches(registry_file, generated.compatibility_registry_text, "workbench_registry.yaml")
        _assert_committed_json_matches(
            contract_catalog_file, generated.contract_catalog_payload, "contract_catalog.json"
        )
        _assert_committed_json_matches(
            resource_manifest_file, generated.resource_manifest_payload, "resource_manifest.json"
        )
        _assert_committed_text_matches(workflow_map_file, generated.workflow_map_text, "workflow_map.md")
        _assert_committed_text_matches(
            workbench_bindings_file,
            generated.workbench_resource_bindings_text,
            "workbench_resource_bindings.md",
        )
        builtin_workflow_map_file = builtin_workflow_map_root_path / f"{selected_workflow.workflow_id}.md"
        _assert_committed_text_matches(
            builtin_workflow_map_file,
            generated.built_in_workflow_map_text,
            f"{selected_workflow.workflow_id}.md",
        )

    return WorkflowLayer(
        runtime_surface_classification=selected_workflow.runtime_surface_classification,
        selected_workflow_id=selected_workflow.workflow_id,
        selected_workflow_display_name=selected_workflow.display_name,
        selected_workflow_source_path=selected_workflow.source_path,
        built_in_workbench_catalog_root=_path_label(built_in_workbench_root, product_root),
        repo_workbench_catalog_root=(
            _path_label(repo_workbench_root, governance_root_path) if repo_workbench_root is not None else None
        ),
        built_in_workflow_catalog_root=_path_label(built_in_workflow_root, product_root),
        repo_workflow_catalog_root=(
            _path_label(repo_workflow_root, governance_root_path) if repo_workflow_root is not None else None
        ),
        workbenches=active_workbenches,
        catalog_workbenches=catalog_workbenches,
        workflow_definitions=workflow_definitions,
        transaction_profiles=transaction_profiles,
        contract_catalog=contract_catalog,
        resource_manifest=resource_manifest,
        grammar_version=grammar_version,
        grammar_package_version=grammar_package_version,
    )


def render_generated_artifacts(
    *,
    workflow_id: str,
    workflow_display_name: str,
    runtime_surface_classification: str,
    workbenches: tuple[WorkflowWorkbench, ...],
    transaction_profiles: tuple[TransactionProfile, ...],
    contract_catalog: tuple[ContractCatalogEntry, ...],
    resource_manifest: tuple[ResourceManifestEntry, ...],
) -> GeneratedArtifacts:
    del transaction_profiles

    contract_payload = [_contract_entry_to_dict(entry) for entry in contract_catalog]
    resource_payload = [_resource_entry_to_dict(entry) for entry in resource_manifest]
    registry_payload = {
        "runtime_surface_classification": runtime_surface_classification,
        "workbenches": [_workbench_to_projection_dict(workbench) for workbench in workbenches],
    }

    workflow_map_lines = [
        "# Workflow map",
        "",
        f"Workflow ID: `{workflow_id}`",
        f"Display name: `{workflow_display_name}`",
        f"Runtime surface classification: `{runtime_surface_classification}`",
        "",
        "| Workbench | Lifecycle placement | Transactions | Inspect views | Artifact families |",
        "|---|---|---|---|---|",
    ]
    for workbench in workbenches:
        workflow_map_lines.append(
            "| {wb} | {placement} | {tx} | {views} | {families} |".format(
                wb=workbench.workbench_id,
                placement=_format_lifecycle(workbench.lifecycle_placement),
                tx=", ".join(workbench.allowed_transaction_kinds),
                views=", ".join(workbench.inspect_views) or "-",
                families=", ".join(workbench.artifacts_in_scope),
            )
        )
    workflow_map_text = "\n".join(workflow_map_lines) + "\n"

    resource_lookup: dict[tuple[str, str], list[str]] = {}
    for entry in resource_manifest:
        for role in entry.roles:
            resource_lookup.setdefault((entry.workbench_id, role), []).append(entry.resource_id)

    bindings_lines = [
        "# Workbench resource bindings",
        "",
        f"Workflow ID: `{workflow_id}`",
        "",
        "| Workbench | Instruction resource | Administration guides | Authoritative guides | Manifest resource ids |",
        "|---|---|---|---|---|",
    ]
    for workbench in workbenches:
        manifest_ids: list[str] = []
        for role in ("instruction_resource", "administration_guides", "authoritative_guides"):
            manifest_ids.extend(resource_lookup.get((workbench.workbench_id, role), []))
        bindings_lines.append(
            "| {wb} | {instruction} | {admin} | {authoritative} | {manifest_ids} |".format(
                wb=workbench.workbench_id,
                instruction=workbench.instruction_resource,
                admin="<br>".join(workbench.administration_guides),
                authoritative="<br>".join(workbench.authoritative_guides),
                manifest_ids="<br>".join(sorted(manifest_ids)),
            )
        )
    workbench_resource_bindings_text = "\n".join(bindings_lines) + "\n"

    compatibility_registry_text = _render_compatibility_registry_text(registry_payload)
    built_in_workflow_map_text = workflow_map_text.replace("# Workflow map", f"# Workflow map: {workflow_id}", 1)

    return GeneratedArtifacts(
        compatibility_registry_text=compatibility_registry_text,
        contract_catalog_payload=contract_payload,
        resource_manifest_payload=resource_payload,
        workflow_map_text=workflow_map_text,
        workbench_resource_bindings_text=workbench_resource_bindings_text,
        built_in_workflow_map_text=built_in_workflow_map_text,
    )


def _resolve_repo_catalog_root(
    *,
    governance_root: Path | None,
    override_root: str | Path | None,
    folder_name: str,
) -> Path | None:
    if override_root is not None:
        candidate = Path(override_root).resolve()
        if not candidate.is_dir():
            raise WorkflowLayerError(f"Missing repo-local {folder_name} catalog root: {candidate}")
        return candidate
    if governance_root is None:
        return None
    candidate = governance_root / "workflow" / "definitions" / folder_name
    if not candidate.exists():
        return None
    if not candidate.is_dir():
        raise WorkflowLayerError(f"Repo-local {folder_name} catalog root is not a directory: {candidate}")
    return candidate.resolve()


def _product_root_from_catalog_root(catalog_root: Path) -> Path:
    return catalog_root.resolve().parents[3]


def _yaml_paths(catalog_root: Path | None) -> tuple[Path, ...]:
    if catalog_root is None:
        return ()
    yaml_paths = sorted(catalog_root.glob("*.yaml")) + sorted(catalog_root.glob("*.yml"))
    return tuple(dict.fromkeys(path.resolve() for path in yaml_paths))


def _load_workbench_catalog(
    *,
    catalog_root: Path | None,
    schema_payload: Mapping[str, Any],
    catalog_source: str,
    anchor_root: Path | None,
    expected_ids: tuple[str, ...] | None = None,
) -> tuple[WorkflowWorkbench, ...]:
    paths = _yaml_paths(catalog_root)
    if catalog_root is not None and not paths and expected_ids:
        raise WorkflowLayerError(f"No workbench definitions found in {catalog_root}")
    workbenches: list[WorkflowWorkbench] = []
    seen_ids: dict[str, str] = {}
    seen_names: dict[str, str] = {}
    for path in paths:
        workbench = _parse_workbench_definition(
            payload=_load_yaml(path, f"workbench definition {path.name}"),
            path=path,
            schema_payload=schema_payload,
            catalog_source=catalog_source,
            anchor_root=anchor_root,
        )
        if workbench.workbench_id in seen_ids:
            raise WorkflowLayerError(
                f"Duplicate workbench_id {workbench.workbench_id!r} in {catalog_root}: "
                f"{seen_ids[workbench.workbench_id]} and {workbench.source_path}"
            )
        if workbench.display_name in seen_names:
            raise WorkflowLayerError(
                f"Duplicate workbench display_name {workbench.display_name!r} in {catalog_root}: "
                f"{seen_names[workbench.display_name]} and {workbench.source_path}"
            )
        seen_ids[workbench.workbench_id] = workbench.source_path
        seen_names[workbench.display_name] = workbench.source_path
        workbenches.append(workbench)
    if expected_ids is None:
        return tuple(sorted(workbenches, key=lambda item: item.workbench_id))
    observed_ids = {item.workbench_id for item in workbenches}
    expected_set = set(expected_ids)
    missing = sorted(expected_set - observed_ids)
    unexpected = sorted(observed_ids - expected_set)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing={missing}")
        if unexpected:
            details.append(f"unexpected={unexpected}")
        raise WorkflowLayerError(f"Built-in workbench inventory mismatch in {catalog_root}: {'; '.join(details)}")
    by_id = {item.workbench_id: item for item in workbenches}
    return tuple(by_id[workbench_id] for workbench_id in expected_ids)


def _load_workflow_catalog(
    *,
    catalog_root: Path | None,
    schema_payload: Mapping[str, Any],
    catalog_source: str,
    anchor_root: Path | None,
) -> tuple[WorkflowDefinition, ...]:
    paths = _yaml_paths(catalog_root)
    if catalog_root is not None and catalog_source == "built_in" and not paths:
        raise WorkflowLayerError(f"No workflow definitions found in {catalog_root}")
    workflows: list[WorkflowDefinition] = []
    seen_ids: dict[str, str] = {}
    for path in paths:
        workflow = _parse_workflow_definition(
            payload=_load_yaml(path, f"workflow definition {path.name}"),
            path=path,
            schema_payload=schema_payload,
            catalog_source=catalog_source,
            anchor_root=anchor_root,
        )
        if workflow.workflow_id in seen_ids:
            raise WorkflowLayerError(
                f"Duplicate workflow_id {workflow.workflow_id!r} in {catalog_root}: "
                f"{seen_ids[workflow.workflow_id]} and {workflow.source_path}"
            )
        seen_ids[workflow.workflow_id] = workflow.source_path
        workflows.append(workflow)
    return tuple(sorted(workflows, key=lambda item: item.workflow_id))


def _parse_workbench_definition(
    *,
    payload: Mapping[str, Any],
    path: Path,
    schema_payload: Mapping[str, Any],
    catalog_source: str,
    anchor_root: Path | None,
) -> WorkflowWorkbench:
    if not isinstance(payload, Mapping):
        raise WorkflowLayerError(f"Workbench definition must be a mapping: {path}")
    required_fields = tuple(str(item) for item in schema_payload.get("required_workbench_fields", ()))
    removed_fields = {str(item) for item in schema_payload.get("removed_authority_fields", ())}
    required_surface_fields = tuple(str(item) for item in schema_payload.get("required_workflow_surface_fields", ()))
    allowed_transaction_kinds = {str(item) for item in schema_payload.get("allowed_transaction_kinds", ())}
    allowed_resource_roles = {str(item) for item in schema_payload.get("allowed_resource_roles", ())}
    response_shape = set(schema_payload.get("response_surface_binding_shape", {}).get("required", ()))

    workbench_id = str(payload.get("workbench_id", "")).strip()
    if not workbench_id:
        raise WorkflowLayerError(f"Workbench definition missing workbench_id: {path}")
    for field in required_fields:
        if field not in payload:
            raise WorkflowLayerError(f"{workbench_id} missing required declaration field: {field}")
    present_removed = sorted(field for field in removed_fields if field in payload)
    if present_removed:
        raise WorkflowLayerError(f"{workbench_id} uses removed authority field(s): {present_removed}")

    workflow_surface = payload.get("workflow_surface")
    if not isinstance(workflow_surface, Mapping):
        raise WorkflowLayerError(f"{workbench_id}.workflow_surface must be a mapping")
    for field in required_surface_fields:
        if field not in workflow_surface:
            raise WorkflowLayerError(f"{workbench_id}.workflow_surface missing required field: {field}")

    lifecycle_placement = _parse_lifecycle_placement(
        workbench_id=workbench_id,
        payload=payload.get("lifecycle_placement") or {},
        schema_payload=schema_payload,
    )
    inspect_views = tuple(str(item) for item in workflow_surface.get("inspect_views", ()))
    declared_transactions = tuple(str(item) for item in workflow_surface.get("allowed_transaction_kinds", ()))
    if not declared_transactions:
        raise WorkflowLayerError(f"{workbench_id}.workflow_surface.allowed_transaction_kinds must not be empty")
    for transaction_kind in declared_transactions:
        if transaction_kind not in allowed_transaction_kinds:
            raise WorkflowLayerError(
                f"{workbench_id}.workflow_surface.allowed_transaction_kinds uses unsupported transaction kind {transaction_kind!r}"
            )

    bindings_raw = workflow_surface.get("response_surface_bindings") or []
    if not bindings_raw:
        raise WorkflowLayerError(f"{workbench_id}.workflow_surface.response_surface_bindings must not be empty")
    response_surface_bindings: list[ResponseSurfaceBinding] = []
    for index, binding in enumerate(bindings_raw):
        if not isinstance(binding, Mapping):
            raise WorkflowLayerError(
                f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] must be a mapping"
            )
        if not response_shape.issubset(binding.keys()):
            missing = sorted(response_shape - set(binding.keys()))
            raise WorkflowLayerError(
                f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] missing fields: {missing}"
            )
        transaction_kind = str(binding["transaction_kind"])
        if transaction_kind not in declared_transactions:
            raise WorkflowLayerError(
                f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] uses undeclared transaction kind {transaction_kind!r}"
            )
        response_envelope = str(binding["response_envelope"])
        if transaction_kind == "inspect" and response_envelope not in inspect_views:
            raise WorkflowLayerError(
                f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] must use an inspect view response envelope; got {response_envelope!r}"
            )
        if transaction_kind != "inspect" and response_envelope != "default":
            raise WorkflowLayerError(
                f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] must use response_envelope 'default' for transaction kind {transaction_kind!r}"
            )
        allowed_roles = tuple(str(item) for item in binding.get("allowed_resource_roles", ()))
        if not allowed_roles:
            raise WorkflowLayerError(
                f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] must declare at least one resource role"
            )
        for role in allowed_roles:
            if role not in allowed_resource_roles:
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] uses unsupported resource role {role!r}"
                )
        response_surface_bindings.append(
            ResponseSurfaceBinding(
                transaction_kind=transaction_kind,
                response_envelope=response_envelope,
                allowed_resource_roles=allowed_roles,
            )
        )

    canonical_payload = json.dumps(_to_plain_data(payload), sort_keys=True, separators=(",", ":"))
    return WorkflowWorkbench(
        workbench_id=workbench_id,
        display_name=str(payload["display_name"]),
        lifecycle_placement=lifecycle_placement,
        artifacts_in_scope=tuple(str(item) for item in payload.get("artifacts_in_scope", ())),
        intent_classes=tuple(str(item) for item in payload.get("intent_classes", ())),
        posture_constraints=tuple(str(item) for item in payload.get("posture_constraints", ())),
        allowed_transaction_kinds=declared_transactions,
        draftable_artifact_families=tuple(
            str(item) for item in workflow_surface.get("draftable_artifact_families", ())
        ),
        contract_refs=tuple(str(item) for item in workflow_surface.get("contract_refs", ())),
        inspect_views=inspect_views,
        response_surface_bindings=tuple(response_surface_bindings),
        instruction_resource=str(payload.get("instruction_resource", "")),
        authoritative_guides=tuple(str(item) for item in payload.get("authoritative_guides", ())),
        administration_guides=tuple(str(item) for item in payload.get("administration_guides", ())),
        entry_conditions=tuple(str(item) for item in payload.get("entry_conditions", ())),
        exit_conditions=tuple(str(item) for item in payload.get("exit_conditions", ())),
        source_path=_path_label(path, anchor_root),
        catalog_source=catalog_source,
        content_hash=_sha256_text(canonical_payload),
    )


def _parse_workflow_definition(
    *,
    payload: Mapping[str, Any],
    path: Path,
    schema_payload: Mapping[str, Any],
    catalog_source: str,
    anchor_root: Path | None,
) -> WorkflowDefinition:
    if not isinstance(payload, Mapping):
        raise WorkflowLayerError(f"Workflow definition must be a mapping: {path}")
    required_fields = tuple(str(item) for item in schema_payload.get("required_workflow_fields", ()))
    for field in required_fields:
        if field not in payload:
            workflow_id = str(payload.get("workflow_id", path.stem))
            raise WorkflowLayerError(f"{workflow_id} missing required workflow field: {field}")
    workflow_id = str(payload["workflow_id"]).strip()
    pattern = str(schema_payload.get("workflow_id_pattern", ""))
    if pattern and re.fullmatch(pattern, workflow_id) is None:
        raise WorkflowLayerError(f"workflow_id {workflow_id!r} does not match required pattern {pattern!r}")
    classification = str(payload["runtime_surface_classification"])
    allowed_classifications = {str(item) for item in schema_payload.get("runtime_surface_classification_values", ())}
    if classification not in allowed_classifications:
        raise WorkflowLayerError(
            f"workflow {workflow_id!r} must declare runtime_surface_classification in {sorted(allowed_classifications)}"
        )
    active_workbench_ids = tuple(str(item) for item in payload.get("active_workbench_ids", ()))
    rules = schema_payload.get("rules", {})
    if rules.get("active_workbench_ids_must_be_non_empty", False) and not active_workbench_ids:
        raise WorkflowLayerError(f"workflow {workflow_id!r} must declare at least one active_workbench_id")
    if rules.get("duplicate_active_workbench_ids_forbidden", False) and len(active_workbench_ids) != len(
        set(active_workbench_ids)
    ):
        raise WorkflowLayerError(f"workflow {workflow_id!r} contains duplicate active_workbench_ids")
    canonical_payload = json.dumps(_to_plain_data(payload), sort_keys=True, separators=(",", ":"))
    return WorkflowDefinition(
        workflow_id=workflow_id,
        display_name=str(payload["display_name"]),
        runtime_surface_classification=classification,
        active_workbench_ids=active_workbench_ids,
        source_path=_path_label(path, anchor_root),
        catalog_source=catalog_source,
        content_hash=_sha256_text(canonical_payload),
    )


def _parse_lifecycle_placement(
    *,
    workbench_id: str,
    payload: Mapping[str, Any],
    schema_payload: Mapping[str, Any],
) -> LifecyclePlacement:
    if not isinstance(payload, Mapping):
        raise WorkflowLayerError(f"{workbench_id}.lifecycle_placement must be a mapping")
    kind = str(payload.get("kind", "")).strip()
    variants = schema_payload.get("lifecycle_placement_variants", {})
    if kind not in variants:
        raise WorkflowLayerError(f"{workbench_id}.lifecycle_placement uses unsupported kind {kind!r}")
    for field in variants[kind].get("requires", ()):
        if field not in payload:
            raise WorkflowLayerError(f"{workbench_id}.lifecycle_placement missing required field: {field}")
    if kind == "covered_gates":
        covered_gates = tuple(str(item) for item in payload.get("covered_gates", ()))
        if not covered_gates:
            raise WorkflowLayerError(f"{workbench_id}.lifecycle_placement.covered_gates must not be empty")
        return LifecyclePlacement(kind=kind, covered_gates=covered_gates)
    if kind == "lifecycle_span":
        return LifecyclePlacement(
            kind=kind,
            start_gate=str(payload.get("start_gate", "")).strip(),
            end_gate=str(payload.get("end_gate", "")).strip(),
        )
    return LifecyclePlacement(kind=kind)


def _merge_workbench_catalogs(
    built_in_workbenches: tuple[WorkflowWorkbench, ...],
    repo_workbenches: tuple[WorkflowWorkbench, ...],
) -> tuple[WorkflowWorkbench, ...]:
    combined = list(built_in_workbenches)
    seen_ids = {item.workbench_id: item.source_path for item in built_in_workbenches}
    seen_names = {item.display_name: item.source_path for item in built_in_workbenches}
    for workbench in repo_workbenches:
        if workbench.workbench_id in seen_ids:
            raise WorkflowLayerError(
                f"Repo-local workbench_id {workbench.workbench_id!r} collides with built-in definition: "
                f"{seen_ids[workbench.workbench_id]} vs {workbench.source_path}"
            )
        if workbench.display_name in seen_names:
            raise WorkflowLayerError(
                f"Repo-local workbench display_name {workbench.display_name!r} collides with built-in definition: "
                f"{seen_names[workbench.display_name]} vs {workbench.source_path}"
            )
        seen_ids[workbench.workbench_id] = workbench.source_path
        seen_names[workbench.display_name] = workbench.source_path
        combined.append(workbench)
    return tuple(combined)


def _merge_workflow_catalogs(
    built_in_workflows: tuple[WorkflowDefinition, ...],
    repo_workflows: tuple[WorkflowDefinition, ...],
) -> tuple[WorkflowDefinition, ...]:
    combined = list(built_in_workflows)
    seen_ids = {item.workflow_id: item.source_path for item in built_in_workflows}
    for workflow in repo_workflows:
        if workflow.workflow_id in seen_ids:
            raise WorkflowLayerError(
                f"Repo-local workflow_id {workflow.workflow_id!r} collides with built-in definition: "
                f"{seen_ids[workflow.workflow_id]} vs {workflow.source_path}"
            )
        seen_ids[workflow.workflow_id] = workflow.source_path
        combined.append(workflow)
    return tuple(sorted(combined, key=lambda item: item.workflow_id))


def _validate_workflow_references(
    workflow_definitions: tuple[WorkflowDefinition, ...],
    workbench_by_id: Mapping[str, WorkflowWorkbench],
) -> None:
    for workflow in workflow_definitions:
        for workbench_id in workflow.active_workbench_ids:
            if workbench_id not in workbench_by_id:
                raise WorkflowLayerError(
                    f"workflow {workflow.workflow_id!r} references unknown active_workbench_id {workbench_id!r}"
                )


def _validate_required_artifact_family_coverage(workbenches: Iterable[WorkflowWorkbench]) -> None:
    observed = {family for workbench in workbenches for family in workbench.artifacts_in_scope}
    missing = sorted(_REQUIRED_ARTIFACT_FAMILIES - observed)
    if missing:
        raise WorkflowLayerError(f"Workflow layer is missing required artifact families: {missing}")


def _build_contract_catalog(
    *,
    workbenches: tuple[WorkflowWorkbench, ...],
    transaction_profiles: Mapping[str, TransactionProfile],
    grammar: Any,
    grammar_version: str,
    grammar_package_version: str,
    selected_workflow: WorkflowDefinition,
) -> tuple[ContractCatalogEntry, ...]:
    entries = []
    for workbench in workbenches:
        if not workbench.contract_refs:
            raise WorkflowLayerError(f"{workbench.workbench_id} must declare at least one contract_ref")
        contract_ref = workbench.contract_refs[0]
        primary_transaction_kind = _primary_transaction_kind(workbench)
        if primary_transaction_kind not in transaction_profiles:
            raise WorkflowLayerError(
                f"{workbench.workbench_id} primary transaction kind {primary_transaction_kind!r} is not declared in transaction_profiles.yaml"
            )
        if contract_ref not in transaction_profiles[primary_transaction_kind].allowed_contract_refs:
            raise WorkflowLayerError(
                f"Primary transaction profile {primary_transaction_kind!r} does not allow contract {contract_ref!r} for {workbench.workbench_id}"
            )
        gate_binding = _workbench_gate_binding(workbench)
        compatibility = {
            "grammar_version": grammar_version,
            "grammar_package_version": grammar_package_version,
            "gate_dependencies": {
                gate_id: _to_plain_data(grammar.gate_dependencies(_grammar_gate_entity_id(gate_id)))
                for gate_id in gate_binding
            },
            "runtime_surface_classification": selected_workflow.runtime_surface_classification,
            "selected_workflow_id": selected_workflow.workflow_id,
        }
        provenance = {
            "generated_from": [
                selected_workflow.source_path,
                workbench.source_path,
                "lantern/workflow/definitions/transaction_profiles.yaml",
                "lantern/preservation/relocation_manifest.yaml",
            ],
            "catalog_source": workbench.catalog_source,
        }
        entries.append(
            ContractCatalogEntry(
                contract_ref=contract_ref,
                request_schema_ref=f"schema.request.{workbench.workbench_id}.v1",
                transaction_kind=primary_transaction_kind,
                family_binding=workbench.artifacts_in_scope,
                gate_binding=tuple(gate_binding),
                workbench_refs=(workbench.workbench_id,),
                guide_refs=(
                    workbench.instruction_resource,
                    *workbench.administration_guides,
                    *workbench.authoritative_guides,
                ),
                response_surface_bindings=workbench.response_surface_bindings,
                compatibility=compatibility,
                provenance=provenance,
            )
        )
    return tuple(sorted(entries, key=lambda item: item.contract_ref))


def _primary_transaction_kind(workbench: WorkflowWorkbench) -> str:
    preferred = _PRIMARY_TRANSACTION_KIND.get(workbench.workbench_id)
    if preferred is not None:
        return preferred
    for candidate in ("draft", "commit", "validate", "orient", "inspect"):
        if candidate in workbench.allowed_transaction_kinds:
            return candidate
    raise WorkflowLayerError(f"{workbench.workbench_id} does not declare any transaction kinds")


def _render_compatibility_registry_text(payload: Mapping[str, Any]) -> str:
    comment = "# Generated compatibility projection. Do not use this file as runtime authority.\n"
    return comment + yaml.safe_dump(payload, sort_keys=False)


def _workbench_to_projection_dict(workbench: WorkflowWorkbench) -> dict[str, Any]:
    return {
        "workbench_id": workbench.workbench_id,
        "display_name": workbench.display_name,
        "lifecycle_placement": _lifecycle_to_dict(workbench.lifecycle_placement),
        "artifacts_in_scope": list(workbench.artifacts_in_scope),
        "intent_classes": list(workbench.intent_classes),
        "posture_constraints": list(workbench.posture_constraints),
        "workflow_surface": {
            "allowed_transaction_kinds": list(workbench.allowed_transaction_kinds),
            "draftable_artifact_families": list(workbench.draftable_artifact_families),
            "contract_refs": list(workbench.contract_refs),
            "inspect_views": list(workbench.inspect_views),
            "response_surface_bindings": [
                {
                    "transaction_kind": binding.transaction_kind,
                    "response_envelope": binding.response_envelope,
                    "allowed_resource_roles": list(binding.allowed_resource_roles),
                }
                for binding in workbench.response_surface_bindings
            ],
        },
        "instruction_resource": workbench.instruction_resource,
        "authoritative_guides": list(workbench.authoritative_guides),
        "administration_guides": list(workbench.administration_guides),
        "entry_conditions": list(workbench.entry_conditions),
        "exit_conditions": list(workbench.exit_conditions),
    }


def _lifecycle_to_dict(placement: LifecyclePlacement) -> dict[str, Any]:
    if placement.kind == "covered_gates":
        return {"kind": placement.kind, "covered_gates": list(placement.covered_gates)}
    if placement.kind == "lifecycle_span":
        return {
            "kind": placement.kind,
            "start_gate": placement.start_gate,
            "end_gate": placement.end_gate,
        }
    return {"kind": placement.kind}


def _path_label(path: Path, anchor_root: Path | None) -> str:
    resolved = path.resolve()
    if anchor_root is None:
        return str(resolved)
    try:
        return resolved.relative_to(anchor_root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def load_effective_layer(
    *,
    workflow_layer: WorkflowLayer,
    configuration_root: Path | None = None,
    launcher_overlay_root: Path | None = None,
    workflow_id: str | None = None,
    workflow_folder: Path | None = None,
    workbench_folder: Path | None = None,
) -> "EffectiveLayer":
    del configuration_root, launcher_overlay_root, workflow_id, workflow_folder, workbench_folder

    from lantern.workflow.merger import ConfigurationMerger

    merger = ConfigurationMerger()
    return merger.merge(
        baseline_surface_classification=workflow_layer.runtime_surface_classification,
        baseline_version=workflow_layer.grammar_version or "unknown",
        selected_workflow_id=workflow_layer.selected_workflow_id,
        selected_workflow_display_name=workflow_layer.selected_workflow_display_name,
        selected_workflow_source_path=workflow_layer.selected_workflow_source_path,
        active_workbench_ids=tuple(workbench.workbench_id for workbench in workflow_layer.workbenches),
        workflow_root=workflow_layer.workflow_catalog_root,
        workbench_root=workflow_layer.workbench_catalog_root,
    )
