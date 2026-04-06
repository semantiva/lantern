"""CH-0004 mutation-path tests."""
from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from lantern.artifacts.renderers import canonical_render_markdown
from lantern.mcp.commit import handle_commit
from lantern.mcp.draft import handle_draft
from lantern.mcp.inspect import handle_inspect
from lantern.mcp.validate import handle_validate
from lantern.workflow.loader import load_workflow_layer

PRODUCT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def workflow_layer():
    return load_workflow_layer()


def _valid_ci_payload() -> dict[str, object]:
    return {
        "header": {
            "ch_id": "CH-0004",
            "status": "Candidate",
            "title": "Mutation Spine candidate",
        },
        "title": "Mutation Spine candidate",
        "sections": [
            {"heading": "Intent", "body": "Implement CH-0004 mutation flows."},
            {"heading": "Definition of Done", "body": "All CH-0004 tests pass."},
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
                "title": "Selected CI application fixture",
                "allowed_change_surface": allowed_change_surface,
            },
            artifact_id="CI-0004-selected",
            title="Selected CI application fixture",
            sections=[{"heading": "Intent", "body": "Fixture for bounded product writes."}],
        ),
        encoding="utf-8",
    )
    return ci_path


def _seed_runtime_hygiene_gitignore(product_root: Path) -> None:
    (product_root / ".gitignore").write_text(
        "__pycache__/\n*.py[cod]\n.pytest_cache/\n.mypy_cache/\n.ruff_cache/\n.venv/\nvenv/\n",
        encoding="utf-8",
    )


def test_td0004_c03_invalid_draft_returns_machine_readable_path_based_findings(
    workflow_layer, tmp_path: Path
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    result = handle_draft(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        artifact_family="CI",
        payload={
            "header": {},
            "title": "",
            "sections": [{"heading": "", "body": 7}],
        },
        product_root=product_root,
        governance_root=governance_root,
    )

    assert result["status"] == "invalid"
    findings = result["findings"]
    assert findings
    assert {finding["path"] for finding in findings} >= {
        "payload.title",
        "payload.sections[0].heading",
        "payload.sections[0].body",
    }
    for finding in findings:
        assert isinstance(finding["path"], str) and finding["path"]
        assert isinstance(finding["anchor"], str) and finding["anchor"]


def test_td0004_c04_draft_returns_allocated_id_derived_fields_and_preview(
    workflow_layer, tmp_path: Path
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    result = handle_draft(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        artifact_family="CI",
        payload=_valid_ci_payload(),
        product_root=product_root,
        governance_root=governance_root,
    )

    assert result["status"] == "ok"
    artifact_id = result["derived_fields"]["artifact_id"]
    artifact_path = result["derived_fields"]["artifact_path"]
    assert artifact_id.startswith("CI-0004-")
    assert artifact_path.endswith(f"ci/{artifact_id}.md")
    assert result["preview"].startswith("```yaml\n")
    assert f"# {artifact_id}" in result["preview"]
    assert "## Intent" in result["preview"]
    assert result["validation"] == {"valid": True, "findings": []}


def test_td0004_c05_change_surface_inspection_returns_deterministic_writable_posture(
    workflow_layer, tmp_path: Path
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    _seed_runtime_hygiene_gitignore(product_root)
    ci_path = _write_selected_ci(
        governance_root,
        allowed_change_surface=["lantern/mcp/server.py", "tests/"],
    )

    first = handle_inspect(
        kind="change_surface",
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        product_root=product_root,
        governance_root=governance_root,
        ci_path=str(ci_path),
    )
    second = handle_inspect(
        kind="change_surface",
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        product_root=product_root,
        governance_root=governance_root,
        ci_path=str(ci_path),
    )

    assert first == second
    assert first.allowed_change_surface == ("lantern/mcp/server.py", "tests/")
    assert first.product_root == str(product_root.resolve())
    assert first.governance_root == str(governance_root.resolve())
    assert len(first.change_surface_hash) == 64


def test_td0004_c06_commit_persists_governance_artifact_as_canonical_markdown(
    workflow_layer, tmp_path: Path
) -> None:
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
        actor="ci-author",
    )

    artifact_path = Path(commit_result["artifact_path"])
    assert commit_result["status"] == "committed"
    assert artifact_path.read_text(encoding="utf-8") == draft_result["preview"]
    assert artifact_path.exists()
    assert Path(commit_result["journal_path"]).exists()


def test_td0004_c07_selected_ci_commit_applies_only_allowed_product_writes(
    workflow_layer, tmp_path: Path
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    _seed_runtime_hygiene_gitignore(product_root)
    ci_path = _write_selected_ci(
        governance_root,
        allowed_change_surface=["src/allowed.txt", "tests/"],
    )

    committed = handle_commit(
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        payload={
            "ci_path": str(ci_path),
            "operations": [{"path": "src/allowed.txt", "content": "allowed write\n"}],
        },
        product_root=product_root,
        governance_root=governance_root,
        actor="ci-applicator",
    )
    assert committed["status"] == "committed"
    assert committed["affected_paths"] == [str((product_root / "src/allowed.txt").resolve())]
    assert (product_root / "src/allowed.txt").read_text(encoding="utf-8") == "allowed write\n"

    rejected = handle_commit(
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        payload={
            "ci_path": str(ci_path),
            "operations": [{"path": "README.md", "content": "escape\n"}],
        },
        product_root=product_root,
        governance_root=governance_root,
        actor="ci-applicator",
    )
    assert rejected["status"] == "invalid"
    assert rejected["findings"] == [
        {
            "path": "payload.operations[0].path",
            "message": "path 'README.md' is outside the inspected change surface",
            "anchor": "inspect.change_surface.allowed_change_surface",
        }
    ]
    assert not (product_root / "README.md").exists()


def test_td0004_c08_commits_serialize_under_internal_transaction_lock(
    workflow_layer, tmp_path: Path
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()

    first_draft = handle_draft(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        artifact_family="CI",
        payload=_valid_ci_payload(),
        product_root=product_root,
        governance_root=governance_root,
    )
    second_draft = handle_draft(
        workflow_layer=workflow_layer,
        workbench_id="ci_authoring",
        artifact_family="CI",
        payload=_valid_ci_payload(),
        product_root=product_root,
        governance_root=governance_root,
    )

    results: list[dict[str, object]] = []

    def _commit(draft_id: str, hold_lock_seconds: float) -> None:
        results.append(
            handle_commit(
                workflow_layer=workflow_layer,
                workbench_id="ci_authoring",
                draft_id=draft_id,
                payload={"hold_lock_seconds": hold_lock_seconds},
                product_root=product_root,
                governance_root=governance_root,
                actor="lock-tester",
            )
        )

    first = threading.Thread(target=_commit, args=(first_draft["draft_id"], 0.30))
    second = threading.Thread(target=_commit, args=(second_draft["draft_id"], 0.0))
    first.start()
    time.sleep(0.05)
    second.start()
    first.join()
    second.join()

    statuses = sorted(result["status"] for result in results)
    assert statuses == ["committed", "lock_conflict"]


def test_td0004_c10_workspace_validate_returns_structured_scope_findings(
    workflow_layer, tmp_path: Path
) -> None:
    governance_root = tmp_path / "governance"
    governance_root.mkdir()

    valid_workspace = handle_validate(
        workflow_layer=workflow_layer,
        scope="workspace",
        product_root=PRODUCT_ROOT,
        governance_root=governance_root,
    )
    assert valid_workspace["scope"] == "workspace"
    assert valid_workspace["valid"] is True
    assert valid_workspace["findings"] == []
    assert valid_workspace["workspace"] == {
        "product_root": str(PRODUCT_ROOT.resolve()),
        "governance_root": str(governance_root.resolve()),
        "runtime_surface_classification": "full_governed_surface",
        "consistency_state": "valid",
        "startup_issues": [],
    }

    invalid_workspace = handle_validate(
        workflow_layer=workflow_layer,
        scope="workspace",
        product_root=tmp_path / "missing-product-root",
        governance_root=governance_root / "missing-governance-root",
    )
    assert invalid_workspace["scope"] == "workspace"
    assert invalid_workspace["valid"] is False
    assert invalid_workspace["findings"]
    assert invalid_workspace["findings"][0]["path"] == "workspace.product_root"


def test_td0009_c05_selected_ci_application_records_handoff_and_runtime_managed_hygiene(
    workflow_layer, tmp_path: Path
) -> None:
    product_root = tmp_path / "product"
    governance_root = tmp_path / "governance"
    product_root.mkdir()
    governance_root.mkdir()
    ci_path = _write_selected_ci(
        governance_root,
        allowed_change_surface=["src/allowed.txt"],
    )

    change_surface = handle_inspect(
        kind="change_surface",
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        product_root=product_root,
        governance_root=governance_root,
        ci_path=str(ci_path),
    )
    assert change_surface.runtime_managed_change_surface == (".gitignore",)

    committed = handle_commit(
        workflow_layer=workflow_layer,
        workbench_id="selected_ci_application",
        payload={
            "ci_path": str(ci_path),
            "operations": [{"path": "src/allowed.txt", "content": "allowed write\n"}],
        },
        product_root=product_root,
        governance_root=governance_root,
        actor="ci-applicator",
    )
    assert committed["status"] == "committed"
    assert committed["application_handoff"]["post_application_state"] == "awaiting_gt130"
    assert ".gitignore" in committed["application_handoff"]["effective_change_surface"]
    assert str((product_root / ".gitignore").resolve()) in committed["affected_paths"]
    gitignore_text = (product_root / ".gitignore").read_text(encoding="utf-8")
    assert "# BEGIN LANTERN MANAGED PYTHON HYGIENE" in gitignore_text
    assert "__pycache__/" in gitignore_text
    transaction_validation = handle_validate(
        workflow_layer=workflow_layer,
        scope="transaction",
        transaction_id=committed["transaction_id"],
        product_root=product_root,
        governance_root=governance_root,
    )
    assert transaction_validation["application_handoff"]["post_application_state"] == "awaiting_gt130"
