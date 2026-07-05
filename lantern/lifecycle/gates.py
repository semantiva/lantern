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

"""Gate specifications derived from the released grammar (DB-0002 D4).

Grammar 1.0.0 gates are outcome-locked: each gate entity's relations encode its
subject family (``requires_input.<family>``), outcome status
(``requires_status.<status>``), and evidence posture (``requires_evidence.dec``
/ ``requires_evidence.ev``). Deriving gate specs from those entities keeps the
semantic layer the single authority — no gate table is restated here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_GATE_ID_PREFIX = "lg:gates/"


@dataclass(frozen=True)
class GateSpec:
    """One gate's outcome lock: subject family, outcome status, evidence posture."""

    gate: str  # short name, e.g. "gt_110"
    label: str  # display form, e.g. "GT-110"
    subject_family: str
    outcome_status: str
    requires_dec: bool
    requires_ev: bool


def gates_from_grammar(grammar: Any) -> tuple[GateSpec, ...]:
    """Derive every gate's spec from the loaded grammar's gate entities."""
    specs: list[GateSpec] = []
    for entity in grammar.iter_entities():
        entity_id = entity.get("id", "")
        if not entity_id.startswith(_GATE_ID_PREFIX):
            continue
        gate = entity_id.rsplit("/", 1)[-1]
        subject_family = ""
        outcome_status = ""
        requires_dec = False
        requires_ev = False
        for relation_id in entity.get("relation_ids", ()):
            parts = relation_id.rsplit("/", 1)[-1].split(".")
            if len(parts) != 3:
                continue
            _gate, kind, target = parts
            if kind == "requires_input":
                subject_family = target
            elif kind == "requires_status":
                outcome_status = target
            elif kind == "requires_evidence":
                requires_dec = requires_dec or target == "dec"
                requires_ev = requires_ev or target == "ev"
        specs.append(
            GateSpec(
                gate=gate,
                label=gate.upper().replace("_", "-"),
                subject_family=subject_family,
                outcome_status=outcome_status,
                requires_dec=requires_dec,
                requires_ev=requires_ev,
            )
        )
    return tuple(sorted(specs, key=lambda s: s.gate))


def gates_by_outcome(gates: tuple[GateSpec, ...]) -> dict[tuple[str, str], tuple[GateSpec, ...]]:
    """Index gate specs by (subject family, outcome status)."""
    index: dict[tuple[str, str], tuple[GateSpec, ...]] = {}
    for spec in gates:
        key = (spec.subject_family, spec.outcome_status)
        index[key] = index.get(key, ()) + (spec,)
    return index
