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

"""TD-0021 coverage for the CH-0021 operational CLI, bootstrap, and discovery surfaces."""

from __future__ import annotations

import argparse
import builtins
import io
import importlib
import json
from pathlib import Path

import pytest
import yaml

from lantern.bootstrap.manager import (
    BootstrapOperation,
    BootstrapPlan,
    _MANAGED_BEGIN,
    _MANAGED_END,
    _merge_managed_block,
    apply_bootstrap_plan,
    plan_bootstrap,
)
from lantern.cli.context import (
    ContextResolutionError,
    OperationalContext,
    resolve_operational_context,
)
from lantern.cli.doctor import gather_doctor_report
from lantern.cli.main import _render_human_payload, build_parser, main, run_cli
from lantern.discovery.registry import (
    _extract_h1,
    _resource_title,
    build_discovery_registry,
    diff_index_inventory,
    list_records,
    show_record,
)
from lantern.workflow.loader import WorkflowLayerError
from lantern.workflow.merger import ConfigurationLoadError

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
CLI_MAIN_MODULE = importlib.import_module("lantern.cli.main")
DISCOVERY_FIXTURE_CH_ID = "CH-0021"
DISCOVERY_FIXTURE_CI_ID = "CI-9000-fixture"
DISCOVERY_FIXTURE_CI_PATH = f"ci/{DISCOVERY_FIXTURE_CI_ID}.md"


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_governed_artifact(
    path: Path,
    *,
    header: dict[str, object],
    artifact_id: str,
    title: str,
    sections: tuple[tuple[str, str], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        "```yaml",
        yaml.safe_dump(header, sort_keys=False).rstrip(),
        "```",
        "",
        f"# {artifact_id} — {title}",
    ]
    for heading, body in sections:
        blocks.extend(["", f"## {heading}", "", body])
    path.write_text("\n".join(blocks).rstrip() + "\n", encoding="utf-8")


def _make_discovery_governance_root(root: Path) -> Path:
    _write_governed_artifact(
        root / "ch" / f"{DISCOVERY_FIXTURE_CH_ID}.md",
        header={
            "ch_id": DISCOVERY_FIXTURE_CH_ID,
            "status": "Ready",
            "title": "Operational CLI fixture",
            "depends_on_ch": "CH-0006",
            "allowed_change_surface": ["lantern/lantern/cli/", "lantern/tests/"],
            "gates": "GT-110, GT-115, GT-120, GT-130",
        },
        artifact_id=DISCOVERY_FIXTURE_CH_ID,
        title="Operational CLI fixture",
        sections=(("Technical approach", "Synthetic governed discovery fixture."),),
    )
    _write_governed_artifact(
        root / "ci" / f"{DISCOVERY_FIXTURE_CI_ID}.md",
        header={
            "ch_id": DISCOVERY_FIXTURE_CH_ID,
            "ci_id": DISCOVERY_FIXTURE_CI_ID,
            "status": "Candidate",
            "title": "Synthetic CI fixture",
            "design_baseline_ref": "DB-9000",
            "test_definition_refs": ["TD-9000"],
            "allowed_change_surface": ["src/allowed.txt"],
        },
        artifact_id=DISCOVERY_FIXTURE_CI_ID,
        title="Synthetic CI fixture",
        sections=(("Intent", "Synthetic governed discovery fixture."),),
    )
    _write_yaml(
        root / "workflow" / "artifact_status_contract.yaml",
        {
            "families": [
                {
                    "family": "CH",
                    "canonical_statuses": ["Proposed", "Ready", "Addressed"],
                    "grammar_mapping": {},
                },
                {
                    "family": "CI",
                    "canonical_statuses": ["Draft", "Candidate", "Selected", "Verified"],
                    "grammar_mapping": {},
                },
            ]
        },
    )
    _write_yaml(
        root / "workflow" / "gate_post_conditions.yaml",
        {
            "gates": [
                {"gate": "GT-120", "summary": "selection"},
                {"gate": "GT-130", "summary": "verification"},
            ]
        },
    )
    (root / "INDEX.md").write_text(
        "# Governance Index\n\n"
        "## Change Intents\n\n"
        f"- [{DISCOVERY_FIXTURE_CH_ID}](ch/{DISCOVERY_FIXTURE_CH_ID}.md) — Status: Ready\n\n"
        "## Change Increments\n\n"
        f"- [{DISCOVERY_FIXTURE_CI_ID}]({DISCOVERY_FIXTURE_CI_PATH}) — Status: Candidate\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture(scope="module")
def discovery_governance_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("cli-discovery-governance")
    return _make_discovery_governance_root(root)


def _subcommand_names() -> set[str]:
    parser = build_parser()
    for action in parser._actions:
        if getattr(action, "dest", None) == "command":
            return set(action.choices)
    raise AssertionError("command subparser group not found")


def _make_valid_config_folder(
    root: Path,
    *,
    product_root: Path,
    declared_posture: str = "full_governed_surface",
    guide_refs: tuple[str, ...] = (),
) -> Path:
    cfg = root / "workflow" / "configuration"
    for sub in ("instructions", "workbenches", "guides"):
        (cfg / sub).mkdir(parents=True, exist_ok=True)
    (cfg / "instructions" / "onboarding.md").write_text("# onboarding\n", encoding="utf-8")
    (cfg / "guides" / "override.md").write_text("# override guide\n", encoding="utf-8")
    (cfg / "workbenches" / "ch_and_td_readiness.yaml").write_text(
        yaml.safe_dump(
            {
                "workbench_id": "ch_and_td_readiness",
                "instruction_resource": "instructions/onboarding.md",
                "authoritative_guides": ["guides/override.md"],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    main_yaml = {
        "configuration_version": "1",
        "declared_posture": declared_posture,
        "authoritative_refs": {"product_root": str(product_root.resolve())},
        "workflow_modes": [
            {
                "mode_id": "feature_delivery",
                "entry_workbench": "ch_and_td_readiness",
                "guide_refs": list(guide_refs),
            }
        ],
        "workbench_overrides": [
            {
                "workbench_id": "ch_and_td_readiness",
                "file": "workbenches/ch_and_td_readiness.yaml",
            }
        ],
    }
    (cfg / "main.yaml").write_text(yaml.safe_dump(main_yaml, sort_keys=False), encoding="utf-8")
    return cfg


def _bootstrapped_workspace(tmp_path: Path) -> tuple[Path, Path]:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    (product_root / "AGENTS.md").write_text(
        "Local notes above\n\n<!-- LANTERN-MANAGED:BEGIN -->\nold block\n<!-- LANTERN-MANAGED:END -->\n\nLocal notes below\n",
        encoding="utf-8",
    )
    (governance_root / "AGENTS.md").write_text(
        "Gov notes above\n\n<!-- LANTERN-MANAGED:BEGIN -->\nstale block\n<!-- LANTERN-MANAGED:END -->\n",
        encoding="utf-8",
    )
    preview = plan_bootstrap(product_root=product_root, governance_root=governance_root)
    assert preview.operations, "bootstrap preview must announce managed operations"
    apply_bootstrap_plan(preview)
    return product_root, governance_root


def test_td0021_c01_cli_exposes_exactly_five_public_command_families() -> None:
    assert _subcommand_names() == {"serve", "doctor", "bootstrap-product", "list", "show"}


def test_td0021_c02_operational_context_requires_governance_root_and_uses_configured_product_root(
    tmp_path: Path,
) -> None:
    with pytest.raises(ContextResolutionError, match="governance root"):
        resolve_operational_context(governance_root=None)

    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    _make_valid_config_folder(governance_root, product_root=product_root)

    context = resolve_operational_context(governance_root=governance_root)

    assert context.governance_root == governance_root.resolve()
    assert context.product_root == product_root.resolve()
    assert context.product_root_source == "governed_configuration"


def test_td0021_c03_operational_context_blocks_cli_and_configuration_product_root_mismatch(
    tmp_path: Path,
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    conflicting_root = tmp_path / "other-product"
    product_root.mkdir()
    governance_root.mkdir()
    conflicting_root.mkdir()
    _make_valid_config_folder(governance_root, product_root=product_root)

    with pytest.raises(ContextResolutionError) as exc:
        resolve_operational_context(
            governance_root=governance_root,
            supplied_product_root=conflicting_root,
        )

    message = str(exc.value)
    assert str(product_root.resolve()) in message
    assert str(conflicting_root.resolve()) in message


def test_td0021_c04_doctor_reports_required_categories_and_json_output(
    tmp_path: Path,
) -> None:
    product_root, governance_root = _bootstrapped_workspace(tmp_path)

    report = gather_doctor_report(product_root=product_root, governance_root=governance_root)

    assert report["kind"] == "doctor_report"
    assert set(report["categories"]) == {
        "runtime_availability",
        "grammar_compatibility",
        "workspace_validity",
        "workflow_configuration",
        "bootstrap_posture",
        "managed_file_posture",
        "discovery_availability",
    }
    assert {finding["classification"] for finding in report["findings"]} <= {"blocker", "advisory"}

    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "doctor",
            "--governance-root",
            str(governance_root),
            "--product-root",
            str(product_root),
            "--json",
        ],
        stdout=stdout,
    )
    assert exit_code == 0
    rendered = json.loads(stdout.getvalue())
    assert rendered["categories"] == report["categories"]
    assert rendered["findings"] == report["findings"]


def test_td0021_c05_bootstrap_is_preview_first_idempotent_and_merges_only_managed_blocks(
    tmp_path: Path,
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    (product_root / "AGENTS.md").write_text(
        "keep me\n\n<!-- LANTERN-MANAGED:BEGIN -->\nold\n<!-- LANTERN-MANAGED:END -->\n\nalso keep me\n",
        encoding="utf-8",
    )
    (governance_root / "AGENTS.md").write_text(
        "governance note\n\n<!-- LANTERN-MANAGED:BEGIN -->\nold\n<!-- LANTERN-MANAGED:END -->\n",
        encoding="utf-8",
    )

    preview = plan_bootstrap(product_root=product_root, governance_root=governance_root)

    assert preview.preview_only is True
    assert not (governance_root / "README.md").exists()
    assert not (product_root / "README.md").exists()

    apply_bootstrap_plan(preview)
    second_preview = plan_bootstrap(product_root=product_root, governance_root=governance_root)

    product_agents = (product_root / "AGENTS.md").read_text(encoding="utf-8")
    governance_agents = (governance_root / "AGENTS.md").read_text(encoding="utf-8")
    assert "keep me" in product_agents
    assert "also keep me" in product_agents
    assert "governance note" in governance_agents
    assert (governance_root / "README.md").exists()
    assert not (product_root / "README.md").exists()
    assert (governance_root / "workflow" / "configuration" / "main.yaml").exists()
    assert not (product_root / "workflow" / "configuration" / "main.yaml").exists()
    assert not second_preview.operations


def test_bootstrap_helpers_cover_absent_plaintext_blank_and_invalid_actions(tmp_path: Path) -> None:
    managed_block = f"{_MANAGED_BEGIN}\nmanaged\n{_MANAGED_END}\n"

    assert _merge_managed_block(tmp_path / "missing.md", managed_block) == managed_block

    plain_path = tmp_path / "plain.md"
    plain_path.write_text("plain notes\n", encoding="utf-8")
    merged_plain = _merge_managed_block(plain_path, managed_block)
    assert merged_plain == f"{managed_block.rstrip()}\n\nplain notes\n"

    blank_path = tmp_path / "blank.md"
    blank_path.write_text("\n", encoding="utf-8")
    assert _merge_managed_block(blank_path, managed_block) == managed_block

    managed_only_path = tmp_path / "managed-only.md"
    managed_only_path.write_text(
        f"{_MANAGED_BEGIN}\nold\n{_MANAGED_END}\nlocal trailing text\n",
        encoding="utf-8",
    )
    merged_without_markers = _merge_managed_block(managed_only_path, "replacement block")
    assert merged_without_markers == "replacement block\n\nlocal trailing text\n"

    invalid_plan = BootstrapPlan(
        product_root=tmp_path,
        governance_root=tmp_path,
        preview_only=True,
        operations=(BootstrapOperation(path=tmp_path / "noop", action="explode"),),
    )
    with pytest.raises(ValueError, match="unsupported bootstrap action"):
        apply_bootstrap_plan(invalid_plan)


def test_td0021_c06_discovery_registry_covers_artifacts_and_core_vocabularies(
    discovery_governance_root: Path,
) -> None:
    registry = build_discovery_registry(
        product_root=PRODUCT_ROOT,
        governance_root=discovery_governance_root,
    )

    entity_kinds = {record["entity_kind"] for record in registry["records"]}
    assert {"artifact", "status", "gate", "mode", "workbench", "guide", "template"} <= entity_kinds
    assert any(record["token"] == DISCOVERY_FIXTURE_CH_ID for record in registry["records"])
    assert any(record["token"] == "GT-120" for record in registry["records"])
    assert any(record["token"] == "Ready" for record in registry["records"])


def test_operational_context_supports_setup_flows_and_rejects_missing_paths(
    tmp_path: Path,
) -> None:
    governance_root = tmp_path / "governance"
    product_root = tmp_path / "product"
    governance_root.mkdir()
    product_root.mkdir()

    context = resolve_operational_context(
        governance_root=governance_root,
        supplied_product_root=product_root,
        allow_supplied_product_root=True,
    )

    assert context.product_root == product_root.resolve()
    assert context.product_root_source == "command_line"
    assert context.configuration_path is None

    with pytest.raises(ContextResolutionError, match="governance root not found"):
        resolve_operational_context(governance_root=tmp_path / "missing-governance")

    with pytest.raises(ContextResolutionError, match="product root not found"):
        resolve_operational_context(
            governance_root=governance_root,
            supplied_product_root=tmp_path / "missing-product",
            allow_supplied_product_root=True,
        )

    with pytest.raises(ContextResolutionError, match="run bootstrap-product or supply --product-root"):
        resolve_operational_context(governance_root=governance_root)


def test_operational_context_rejects_invalid_configuration_documents(tmp_path: Path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    config_path = governance_root / "workflow" / "configuration" / "main.yaml"
    config_path.parent.mkdir(parents=True)

    config_path.write_text("authoritative_refs: [\n", encoding="utf-8")
    with pytest.raises(ContextResolutionError, match="invalid governed configuration"):
        resolve_operational_context(governance_root=governance_root)

    config_path.write_text("- not-a-mapping\n", encoding="utf-8")
    with pytest.raises(ContextResolutionError, match="expected a mapping document"):
        resolve_operational_context(governance_root=governance_root)

    config_path.write_text("authoritative_refs: []\n", encoding="utf-8")
    with pytest.raises(ContextResolutionError, match="authoritative_refs must be a mapping"):
        resolve_operational_context(governance_root=governance_root)

    config_path.write_text("", encoding="utf-8")
    with pytest.raises(ContextResolutionError, match="run bootstrap-product or supply --product-root"):
        resolve_operational_context(governance_root=governance_root)

    config_path.write_text("configuration_version: '1'\n", encoding="utf-8")
    with pytest.raises(ContextResolutionError, match="run bootstrap-product or supply --product-root"):
        resolve_operational_context(governance_root=governance_root)

    config_path.write_text("authoritative_refs: {}\n", encoding="utf-8")
    with pytest.raises(ContextResolutionError, match="run bootstrap-product or supply --product-root"):
        resolve_operational_context(governance_root=governance_root)


def test_td0021_c07_list_filters_are_bounded_and_deterministic(
    discovery_governance_root: Path,
) -> None:
    registry = build_discovery_registry(
        product_root=PRODUCT_ROOT,
        governance_root=discovery_governance_root,
    )

    first = list_records(registry, family="CH", status="Ready", heading="Technical approach")
    second = list_records(registry, family="CH", status="Ready", heading="Technical approach")
    assert first == second
    assert any(item["token"] == DISCOVERY_FIXTURE_CH_ID for item in first)

    mode_rows = list_records(registry, mode="ci_authoring")
    workbench_rows = list_records(registry, workbench="ci_authoring")
    guide_rows = list_records(
        registry,
        logical_ref="resource.authoritative_guide.ci_authoring_authoritative_guides_ci_authoring",
    )
    title_rows = list_records(registry, title="Operational CLI")
    gate_rows = list_records(registry, gate="GT-120")

    assert mode_rows
    assert workbench_rows
    assert guide_rows
    assert title_rows
    assert gate_rows

    with pytest.raises(ValueError, match="unsupported"):
        list_records(registry, body="graph traversal")


def test_td0021_c08_show_uses_exact_token_resolution_and_explicit_ambiguity_guidance(
    discovery_governance_root: Path,
) -> None:
    registry = build_discovery_registry(
        product_root=PRODUCT_ROOT,
        governance_root=discovery_governance_root,
    )

    assert show_record(registry, DISCOVERY_FIXTURE_CH_ID)["entity_kind"] == "artifact"
    assert show_record(registry, "GT-120")["entity_kind"] == "gate"
    assert show_record(registry, "Ready")["entity_kind"] == "status"

    ambiguous = show_record(registry, "ci_authoring")
    assert ambiguous["entity_kind"] == "ambiguity"
    assert {candidate["entity_kind"] for candidate in ambiguous["candidates"]} == {"mode", "workbench"}


def test_td0021_c09_show_artifact_exposes_local_fields_and_direct_declared_refs_only(
    discovery_governance_root: Path,
) -> None:
    registry = build_discovery_registry(
        product_root=PRODUCT_ROOT,
        governance_root=discovery_governance_root,
    )

    payload = show_record(registry, DISCOVERY_FIXTURE_CH_ID)

    assert payload["entity_kind"] == "artifact"
    assert payload["token"] == DISCOVERY_FIXTURE_CH_ID
    assert payload["family"] == "CH"
    assert payload["status"] == "Ready"
    assert "allowed_change_surface" in payload["fields"]
    assert "direct_refs" in payload
    assert "CH-0006" in payload["direct_refs"]
    assert "expanded_neighbors" not in payload
    assert "transitive_refs" not in payload


def test_td0021_c10_index_inventory_diff_detects_missing_and_stale_entries(
    tmp_path: Path,
    discovery_governance_root: Path,
) -> None:
    governance_copy = tmp_path / "governance"
    for source in discovery_governance_root.rglob("*"):
        if source.is_dir():
            continue
        target = governance_copy / source.relative_to(discovery_governance_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    index_path = governance_copy / "INDEX.md"
    original = index_path.read_text(encoding="utf-8")
    damaged = original.replace(
        DISCOVERY_FIXTURE_CI_PATH,
        "ci/CI-9999-missing.md",
        1,
    )
    damaged = damaged.replace(f"[{DISCOVERY_FIXTURE_CH_ID}](ch/{DISCOVERY_FIXTURE_CH_ID}.md) — Status: Ready\n", "", 1)
    index_path.write_text(damaged, encoding="utf-8")

    diff = diff_index_inventory(governance_copy)

    assert f"ch/{DISCOVERY_FIXTURE_CH_ID}.md" in diff["missing"]
    assert DISCOVERY_FIXTURE_CI_PATH in diff["missing"]
    assert "ci/CI-9999-missing.md" in diff["stale"]


def test_td0021_c11_discovery_surfaces_mode_workbench_and_logical_ref_debug_state(
    tmp_path: Path,
) -> None:
    governance_root = tmp_path / "governance"
    governance_root.mkdir()
    _make_valid_config_folder(
        governance_root,
        product_root=PRODUCT_ROOT,
        guide_refs=("resource.authoritative_guide.ci_authoring_authoritative_guides_ci_authoring",),
    )

    registry = build_discovery_registry(
        product_root=PRODUCT_ROOT,
        governance_root=governance_root,
    )

    mode_payload = show_record(registry, "feature_delivery", entity_kind="mode")
    workbench_payload = show_record(registry, "ch_and_td_readiness", entity_kind="workbench")

    assert mode_payload["entry_workbench"] == "ch_and_td_readiness"
    assert "resource.authoritative_guide.ci_authoring_authoritative_guides_ci_authoring" in mode_payload["guide_refs"]
    assert workbench_payload["instruction_resource"].endswith("instructions/onboarding.md")
    assert "guides/override.md" in workbench_payload["authoritative_guides"]


def test_td0021_c12_discovery_reuses_doctor_classifications_without_inventing_new_ones(
    tmp_path: Path,
) -> None:
    product_root, governance_root = _bootstrapped_workspace(tmp_path)
    report = gather_doctor_report(product_root=product_root, governance_root=governance_root)
    registry = build_discovery_registry(product_root=product_root, governance_root=governance_root)

    payload = show_record(registry, "GT-120", doctor_report=report)

    assert {finding["classification"] for finding in payload["doctor_findings"]} <= {"blocker", "advisory"}
    assert payload["doctor_findings"] == report["findings"]


def test_td0021_c13_cli_rejects_authoring_or_search_commands() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["search"])

    with pytest.raises(SystemExit):
        parser.parse_args(["draft"])


def test_doctor_reports_degraded_runtime_and_blocked_discovery_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    real_import = builtins.__import__

    def fake_import(name: str, globals=None, locals=None, fromlist=(), level: int = 0):
        if name in {"mcp.server.fastmcp", "lantern_grammar"}:
            raise ImportError(f"missing dependency: {name}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(
        "lantern.cli.doctor.validate_workspace_readiness",
        lambda **_: [{"path": "workspace.product", "message": "workspace mismatch"}],
    )
    monkeypatch.setattr(
        "lantern.cli.doctor.load_workflow_layer",
        lambda: (_ for _ in ()).throw(WorkflowLayerError("stale generated artifacts")),
    )
    monkeypatch.setattr(
        "lantern.cli.doctor.build_discovery_registry",
        lambda **_: (_ for _ in ()).throw(RuntimeError("registry exploded")),
    )

    report = gather_doctor_report(product_root=product_root, governance_root=governance_root)

    assert report["checks"]["runtime_availability"]["mcp_runtime"] == "degraded"
    assert report["checks"]["grammar_compatibility"]["status"] == "missing"
    assert report["checks"]["workspace_validity"]["status"] == "blocked"
    assert report["checks"]["workflow_configuration"]["status"] == "absent"
    assert report["checks"]["bootstrap_posture"]["status"] == "not_bootstrapped"
    assert report["checks"]["managed_file_posture"]["status"] == "partial"
    assert report["checks"]["discovery_availability"] == {
        "status": "blocked",
        "record_count": 0,
        "strict_status": "stale_generated_artifacts",
    }
    assert {finding["classification"] for finding in report["findings"]} == {"advisory", "blocker"}
    assert any(finding["subject"] == "mcp_runtime" for finding in report["findings"])
    assert any(finding["subject"] == "lantern_grammar" for finding in report["findings"])
    assert any(finding["subject"] == "workflow.configuration" for finding in report["findings"])
    assert any(finding["subject"] == "discovery_registry" for finding in report["findings"])


def test_doctor_reports_invalid_configuration_bootstrap_drift_and_invalid_bootstrap_shapes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_root = tmp_path / "product"
    drifted_root = tmp_path / "drifted-product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    drifted_root.mkdir()
    governance_root.mkdir()
    config_root = governance_root / "workflow" / "configuration"
    config_root.mkdir(parents=True)
    config_path = config_root / "main.yaml"

    class BrokenLoader:
        def load_and_validate(self, path: Path) -> object:
            raise ConfigurationLoadError(f"invalid configuration: {path}")

    monkeypatch.setattr("lantern.cli.doctor.ConfigurationLoader", lambda: BrokenLoader())
    monkeypatch.setattr("lantern.cli.doctor.validate_workspace_readiness", lambda **_: [])
    monkeypatch.setattr("lantern.cli.doctor.load_workflow_layer", lambda: object())
    monkeypatch.setattr("lantern.cli.doctor.build_discovery_registry", lambda **_: {"records": [{"token": "ok"}]})

    config_path.write_text(
        yaml.safe_dump(
            {
                "configuration_version": "1",
                "authoritative_refs": {"product_root": str(drifted_root.resolve())},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    drift_report = gather_doctor_report(product_root=product_root, governance_root=governance_root)
    assert drift_report["checks"]["workflow_configuration"]["status"] == "invalid"
    assert drift_report["checks"]["bootstrap_posture"]["status"] == "drifted"
    assert drift_report["checks"]["discovery_availability"] == {
        "status": "ok",
        "record_count": 1,
        "strict_status": "ok",
    }
    assert any(finding["subject"] == "authoritative_refs.product_root" for finding in drift_report["findings"])

    config_path.write_text("- invalid\n", encoding="utf-8")
    invalid_root_report = gather_doctor_report(product_root=product_root, governance_root=governance_root)
    assert invalid_root_report["checks"]["bootstrap_posture"]["status"] == "invalid"
    assert any(
        finding["message"] == "bootstrap configuration root document must be a mapping"
        for finding in invalid_root_report["findings"]
    )

    config_path.write_text("authoritative_refs: []\n", encoding="utf-8")
    invalid_refs_report = gather_doctor_report(product_root=product_root, governance_root=governance_root)
    assert invalid_refs_report["checks"]["bootstrap_posture"]["status"] == "invalid"
    assert any(finding["subject"] == "authoritative_refs" for finding in invalid_refs_report["findings"])

    config_path.write_text("authoritative_refs: [\n", encoding="utf-8")
    invalid_yaml_report = gather_doctor_report(product_root=product_root, governance_root=governance_root)
    assert invalid_yaml_report["checks"]["bootstrap_posture"]["status"] == "invalid"
    assert any(
        "bootstrap configuration is invalid:" in finding["message"] for finding in invalid_yaml_report["findings"]
    )

    config_path.write_text("", encoding="utf-8")
    empty_payload_report = gather_doctor_report(product_root=product_root, governance_root=governance_root)
    assert empty_payload_report["checks"]["bootstrap_posture"]["status"] == "drifted"


def test_cli_dispatch_covers_serve_doctor_list_show_and_error_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    context = OperationalContext(
        governance_root=governance_root.resolve(),
        product_root=product_root.resolve(),
        product_root_source="command_line",
        configuration_path=None,
    )

    configured_paths: list[tuple[Path, Path]] = []
    server_runs: list[str] = []
    monkeypatch.setattr(CLI_MAIN_MODULE, "resolve_operational_context", lambda **_: context)
    monkeypatch.setattr(
        CLI_MAIN_MODULE,
        "configure_server_paths",
        lambda *, product_root, governance_root: configured_paths.append((product_root, governance_root)),
    )
    monkeypatch.setattr(CLI_MAIN_MODULE.mcp_server, "run", lambda: server_runs.append("ran"))
    monkeypatch.setattr(
        CLI_MAIN_MODULE,
        "gather_doctor_report",
        lambda **_: {
            "kind": "doctor_report",
            "categories": ["runtime_availability"],
            "checks": {"runtime_availability": {"status": "ok"}},
            "findings": [],
            "summary": {"blocker_count": 0, "advisory_count": 0},
        },
    )
    monkeypatch.setattr(CLI_MAIN_MODULE, "build_discovery_registry", lambda **_: {"records": []})
    monkeypatch.setattr(CLI_MAIN_MODULE, "list_records", lambda registry, **filters: [])
    monkeypatch.setattr(
        CLI_MAIN_MODULE,
        "show_record",
        lambda registry, token, entity_kind=None: {
            "entity_kind": entity_kind or "artifact",
            "token": token,
        },
    )

    serve_stdout = io.StringIO()
    assert (
        run_cli(
            ["serve", "--governance-root", str(governance_root), "--product-root", str(product_root)],
            stdout=serve_stdout,
            run_server=False,
        )
        == 0
    )
    assert "configured server roots" in serve_stdout.getvalue()

    assert (
        run_cli(
            ["serve", "--governance-root", str(governance_root), "--product-root", str(product_root)],
            run_server=True,
        )
        == 0
    )
    assert configured_paths == [
        (product_root.resolve(), governance_root.resolve()),
        (product_root.resolve(), governance_root.resolve()),
    ]
    assert server_runs == ["ran"]

    doctor_stdout = io.StringIO()
    assert run_cli(["doctor", "--governance-root", str(governance_root)], stdout=doctor_stdout) == 0
    assert doctor_stdout.getvalue() == "Doctor Report\n- runtime_availability: ok\n"

    list_stdout = io.StringIO()
    assert run_cli(["list", "--governance-root", str(governance_root)], stdout=list_stdout) == 0
    assert list_stdout.getvalue() == "(no records)\n"

    show_stdout = io.StringIO()
    assert run_cli(["show", "CH-0021", "--governance-root", str(governance_root)], stdout=show_stdout) == 0
    assert json.loads(show_stdout.getvalue()) == {"entity_kind": "artifact", "token": "CH-0021"}

    monkeypatch.setattr(
        CLI_MAIN_MODULE,
        "resolve_operational_context",
        lambda **_: (_ for _ in ()).throw(ContextResolutionError("context failed")),
    )
    error_stderr = io.StringIO()
    assert run_cli(["doctor", "--governance-root", str(governance_root)], stderr=error_stderr) == 2
    assert error_stderr.getvalue() == "context failed\n"


def test_cli_bootstrap_renders_human_and_json_payloads(tmp_path: Path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    preview_stdout = io.StringIO()
    assert (
        run_cli(
            [
                "bootstrap-product",
                "--governance-root",
                str(governance_root),
                "--product-root",
                str(product_root),
            ],
            stdout=preview_stdout,
        )
        == 0
    )
    assert preview_stdout.getvalue().startswith("Bootstrap Plan\n- ")

    applied_stdout = io.StringIO()
    assert (
        run_cli(
            [
                "bootstrap-product",
                "--governance-root",
                str(governance_root),
                "--product-root",
                str(product_root),
                "--apply",
                "--json",
            ],
            stdout=applied_stdout,
        )
        == 0
    )
    payload = json.loads(applied_stdout.getvalue())
    assert payload["kind"] == "bootstrap_plan"
    assert payload["applied"] is True


def test_cli_main_wrapper_and_fake_unsupported_command_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CLI_MAIN_MODULE, "run_cli", lambda argv=None: 7)
    assert main(["ignored"]) == 7

    class FakeParser:
        def __init__(self) -> None:
            self.message: str | None = None

        def parse_args(self, argv: list[str] | None) -> argparse.Namespace:
            return argparse.Namespace(command="unsupported")

        def error(self, message: str) -> None:
            self.message = message

    parser = FakeParser()
    monkeypatch.setattr(CLI_MAIN_MODULE, "build_parser", lambda: parser)
    assert run_cli([]) == 2
    assert parser.message == "unsupported command: unsupported"


def test_discovery_helpers_cover_private_fallbacks_and_missing_index_cases(
    tmp_path: Path,
    discovery_governance_root: Path,
) -> None:
    registry = build_discovery_registry(
        product_root=PRODUCT_ROOT,
        governance_root=discovery_governance_root,
    )

    exact = list_records(registry, id=DISCOVERY_FIXTURE_CH_ID)
    assert [record["token"] for record in exact] == [DISCOVERY_FIXTURE_CH_ID]
    assert list_records(registry, heading="heading-that-does-not-exist") == []

    assert _resource_title("plain text\n", "lantern/resources/guides/no-heading.md") == "no-heading"
    assert _extract_h1("## Only H2\n") is None

    governance_root = tmp_path / "governance"
    (governance_root / "ch").mkdir(parents=True)
    (governance_root / "ch" / "CH-9000.md").write_text("# CH-9000\n", encoding="utf-8")

    diff = diff_index_inventory(governance_root)
    assert diff == {
        "expected": ["ch/CH-9000.md"],
        "actual": [],
        "missing": ["ch/CH-9000.md"],
        "stale": [],
    }


def test_render_human_payload_covers_known_and_fallback_kinds() -> None:
    assert (
        _render_human_payload(
            {
                "kind": "doctor_report",
                "categories": ["runtime_availability"],
                "checks": {"runtime_availability": {"status": "degraded"}},
                "findings": [
                    {
                        "classification": "advisory",
                        "subject": "mcp_runtime",
                        "message": "missing",
                    }
                ],
            }
        )
        == "Doctor Report\n- runtime_availability: degraded\n- advisory: mcp_runtime — missing"
    )
    assert _render_human_payload({"kind": "discovery_list", "records": []}) == "(no records)"
    assert (
        _render_human_payload(
            {
                "kind": "bootstrap_plan",
                "operations": [{"action": "mkdir", "path": "/tmp/example"}],
            }
        )
        == "Bootstrap Plan\n- mkdir: /tmp/example"
    )
    assert json.loads(_render_human_payload({"entity_kind": "artifact", "token": "CH-0021"})) == {
        "entity_kind": "artifact",
        "token": "CH-0021",
    }
