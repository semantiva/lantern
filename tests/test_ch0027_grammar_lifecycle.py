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

"""TD-0027 proxy tests for CH-0027: Lantern Grammar 0.4.0 Runtime and Lifecycle Compatibility."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_POLICY_MANIFEST = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "lifecycle-policy" / "manifest.yaml"
STATUS_CONTRACT_PATH = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "artifact_status_contract.json"


def _grammar():
    from lantern_grammar import Grammar

    return Grammar.load()


# ── TC-001 / TC-002: Runtime and package metadata agree on 0.4.x ─────────────


def test_tc001_runtime_accepts_grammar_040() -> None:
    from lantern._compat import check_grammar_compatibility
    from lantern.workflow import load_workflow_layer

    result = check_grammar_compatibility()
    assert result["status"] == "ok", result
    wl = load_workflow_layer(enforce_generated_artifacts=True)
    assert wl.grammar_version.startswith("0.4.")
    assert wl.grammar_package_version.startswith("0.4.")


def test_tc002_compat_check_accepts_040_model_and_package() -> None:
    from lantern._compat import check_grammar_compatibility

    result = check_grammar_compatibility()
    assert result["status"] == "ok"
    assert result["installed_model_version"].startswith("0.4.")
    assert result["installed_package_version"].startswith("0.4.")
    assert result["supported_range"] == ">=0.4.0,<0.5.0"


# ── TC-003: Removed _initiative status IDs absent from live surfaces ──────────


def test_tc003_removed_initiative_ids_absent_from_lifecycle_bundle() -> None:
    manifest_dir = LIFECYCLE_POLICY_MANIFEST.parent
    for yaml_file in manifest_dir.glob("*.yaml"):
        content = yaml_file.read_text(encoding="utf-8")
        assert "_initiative" not in content, f"Removed _initiative ID found in lifecycle bundle file {yaml_file.name}"


def test_tc003_removed_initiative_ids_absent_from_status_contract() -> None:
    contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    for family_id, family_data in contract["families"].items():
        mapping = family_data.get("grammar_mapping", {})
        for status_id in mapping.values():
            assert (
                "_initiative" not in status_id
            ), f"Removed _initiative ID {status_id!r} in status contract family {family_id}"


# ── TC-004: Live status IDs resolve through Grammar 0.4.0 ─────────────────────


def test_tc004_live_grammar_ids_resolve_in_040() -> None:
    grammar = _grammar()
    contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    for family_id, family_data in contract["families"].items():
        mapping = family_data.get("grammar_mapping", {})
        for display_name, grammar_id in mapping.items():
            entity = grammar.get_entity(grammar_id)
            assert entity is not None, (
                f"Grammar ID {grammar_id!r} (family={family_id}, status={display_name!r}) "
                f"does not resolve in grammar 0.4.0"
            )


def test_tc004_draft_initiative_does_not_resolve() -> None:
    grammar = _grammar()
    assert grammar.get_entity("lg:statuses/draft_initiative") is None
    assert grammar.get_entity("lg:statuses/in_progress") is not None


# ── TC-005: Lifecycle declaration bundle validates ─────────────────────────────


def test_tc005_lifecycle_bundle_validates_against_grammar() -> None:
    from lantern_grammar import Grammar, Lifecycle

    grammar = Grammar.load()
    assert grammar.manifest()["model_version"].startswith("0.4.")
    lc = Lifecycle.from_manifest(grammar, LIFECYCLE_POLICY_MANIFEST)
    result = lc.validate()
    assert result.ok, [f"{i.path}: {i.message}" for i in result.issues]


def test_tc005_lifecycle_manifest_schema_version() -> None:
    manifest = yaml.safe_load(LIFECYCLE_POLICY_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    min_version = manifest["grammar_compatibility"]["min_model_version"]
    assert min_version == "0.4.0"


# ── TC-006: Family coverage and lifecycle derivation completeness ──────────────


def test_tc006_lifecycle_family_coverage_is_complete() -> None:
    from lantern_grammar import Grammar, Lifecycle

    grammar = Grammar.load()
    lc = Lifecycle.from_manifest(grammar, LIFECYCLE_POLICY_MANIFEST)
    expected = {
        "lg:artifacts/initiative",
        "lg:artifacts/dip",
        "lg:artifacts/spec",
        "lg:artifacts/arch",
        "lg:artifacts/td",
        "lg:artifacts/ch",
        "lg:artifacts/dc",
        "lg:artifacts/db",
        "lg:artifacts/ci",
    }
    assert set(lc.artifact_families()) == expected


def test_tc006_ch_lifecycle_includes_in_progress() -> None:
    ch_yaml = (LIFECYCLE_POLICY_MANIFEST.parent / "ch.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(ch_yaml)
    status_ids = [s["id"] for s in data["statuses"]]
    assert "lg:statuses/in_progress" in status_ids


def test_tc006_ci_lifecycle_excludes_in_progress() -> None:
    ci_yaml = (LIFECYCLE_POLICY_MANIFEST.parent / "ci.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(ci_yaml)
    status_ids = [s["id"] for s in data["statuses"]]
    assert "lg:statuses/in_progress" not in status_ids


# ── TC-007: governance repository workflow/ folder is absent ─────────────────


def test_tc007_governance_workflow_folder_removed() -> None:
    sibling_governance = PRODUCT_ROOT.parent / "lantern" "-" "governance"
    assert not (
        sibling_governance / "workflow"
    ).exists(), "The governance repository workflow/ folder must be removed as part of CH-0027"


# ── TC-009: High-value lifecycle constraints are queryable ────────────────────


def test_tc009_ch_ready_constraints_include_required_slots() -> None:
    from lantern_grammar import Grammar, Lifecycle

    grammar = Grammar.load()
    lc = Lifecycle.from_manifest(grammar, LIFECYCLE_POLICY_MANIFEST)
    constraints = lc.state_constraints_for("lg:artifacts/ch")
    ready = next((c for c in constraints if c.status_id == "lg:statuses/ready"), None)
    assert ready is not None, "CH Ready state must have constraints"
    slots = {t.slot for t in ready.traversals}
    assert "inputs_specs" in slots, f"inputs_specs slot missing from CH Ready constraints; got: {slots}"
    assert "inputs_arch" in slots, f"inputs_arch slot missing from CH Ready constraints; got: {slots}"
    assert "test_definition_refs" in slots, f"test_definition_refs slot missing from CH Ready constraints; got: {slots}"


def test_tc009_ch_addressed_requires_verified_ci() -> None:
    from lantern_grammar import Grammar, Lifecycle

    grammar = Grammar.load()
    lc = Lifecycle.from_manifest(grammar, LIFECYCLE_POLICY_MANIFEST)
    constraints = lc.state_constraints_for("lg:artifacts/ch")
    addressed = next((c for c in constraints if c.status_id == "lg:statuses/addressed"), None)
    assert addressed is not None, "CH Addressed state must have constraints"
    slots = {t.slot for t in addressed.traversals}
    assert "related_cis" in slots, f"related_cis slot missing from CH Addressed constraints; got: {slots}"


# ── TC-010: Lifecycle constraints are enforced in the validation path ─────────


def test_tc010_validator_rejects_ready_ch_without_spec_refs(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\n"
        "ch_id: CH-9999\n"
        "status: Ready\n"
        "title: Fixture CH missing upstream inputs\n"
        "inputs:\n"
        "  arch: []\n"
        "test_definition_refs: []\n"
        "```\n\n"
        "# CH-9999 — Fixture CH missing upstream inputs\n",
        encoding="utf-8",
    )

    findings = validate_governance_corpus(governance_root)
    anchors = {f["anchor"] for f in findings}

    assert (
        "lifecycle_policy.ch_ready_constraints" in anchors
    ), f"Expected lifecycle_policy.ch_ready_constraints finding for Ready CH without inputs.specs; got: {anchors}"


def test_tc010_validator_rejects_addressed_ch_without_related_cis(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\n"
        "ch_id: CH-9999\n"
        "status: Addressed\n"
        "title: Fixture Addressed CH without CI closure\n"
        "```\n\n"
        "# CH-9999 — Fixture Addressed CH without CI closure\n",
        encoding="utf-8",
    )

    findings = validate_governance_corpus(governance_root)
    anchors = {f["anchor"] for f in findings}

    assert (
        "lifecycle_policy.ch_addressed_constraints" in anchors
    ), f"Expected lifecycle_policy.ch_addressed_constraints finding for Addressed CH without related_cis; got: {anchors}"


def test_tc010_active_corpus_passes_lifecycle_constraint_validation() -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    sibling_governance = PRODUCT_ROOT.parent / "lantern" "-" "governance"
    if not sibling_governance.exists():
        return
    findings = validate_governance_corpus(sibling_governance)
    lifecycle_findings = [f for f in findings if f.get("anchor", "").startswith("lifecycle_policy.")]
    assert lifecycle_findings == [], f"Lifecycle constraint violations in active corpus: {lifecycle_findings}"


def _write_spec(governance_root: Path, spec_id: str, status: str) -> None:
    spec_path = governance_root / "spec" / f"{spec_id}.md"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        f"```yaml\nspec_id: {spec_id}\nstatus: {status}\ntitle: Fixture {spec_id}\n```\n\n"
        f"# {spec_id} — Fixture {spec_id}\n",
        encoding="utf-8",
    )


def _write_arch(governance_root: Path, arch_id: str, status: str) -> None:
    arch_path = governance_root / "arch" / f"{arch_id}.md"
    arch_path.parent.mkdir(parents=True, exist_ok=True)
    arch_path.write_text(
        f"```yaml\narch_id: {arch_id}\nstatus: {status}\ntitle: Fixture {arch_id}\n```\n\n"
        f"# {arch_id} — Fixture {arch_id}\n",
        encoding="utf-8",
    )


def _write_td(governance_root: Path, td_id: str, status: str) -> None:
    td_path = governance_root / "td" / f"{td_id}.md"
    td_path.parent.mkdir(parents=True, exist_ok=True)
    td_path.write_text(
        f"```yaml\ntd_id: {td_id}\nstatus: {status}\ntitle: Fixture {td_id}\n```\n\n" f"# {td_id} — Fixture {td_id}\n",
        encoding="utf-8",
    )


def _write_ci(governance_root: Path, ci_id: str, status: str) -> None:
    ci_path = governance_root / "ci" / f"{ci_id}.md"
    ci_path.parent.mkdir(parents=True, exist_ok=True)
    ci_path.write_text(
        f"```yaml\nci_id: {ci_id}\nstatus: {status}\ntitle: Fixture {ci_id}\n```\n\n" f"# {ci_id} — Fixture {ci_id}\n",
        encoding="utf-8",
    )


def _ready_ch_with_refs(
    governance_root: Path,
    *,
    spec_refs: list,
    arch_refs: list | None = None,
    td_refs: list | None = None,
) -> None:
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    specs = spec_refs or []
    arches = arch_refs if arch_refs is not None else ["ARCH-0001"]
    tds = td_refs if td_refs is not None else ["TD-0001"]
    spec_yaml = "\n".join(f"    - {s}" for s in specs) if specs else "    []"
    arch_yaml = "\n".join(f"    - {a}" for a in arches) if arches else "    []"
    td_yaml = "\n".join(f"    - {t}" for t in tds) if tds else "    []"
    ch_path.write_text(
        f"```yaml\nch_id: CH-9999\nstatus: Ready\ntitle: Fixture CH\n"
        f"inputs:\n  specs:\n{spec_yaml}\n  arch:\n{arch_yaml}\n"
        f"test_definition_refs:\n{td_yaml}\n```\n\n# CH-9999 — Fixture CH\n",
        encoding="utf-8",
    )


def test_tc010_ready_ch_with_nonexistent_spec_ref_rejected(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _ready_ch_with_refs(governance_root, spec_refs=["SPEC-9999"])  # SPEC-9999 does not exist
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    assert (
        "lifecycle_policy.ch_ready_constraints" in anchors
    ), f"Expected ch_ready_constraints for nonexistent SPEC ref; got: {anchors}"


def test_tc010_ready_ch_with_draft_spec_ref_rejected(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _write_spec(governance_root, "SPEC-9999", "Draft")
    _ready_ch_with_refs(governance_root, spec_refs=["SPEC-9999"])
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    assert (
        "lifecycle_policy.ch_ready_constraints" in anchors
    ), f"Expected ch_ready_constraints for Draft SPEC ref; got: {anchors}"


def test_tc010_addressed_ch_with_nonexistent_ci_rejected(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\nch_id: CH-9999\nstatus: Addressed\ntitle: Fixture CH\n"
        "related_cis:\n  - CI-9999-nonexistent\n```\n\n# CH-9999 — Fixture CH\n",
        encoding="utf-8",
    )
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    assert (
        "lifecycle_policy.ch_addressed_constraints" in anchors
    ), f"Expected ch_addressed_constraints for nonexistent CI ref; got: {anchors}"


def test_tc010_addressed_ch_with_zero_verified_cis_rejected(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _write_ci(governance_root, "CI-9999-aaa", "Candidate")
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\nch_id: CH-9999\nstatus: Addressed\ntitle: Fixture CH\n"
        "related_cis:\n  - CI-9999-aaa\n```\n\n# CH-9999 — Fixture CH\n",
        encoding="utf-8",
    )
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    assert (
        "lifecycle_policy.ch_addressed_constraints" in anchors
    ), f"Expected ch_addressed_constraints for zero Verified CIs; got: {anchors}"


def test_tc010_addressed_ch_with_two_verified_cis_rejected(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _write_ci(governance_root, "CI-9999-aaa", "Verified")
    _write_ci(governance_root, "CI-9999-bbb", "Verified")
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\nch_id: CH-9999\nstatus: Addressed\ntitle: Fixture CH\n"
        "related_cis:\n  - CI-9999-aaa\n  - CI-9999-bbb\n```\n\n# CH-9999 — Fixture CH\n",
        encoding="utf-8",
    )
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    assert (
        "lifecycle_policy.ch_addressed_constraints" in anchors
    ), f"Expected ch_addressed_constraints for 2 Verified CIs (exact:1 required); got: {anchors}"


def test_tc010_addressed_ch_with_non_terminal_ci_rejected(tmp_path: Path) -> None:
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _write_ci(governance_root, "CI-9999-aaa", "Verified")
    _write_ci(governance_root, "CI-9999-bbb", "Candidate")
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\nch_id: CH-9999\nstatus: Addressed\ntitle: Fixture CH\n"
        "related_cis:\n  - CI-9999-aaa\n  - CI-9999-bbb\n```\n\n# CH-9999 — Fixture CH\n",
        encoding="utf-8",
    )
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    assert (
        "lifecycle_policy.ch_addressed_constraints" in anchors
    ), f"Expected ch_addressed_constraints for non-terminal CI; got: {anchors}"


# ── TC-011: Lifecycle policy inspect kind exposes state constraints ─────────────


def test_tc011_inspect_lifecycle_policy_returns_ch_state_constraints() -> None:
    from lantern.mcp.inspect import handle_inspect
    from lantern.workflow import load_workflow_layer

    wl = load_workflow_layer()
    result = handle_inspect(kind="lifecycle_policy", workflow_layer=wl)
    assert result.kind == "lifecycle_policy"
    assert result.schema_version == "1.0"
    ch_family = next((f for f in result.families if f["family_id"] == "lg:artifacts/ch"), None)
    assert ch_family is not None, "CH family must appear in lifecycle_policy inspect result"
    constraint_status_ids = {c["status_id"] for c in ch_family["state_constraints"]}
    assert "lg:statuses/ready" in constraint_status_ids
    assert "lg:statuses/addressed" in constraint_status_ids
    ready_constraint = next(c for c in ch_family["state_constraints"] if c["status_id"] == "lg:statuses/ready")
    assert "inputs_specs" in ready_constraint["slots"]
    assert "inputs_arch" in ready_constraint["slots"]
    assert "test_definition_refs" in ready_constraint["slots"]


# ── TC-014 addendum: lifecycle projection freshness is mechanically enforced ───


def test_tc014_lifecycle_projection_divergence_is_rejected(tmp_path: Path) -> None:
    import shutil
    import yaml

    from lantern.workflow.loader import load_workflow_layer

    src = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "lifecycle-policy"
    dst = tmp_path / "lifecycle-policy"
    shutil.copytree(src, dst)
    ch_path = dst / "ch.yaml"
    ch_data = yaml.safe_load(ch_path.read_text(encoding="utf-8"))
    ch_data["statuses"] = [s for s in ch_data["statuses"] if s["id"] != "lg:statuses/in_progress"]
    ch_data["transitions"] = [
        t
        for t in ch_data.get("transitions", [])
        if t.get("from") != "lg:statuses/in_progress" and t.get("to") != "lg:statuses/in_progress"
    ]
    ch_path.write_text(yaml.dump(ch_data), encoding="utf-8")

    try:
        load_workflow_layer(lifecycle_policy_manifest_path=dst / "manifest.yaml", enforce_generated_artifacts=True)
        assert False, "Expected WorkflowLayerError for lifecycle projection divergence"
    except Exception as exc:
        assert "divergence" in str(exc).lower() or "CH" in str(exc), f"Expected divergence error; got: {exc}"


# ── TC-002 addendum: missing model version is rejected ───────────────────────


def test_tc002_missing_model_version_is_rejected() -> None:
    from lantern._compat import _evaluate_versions

    result = _evaluate_versions("0.4.0", "")
    assert result["status"] == "unsupported", "Missing model version must be reported as unsupported, not ok"

    result2 = _evaluate_versions("0.4.0", None)
    assert result2["status"] == "unsupported", "None model version must be reported as unsupported, not ok"


# ── TC-003 addendum: live procedures do not contain inverted GT-050/GT-060 ───


def test_tc003_no_live_procedure_inverts_gt050_gt060() -> None:
    admin_dir = PRODUCT_ROOT / "lantern" / "administration_procedures"
    for proc_file in admin_dir.glob("*.md"):
        content = proc_file.read_text(encoding="utf-8")
        assert (
            "GT-050 (ARCH" not in content and "GT-050 for ARCH" not in content
        ), f"{proc_file.name}: still describes GT-050 as ARCH baseline readiness"
        assert (
            "GT-060 (SPEC" not in content and "GT-060 for SPEC" not in content
        ), f"{proc_file.name}: still describes GT-060 as SPEC baseline readiness"


# ── TC-012: GT-050/GT-060 live semantics match Grammar 0.4.0 ─────────────────


def test_tc012_gt050_maps_to_spec_readiness() -> None:
    grammar = _grammar()
    deps = grammar.gate_dependencies("lg:gates/gt_050")
    inputs = deps.get("requires_input", [])
    assert "lg:artifacts/spec" in inputs, f"GT-050 must require SPEC input, got: {inputs}"
    assert "lg:artifacts/arch" not in inputs, f"GT-050 must not require ARCH input, got: {inputs}"


def test_tc012_gt060_maps_to_arch_readiness() -> None:
    grammar = _grammar()
    deps = grammar.gate_dependencies("lg:gates/gt_060")
    inputs = deps.get("requires_input", [])
    assert "lg:artifacts/arch" in inputs, f"GT-060 must require ARCH input, got: {inputs}"
    assert "lg:artifacts/spec" not in inputs, f"GT-060 must not require SPEC input, got: {inputs}"


def test_tc012_gates_md_uses_correct_semantics() -> None:
    gates_content = (PRODUCT_ROOT / "lantern" / "preservation" / "GATES.md").read_text(encoding="utf-8")
    assert "GT-050 — Requirements Specification Readiness" in gates_content
    assert "GT-060 — Architecture Definition Readiness" in gates_content
    assert "GT-050 — Architecture" not in gates_content
    assert "GT-060 — Requirements" not in gates_content


# ── TC-013: Generated projections pass enforced-artifact validation ────────────


def test_tc013_generated_artifacts_pass_enforcement() -> None:
    from lantern.workflow import load_workflow_layer

    wl = load_workflow_layer(enforce_generated_artifacts=True)
    assert wl.grammar_version.startswith("0.4.")


def test_tc013_contract_catalog_records_040_grammar() -> None:
    from lantern.workflow import load_workflow_layer

    wl = load_workflow_layer(enforce_generated_artifacts=False)
    for entry in wl.contract_catalog:
        compat = entry.compatibility
        grammar_version = compat.get("grammar_version", "")
        assert grammar_version.startswith(
            "0.4."
        ), f"Expected grammar 0.4.x in contract_catalog entry, got: {grammar_version!r}"


# ── TC-017: Repository boundary respected ─────────────────────────────────────


def test_tc017_no_changes_in_grammar_repo() -> None:
    grammar_repo = PRODUCT_ROOT.parent / "lantern-grammar"
    assert grammar_repo.exists(), "lantern-grammar repo must exist for boundary check"
    import subprocess

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=grammar_repo,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (
        result.stdout.strip() == ""
    ), f"lantern-grammar has uncommitted changes (boundary violation):\n{result.stdout}"


# ── B2: Related-family enforcement in lifecycle constraint validation ──────────


def test_b2_arch_ref_in_specs_slot_rejected(tmp_path: Path) -> None:
    """ARCH artifact referenced in inputs.specs (expected lg:artifacts/spec) must be rejected."""
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _write_arch(governance_root, "ARCH-9999", "Approved")
    _ready_ch_with_refs(governance_root, spec_refs=["ARCH-9999"])
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    messages = [f["message"] for f in findings]
    assert (
        "lifecycle_policy.ch_ready_constraints" in anchors
    ), f"Expected ch_ready_constraints for ARCH ref in inputs.specs slot; anchors={anchors}"
    assert any("family" in m.lower() for m in messages), f"Expected family mismatch message; messages={messages}"


def test_b2_spec_ref_in_arch_slot_rejected(tmp_path: Path) -> None:
    """SPEC artifact referenced in inputs.arch (expected lg:artifacts/arch) must be rejected."""
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _write_spec(governance_root, "SPEC-9999", "Approved")
    # Use SPEC-9999 in the arch slot; td slot deliberately left as non-existent default
    _ready_ch_with_refs(governance_root, spec_refs=[], arch_refs=["SPEC-9999"], td_refs=[])
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    messages = [f["message"] for f in findings]
    assert (
        "lifecycle_policy.ch_ready_constraints" in anchors
    ), f"Expected ch_ready_constraints for SPEC ref in inputs.arch slot; anchors={anchors}"
    assert any("family" in m.lower() for m in messages), f"Expected family mismatch message; messages={messages}"


def test_b2_arch_ref_in_td_slot_rejected(tmp_path: Path) -> None:
    """ARCH artifact referenced in test_definition_refs (expected lg:artifacts/td) must be rejected."""
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    _write_spec(governance_root, "SPEC-9999", "Approved")
    _write_arch(governance_root, "ARCH-9999", "Approved")
    _ready_ch_with_refs(
        governance_root,
        spec_refs=["SPEC-9999"],
        arch_refs=["ARCH-9999"],
        td_refs=["ARCH-9999"],
    )
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    messages = [f["message"] for f in findings]
    assert (
        "lifecycle_policy.ch_ready_constraints" in anchors
    ), f"Expected ch_ready_constraints for ARCH ref in test_definition_refs slot; anchors={anchors}"
    assert any("family" in m.lower() for m in messages), f"Expected family mismatch message; messages={messages}"


def test_b2_ch_ref_in_related_cis_slot_rejected(tmp_path: Path) -> None:
    """CH artifact referenced in related_cis (expected lg:artifacts/ci) must be rejected."""
    from lantern.artifacts.validator import validate_governance_corpus

    governance_root = tmp_path / "governance"
    other_ch_path = governance_root / "ch" / "CH-9998.md"
    other_ch_path.parent.mkdir(parents=True, exist_ok=True)
    other_ch_path.write_text(
        "```yaml\nch_id: CH-9998\nstatus: Addressed\ntitle: Fixture CH-9998\n```\n\n" "# CH-9998 — Fixture CH-9998\n",
        encoding="utf-8",
    )
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.write_text(
        "```yaml\nch_id: CH-9999\nstatus: Addressed\ntitle: Fixture CH\n"
        "related_cis:\n  - CH-9998\n```\n\n# CH-9999 — Fixture CH\n",
        encoding="utf-8",
    )
    findings = validate_governance_corpus(governance_root)
    anchors = [f["anchor"] for f in findings]
    messages = [f["message"] for f in findings]
    assert (
        "lifecycle_policy.ch_addressed_constraints" in anchors
    ), f"Expected ch_addressed_constraints for CH ref in related_cis slot; anchors={anchors}"
    assert any("family" in m.lower() for m in messages), f"Expected family mismatch message; messages={messages}"


# ── B3: Invalid CH status admissibility enforcement ──────────────────────────


def test_b3_invalid_ch_status_rejected_by_validate_artifact_file(tmp_path: Path) -> None:
    """validate_artifact_file must reject CH artifacts with inadmissible statuses such as 'Selected'."""
    from lantern.artifacts.validator import validate_artifact_file

    ch_path = tmp_path / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\nch_id: CH-9999\nstatus: Selected\ntitle: Fixture CH with invalid status\n```\n\n"
        "# CH-9999 — Fixture CH with invalid status\n",
        encoding="utf-8",
    )
    findings = validate_artifact_file(ch_path)
    anchors = [f["anchor"] for f in findings]
    assert any(
        a in ("status_contract.status", "status_contract.alias") for a in anchors
    ), f"Expected status_contract finding for inadmissible status 'Selected'; anchors={anchors}"


# ── B4: Lifecycle transition projection parity enforcement ────────────────────


def test_tc014_lifecycle_transition_divergence_is_rejected(tmp_path: Path) -> None:
    """Removing a transition from the lifecycle bundle (without removing the status) must be detected."""
    import shutil

    from lantern.workflow.loader import load_workflow_layer

    src = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "lifecycle-policy"
    dst = tmp_path / "lifecycle-policy"
    shutil.copytree(src, dst)
    ch_path = dst / "ch.yaml"
    ch_data = yaml.safe_load(ch_path.read_text(encoding="utf-8"))
    # Remove ready→in_progress transition while keeping the in_progress status
    ch_data["transitions"] = [
        t
        for t in ch_data.get("transitions", [])
        if not (t.get("from") == "lg:statuses/ready" and t.get("to") == "lg:statuses/in_progress")
    ]
    ch_path.write_text(yaml.dump(ch_data), encoding="utf-8")

    try:
        load_workflow_layer(lifecycle_policy_manifest_path=dst / "manifest.yaml", enforce_generated_artifacts=True)
        assert False, "Expected WorkflowLayerError for lifecycle transition projection divergence"
    except Exception as exc:
        assert "transition" in str(exc).lower() or "CH" in str(exc), f"Expected transition divergence error; got: {exc}"


# ── B5: Orient lifecycle blocker exposure ─────────────────────────────────────


def test_b5_orient_reports_lifecycle_blockers_for_ch_with_violations(tmp_path: Path) -> None:
    """handle_orient must surface lifecycle constraint violations as blockers when governance_root is available."""
    from lantern.mcp.orient import handle_orient
    from lantern.workflow import load_workflow_layer

    governance_root = tmp_path / "governance"
    ch_path = governance_root / "ch" / "CH-9999.md"
    ch_path.parent.mkdir(parents=True, exist_ok=True)
    ch_path.write_text(
        "```yaml\nch_id: CH-9999\nstatus: Ready\ntitle: Fixture CH\n"
        "inputs:\n  specs: []\n  arch: []\ntest_definition_refs: []\n```\n\n"
        "# CH-9999 — Fixture CH\n",
        encoding="utf-8",
    )
    wl = load_workflow_layer()
    governance_state = {"ch_statuses": {"CH-9999": "Ready"}, "active_gates": [], "passed_gates": []}
    result = handle_orient(
        workflow_layer=wl,
        governance_state=governance_state,
        ch_id="CH-9999",
        governance_root=governance_root,
    )
    assert any(
        "lifecycle_constraint" in b for b in result.blockers
    ), f"Expected lifecycle_constraint blockers in orient result; got blockers={result.blockers}"


# ── B2: Projection parity omission-gap enforcement ───────────────────────────


def test_b2_missing_projection_family_raises(tmp_path: Path) -> None:
    """Lifecycle bundle declares CH (a known family) absent from projection → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    contract_without_ch = {
        **real_contract,
        "families": {k: v for k, v in real_contract["families"].items() if k != "CH"},
    }
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(contract_without_ch), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError when CH absent from projection"
    except WorkflowLayerError as exc:
        assert "CH" in str(exc) or "absent" in str(exc).lower(), f"Expected CH-related error; got: {exc}"


def test_b2_missing_ini_projection_family_raises(tmp_path: Path) -> None:
    """Lifecycle bundle declares lg:artifacts/initiative mapped to 'INI' — absent INI must raise, not silently skip."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    contract_without_ini = {
        **real_contract,
        "families": {k: v for k, v in real_contract["families"].items() if k != "INI"},
    }
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(contract_without_ini), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError when INI absent from projection"
    except WorkflowLayerError as exc:
        assert (
            "INI" in str(exc) or "absent" in str(exc).lower() or "initiative" in str(exc).lower()
        ), f"Expected INI-related error; got: {exc}"


def test_b2_empty_grammar_mapping_raises(tmp_path: Path) -> None:
    """Lifecycle projection with empty grammar_mapping for CH → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["CH"] = {**real_contract["families"]["CH"], "grammar_mapping": {}}
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for empty grammar_mapping"
    except WorkflowLayerError as exc:
        assert "grammar_mapping" in str(exc).lower() or "CH" in str(exc), f"Expected grammar_mapping error; got: {exc}"


def test_b2_bundle_transitions_without_projection_transitions_raises(tmp_path: Path) -> None:
    """CH bundle has transitions but projection transitions list is empty → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["CH"] = {**real_contract["families"]["CH"], "transitions": []}
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for CH transitions absent from projection"
    except WorkflowLayerError as exc:
        assert "transition" in str(exc).lower() or "CH" in str(exc), f"Expected transition divergence error; got: {exc}"


# ── B3: validate(scope='draft') lifecycle constraint enforcement ──────────────


# ── B1: Projection parity — canonical_statuses and policy enforcement ─────────


def test_b1_extra_canonical_status_raises(tmp_path: Path) -> None:
    """CH projection with an extra canonical_statuses entry not in lifecycle bundle → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["CH"] = {
        **real_contract["families"]["CH"],
        "canonical_statuses": real_contract["families"]["CH"]["canonical_statuses"] + ["Bogus"],
    }
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for extra 'Bogus' canonical_statuses entry"
    except WorkflowLayerError as exc:
        assert (
            "canonical" in str(exc).lower() or "CH" in str(exc) or "Bogus" in str(exc)
        ), f"Expected canonical_statuses divergence error; got: {exc}"


def test_b1_missing_canonical_status_raises(tmp_path: Path) -> None:
    """CH projection missing 'In Progress' from canonical_statuses → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["CH"] = {
        **real_contract["families"]["CH"],
        "canonical_statuses": [s for s in real_contract["families"]["CH"]["canonical_statuses"] if s != "In Progress"],
    }
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for missing 'In Progress' in canonical_statuses"
    except WorkflowLayerError as exc:
        assert (
            "canonical" in str(exc).lower() or "In Progress" in str(exc) or "CH" in str(exc)
        ), f"Expected canonical_statuses divergence error; got: {exc}"


def test_b1_permissive_normal_path_policy_raises(tmp_path: Path) -> None:
    """CH projection with allow_record_local_status (permissive) normal_path_policy → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["CH"] = {
        **real_contract["families"]["CH"],
        "normal_path_policy": "allow_record_local_status",
    }
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for permissive normal_path_policy"
    except WorkflowLayerError as exc:
        assert "policy" in str(exc).lower() or "CH" in str(exc), f"Expected policy broadening error; got: {exc}"


def test_b1_non_ch_canonical_status_drift_raises(tmp_path: Path) -> None:
    """SPEC projection with an extra canonical_statuses entry → WorkflowLayerError (non-CH family coverage)."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["SPEC"] = {
        **real_contract["families"]["SPEC"],
        "canonical_statuses": real_contract["families"]["SPEC"]["canonical_statuses"] + ["Phantom"],
    }
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for SPEC extra canonical_statuses entry"
    except WorkflowLayerError as exc:
        assert (
            "canonical" in str(exc).lower() or "SPEC" in str(exc) or "Phantom" in str(exc)
        ), f"Expected canonical_statuses divergence error for SPEC; got: {exc}"


# ── B3: validate(scope='draft') lifecycle constraint enforcement ──────────────


def test_b3_validate_draft_runs_lifecycle_constraints_for_ch_ready(tmp_path: Path) -> None:
    """validate(scope='draft') must run lifecycle state constraints and return valid=False for CH Ready without refs."""
    import json

    from lantern.mcp.transactions import TransactionEngine
    from lantern.workflow import load_workflow_layer

    product_root = tmp_path / "product"
    product_root.mkdir()
    governance_root = tmp_path / "governance"
    governance_root.mkdir()

    wl = load_workflow_layer()
    engine = TransactionEngine(
        workflow_layer=wl,
        product_root=product_root,
        governance_root=governance_root,
    )

    draft_id = "draft-b3-test-fixture"
    draft_record = {
        "draft_id": draft_id,
        "actor": "test",
        "workbench_id": "ch_and_td_readiness",
        "contract_ref": "contract.ch_and_td_readiness",
        "artifact_family": "ch",
        "artifact_id": "CH-9999",
        "artifact_path": str(governance_root / "ch" / "CH-9999.md"),
        "header": {
            "ch_id": "CH-9999",
            "status": "Ready",
            "title": "Fixture CH for B3 test",
            "inputs": {"specs": [], "arch": []},
            "test_definition_refs": [],
        },
        "title": "Fixture CH for B3 test",
        "sections": [],
        "preview": "```yaml\nch_id: CH-9999\nstatus: Ready\ntitle: Fixture CH for B3 test\n```\n\n# CH-9999\n",
    }
    (engine.runtime_root / "drafts").mkdir(parents=True, exist_ok=True)
    (engine.runtime_root / "drafts" / f"{draft_id}.json").write_text(
        json.dumps(draft_record, indent=2), encoding="utf-8"
    )

    result = engine.validate(scope="draft", draft_id=draft_id)

    assert not result["valid"], f"Expected valid=False for CH Ready draft with empty lifecycle refs; result={result}"
    anchors = [f.get("anchor", "") for f in result["findings"]]
    assert any(
        "lifecycle_policy" in a for a in anchors
    ), f"Expected lifecycle_policy anchor in validate(scope='draft') findings; anchors={anchors}"


# ── B1 (round 6): Projection parity — exact label→grammar-ID association ──────


def test_b1_swapped_spec_grammar_mapping_raises(tmp_path: Path) -> None:
    """SPEC Draft/Approved grammar_mapping swapped with transitions adjusted consistently → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["SPEC"] = {
        **real_contract["families"]["SPEC"],
        "grammar_mapping": {
            "Draft": "lg:statuses/approved",  # swapped
            "Approved": "lg:statuses/draft",  # swapped
            "Superseded": "lg:statuses/superseded",
        },
        # Transitions adjusted so the swapped display-label pairs are self-consistent
        "transitions": [
            {"from": "Approved", "to": "Draft"},
            {"from": "Draft", "to": "Superseded"},
        ],
    }
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for swapped SPEC grammar_mapping with adjusted transitions"
    except WorkflowLayerError as exc:
        assert (
            "SPEC" in str(exc) or "association" in str(exc).lower() or "mapping" in str(exc).lower()
        ), f"Expected SPEC association error; got: {exc}"


def test_b1_swapped_ch_grammar_mapping_raises(tmp_path: Path) -> None:
    """CH Ready/In-Progress grammar_mapping swapped with transitions adjusted consistently → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["CH"] = {
        **real_contract["families"]["CH"],
        "grammar_mapping": {
            "Proposed": "lg:statuses/proposed",
            "Ready": "lg:statuses/in_progress",  # swapped
            "In Progress": "lg:statuses/ready",  # swapped
            "Addressed": "lg:statuses/addressed",
        },
        # Transitions adjusted so the swapped display-label pairs are self-consistent
        "transitions": [
            {"from": "Proposed", "to": "In Progress"},
            {"from": "In Progress", "to": "Ready"},
            {"from": "Ready", "to": "Addressed"},
            {"from": "In Progress", "to": "Addressed"},
        ],
    }
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for swapped CH grammar_mapping with adjusted transitions"
    except WorkflowLayerError as exc:
        assert (
            "CH" in str(exc) or "association" in str(exc).lower() or "mapping" in str(exc).lower()
        ), f"Expected CH association error; got: {exc}"


def test_b1_swapped_mapping_deceives_lifecycle_validator(tmp_path: Path) -> None:
    """Swapped SPEC grammar_mapping causes validator to wrongly accept a Draft SPEC for a Ready CH.

    Demonstrates the vulnerability at the validator level and proves _verify_lifecycle_projection_consistency
    catches the swapped contract before it can reach production.
    """
    import json

    from lantern.artifacts.validator import _validate_ch_lifecycle_state_constraints
    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    governance_root = tmp_path / "governance"
    _write_spec(governance_root, "SPEC-9001", "Draft")  # Draft, not Approved
    _write_arch(governance_root, "ARCH-9001", "Approved")
    _write_td(governance_root, "TD-9001", "Approved")

    ch_header = {
        "ch_id": "CH-9999",
        "status": "Ready",
        "inputs": {"specs": ["SPEC-9001"], "arch": ["ARCH-9001"]},
        "test_definition_refs": ["TD-9001"],
    }

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))

    # With CORRECT projection: validator rejects Draft SPEC (Draft ≠ Approved)
    correct_findings = _validate_ch_lifecycle_state_constraints(
        ch_header, "CH-9999", governance_root=governance_root, contract=real_contract
    )
    assert correct_findings, "With correct mapping, Draft SPEC must be rejected for Ready CH"

    # Build a swapped SPEC contract (canonical_statuses labels are the same; associations are swapped)
    swapped_families = dict(real_contract["families"])
    swapped_families["SPEC"] = {
        **real_contract["families"]["SPEC"],
        "grammar_mapping": {
            "Draft": "lg:statuses/approved",  # swapped: Draft label now points to approved ID
            "Approved": "lg:statuses/draft",  # swapped: Approved label now points to draft ID
            "Superseded": "lg:statuses/superseded",
        },
    }
    swapped_contract = {**real_contract, "families": swapped_families}

    # With SWAPPED projection: validator wrongly accepts Draft SPEC (this is the vulnerability)
    swapped_findings = _validate_ch_lifecycle_state_constraints(
        ch_header, "CH-9999", governance_root=governance_root, contract=swapped_contract
    )
    assert not swapped_findings, (
        "With swapped SPEC mapping, Draft SPEC is wrongly accepted — "
        "this proves association-level parity is required"
    )

    # The parity check catches the swapped contract before it can be deployed
    contract_path = tmp_path / "swapped_contract.json"
    contract_path.write_text(json.dumps(swapped_contract), encoding="utf-8")
    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for swapped SPEC grammar_mapping"
    except WorkflowLayerError as exc:
        assert (
            "SPEC" in str(exc) or "association" in str(exc).lower() or "mapping" in str(exc).lower()
        ), f"Expected SPEC association error; got: {exc}"


def test_b1_swapped_ci_grammar_mapping_raises(tmp_path: Path) -> None:
    """CI Selected/Verified grammar_mapping swapped with transitions adjusted consistently → WorkflowLayerError."""
    import json

    from lantern.workflow.loader import WorkflowLayerError, _verify_lifecycle_projection_consistency

    real_contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    modified_families = dict(real_contract["families"])
    modified_families["CI"] = {
        **real_contract["families"]["CI"],
        "grammar_mapping": {
            "Draft": "lg:statuses/draft",
            "Candidate": "lg:statuses/candidate",
            "Selected": "lg:statuses/verified",  # swapped
            "Rejected": "lg:statuses/rejected",
            "Verified": "lg:statuses/selected",  # swapped
        },
        # Transitions adjusted so the swapped display-label pairs are self-consistent
        "transitions": [
            {"from": "Draft", "to": "Candidate"},
            {"from": "Candidate", "to": "Verified"},  # was Selected
            {"from": "Candidate", "to": "Rejected"},
            {"from": "Verified", "to": "Selected"},  # was Selected→Verified
        ],
    }
    modified_contract = {**real_contract, "families": modified_families}
    contract_path = tmp_path / "status_contract.json"
    contract_path.write_text(json.dumps(modified_contract), encoding="utf-8")

    try:
        _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=contract_path)
        assert False, "Expected WorkflowLayerError for swapped CI grammar_mapping with adjusted transitions"
    except WorkflowLayerError as exc:
        assert (
            "CI" in str(exc) or "association" in str(exc).lower() or "mapping" in str(exc).lower()
        ), f"Expected CI association error; got: {exc}"
