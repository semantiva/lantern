"""Flat discovery registry helpers for the CH-0021 operational CLI."""

from .registry import (
    build_discovery_registry,
    diff_index_inventory,
    list_records,
    show_record,
)

__all__ = [
    "build_discovery_registry",
    "diff_index_inventory",
    "list_records",
    "show_record",
]
