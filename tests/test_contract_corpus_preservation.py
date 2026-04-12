from __future__ import annotations

import subprocess
import shutil
import sys
from pathlib import Path

import pytest

from lantern.preservation import collect_emitted_refs, resolve_guide_refs, validate_manifest

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_ROOT = PRODUCT_ROOT.parent / "lantern-ops-bridge"
MANIFEST = PRODUCT_ROOT / "lantern/preservation/relocation_manifest.yaml"
SOURCE_LOCKS = PRODUCT_ROOT / "lantern/preservation/source_locks.yaml"
REGISTRY = PRODUCT_ROOT / "lantern/workflow/definitions/workbench_registry.yaml"
INSTRUCTIONS = PRODUCT_ROOT / "lantern/resources/instructions"


def _fatal_checks(findings: list) -> set[str]:
    return {finding.check for finding in findings if finding.severity == "FATAL"}


def test_full_corpus_inventory_present() -> None:
    findings = validate_manifest(MANIFEST, PRODUCT_ROOT, source_locks_path=SOURCE_LOCKS)
    assert "MISSING_FILE" not in _fatal_checks(findings)


def test_preservation_signatures_pass() -> None:
    findings = validate_manifest(MANIFEST, PRODUCT_ROOT, source_locks_path=SOURCE_LOCKS)
    assert [finding for finding in findings if finding.severity == "FATAL"] == []


def test_no_forbidden_patterns_in_corpus() -> None:
    findings = validate_manifest(MANIFEST, PRODUCT_ROOT, source_locks_path=SOURCE_LOCKS)
    assert "FORBIDDEN_PATTERN" not in _fatal_checks(findings)


def test_binding_uses_current_grammar_namespace() -> None:
    content = (PRODUCT_ROOT / "lantern/preservation/LANTERN_MODEL_BINDING.md").read_text(encoding="utf-8")
    assert "lg:artifacts/ch" in content
    assert "lg:statuses/draft_initiative" in content
    assert "th:" not in content


def test_removed_preflight_gates_absent_from_active_corpus() -> None:
    targets = [
        PRODUCT_ROOT / "lantern/preservation/GATES.md",
        PRODUCT_ROOT / "lantern/preservation/WORKBENCH_MAP.md",
        PRODUCT_ROOT / "lantern/preservation/LANTERN_MODEL_BINDING.md",
        PRODUCT_ROOT / "lantern/preservation/relocation_manifest.yaml",
        PRODUCT_ROOT / "lantern/administration_procedures/GT-030__DIP_LOCK_ADMINISTRATION_v0.1.0.md",
        PRODUCT_ROOT / "lantern/administration_procedures/GT-050_GT-060__BASELINE_READINESS_ADMINISTRATION_v0.1.0.md",
        PRODUCT_ROOT / "lantern/administration_procedures/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md",
        PRODUCT_ROOT / "lantern/administration_procedures/SSOT_BLOB_INGESTION_v0.2.0.md",
        PRODUCT_ROOT / "lantern/administration_procedures/AI_OPERATOR_INVOCATION_TEMPLATES_v0.2.0.md",
        PRODUCT_ROOT / "lantern/administration_procedures/AI_OPERATOR_INVOCATION_TEMPLATES_v0.2.1.md",
        PRODUCT_ROOT / "lantern/templates/TEMPLATE__INITIATIVE.md",
        PRODUCT_ROOT / "lantern/templates/TEMPLATE__SPEC.md",
    ]
    for path in targets:
        content = path.read_text(encoding="utf-8")
        assert "GT-035" not in content, f"GT-035 remains in {path}"
        assert "GT-036" not in content, f"GT-036 remains in {path}"
        assert "GT-045" not in content, f"GT-045 remains in {path}"


def test_emitted_guide_refs_resolve() -> None:
    refs = collect_emitted_refs(REGISTRY, INSTRUCTIONS)
    unresolved = resolve_guide_refs(MANIFEST, refs, PRODUCT_ROOT)
    assert unresolved == []


def test_preservation_checker_fails_on_drift(tmp_path: Path) -> None:
    sandbox = tmp_path / "product"
    shutil.copytree(PRODUCT_ROOT, sandbox)
    target = sandbox / "lantern/resources/instructions/ci_authoring.md"
    original = target.read_text(encoding="utf-8")
    target.write_text(original.replace("## MCP usage\n", "", 1), encoding="utf-8")
    findings = validate_manifest(
        sandbox / "lantern/preservation/relocation_manifest.yaml",
        sandbox,
        source_locks_path=sandbox / "lantern/preservation/source_locks.yaml",
    )
    assert "MISSING_HEADING" in _fatal_checks(findings)


def test_name_isolation_and_preservation_pass_together() -> None:
    findings = validate_manifest(MANIFEST, PRODUCT_ROOT, source_locks_path=SOURCE_LOCKS)
    fatal_checks = _fatal_checks(findings)
    assert "FORBIDDEN_PATTERN" not in fatal_checks
    assert "MISSING_HEADING" not in fatal_checks
    assert "UNRESOLVED_REF" not in fatal_checks


def test_sync_module_executes_without_runtime_warning() -> None:
    if not BRIDGE_ROOT.exists():
        pytest.skip("bridge workspace is required for sync-module execution")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lantern.preservation.sync",
            "--manifest",
            str(MANIFEST.relative_to(PRODUCT_ROOT)),
            "--source-locks",
            str(SOURCE_LOCKS.relative_to(PRODUCT_ROOT)),
            "--bridge-root",
            str(BRIDGE_ROOT),
            "--product-root",
            ".",
            "--mode",
            "plan",
        ],
        cwd=PRODUCT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RuntimeWarning" not in result.stderr
