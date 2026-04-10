"""Grammar-backed workflow layer loader for Lantern."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable, Mapping

if TYPE_CHECKING:
    from lantern.workflow.merger import EffectiveLayer

import yaml

from lantern.registry.loader import (
    DEFAULT_SCHEMA_JSON_PATH,
    _build_projected_workbench_registry,
)

try:
    from lantern_grammar import Grammar, LanternGrammarLoadError
except Exception as exc:  # pragma: no cover - exercised in runtime environments missing the package
    Grammar = None  # type: ignore[assignment]
    LanternGrammarLoadError = RuntimeError  # type: ignore[assignment]
    _GRAMMAR_IMPORT_ERROR = exc
else:
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

_ALLOWED_RESOURCE_ROLES = {"instruction_resource", "authoritative_guides", "administration_guides"}
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


@dataclass(frozen=True)
class WorkflowWorkbench:
    workbench_id: str
    display_name: str
    lifecycle_placement: Any
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
    source: str
    enabled: bool
    governance_mode: str
    content_hash: str


@dataclass(frozen=True)
class WorkflowLayer:
    runtime_surface_classification: str
    workbenches: tuple[WorkflowWorkbench, ...]
    transaction_profiles: tuple[TransactionProfile, ...]
    contract_catalog: tuple[ContractCatalogEntry, ...]
    resource_manifest: tuple[ResourceManifestEntry, ...]
    grammar_version: str
    grammar_package_version: str

    def get_workbench(self, workbench_id: str) -> WorkflowWorkbench:
        for workbench in self.workbenches:
            if workbench.workbench_id == workbench_id:
                return workbench
        raise KeyError(workbench_id)


@dataclass(frozen=True)
class GeneratedArtifacts:
    contract_catalog_payload: list[dict[str, Any]]
    resource_manifest_payload: list[dict[str, Any]]
    workflow_map_text: str
    workbench_resource_bindings_text: str


def load_workflow_layer(
    *,
    registry_path: str | Path | None = None,
    schema_path: str | Path | None = None,
    transaction_profiles_path: str | Path | None = None,
    contract_catalog_path: str | Path | None = None,
    resource_manifest_path: str | Path | None = None,
    workflow_map_path: str | Path | None = None,
    workbench_resource_bindings_path: str | Path | None = None,
    relocation_manifest_path: str | Path | None = None,
) -> WorkflowLayer:
    grammar = _load_grammar()
    grammar_manifest = dict(grammar.manifest())
    grammar_version = str(grammar_manifest.get("model_version", ""))
    grammar_package_version = str(grammar.package_version())

    registry_file = Path(registry_path or DEFAULT_REGISTRY_PATH)
    schema_file = Path(schema_path or DEFAULT_SCHEMA_PATH)
    transaction_profiles_file = Path(transaction_profiles_path or DEFAULT_TRANSACTION_PROFILES_PATH)
    contract_catalog_file = Path(contract_catalog_path or DEFAULT_CONTRACT_CATALOG_PATH)
    resource_manifest_file = Path(resource_manifest_path or DEFAULT_RESOURCE_MANIFEST_PATH)
    workflow_map_file = Path(workflow_map_path or DEFAULT_WORKFLOW_MAP_PATH)
    workbench_bindings_file = Path(workbench_resource_bindings_path or DEFAULT_WORKBENCH_BINDINGS_PATH)
    relocation_manifest_file = Path(relocation_manifest_path or DEFAULT_RELOCATION_MANIFEST_PATH)

    registry_payload = _load_yaml(registry_file, "workflow registry")
    schema_payload = _load_yaml(schema_file, "workflow schema")
    profiles_payload = _load_yaml(transaction_profiles_file, "transaction profiles")
    relocation_manifest = _load_yaml(relocation_manifest_file, "relocation manifest")

    foundation_registry = _load_foundation_projection(registry_payload, schema_file)
    _validate_additive_schema(registry_payload, schema_payload)
    transaction_profiles = _load_transaction_profiles(profiles_payload)
    transaction_profile_map = {profile.transaction_kind: profile for profile in transaction_profiles}

    workbenches = _build_workbenches(
        registry_payload=registry_payload,
        foundation_registry=foundation_registry,
        transaction_profiles=transaction_profile_map,
    )
    _validate_collective_artifact_family_coverage(workbenches)
    _validate_grammar_gate_compatibility(grammar, workbenches, grammar_version)

    resource_manifest = _derive_resource_manifest(
        relocation_manifest=relocation_manifest,
        workbenches=workbenches,
        product_root=_product_root(registry_file),
    )
    contract_catalog = _build_contract_catalog(
        workbenches=workbenches,
        transaction_profiles=transaction_profile_map,
        grammar=grammar,
        grammar_version=grammar_version,
        grammar_package_version=grammar_package_version,
    )
    generated = render_generated_artifacts(
        runtime_surface_classification=foundation_registry.runtime_surface_classification,
        workbenches=workbenches,
        transaction_profiles=transaction_profiles,
        contract_catalog=contract_catalog,
        resource_manifest=resource_manifest,
    )

    _assert_committed_json_matches(contract_catalog_file, generated.contract_catalog_payload, "contract_catalog.json")
    _assert_committed_json_matches(resource_manifest_file, generated.resource_manifest_payload, "resource_manifest.json")
    _assert_committed_text_matches(workflow_map_file, generated.workflow_map_text, "workflow_map.md")
    _assert_committed_text_matches(workbench_bindings_file, generated.workbench_resource_bindings_text, "workbench_resource_bindings.md")

    return WorkflowLayer(
        runtime_surface_classification=foundation_registry.runtime_surface_classification,
        workbenches=workbenches,
        transaction_profiles=transaction_profiles,
        contract_catalog=contract_catalog,
        resource_manifest=resource_manifest,
        grammar_version=grammar_version,
        grammar_package_version=grammar_package_version,
    )


def render_generated_artifacts(
    *,
    runtime_surface_classification: str,
    workbenches: tuple[WorkflowWorkbench, ...],
    transaction_profiles: tuple[TransactionProfile, ...],
    contract_catalog: tuple[ContractCatalogEntry, ...],
    resource_manifest: tuple[ResourceManifestEntry, ...],
) -> GeneratedArtifacts:
    contract_payload = [_contract_entry_to_dict(entry) for entry in contract_catalog]
    resource_payload = [_resource_entry_to_dict(entry) for entry in resource_manifest]

    workflow_map_lines = [
        "# Workflow map",
        "",
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

    return GeneratedArtifacts(
        contract_catalog_payload=contract_payload,
        resource_manifest_payload=resource_payload,
        workflow_map_text=workflow_map_text,
        workbench_resource_bindings_text=workbench_resource_bindings_text,
    )


def _load_grammar():
    if Grammar is None:
        raise WorkflowLayerError(
            "lantern_grammar public API import failed; install lantern_grammar before loading the workflow layer (for example from a sibling checkout: pip install -e ../lantern-grammar)"
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
    return grammar


def _load_yaml(path: Path, label: str) -> Any:
    if not path.exists():
        raise WorkflowLayerError(f"Missing {label}: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_foundation_projection(registry_payload: Mapping[str, Any], schema_file: Path):
    schema_metadata = _load_yaml(schema_file, "workflow schema")
    schema_payload = json.loads(DEFAULT_SCHEMA_JSON_PATH.read_text(encoding="utf-8"))
    return _build_projected_workbench_registry(
        registry_payload=registry_payload,
        schema_metadata=schema_metadata,
        schema_payload=schema_payload,
    )


def _validate_additive_schema(registry_payload: Mapping[str, Any], schema_payload: Mapping[str, Any]) -> None:
    runtime_classification = registry_payload.get("runtime_surface_classification")
    allowed_classifications = set(schema_payload.get("runtime_surface_classification_values", []))
    if runtime_classification not in allowed_classifications:
        raise WorkflowLayerError(
            f"runtime_surface_classification must be one of {sorted(allowed_classifications)}; got {runtime_classification!r}"
        )
    required_workbench_fields = schema_payload.get("required_workbench_fields", [])
    required_surface_fields = schema_payload.get("required_workflow_surface_fields", [])
    allowed_resource_roles = set(schema_payload.get("allowed_resource_roles", []))
    profile_shape = set(schema_payload.get("response_surface_binding_shape", {}).get("required", []))

    seen_ids: list[str] = []
    for workbench in registry_payload.get("workbenches", []):
        workbench_id = str(workbench.get("workbench_id", "<unknown-workbench>"))
        seen_ids.append(workbench_id)
        for field in required_workbench_fields:
            if field not in workbench:
                raise WorkflowLayerError(f"{workbench_id} missing required declaration field: {field}")
        workflow_surface = workbench.get("workflow_surface", {})
        for field in required_surface_fields:
            if field not in workflow_surface:
                raise WorkflowLayerError(f"{workbench_id}.workflow_surface missing required field: {field}")
        bindings = workflow_surface.get("response_surface_bindings", [])
        if not bindings:
            raise WorkflowLayerError(f"{workbench_id}.workflow_surface.response_surface_bindings must not be empty")
        inspect_views = set(workflow_surface.get("inspect_views", []))
        transaction_kinds = set(workflow_surface.get("allowed_transaction_kinds", []))
        for index, binding in enumerate(bindings):
            if not profile_shape.issubset(binding.keys()):
                missing = sorted(profile_shape - set(binding.keys()))
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] missing fields: {missing}"
                )
            tx = binding["transaction_kind"]
            if tx not in transaction_kinds:
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] uses undeclared transaction kind {tx!r}"
                )
            envelope = binding["response_envelope"]
            if tx == "inspect" and envelope not in inspect_views:
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] must use an inspect view response envelope; got {envelope!r}"
                )
            if tx != "inspect" and envelope != "default":
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] must use response_envelope 'default' for transaction kind {tx!r}"
                )
            roles = tuple(binding["allowed_resource_roles"])
            if not roles:
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] must declare at least one resource role"
                )
            for role in roles:
                if role not in allowed_resource_roles:
                    raise WorkflowLayerError(
                        f"{workbench_id}.workflow_surface.response_surface_bindings[{index}] uses unsupported resource role {role!r}"
                    )
    expected_ids = tuple(schema_payload.get("built_in_workbench_ids", []))
    if tuple(seen_ids) != expected_ids:
        raise WorkflowLayerError(f"Built-in workbench inventory mismatch: expected {expected_ids}, got {tuple(seen_ids)}")


def _load_transaction_profiles(profiles_payload: Mapping[str, Any]) -> tuple[TransactionProfile, ...]:
    profiles = []
    seen_kinds: set[str] = set()
    for item in profiles_payload.get("transaction_profiles", []):
        required = {"transaction_kind", "required_refs", "bounded_families", "allowed_contract_refs", "side_effect_class"}
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


def _build_workbenches(
    *,
    registry_payload: Mapping[str, Any],
    foundation_registry: Any,
    transaction_profiles: Mapping[str, TransactionProfile],
) -> tuple[WorkflowWorkbench, ...]:
    workbenches = []
    for base, raw in zip(foundation_registry.workbenches, registry_payload["workbenches"], strict=True):
        workbench_id = raw["workbench_id"]
        response_surface_bindings = []
        for binding in raw["workflow_surface"]["response_surface_bindings"]:
            transaction_kind = str(binding["transaction_kind"])
            if transaction_kind not in transaction_profiles:
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.response_surface_bindings references unknown transaction kind {transaction_kind!r}"
                )
            if raw["workflow_surface"]["contract_refs"][0] not in transaction_profiles[transaction_kind].allowed_contract_refs:
                raise WorkflowLayerError(
                    f"{workbench_id}.workflow_surface.contract_refs[0] is not allowed by transaction profile {transaction_kind!r}"
                )
            response_surface_bindings.append(
                ResponseSurfaceBinding(
                    transaction_kind=transaction_kind,
                    response_envelope=str(binding["response_envelope"]),
                    allowed_resource_roles=tuple(str(v) for v in binding["allowed_resource_roles"]),
                )
            )
        workbenches.append(
            WorkflowWorkbench(
                workbench_id=base.workbench_id,
                display_name=base.display_name,
                lifecycle_placement=base.lifecycle_placement,
                artifacts_in_scope=base.artifacts_in_scope,
                intent_classes=base.intent_classes,
                posture_constraints=base.posture_constraints,
                allowed_transaction_kinds=base.workflow_surface.allowed_transaction_kinds,
                draftable_artifact_families=base.workflow_surface.draftable_artifact_families,
                contract_refs=base.workflow_surface.contract_refs,
                inspect_views=base.workflow_surface.inspect_views,
                response_surface_bindings=tuple(response_surface_bindings),
                instruction_resource=base.instruction_resource,
                authoritative_guides=base.authoritative_guides,
                administration_guides=base.administration_guides,
                entry_conditions=base.entry_conditions,
                exit_conditions=base.exit_conditions,
                source=base.source,
                enabled=base.enabled,
                governance_mode=base.governance_mode,
                content_hash=_sha256_text(json.dumps(raw, sort_keys=True, separators=(",", ":"))),
            )
        )
    return tuple(workbenches)


def _validate_collective_artifact_family_coverage(workbenches: Iterable[WorkflowWorkbench]) -> None:
    observed = {family for workbench in workbenches if workbench.enabled for family in workbench.artifacts_in_scope}
    missing = sorted(_REQUIRED_ARTIFACT_FAMILIES - observed)
    if missing:
        raise WorkflowLayerError(f"Workflow layer is missing required artifact families: {missing}")


def _validate_grammar_gate_compatibility(grammar: Any, workbenches: Iterable[WorkflowWorkbench], grammar_version: str) -> None:
    for workbench in workbenches:
        gate_ids = []
        placement = workbench.lifecycle_placement
        if placement.kind == "covered_gates":
            gate_ids.extend(placement.covered_gates)
        elif placement.kind == "lifecycle_span":
            gate_ids.extend([placement.start_gate, placement.end_gate])
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


def _build_contract_catalog(
    *,
    workbenches: tuple[WorkflowWorkbench, ...],
    transaction_profiles: Mapping[str, TransactionProfile],
    grammar: Any,
    grammar_version: str,
    grammar_package_version: str,
) -> tuple[ContractCatalogEntry, ...]:
    entries = []
    for workbench in workbenches:
        contract_ref = workbench.contract_refs[0]
        primary_transaction_kind = _PRIMARY_TRANSACTION_KIND[workbench.workbench_id]
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
            "runtime_surface_classification": "full_governed_surface",
        }
        provenance = {
            "generated_from": [
                "lantern/workflow/definitions/workbench_registry.yaml",
                "lantern/workflow/definitions/transaction_profiles.yaml",
                "lantern/preservation/relocation_manifest.yaml",
            ],
            "source": workbench.source,
        }
        entries.append(
            ContractCatalogEntry(
                contract_ref=contract_ref,
                request_schema_ref=f"schema.request.{workbench.workbench_id}.v1",
                transaction_kind=primary_transaction_kind,
                family_binding=workbench.artifacts_in_scope,
                gate_binding=tuple(gate_binding),
                workbench_refs=(workbench.workbench_id,),
                guide_refs=(workbench.instruction_resource, *workbench.administration_guides, *workbench.authoritative_guides),
                response_surface_bindings=workbench.response_surface_bindings,
                compatibility=compatibility,
                provenance=provenance,
            )
        )
    return tuple(sorted(entries, key=lambda item: item.contract_ref))


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
        return [placement.start_gate, placement.end_gate]
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



def load_effective_layer(
    *,
    workflow_layer: WorkflowLayer,
    configuration_root: Path | None = None,
    launcher_overlay_root: Path | None = None,
) -> "EffectiveLayer":
    """Build an EffectiveLayer from a loaded WorkflowLayer and an optional configuration surface.

    Imports merger components lazily to avoid circular imports at module load time.
    """
    from lantern.workflow.merger import (
        ConfigurationLoader,
        ConfigurationMerger,
        EffectiveLayer,
    )

    loader = ConfigurationLoader()
    merger = ConfigurationMerger()

    config_surface = None
    if configuration_root is not None:
        config_folder = Path(configuration_root) / "workflow" / "configuration"
        if config_folder.exists():
            config_surface = loader.load_and_validate(config_folder)

    overlay_surface = None
    if launcher_overlay_root is not None:
        overlay_folder = Path(launcher_overlay_root) / "workflow" / "configuration"
        if overlay_folder.exists():
            overlay_surface = loader.load_and_validate(overlay_folder)

    return merger.merge(
        baseline_surface_classification=workflow_layer.runtime_surface_classification,
        baseline_version=workflow_layer.grammar_version or "unknown",
        configuration_surface=config_surface,
        launcher_overlay_surface=overlay_surface,
    )
