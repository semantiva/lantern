"""Workspace topology resolution and startup-validation posture."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


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
    if governance_root is None:
        issues.append("governance root not configured")
    else:
        resolved_governance = Path(governance_root).resolve()
        if not resolved_governance.is_dir():
            issues.append(f"governance root not found: {resolved_governance}")

    registry_path = root / "lantern" / "workflow" / "definitions" / "workbench_registry.yaml"
    if not registry_path.exists():
        issues.append(f"workflow registry missing: {registry_path.relative_to(root)}")

    runtime_surface = _read_runtime_surface(registry_path)
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
