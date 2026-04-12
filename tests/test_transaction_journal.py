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

"""CH-0004 transaction journal and validation-correlation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from lantern.artifacts.renderers import canonical_render_markdown
from lantern.mcp.commit import handle_commit
from lantern.mcp.draft import handle_draft
from lantern.mcp.journal import (
    load_application_handoff,
    load_journal_record,
    load_validation_snapshot,
    runtime_state_root,
)
from lantern.mcp.validate import handle_validate
from lantern.workflow.loader import load_workflow_layer


@pytest.fixture(scope="module")
def workflow_layer():
    return load_workflow_layer()


def _valid_ci_payload() -> dict[str, object]:
    return {
        "header": {
            "ch_id": "CH-0004",
            "status": "Candidate",
            "title": "Journal coverage candidate",
        },
        "title": "Journal coverage candidate",
        "sections": [
            {"heading": "Intent", "body": "Exercise journal correlation."},
            {"heading": "Verification Plan", "body": "Run the mutation tests."},
        ],
    }


def _write_selected_ci(governance_root: Path, *, allowed_change_surface: list[str]) -> Path:
    ci_path = governance_root / "ci" / "CI-0004-selected.md"
    ci_path.parent.mkdir(parents=True, exist_ok=True)
    ci_path.write_text(
        canonical_render_markdown(
            header={
                "ch_id": "CH-0004",
                "ci_id": "CI-0004-selected",
                "status": "Selected",
                "title": "Transaction journal fixture",
                "allowed_change_surface": allowed_change_surface,
            },
            artifact_id="CI-0004-selected",
            title="Transaction journal fixture",
            sections=[{"heading": "Intent", "body": "Fixture for transaction journal tests."}],
        ),
        encoding="utf-8",
    )
    return ci_path


def _seed_runtime_hygiene_gitignore(product_root: Path) -> None:
    (product_root / ".gitignore").write_text(
        "__pycache__/\n*.py[cod]\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n.venv/\nvenv/\n",
        encoding="utf-8",
    )


def test_td0004_c09_commit_and_journal_capture_transaction_correlation_metadata(workflow_layer, tmp_path: Path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    draft_result = handle_draft(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        artifact_family="CI",
        payload=_valid_ci_payload(),
        product_root=product_root,
        governance_root=governance_root,
    )
    commit_result = handle_commit(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        draft_id=draft_result["draft_id"],
        product_root=product_root,
        governance_root=governance_root,
        actor="journal-checker",
    )

    runtime_root = runtime_state_root(product_root=product_root, governance_root=governance_root)
    journal = load_journal_record(runtime_root=runtime_root, transaction_id=commit_result["transaction_id"])
    snapshot = load_validation_snapshot(runtime_root=runtime_root, transaction_id=commit_result["transaction_id"])

    assert commit_result["status"] == "committed"
    assert commit_result["correlation"] == {
        "transaction_id": commit_result["transaction_id"],
        "contract_ref": draft_result["contract_ref"],
        "actor": "journal-checker",
        "artifact_id": draft_result["derived_fields"]["artifact_id"],
        "journal_path": commit_result["journal_path"],
    }
    assert journal["tx_id"] == commit_result["transaction_id"]
    assert journal["name"] == "commit_governance_artifact"
    assert journal["status"] == "COMMITTED"
    assert journal["metadata"] == {
        "actor": "journal-checker",
        "workbench_id": "ci_authoring",
        "contract_ref": draft_result["contract_ref"],
        "artifact_id": draft_result["derived_fields"]["artifact_id"],
        "validation_scope": "transaction",
    }
    assert journal["touched_paths"] == [commit_result["artifact_path"]]
    assert journal["validation_snapshot"].endswith(f"{commit_result['transaction_id']}.json")
    assert snapshot["scope"] == "transaction"
    assert snapshot["transaction_id"] == commit_result["transaction_id"]
    assert snapshot["affected_paths"] == [commit_result["artifact_path"]]


def test_td0004_c11_validate_supports_draft_artifact_and_transaction_scopes(workflow_layer, tmp_path: Path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    draft_result = handle_draft(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        artifact_family="CI",
        payload=_valid_ci_payload(),
        product_root=product_root,
        governance_root=governance_root,
    )
    commit_result = handle_commit(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        draft_id=draft_result["draft_id"],
        product_root=product_root,
        governance_root=governance_root,
        actor="validator",
    )

    draft_validation = handle_validate(
        workflow_layer=workflow_layer,
        scope="draft",
        draft_id=draft_result["draft_id"],
        product_root=product_root,
        governance_root=governance_root,
    )
    artifact_validation = handle_validate(
        workflow_layer=workflow_layer,
        scope="artifact",
        artifact_path=commit_result["artifact_path"],
        product_root=product_root,
        governance_root=governance_root,
    )
    transaction_validation = handle_validate(
        workflow_layer=workflow_layer,
        scope="transaction",
        transaction_id=commit_result["transaction_id"],
        product_root=product_root,
        governance_root=governance_root,
    )

    assert draft_validation == {
        "scope": "draft",
        "draft_id": draft_result["draft_id"],
        "valid": True,
        "findings": [],
    }
    assert artifact_validation == {
        "scope": "artifact",
        "artifact_path": commit_result["artifact_path"],
        "valid": True,
        "findings": [],
    }
    assert transaction_validation["scope"] == "transaction"
    assert transaction_validation["transaction_id"] == commit_result["transaction_id"]
    assert transaction_validation["valid"] is True
    assert transaction_validation["findings"] == []
    assert transaction_validation["affected_paths"] == [commit_result["artifact_path"]]


def test_td0004_c12_post_commit_validation_remains_correlated_to_transaction(workflow_layer, tmp_path: Path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    _seed_runtime_hygiene_gitignore(product_root)
    ci_path = _write_selected_ci(
        governance_root,
        allowed_change_surface=["src/allowed.txt"],
    )

    commit_result = handle_commit(
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        payload={
            "ci_path": str(ci_path),
            "operations": [{"path": "src/allowed.txt", "content": "FAIL_VALIDATION\n"}],
        },
        product_root=product_root,
        governance_root=governance_root,
        actor="validator",
    )
    transaction_validation = handle_validate(
        workflow_layer=workflow_layer,
        scope="transaction",
        transaction_id=commit_result["transaction_id"],
        product_root=product_root,
        governance_root=governance_root,
    )

    failing_path = str((product_root / "src/allowed.txt").resolve())
    expected_finding = {
        "path": failing_path,
        "message": "FAIL_VALIDATION marker present in committed product file",
        "anchor": "post_commit_validation",
    }
    assert commit_result["status"] == "committed"
    assert commit_result["validation"]["scope"] == "transaction"
    assert commit_result["validation"]["path"]
    assert commit_result["validation"]["valid"] is False
    assert commit_result["validation"]["findings"] == [expected_finding]
    assert commit_result["validation"]["application_handoff"]["ci_id"] == "CI-0004-selected"
    assert commit_result["validation"]["application_handoff"]["post_application_state"] == "awaiting_gt130"
    assert commit_result["correlation"] == {
        "transaction_id": commit_result["transaction_id"],
        "contract_ref": "contract.selected_ci_application.v1",
        "actor": "validator",
        "affected_paths": [failing_path],
        "journal_path": commit_result["journal_path"],
    }
    assert transaction_validation == {
        "scope": "transaction",
        "transaction_id": commit_result["transaction_id"],
        "valid": False,
        "findings": [expected_finding],
        "journal_path": str(
            (
                runtime_state_root(product_root=product_root, governance_root=governance_root)
                / "journal"
                / commit_result["transaction_id"]
                / "journal.json"
            ).resolve()
        ),
        "affected_paths": [failing_path],
        "application_handoff": commit_result["validation"]["application_handoff"],
    }


def test_td0009_c05_application_handoff_is_persisted_for_selected_ci_delivery(workflow_layer, tmp_path: Path) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    ci_path = _write_selected_ci(
        governance_root,
        allowed_change_surface=["src/allowed.txt"],
    )

    commit_result = handle_commit(
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        payload={
            "ci_path": str(ci_path),
            "operations": [{"path": "src/allowed.txt", "content": "ok\n"}],
        },
        product_root=product_root,
        governance_root=governance_root,
        actor="validator",
    )

    runtime_root = runtime_state_root(product_root=product_root, governance_root=governance_root)
    handoff = load_application_handoff(runtime_root=runtime_root, transaction_id=commit_result["transaction_id"])
    assert handoff is not None
    assert handoff["post_application_state"] == "awaiting_gt130"
    assert handoff["ci_id"] == "CI-0004-selected"
    assert ".gitignore" in handoff["effective_change_surface"]
