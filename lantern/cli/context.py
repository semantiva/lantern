"""Root-resolution helpers shared by the CH-0021 operational CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class ContextResolutionError(RuntimeError):
    """Raised when the CLI cannot resolve a valid operational context."""


@dataclass(frozen=True)
class OperationalContext:
    governance_root: Path
    product_root: Path
    product_root_source: str
    configuration_path: Path | None


def resolve_operational_context(
    *,
    governance_root: Path | None,
    supplied_product_root: Path | None = None,
    allow_supplied_product_root: bool = False,
) -> OperationalContext:
    if governance_root is None:
        raise ContextResolutionError("governance root is required for this command")

    governance_root = Path(governance_root).resolve()
    if not governance_root.is_dir():
        raise ContextResolutionError(f"governance root not found: {governance_root}")

    configuration_path = governance_root / "workflow" / "configuration" / "main.yaml"
    configured_product_root = _configured_product_root(configuration_path)
    supplied = Path(supplied_product_root).resolve() if supplied_product_root is not None else None

    if configured_product_root is not None:
        if supplied is not None and supplied != configured_product_root:
            raise ContextResolutionError(
                "configured product root and supplied product root do not match: "
                f"configured={configured_product_root} supplied={supplied}"
            )
        product_root = configured_product_root
        source = "governed_configuration"
    elif supplied is not None and allow_supplied_product_root:
        product_root = supplied
        source = "command_line"
    else:
        raise ContextResolutionError(
            "governed configuration does not declare a product root; "
            "run bootstrap-product or supply --product-root in an explicitly declared setup flow"
        )

    if not product_root.is_dir():
        raise ContextResolutionError(f"product root not found: {product_root}")

    return OperationalContext(
        governance_root=governance_root,
        product_root=product_root,
        product_root_source=source,
        configuration_path=configuration_path if configuration_path.exists() else None,
    )


def _configured_product_root(configuration_path: Path) -> Path | None:
    if not configuration_path.exists():
        return None
    try:
        payload = yaml.safe_load(configuration_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ContextResolutionError(f"invalid governed configuration at {configuration_path}: {exc}") from exc
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise ContextResolutionError(
            f"invalid governed configuration at {configuration_path}: expected a mapping document"
        )
    authoritative_refs = payload.get("authoritative_refs")
    if authoritative_refs is None:
        authoritative_refs = {}
    if not isinstance(authoritative_refs, dict):
        raise ContextResolutionError(
            f"invalid governed configuration at {configuration_path}: authoritative_refs must be a mapping"
        )
    product_root = authoritative_refs.get("product_root")
    if not isinstance(product_root, str) or not product_root.strip():
        return None
    return Path(product_root).resolve()
