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

"""Fail-closed loading of the lifecycle bundle (DB-0002 D1, D3).

The bundle is authored in the grammar's published lifecycle-declaration format
(the schema-validated manifest-plus-family-files bundle loaded by the grammar's
``Lifecycle`` API). The runtime authors content only; format and vocabulary
authority stay with the semantic layer. A lifecycle declaration is one coherent
eligibility source: any validation issue refuses the whole bundle — partial
service would decide eligibility inconsistently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping

from lantern.context_policy import Vocabulary

BUNDLE_DIR = "bundle"


def short_name(entity_id: str) -> str:
    """Short name of a grammar entity id: ``lg:artifacts/ch`` -> ``ch``."""
    return entity_id.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class BundleDefect:
    """One named validation failure of the lifecycle bundle."""

    path: str  # location path inside the bundle (declaration-format coordinates)
    message: str

    def render(self) -> str:
        return f"{self.path}: {self.message}"


class LifecycleBundleError(Exception):
    """Strict loading failed. Carries every defect, each naming its location."""

    def __init__(self, defects: tuple[BundleDefect, ...]):
        self.defects = defects
        lines = "\n".join(d.render() for d in defects)
        super().__init__(f"lifecycle bundle has {len(defects)} defect(s):\n{lines}")


@dataclass(frozen=True)
class CardinalityRule:
    """One cardinality predicate over a status set (short names)."""

    statuses: tuple[str, ...]
    exact: int | None = None
    min_count: int | None = None
    max_count: int | None = None
    is_all: bool = False
    is_none: bool = False


@dataclass(frozen=True)
class SlotConstraint:
    """A named slot's constraints: related family + AND-combined cardinality rules."""

    slot: str
    related_family: str
    rules: tuple[CardinalityRule, ...]


@dataclass(frozen=True)
class LifecycleBundle:
    """The loaded lifecycle declarations, normalized to short names; or a refusal."""

    families: tuple[str, ...] = ()
    statuses: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    transitions: Mapping[str, frozenset[tuple[str, str]]] = field(default_factory=dict)
    constraints: Mapping[tuple[str, str], tuple[SlotConstraint, ...]] = field(default_factory=dict)
    defects: tuple[BundleDefect, ...] = ()

    @property
    def is_healthy(self) -> bool:
        return not self.defects

    def statuses_for(self, family: str) -> tuple[str, ...]:
        return self.statuses.get(family, ())

    def transitions_for(self, family: str) -> frozenset[tuple[str, str]]:
        return self.transitions.get(family, frozenset())

    def constraints_for(self, family: str, status: str) -> tuple[SlotConstraint, ...]:
        return self.constraints.get((family, status), ())

    def vocabulary(self) -> Vocabulary:
        """The context-policy layer's injected vocabulary, fed from these declarations."""
        all_statuses: set[str] = set()
        for family_statuses in self.statuses.values():
            all_statuses.update(family_statuses)
        return Vocabulary(families=frozenset(self.families), statuses=frozenset(all_statuses))


def default_bundle_root() -> Path:
    """The shipped bundle location inside the installed package."""
    return Path(str(files("lantern").joinpath("lifecycle").joinpath(BUNDLE_DIR)))


def load_bundle(grammar: Any, bundle_root: Path | None = None) -> LifecycleBundle:
    """Load and validate the bundle at ``bundle_root`` against the loaded grammar.

    Returns a healthy bundle, or a bundle refusing as a whole with every
    validation issue as a named defect. Never raises on content defects.
    """
    from lantern_grammar import Lifecycle

    root = default_bundle_root() if bundle_root is None else bundle_root
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        return LifecycleBundle(defects=(BundleDefect("/manifest", "bundle root has no manifest.yaml"),))
    try:
        lifecycle = Lifecycle.from_manifest(grammar, manifest_path)
    except Exception as exc:  # grammar load errors and I/O problems refuse the bundle
        return LifecycleBundle(defects=(BundleDefect("/manifest", f"bundle failed to load: {exc}"),))

    result = lifecycle.validate()
    if not result.ok:
        defects = tuple(BundleDefect(issue.path, issue.message) for issue in result.issues)
        return LifecycleBundle(defects=defects)

    families: list[str] = []
    statuses: dict[str, tuple[str, ...]] = {}
    transitions: dict[str, frozenset[tuple[str, str]]] = {}
    constraints: dict[tuple[str, str], tuple[SlotConstraint, ...]] = {}
    for family_id in lifecycle.artifact_families():
        family = short_name(family_id)
        families.append(family)
        statuses[family] = tuple(short_name(s.status_id) for s in lifecycle.statuses_for(family_id))
        transitions[family] = frozenset(
            (short_name(t.from_status), short_name(t.to_status)) for t in lifecycle.transitions_for(family_id)
        )
        for state_constraint in lifecycle.state_constraints_for(family_id):
            slots: list[SlotConstraint] = []
            for traversal in state_constraint.traversals:
                rules = tuple(
                    CardinalityRule(
                        statuses=tuple(short_name(s) for s in rule.statuses),
                        exact=rule.cardinality.exact,
                        min_count=rule.cardinality.min_count,
                        max_count=rule.cardinality.max_count,
                        is_all=rule.cardinality.is_all,
                        is_none=rule.cardinality.is_none,
                    )
                    for rule in traversal.rules
                )
                slots.append(
                    SlotConstraint(
                        slot=traversal.slot,
                        related_family=short_name(traversal.related_family_id),
                        rules=rules,
                    )
                )
            constraints[(family, short_name(state_constraint.status_id))] = tuple(slots)

    return LifecycleBundle(
        families=tuple(families),
        statuses=statuses,
        transitions=transitions,
        constraints=constraints,
    )


def load_bundle_strict(grammar: Any, bundle_root: Path | None = None) -> LifecycleBundle:
    """Load the bundle; raise ``LifecycleBundleError`` naming every defect."""
    bundle = load_bundle(grammar, bundle_root)
    if bundle.defects:
        raise LifecycleBundleError(bundle.defects)
    return bundle
