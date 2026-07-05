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

"""Context-policy unit model (lantern.context_policy.unit.v1).

The authored format that owns a transition's operating contract, keyed by
transition pattern (family, current status -> target status). Design baseline:
DB-0001 in the Lantern governance workspace (architecture ARCH-0003).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from lantern.outcomes import BLOCKED_OUTCOME_SCHEMA_ID

UNIT_SCHEMA_ID = "lantern.context_policy.unit.v1"
GROUPING_SCHEMA_ID = "lantern.context_policy.grouping.v1"
CONTRACT_SCHEMA_ID = "lantern.context_policy.contract.v1"
# The blocked payload is the standard shared across the resolution surface.
BLOCKED_SCHEMA_ID = BLOCKED_OUTCOME_SCHEMA_ID
VIEW_HUMAN_TEMPLATE_SCHEMA_ID = "lantern.context_policy.view.human_template.v1"
VIEW_VALIDATION_RULES_SCHEMA_ID = "lantern.context_policy.view.validation_rules.v1"
VIEW_TASK_CARD_SCHEMA_ID = "lantern.context_policy.view.task_card.v1"

# Component kinds with structured, strictly validated payloads. The kind
# vocabulary itself is open: any other identifier-shaped kind is accepted with a
# free mapping payload.
KIND_ARTIFACT_CONTRACT = "artifact_contract"
KIND_AUTHORING_INSTRUCTIONS = "authoring_instructions"
KIND_EVIDENCE_EXPECTATIONS = "evidence_expectations"
KIND_DECISION_POSTURE = "decision_posture"
KIND_VERIFICATION_POSTURE = "verification_posture"

KNOWN_COMPONENT_KINDS = (
    KIND_ARTIFACT_CONTRACT,
    KIND_AUTHORING_INSTRUCTIONS,
    KIND_EVIDENCE_EXPECTATIONS,
    KIND_DECISION_POSTURE,
    KIND_VERIFICATION_POSTURE,
)

PatternKey = tuple[str, str, str]


@dataclass(frozen=True)
class TransitionPattern:
    """A transition pattern: family, current status -> target status."""

    family: str
    from_status: str
    to_status: str

    @property
    def key(self) -> PatternKey:
        return (self.family, self.from_status, self.to_status)

    def label(self) -> str:
        return f"{self.family}: {self.from_status} -> {self.to_status}"

    def as_payload(self) -> dict[str, str]:
        return {
            "family": self.family,
            "from_status": self.from_status,
            "to_status": self.to_status,
        }


@dataclass(frozen=True)
class PolicyComponent:
    """One declared component of a unit: kind, structured payload, prose body."""

    kind: str
    payload: Mapping[str, Any]
    body: str = ""


@dataclass(frozen=True)
class PolicyUnit:
    """A loaded, valid context-policy unit owning one transition pattern."""

    unit_id: str
    version: str
    title: str
    pattern: TransitionPattern
    components: tuple[PolicyComponent, ...]
    content_digest: str  # "sha256:<hex>" over the unit file bytes
    source_name: str  # filename relative to the policy root (diagnostics only)

    def component(self, kind: str) -> PolicyComponent | None:
        for comp in self.components:
            if comp.kind == kind:
                return comp
        return None


@dataclass(frozen=True)
class PolicyGrouping:
    """An optional named grouping: pattern references only, no contract content."""

    grouping_id: str
    title: str
    patterns: tuple[TransitionPattern, ...]
    source_name: str


@dataclass(frozen=True)
class PolicyDefect:
    """One named validation failure. Fail-closed: the affected source never serves."""

    source: str  # unit/grouping filename relative to the policy root
    rule: str  # machine-stable rule id, e.g. "unit.header.missing_field"
    detail: str

    def render(self) -> str:
        return f"{self.source}: [{self.rule}] {self.detail}"


@dataclass(frozen=True)
class Vocabulary:
    """Injected family/status name sets (consumed, never defined here).

    The semantic model remains the grammar's; the lifecycle bundle becomes the
    supplier once it exists. When absent, pattern fields are validated
    syntactically only.
    """

    families: frozenset[str]
    statuses: frozenset[str]


class PolicyLoadError(Exception):
    """Strict loading failed. Carries every defect, each naming its source and rule."""

    def __init__(self, defects: tuple[PolicyDefect, ...]):
        self.defects = defects
        lines = "\n".join(d.render() for d in defects)
        super().__init__(f"context-policy corpus has {len(defects)} defect(s):\n{lines}")


class ViewDriftError(Exception):
    """Delivered derived views do not match regeneration from their units."""

    def __init__(self, findings: tuple[str, ...]):
        self.findings = findings
        lines = "\n".join(findings)
        super().__init__(f"derived views drifted from their units ({len(findings)} finding(s)):\n{lines}")


@dataclass(frozen=True)
class PolicyCorpus:
    """The loaded policy corpus: healthy units by pattern, refusals, defects, groupings.

    A defective or collided pattern appears in ``refused_patterns`` and never in
    ``units_by_pattern``; resolution for it yields a blocked outcome carrying the
    named defects, never a degraded contract.
    """

    units_by_pattern: Mapping[PatternKey, PolicyUnit] = field(default_factory=dict)
    refused_patterns: Mapping[PatternKey, tuple[PolicyDefect, ...]] = field(default_factory=dict)
    defects: tuple[PolicyDefect, ...] = ()
    groupings: tuple[PolicyGrouping, ...] = ()

    @property
    def is_healthy(self) -> bool:
        return not self.defects
