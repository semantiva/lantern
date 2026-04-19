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

from __future__ import annotations

import io
import json
from pathlib import Path

import yaml

from lantern.cli.main import build_parser, run_cli
from lantern.discovery.registry import build_discovery_registry
from lantern.workflow.loader import DEFAULT_WORKFLOW_ID


PRODUCT_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_FIXTURE_CH_ID = "CH-0024"
DISCOVERY_FIXTURE_CI_ID = "CI-0024-fixture"
DISCOVERY_FIXTURE_CI_PATH = f"ci/{DISCOVERY_FIXTURE_CI_ID}.md"

REPO_LOCAL_TRIAGE_WORKBENCH = {
    "workbench_id": "repo_local_triage",
    "display_name": "Repo Local Triage",
    "lifecycle_placement": {"kind": "lifecycle-independent"},
    "artifacts_in_scope": ["IS"],
    "intent_classes": ["repo_local_triage"],
    "posture_constraints": ["repo_local_only"],
    "workflow_surface": {
        "allowed_transaction_kinds": ["inspect", "draft", "validate"],
        "draftable_artifact_families": ["IS"],
        "contract_refs": ["contract.issue_operations.v1"],
        "inspect_views": ["catalog", "issues"],
        "response_surface_bindings": [
            {
                "transaction_kind": "inspect",
                "response_envelope": "catalog",
                "allowed_resource_roles": [
                    "instruction_resource",
                    "authoritative_guides",
                    "artifact_templates",
                ],
            },
            {
                "transaction_kind": "inspect",
                "response_envelope": "issues",
                "allowed_resource_roles": [
                    "instruction_resource",
                    "authoritative_guides",
                    "artifact_templates",
                ],
            },
            {
                "transaction_kind": "draft",
                "response_envelope": "default",
                "allowed_resource_roles": [
                    "instruction_resource",
                    "authoritative_guides",
                    "administration_guides",
                ],
            },
            {
                "transaction_kind": "validate",
                "response_envelope": "default",
                "allowed_resource_roles": ["instruction_resource", "authoritative_guides"],
            },
        ],
    },
    "instruction_resource": "lantern/resources/instructions/issue_operations.md",
    "authoritative_guides": ["lantern/resources/guides/issue_operations.md"],
    "administration_guides": ["lantern/administration_procedures/ISSUE__INTAKE_TRIAGE_RESOLUTION_v0.2.0.md"],
    "entry_conditions": ["repo local issue intake"],
    "exit_conditions": ["repo local issue resolved"],
}


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_governed_artifact(
    path: Path,
    *,
    header: dict[str, object],
    artifact_id: str,
    title: str,
) -> None:
    body = [
        "```yaml",
        yaml.safe_dump(header, sort_keys=False).rstrip(),
        "```",
        "",
        f"# {artifact_id} — {title}",
        "",
        "## Purpose",
        "",
        "Synthetic CLI/discovery fixture.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def _make_governance_root(root: Path) -> Path:
    _write_governed_artifact(
        root / "ch" / f"{DISCOVERY_FIXTURE_CH_ID}.md",
        header={
            "ch_id": DISCOVERY_FIXTURE_CH_ID,
            "status": "Ready",
            "title": "CLI workflow selection fixture",
        },
        artifact_id=DISCOVERY_FIXTURE_CH_ID,
        title="CLI workflow selection fixture",
    )
    _write_governed_artifact(
        root / "ci" / f"{DISCOVERY_FIXTURE_CI_ID}.md",
        header={
            "ch_id": DISCOVERY_FIXTURE_CH_ID,
            "ci_id": DISCOVERY_FIXTURE_CI_ID,
            "status": "Candidate",
            "title": "Synthetic CI fixture",
            "design_baseline_ref": "DB-0024",
            "test_definition_refs": ["TD-0024"],
            "allowed_change_surface": ["lantern/lantern/workflow/", "lantern/tests/"],
        },
        artifact_id=DISCOVERY_FIXTURE_CI_ID,
        title="Synthetic CI fixture",
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


def _write_repo_local_catalog(
    governance_root: Path,
    *,
    workflow_id: str,
    workbench_id: str = "repo_local_triage",
    workflow_folder: Path | None = None,
    workbench_folder: Path | None = None,
) -> None:
    workflow_root = workflow_folder or governance_root / "workflow" / "definitions" / "workflows"
    workbench_root = workbench_folder or governance_root / "workflow" / "definitions" / "workbenches"
    workbench_payload = dict(REPO_LOCAL_TRIAGE_WORKBENCH)
    workbench_payload["workbench_id"] = workbench_id
    workbench_payload["display_name"] = workbench_id.replace("_", " ").title()
    _write_yaml(workbench_root / f"{workbench_id}.yaml", workbench_payload)
    _write_yaml(
        workflow_root / f"{workflow_id}.yaml",
        {
            "workflow_id": workflow_id,
            "display_name": workflow_id.replace("_", " ").title(),
            "runtime_surface_classification": "partial_governed_surface",
            "active_workbench_ids": [workbench_id],
        },
    )


def _subcommand_action(parser, name: str):
    for action in parser._actions:
        if getattr(action, "dest", None) == "command":
            return action.choices[name]
    raise AssertionError("command subparser group not found")


def test_td0024_c02_cli_preserves_five_commands_and_adds_workflow_flags() -> None:
    parser = build_parser()
    commands = {action.dest for action in parser._actions if getattr(action, "choices", None)}
    assert commands == {"command"}
    subcommands = {"serve", "doctor", "bootstrap-product", "list", "show"}
    assert set(_subcommand_action(parser, name).prog.split()[-1] for name in subcommands) == subcommands

    for name in ("serve", "doctor", "list", "show"):
        option_dests = {action.dest for action in _subcommand_action(parser, name)._actions}
        assert {"workflow_id", "workflow_folder", "workbench_folder"} <= option_dests

    bootstrap_option_dests = {action.dest for action in _subcommand_action(parser, "bootstrap-product")._actions}
    assert "workflow_id" not in bootstrap_option_dests


def test_td0024_c02_doctor_resolves_selected_workflow_by_id(tmp_path: Path) -> None:
    governance_root = _make_governance_root(tmp_path / "governance")
    _write_repo_local_catalog(governance_root, workflow_id="repo_local_triage_flow")

    stdout = io.StringIO()
    exit_code = run_cli(
        [
            "doctor",
            "--governance-root",
            str(governance_root),
            "--product-root",
            str(PRODUCT_ROOT),
            "--workflow-id",
            "repo_local_triage_flow",
            "--json",
        ],
        stdout=stdout,
    )

    assert exit_code == 0
    payload = json.loads(stdout.getvalue())
    assert payload["checks"]["workflow_configuration"]["selected_workflow_id"] == "repo_local_triage_flow"
    assert payload["checks"]["workflow_configuration"]["runtime_surface_classification"] == "partial_governed_surface"


def test_td0024_c03_list_and_show_use_selected_workflow(tmp_path: Path) -> None:
    governance_root = _make_governance_root(tmp_path / "governance")
    _write_repo_local_catalog(governance_root, workflow_id="repo_local_triage_flow")

    list_stdout = io.StringIO()
    exit_code = run_cli(
        [
            "list",
            "--governance-root",
            str(governance_root),
            "--product-root",
            str(PRODUCT_ROOT),
            "--workflow-id",
            "repo_local_triage_flow",
            "--mode",
            "repo_local_triage_flow",
            "--json",
        ],
        stdout=list_stdout,
    )
    assert exit_code == 0
    listed = json.loads(list_stdout.getvalue())
    listed_tokens = {record["token"] for record in listed["records"]}
    assert "repo_local_triage_flow" in listed_tokens
    assert "repo_local_triage" in listed_tokens

    show_stdout = io.StringIO()
    exit_code = run_cli(
        [
            "show",
            "repo_local_triage",
            "--governance-root",
            str(governance_root),
            "--product-root",
            str(PRODUCT_ROOT),
            "--workflow-id",
            "repo_local_triage_flow",
            "--entity-kind",
            "workbench",
            "--json",
        ],
        stdout=show_stdout,
    )
    assert exit_code == 0
    shown = json.loads(show_stdout.getvalue())
    assert shown["workbench_id"] == "repo_local_triage"
    assert shown["fields"]["selected"] is True


def test_td0024_c03_folder_overrides_only_replace_repo_local_catalog_roots(tmp_path: Path) -> None:
    governance_root = _make_governance_root(tmp_path / "governance")
    alt_workflow_root = governance_root / "alt" / "workflows"
    alt_workbench_root = governance_root / "alt" / "workbenches"
    _write_repo_local_catalog(
        governance_root,
        workflow_id="override_repo_local_flow",
        workbench_id="override_repo_local_triage",
        workflow_folder=alt_workflow_root,
        workbench_folder=alt_workbench_root,
    )

    registry = build_discovery_registry(
        product_root=PRODUCT_ROOT,
        governance_root=governance_root,
        workflow_id="override_repo_local_flow",
        workflow_folder=alt_workflow_root,
        workbench_folder=alt_workbench_root,
    )

    mode_tokens = {record["token"] for record in registry["records"] if record["entity_kind"] == "mode"}
    workbench_tokens = {record["token"] for record in registry["records"] if record["entity_kind"] == "workbench"}
    assert DEFAULT_WORKFLOW_ID in mode_tokens
    assert "override_repo_local_flow" in mode_tokens
    assert "upstream_intake_and_baselines" in workbench_tokens
    assert "override_repo_local_triage" in workbench_tokens


def test_td0024_c04_serve_fails_closed_on_catalog_collision(tmp_path: Path) -> None:
    governance_root = _make_governance_root(tmp_path / "governance")
    colliding_payload = dict(REPO_LOCAL_TRIAGE_WORKBENCH)
    colliding_payload["workbench_id"] = "issue_operations"
    colliding_payload["display_name"] = "Repo Local Collision"
    _write_yaml(
        governance_root / "workflow" / "definitions" / "workbenches" / "issue_operations.yaml",
        colliding_payload,
    )

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = run_cli(
        [
            "serve",
            "--governance-root",
            str(governance_root),
            "--product-root",
            str(PRODUCT_ROOT),
        ],
        stdout=stdout,
        stderr=stderr,
        run_server=False,
    )

    assert exit_code == 2
    assert "collides with built-in definition" in stderr.getvalue()
