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

"""Structured diagnostics for the CH-0021 operational CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from lantern.artifacts.validator import validate_workspace_readiness
from lantern.discovery.registry import build_discovery_registry
from lantern.workflow.loader import WorkflowLayerError, load_workflow_layer
from lantern.workflow.merger import ConfigurationLoadError, ConfigurationLoader


_CATEGORY_ORDER = (
    "runtime_availability",
    "grammar_compatibility",
    "workspace_validity",
    "workflow_configuration",
    "bootstrap_posture",
    "managed_file_posture",
    "discovery_availability",
)


def gather_doctor_report(
    *,
    governance_root: Path,
    product_root: Path,
) -> dict[str, Any]:
    governance_root = Path(governance_root).resolve()
    product_root = Path(product_root).resolve()

    findings: list[dict[str, str]] = []

    runtime_availability = {
        "product_root": str(product_root),
        "governance_root": str(governance_root),
        "mcp_runtime": _probe_mcp_runtime(findings),
    }
    grammar_compatibility = _probe_grammar(findings)
    workspace_validity = _probe_workspace(product_root, governance_root, findings)
    workflow_configuration = _probe_configuration(governance_root, findings)
    bootstrap_posture = _probe_bootstrap(governance_root, product_root, findings)
    managed_file_posture = _probe_managed_files(governance_root, product_root, findings)
    discovery_availability = _probe_discovery(governance_root, product_root, findings)

    report = {
        "kind": "doctor_report",
        "categories": list(_CATEGORY_ORDER),
        "checks": {
            "runtime_availability": runtime_availability,
            "grammar_compatibility": grammar_compatibility,
            "workspace_validity": workspace_validity,
            "workflow_configuration": workflow_configuration,
            "bootstrap_posture": bootstrap_posture,
            "managed_file_posture": managed_file_posture,
            "discovery_availability": discovery_availability,
        },
        "findings": findings,
        "summary": {
            "blocker_count": sum(1 for finding in findings if finding["classification"] == "blocker"),
            "advisory_count": sum(1 for finding in findings if finding["classification"] == "advisory"),
        },
    }
    return report


def _probe_mcp_runtime(findings: list[dict[str, str]]) -> str:
    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401
    except Exception as exc:
        findings.append(
            _finding(
                category="runtime_availability",
                classification="advisory",
                subject="mcp_runtime",
                message=f"FastMCP runtime is not importable: {exc}",
                remediation="Install the mcp package before using the serve command in a packaged environment.",
            )
        )
        return "degraded"
    return "ok"


def _probe_grammar(findings: list[dict[str, str]]) -> dict[str, Any]:
    from lantern._compat import check_grammar_compatibility

    result = check_grammar_compatibility()
    if result["status"] in {"missing", "unsupported"}:
        findings.append(
            _finding(
                category="grammar_compatibility",
                classification="blocker",
                subject="lantern_grammar",
                message=result["message"],
                remediation=(
                    "Install a compatible published lantern-grammar package into the active Python "
                    f"environment: pip install 'lantern-grammar{result['supported_range']}'"
                ),
            )
        )
    return {
        "status": result["status"],
        "supported_range": result["supported_range"],
        "installed_package_version": result["installed_package_version"],
        "installed_model_version": result["installed_model_version"],
    }


def _probe_workspace(
    product_root: Path,
    governance_root: Path,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    workspace_findings = validate_workspace_readiness(
        product_root=product_root,
        governance_root=governance_root,
    )
    for finding in workspace_findings:
        findings.append(
            _finding(
                category="workspace_validity",
                classification="blocker",
                subject=finding.get("path", "workspace"),
                message=finding["message"],
                remediation="Correct the reported product or governance workspace issue.",
            )
        )
    return {
        "status": "ok" if not workspace_findings else "blocked",
        "finding_count": len(workspace_findings),
    }


def _probe_configuration(
    governance_root: Path,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    config_root = governance_root / "workflow" / "configuration"
    if not config_root.exists():
        findings.append(
            _finding(
                category="workflow_configuration",
                classification="advisory",
                subject="workflow.configuration",
                message=f"configuration folder is absent: {config_root}",
                remediation="Run bootstrap-product to create the governed configuration surface.",
            )
        )
        return {"status": "absent", "configuration_root": str(config_root)}

    loader = ConfigurationLoader()
    try:
        surface = loader.load_and_validate(config_root)
    except ConfigurationLoadError as exc:
        findings.append(
            _finding(
                category="workflow_configuration",
                classification="blocker",
                subject="workflow.configuration",
                message=str(exc),
                remediation="Repair the governed configuration folder so Lantern can validate it.",
            )
        )
        return {"status": "invalid", "configuration_root": str(config_root)}

    return {
        "status": "ok",
        "configuration_root": str(config_root),
        "declared_posture": surface.declared_posture,
    }


def _probe_bootstrap(
    governance_root: Path,
    product_root: Path,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    config_path = governance_root / "workflow" / "configuration" / "main.yaml"
    if not config_path.exists():
        findings.append(
            _finding(
                category="bootstrap_posture",
                classification="advisory",
                subject="workflow.configuration.main_yaml",
                message="bootstrap configuration has not been created yet",
                remediation="Run bootstrap-product and review the preview plan before applying it.",
            )
        )
        return {"status": "not_bootstrapped", "configured_product_root": None}

    import yaml

    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        findings.append(
            _finding(
                category="bootstrap_posture",
                classification="blocker",
                subject="workflow.configuration.main_yaml",
                message=f"bootstrap configuration is invalid: {exc}",
                remediation="Repair workflow/configuration/main.yaml so Lantern can read authoritative_refs.product_root.",
            )
        )
        return {"status": "invalid", "configured_product_root": None}
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        findings.append(
            _finding(
                category="bootstrap_posture",
                classification="blocker",
                subject="workflow.configuration.main_yaml",
                message="bootstrap configuration root document must be a mapping",
                remediation="Repair workflow/configuration/main.yaml so Lantern can read authoritative_refs.product_root.",
            )
        )
        return {"status": "invalid", "configured_product_root": None}
    authoritative_refs = payload.get("authoritative_refs")
    if authoritative_refs is None:
        authoritative_refs = {}
    if not isinstance(authoritative_refs, dict):
        findings.append(
            _finding(
                category="bootstrap_posture",
                classification="blocker",
                subject="authoritative_refs",
                message="bootstrap configuration authoritative_refs must be a mapping",
                remediation="Repair workflow/configuration/main.yaml so Lantern can read authoritative_refs.product_root.",
            )
        )
        return {"status": "invalid", "configured_product_root": None}
    configured_product_root = authoritative_refs.get("product_root")
    if configured_product_root != str(product_root):
        findings.append(
            _finding(
                category="bootstrap_posture",
                classification="advisory",
                subject="authoritative_refs.product_root",
                message=(
                    "configured product root does not match the supplied product root: "
                    f"configured={configured_product_root!r} supplied={product_root}"
                ),
                remediation="Re-run bootstrap-product or update workflow/configuration/main.yaml intentionally.",
            )
        )
    return {
        "status": "ok" if configured_product_root == str(product_root) else "drifted",
        "configured_product_root": configured_product_root,
    }


def _probe_managed_files(
    governance_root: Path,
    product_root: Path,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    managed_paths = {
        "product_agents": product_root / "AGENTS.md",
        "governance_agents": governance_root / "AGENTS.md",
        "governance_readme": governance_root / "README.md",
    }
    missing = [name for name, path in managed_paths.items() if not path.exists()]
    for name in missing:
        findings.append(
            _finding(
                category="managed_file_posture",
                classification="advisory",
                subject=name,
                message=f"managed bootstrap file is missing: {managed_paths[name]}",
                remediation="Run bootstrap-product apply to restore the managed file set.",
            )
        )
    return {
        "status": "ok" if not missing else "partial",
        "missing": missing,
    }


def _probe_discovery(
    governance_root: Path,
    product_root: Path,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    strict_status = "ok"
    try:
        load_workflow_layer()
    except WorkflowLayerError as exc:
        strict_status = "stale_generated_artifacts"
        findings.append(
            _finding(
                category="discovery_availability",
                classification="advisory",
                subject="workflow.generated_artifacts",
                message=str(exc),
                remediation="Refresh the committed workflow projections before relying on packaged release parity.",
            )
        )

    try:
        registry = build_discovery_registry(
            product_root=product_root,
            governance_root=governance_root,
        )
    except Exception as exc:
        findings.append(
            _finding(
                category="discovery_availability",
                classification="blocker",
                subject="discovery_registry",
                message=f"discovery registry could not be built: {exc}",
                remediation="Repair the workflow or governance inputs so flat discovery can be derived.",
            )
        )
        return {"status": "blocked", "record_count": 0, "strict_status": strict_status}

    return {
        "status": "ok",
        "record_count": len(registry["records"]),
        "strict_status": strict_status,
    }


def _finding(
    *,
    category: str,
    classification: str,
    subject: str,
    message: str,
    remediation: str,
) -> dict[str, str]:
    return {
        "category": category,
        "classification": classification,
        "subject": subject,
        "message": message,
        "remediation": remediation,
    }
