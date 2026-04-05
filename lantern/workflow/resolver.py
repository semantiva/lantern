"""Workflow resolver for Lantern.

Computes the active workbench set and preferred workbench from governed state,
the validated CH-0002 workflow layer, and an optional intent string.

No authoritative hardcoded stage maps or stage-ID if/elif chains are used.
Workbench eligibility is derived entirely from each workbench's
lifecycle_placement declaration and the supplied governance_state dict.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

_NON_TERMINAL_CH_STATUSES: frozenset[str] = frozenset(
    {"Draft", "Ready", "InProgress", "Selected"}
)


class ResolverAmbiguityError(RuntimeError):
    """Raised when CH context is required but no explicit CH is available."""


@dataclass(frozen=True)
class ResolvedWorkbenchSet:
    active_workbench_ids: tuple[str, ...]
    preferred_workbench_id: Optional[str]
    runtime_surface_classification: str
    blockers: tuple[str, ...]
    preconditions: tuple[str, ...]
    next_valid_actions: tuple[str, ...]


def resolve_active_workbenches(
    *,
    workflow_layer: Any,
    governance_state: dict[str, Any],
    intent: Optional[str] = None,
    ch_id: Optional[str] = None,
) -> ResolvedWorkbenchSet:
    ch_statuses: dict[str, str] = governance_state.get("ch_statuses", {})
    active_gates: frozenset[str] = frozenset(governance_state.get("active_gates", []))
    passed_gates: frozenset[str] = frozenset(governance_state.get("passed_gates", []))

    _check_multi_ch_ambiguity(ch_statuses, ch_id)

    active: list[Any] = []
    blockers: list[str] = []
    preconditions_seen: set[str] = set()
    preconditions: list[str] = []

    for workbench in workflow_layer.workbenches:
        if not workbench.enabled:
            continue
        eligible, reason = _is_eligible(workbench, active_gates, passed_gates)
        if eligible:
            active.append(workbench)
            for cond in workbench.entry_conditions:
                if cond not in preconditions_seen:
                    preconditions_seen.add(cond)
                    preconditions.append(cond)
        elif reason:
            blockers.append(f"{workbench.workbench_id}: {reason}")

    active_ids = tuple(w.workbench_id for w in active)
    preferred = _select_preferred(active, intent)
    next_valid = _derive_next_valid_actions(active)

    return ResolvedWorkbenchSet(
        active_workbench_ids=active_ids,
        preferred_workbench_id=preferred,
        runtime_surface_classification=workflow_layer.runtime_surface_classification,
        blockers=tuple(blockers),
        preconditions=tuple(preconditions),
        next_valid_actions=tuple(next_valid),
    )


def _check_multi_ch_ambiguity(
    ch_statuses: dict[str, str],
    ch_id: Optional[str],
) -> None:
    non_terminal = [
        ch for ch, status in ch_statuses.items() if status in _NON_TERMINAL_CH_STATUSES
    ]
    if len(non_terminal) > 1 and ch_id is None:
        raise ResolverAmbiguityError(
            f"Multiple non-terminal CHs exist ({', '.join(sorted(non_terminal))}) "
            f"and no explicit ch_id was provided. Provide ch_id to resolve CH context ambiguity."
        )


def _is_eligible(
    workbench: Any,
    active_gates: frozenset[str],
    passed_gates: frozenset[str],
) -> tuple[bool, str]:
    placement = workbench.lifecycle_placement
    kind = placement.kind

    if kind == "lifecycle-independent":
        return True, ""

    if kind == "covered_gates":
        covered = frozenset(placement.covered_gates)
        if covered & active_gates:
            return True, ""
        return False, f"no covered gate in {sorted(covered)} is currently active"

    if kind == "lifecycle_span":
        start = placement.start_gate
        end = placement.end_gate
        if start not in passed_gates:
            return False, f"start gate {start} not yet passed"
        if end in passed_gates:
            return False, f"end gate {end} already passed"
        return True, ""

    return False, f"unrecognised lifecycle_placement kind: {kind!r}"


def _select_preferred(
    active: list[Any],
    intent: Optional[str],
) -> Optional[str]:
    if not active:
        return None
    if len(active) == 1:
        return active[0].workbench_id
    if intent is None:
        return None

    intent_lower = intent.lower()
    for workbench in active:
        for intent_class in workbench.intent_classes:
            normalized = intent_class.lower().replace("_", " ")
            if normalized in intent_lower or intent_lower in normalized:
                return workbench.workbench_id

    return None


def _derive_next_valid_actions(active: list[Any]) -> list[str]:
    seen: set[str] = set()
    actions: list[str] = []
    for workbench in active:
        for tx_kind in workbench.allowed_transaction_kinds:
            if tx_kind not in seen:
                seen.add(tx_kind)
                actions.append(tx_kind)
    return actions
