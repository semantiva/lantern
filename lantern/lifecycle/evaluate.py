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

"""Declarative transition eligibility (DB-0002 D5).

A pure function of the lifecycle declarations, the grammar-derived gate specs,
and the supplied state view. Every failed constraint is collected into one
standard blocked outcome (REQ-0003); no check consults ordering or any input
beyond the declarations and the view (REQ-0006).
"""

from __future__ import annotations

from typing import Any

from lantern.outcomes import blocked_outcome

from .bundle import CardinalityRule, LifecycleBundle, SlotConstraint
from .gates import GateSpec, gates_by_outcome
from .view import RelatedRef, StateView

ELIGIBLE_SCHEMA_ID = "lantern.lifecycle.eligible.v1"

REASON_BUNDLE_INVALID = "bundle_invalid"
REASON_UNDECLARED_FAMILY = "undeclared_family"
REASON_UNDECLARED_STATUS = "undeclared_status"
REASON_UNDECLARED_TRANSITION = "undeclared_transition"
REASON_STATE_CONSTRAINT = "state_constraint"
REASON_GATE_EVIDENCE = "gate_evidence"

_APPROVED = "approved"


def evaluate_transition(
    bundle: LifecycleBundle,
    gates: tuple[GateSpec, ...],
    view: StateView,
    family: str,
    from_status: str,
    to_status: str,
    subject_id: str,
) -> dict[str, Any]:
    """Evaluate one transition; return an eligible payload or a blocked outcome."""
    pattern = {"family": family, "from_status": from_status, "to_status": to_status}

    if not bundle.is_healthy:
        defect_reasons = [{"code": REASON_BUNDLE_INVALID, "detail": d.render()} for d in bundle.defects]
        return blocked_outcome(pattern=pattern, reasons=defect_reasons, subject=subject_id)

    reasons: list[dict[str, str]] = []
    if family not in bundle.families:
        reasons.append({"code": REASON_UNDECLARED_FAMILY, "detail": f"family {family!r} has no lifecycle declaration"})
        return blocked_outcome(pattern=pattern, reasons=reasons, subject=subject_id)

    declared = bundle.statuses_for(family)
    for status in (from_status, to_status):
        if status not in declared:
            reasons.append(
                {
                    "code": REASON_UNDECLARED_STATUS,
                    "detail": f"status {status!r} is not declared for family {family!r} (declared: {', '.join(declared)})",
                }
            )
    if reasons:
        return blocked_outcome(pattern=pattern, reasons=reasons, subject=subject_id)

    if (from_status, to_status) not in bundle.transitions_for(family):
        reasons.append(
            {
                "code": REASON_UNDECLARED_TRANSITION,
                "detail": f"transition {from_status} -> {to_status} is not declared for family {family!r}",
            }
        )

    for constraint in bundle.constraints_for(family, to_status):
        members = view.related(subject_id, constraint.slot)
        for rule in constraint.rules:
            failure = _evaluate_rule(constraint, rule, members)
            if failure is not None:
                reasons.append({"code": REASON_STATE_CONSTRAINT, "detail": failure})

    for gate in gates_by_outcome(gates).get((family, to_status), ()):
        failure = _evaluate_gate(gate, view, subject_id)
        if failure is not None:
            reasons.append({"code": REASON_GATE_EVIDENCE, "detail": failure})

    if reasons:
        return blocked_outcome(pattern=pattern, reasons=reasons, subject=subject_id)
    return {
        "schema_id": ELIGIBLE_SCHEMA_ID,
        "eligible": True,
        "pattern": pattern,
        "subject": subject_id,
    }


def _evaluate_rule(constraint: SlotConstraint, rule: CardinalityRule, members: tuple[RelatedRef, ...]) -> str | None:
    """Return a failure detail naming slot, rule, and observed state; None if satisfied."""
    of_family = [m for m in members if m.family == constraint.related_family]
    matching = [m for m in of_family if m.status in rule.statuses]
    where = f"slot {constraint.slot!r} ({constraint.related_family})"
    status_set = "/".join(rule.statuses)

    if rule.is_all:
        offending = [m for m in of_family if m.status not in rule.statuses]
        if offending:
            named = ", ".join(f"{m.artifact_id}={m.status}" for m in offending)
            return f"{where}: every related artifact must be {status_set}; found {named}"
        return None
    if rule.is_none:
        if matching:
            named = ", ".join(m.artifact_id for m in matching)
            return f"{where}: no related artifact may be {status_set}; found {named}"
        return None
    count = len(matching)
    if rule.exact is not None and count != rule.exact:
        return f"{where}: requires exactly {rule.exact} artifact(s) at {status_set}; found {count}"
    if rule.min_count is not None and count < rule.min_count:
        return f"{where}: requires at least {rule.min_count} artifact(s) at {status_set}; found {count}"
    if rule.max_count is not None and count > rule.max_count:
        return f"{where}: allows at most {rule.max_count} artifact(s) at {status_set}; found {count}"
    return None


def _evaluate_gate(gate: GateSpec, view: StateView, subject_id: str) -> str | None:
    """Return a failure detail for the gate's decision/evidence posture; None if satisfied."""
    records = view.gate_records(subject_id, gate.gate)
    for record in records:
        if record.status != _APPROVED:
            continue
        if gate.requires_ev and not any(status == _APPROVED for status in record.evidence_statuses):
            continue
        return None
    if not records:
        return (
            f"gate {gate.label}: outcome {gate.outcome_status!r} requires an approved decision record"
            + (" citing at least one approved evidence record" if gate.requires_ev else "")
            + "; found none"
        )
    return f"gate {gate.label}: no decision record for subject {subject_id!r} is approved" + (
        " with at least one approved evidence record cited" if gate.requires_ev else ""
    )
