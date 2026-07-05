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

"""The state view consumed by eligibility evaluation (DB-0002 D5).

Eligibility is decided solely from declarations plus this view of the governed
state. Binding slots to a concrete corpus is an adapter's concern, not policy;
the in-memory implementation serves tests and the manual-administration flip.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol


@dataclass(frozen=True)
class RelatedRef:
    """A related artifact as seen through a constraint slot."""

    artifact_id: str
    family: str
    status: str


@dataclass(frozen=True)
class GateRecord:
    """A decision record for (subject, gate): its status and cited-evidence statuses."""

    decision_id: str
    status: str
    evidence_statuses: tuple[str, ...] = ()


class StateView(Protocol):
    """Protocol supplying slot members and gate records for a subject artifact."""

    def related(self, subject_id: str, slot: str) -> tuple[RelatedRef, ...]: ...

    def gate_records(self, subject_id: str, gate: str) -> tuple[GateRecord, ...]: ...


@dataclass(frozen=True)
class InMemoryStateView:
    """Dict-backed state view: {(subject, slot): refs}, {(subject, gate): records}."""

    slot_members: Mapping[tuple[str, str], tuple[RelatedRef, ...]] = field(default_factory=dict)
    decisions: Mapping[tuple[str, str], tuple[GateRecord, ...]] = field(default_factory=dict)

    def related(self, subject_id: str, slot: str) -> tuple[RelatedRef, ...]:
        return self.slot_members.get((subject_id, slot), ())

    def gate_records(self, subject_id: str, gate: str) -> tuple[GateRecord, ...]:
        return self.decisions.get((subject_id, gate), ())
