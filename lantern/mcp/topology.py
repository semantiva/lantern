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

"""Workspace topology resolution and startup-validation posture."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from lantern.artifacts.validator import validate_workspace_readiness
from lantern.workflow.loader import DEFAULT_REGISTRY_PATH


@dataclass(frozen=True)
class TopologyPosture:
    product_root: Path
    governance_root: Optional[Path]
    runtime_surface_classification: str
    consistency_state: str
    startup_issues: tuple[str, ...]
    read_only: bool = True


def resolve_topology(
    *,
    product_root: Path,
    governance_root: Optional[Path] = None,
) -> TopologyPosture:
    """Resolve workspace topology from explicitly supplied roots.

    The product repository must not assume a default governance location.
    Missing governance_root degrades the posture instead of preventing product use.
    """
    root = Path(product_root).resolve()
    issues: list[str] = []
    resolved_governance = None
    if not root.is_dir():
        issues.append(f"product root not found: {root}")
    if governance_root is None:
        issues.append("governance root not configured")
    else:
        resolved_governance = Path(governance_root).resolve()
        if not resolved_governance.is_dir():
            issues.append(f"governance root not found: {resolved_governance}")

    readiness_findings = []
    if root.is_dir():
        readiness_findings = validate_workspace_readiness(
            product_root=root,
            governance_root=resolved_governance if resolved_governance and resolved_governance.is_dir() else None,
        )
        for finding in readiness_findings:
            artifact_id = finding.get("artifact_id")
            prefix = f"{artifact_id}: " if artifact_id else ""
            issues.append(prefix + finding["message"])

    runtime_surface = _read_runtime_surface(DEFAULT_REGISTRY_PATH)
    consistency = "valid" if not issues else ("missing_governance" if resolved_governance is None else "degraded")

    return TopologyPosture(
        product_root=root,
        governance_root=resolved_governance,
        runtime_surface_classification=runtime_surface,
        consistency_state=consistency,
        startup_issues=tuple(issues),
        read_only=True,
    )


def _read_runtime_surface(registry_path: Path) -> str:
    if not registry_path.exists():
        return "unknown"
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        return str(payload.get("runtime_surface_classification", "unknown"))
    except Exception:
        return "unknown"


def resolve_configuration_surface(
    *,
    governance_root: Optional[Path],
) -> Optional[Path]:
    """Return the product-governance configuration folder path if it exists.

    Returns None when governance_root is None or the configuration folder is absent.
    The returned path is the directory containing main.yaml, i.e.
    <governance_root>/workflow/configuration/.
    """
    if governance_root is None:
        return None
    config_folder = Path(governance_root).resolve() / "workflow" / "configuration"
    if config_folder.is_dir() and (config_folder / "main.yaml").exists():
        return config_folder
    return None
