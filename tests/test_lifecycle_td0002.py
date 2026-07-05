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

"""TD-0002 acceptance — lifecycle bundle verification for the ten families.

Mechanism cases run under any installed grammar model (fixture bundles use
families and statuses common to the 0.5 and 1.0 models). Shipped-bundle cases
bind to the Grammar 1.0.0 model and are skipped, with a named reason, under
earlier models; they are executed in a grammar-1.0.0 environment for
verification. Governance: CH-0002 / DB-0002 / CI-0002.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lantern_grammar import Grammar

from lantern.lifecycle import (
    GateRecord,
    GateSpec,
    InMemoryStateView,
    RelatedRef,
    evaluate_transition,
    gates_from_grammar,
    load_bundle_strict,
)
from lantern.outcomes import BLOCKED_OUTCOME_SCHEMA_ID

_GRAMMAR = Grammar.load()
_MODEL = _GRAMMAR.manifest()["model_version"]

requires_model_1 = pytest.mark.skipif(
    _MODEL != "1.0.0",
    reason=f"shipped lifecycle bundle binds to grammar model 1.0.0; installed model is {_MODEL}",
)

_FIXTURE_MANIFEST = """schema_version: "1.0"
grammar_compatibility:
  min_model_version: "0.5.0"
families:
  - spec.yaml
  - td.yaml
  - db.yaml
  - ch.yaml
  - ci.yaml
"""

_FIXTURE_FAMILIES = {
    "spec.yaml": """id: lg:artifacts/spec
statuses:
  - {id: lg:statuses/draft,    label: Draft}
  - {id: lg:statuses/proposed, label: Proposed}
  - {id: lg:statuses/approved, label: Approved}
transitions:
  - {from: lg:statuses/draft,    to: lg:statuses/proposed}
  - {from: lg:statuses/proposed, to: lg:statuses/approved}
state_constraints: []
""",
    "td.yaml": """id: lg:artifacts/td
statuses:
  - {id: lg:statuses/draft,    label: Draft}
  - {id: lg:statuses/proposed, label: Proposed}
  - {id: lg:statuses/approved, label: Approved}
transitions:
  - {from: lg:statuses/draft,    to: lg:statuses/proposed}
  - {from: lg:statuses/proposed, to: lg:statuses/approved}
state_constraints: []
""",
    "db.yaml": """id: lg:artifacts/db
statuses:
  - {id: lg:statuses/draft,     label: Draft}
  - {id: lg:statuses/candidate, label: Candidate}
  - {id: lg:statuses/approved,  label: Approved}
transitions:
  - {from: lg:statuses/draft,     to: lg:statuses/candidate}
  - {from: lg:statuses/candidate, to: lg:statuses/approved}
state_constraints: []
""",
    "ch.yaml": """id: lg:artifacts/ch
statuses:
  - {id: lg:statuses/draft,     label: Draft}
  - {id: lg:statuses/proposed,  label: Proposed}
  - {id: lg:statuses/ready,     label: Ready}
  - {id: lg:statuses/addressed, label: Addressed}
transitions:
  - {from: lg:statuses/draft,    to: lg:statuses/proposed}
  - {from: lg:statuses/proposed, to: lg:statuses/ready}
  - {from: lg:statuses/ready,    to: lg:statuses/addressed}
state_constraints:
  - status: lg:statuses/ready
    rules:
      upstream_tds:
        related_family_id: lg:artifacts/td
        constraints:
          - statuses: [lg:statuses/approved]
            cardinality: {min: 1}
          - statuses: [lg:statuses/approved]
            cardinality: {all: true}
      upstream_specs:
        related_family_id: lg:artifacts/spec
        constraints:
          - statuses: [lg:statuses/approved]
            cardinality: {all: true}
""",
    "ci.yaml": """id: lg:artifacts/ci
statuses:
  - {id: lg:statuses/draft,     label: Draft}
  - {id: lg:statuses/candidate, label: Candidate}
  - {id: lg:statuses/approved,  label: Approved}
  - {id: lg:statuses/verified,  label: Verified}
transitions:
  - {from: lg:statuses/draft,     to: lg:statuses/candidate}
  - {from: lg:statuses/candidate, to: lg:statuses/approved}
  - {from: lg:statuses/approved,  to: lg:statuses/verified}
state_constraints:
  - status: lg:statuses/approved
    rules:
      change_intent:
        related_family_id: lg:artifacts/ch
        constraints:
          - statuses: [lg:statuses/ready, lg:statuses/addressed]
            cardinality: {exact: 1}
      design_baseline:
        related_family_id: lg:artifacts/db
        constraints:
          - statuses: [lg:statuses/approved]
            cardinality: {exact: 1}
""",
}

FIXTURE_GATES = (
    GateSpec(
        gate="gt_110", label="GT-110", subject_family="ch", outcome_status="ready", requires_dec=True, requires_ev=True
    ),
    GateSpec(
        gate="gt_120",
        label="GT-120",
        subject_family="ci",
        outcome_status="approved",
        requires_dec=True,
        requires_ev=True,
    ),
)


def write_fixture_bundle(tmp_path: Path) -> Path:
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "manifest.yaml").write_text(_FIXTURE_MANIFEST, encoding="utf-8")
    for name, text in _FIXTURE_FAMILIES.items():
        (root / name).write_text(text, encoding="utf-8")
    return root


def fixture_bundle(tmp_path: Path):
    return load_bundle_strict(_GRAMMAR, write_fixture_bundle(tmp_path))


def approved_gate_record(gate: str, subject: str) -> dict:
    return {(subject, gate): (GateRecord(decision_id="DEC-X", status="approved", evidence_statuses=("approved",)),)}


class TestTC002EligibilityEnforcedMechanism:
    """TC-002 (mechanism) — undeclared transitions block for every declared family."""

    def test_undeclared_transitions_block_per_family(self, tmp_path: Path) -> None:
        bundle = fixture_bundle(tmp_path)
        view = InMemoryStateView()
        probes = {
            "spec": ("approved", "draft"),
            "td": ("approved", "draft"),
            "db": ("approved", "draft"),
            "ch": ("addressed", "draft"),
            "ci": ("verified", "draft"),
        }
        assert set(probes) == set(bundle.families)
        for family, (from_status, to_status) in probes.items():
            outcome = evaluate_transition(bundle, FIXTURE_GATES, view, family, from_status, to_status, "X-1")
            assert outcome["schema_id"] == BLOCKED_OUTCOME_SCHEMA_ID, family
            assert outcome["blocked"] is True and not outcome.get("eligible"), family
            assert any(r["code"] == "undeclared_transition" for r in outcome["reasons"]), family


class TestTC003BlockedOutcomesEnumerateMechanism:
    """TC-003 (mechanism) — several failed constraints, one outcome naming each."""

    def test_multi_constraint_failure_is_one_outcome(self, tmp_path: Path) -> None:
        bundle = fixture_bundle(tmp_path)
        view = InMemoryStateView(
            slot_members={
                ("CH-9", "upstream_tds"): (),
                ("CH-9", "upstream_specs"): (RelatedRef("SPEC-1", "spec", "proposed"),),
            },
        )
        outcome = evaluate_transition(bundle, FIXTURE_GATES, view, "ch", "proposed", "ready", "CH-9")

        assert outcome["schema_id"] == BLOCKED_OUTCOME_SCHEMA_ID
        details = "\n".join(r["detail"] for r in outcome["reasons"])
        codes = [r["code"] for r in outcome["reasons"]]
        assert codes.count("state_constraint") == 2 and codes.count("gate_evidence") == 1
        assert "upstream_tds" in details and "at least 1" in details
        assert "upstream_specs" in details and "SPEC-1=proposed" in details
        assert "GT-110" in details


class TestTC004CrossArtifactMechanism:
    """TC-004 (mechanism twins) — declared constraints fire, and only they block."""

    def test_readiness_without_approved_td_blocks(self, tmp_path: Path) -> None:
        bundle = fixture_bundle(tmp_path)
        view = InMemoryStateView(
            slot_members={("CH-9", "upstream_specs"): (RelatedRef("SPEC-1", "spec", "approved"),)},
            decisions=approved_gate_record("gt_110", "CH-9"),
        )
        outcome = evaluate_transition(bundle, FIXTURE_GATES, view, "ch", "proposed", "ready", "CH-9")
        assert [r["code"] for r in outcome["reasons"]] == ["state_constraint"]
        assert "upstream_tds" in outcome["reasons"][0]["detail"]

    def test_ci_approval_against_non_approved_db_blocks(self, tmp_path: Path) -> None:
        bundle = fixture_bundle(tmp_path)
        view = InMemoryStateView(
            slot_members={
                ("CI-9", "change_intent"): (RelatedRef("CH-9", "ch", "ready"),),
                ("CI-9", "design_baseline"): (RelatedRef("DB-9", "db", "candidate"),),
            },
            decisions=approved_gate_record("gt_120", "CI-9"),
        )
        outcome = evaluate_transition(bundle, FIXTURE_GATES, view, "ci", "candidate", "approved", "CI-9")
        assert [r["code"] for r in outcome["reasons"]] == ["state_constraint"]
        assert "design_baseline" in outcome["reasons"][0]["detail"]

    def test_gate_decision_without_evidence_blocks(self, tmp_path: Path) -> None:
        bundle = fixture_bundle(tmp_path)
        view = InMemoryStateView(
            slot_members={
                ("CH-9", "upstream_tds"): (RelatedRef("TD-1", "td", "approved"),),
                ("CH-9", "upstream_specs"): (RelatedRef("SPEC-1", "spec", "approved"),),
            },
            decisions={("CH-9", "gt_110"): (GateRecord("DEC-9", "approved", evidence_statuses=()),)},
        )
        outcome = evaluate_transition(bundle, FIXTURE_GATES, view, "ch", "proposed", "ready", "CH-9")
        assert [r["code"] for r in outcome["reasons"]] == ["gate_evidence"]
        assert "GT-110" in outcome["reasons"][0]["detail"]

    def test_satisfied_declarations_are_eligible(self, tmp_path: Path) -> None:
        bundle = fixture_bundle(tmp_path)
        view = InMemoryStateView(
            slot_members={
                ("CH-9", "upstream_tds"): (RelatedRef("TD-1", "td", "approved"),),
                ("CH-9", "upstream_specs"): (RelatedRef("SPEC-1", "spec", "approved"),),
            },
            decisions=approved_gate_record("gt_110", "CH-9"),
        )
        outcome = evaluate_transition(bundle, FIXTURE_GATES, view, "ch", "proposed", "ready", "CH-9")
        assert outcome == {
            "schema_id": "lantern.lifecycle.eligible.v1",
            "eligible": True,
            "pattern": {"family": "ch", "from_status": "proposed", "to_status": "ready"},
            "subject": "CH-9",
        }


class TestTC005NoExtraSequencingMechanism:
    """TC-005 — two eligible transitions administer identically in both orders."""

    def test_both_orders_succeed_identically(self, tmp_path: Path) -> None:
        bundle = fixture_bundle(tmp_path)

        def make_view() -> InMemoryStateView:
            return InMemoryStateView(
                slot_members={
                    ("CH-A", "upstream_tds"): (RelatedRef("TD-1", "td", "approved"),),
                    ("CH-A", "upstream_specs"): (),
                    ("CH-B", "upstream_tds"): (RelatedRef("TD-2", "td", "approved"),),
                    ("CH-B", "upstream_specs"): (),
                },
                decisions={
                    **approved_gate_record("gt_110", "CH-A"),
                    **approved_gate_record("gt_110", "CH-B"),
                },
            )

        def administer(order: list[str]) -> list[dict]:
            view = make_view()
            results = []
            for subject in order:
                results.append(evaluate_transition(bundle, FIXTURE_GATES, view, "ch", "proposed", "ready", subject))
            return results

        first = administer(["CH-A", "CH-B"])
        second = administer(["CH-B", "CH-A"])
        assert all(r["eligible"] is True for r in first + second)
        by_subject_first = {r["subject"]: r for r in first}
        by_subject_second = {r["subject"]: r for r in second}
        assert by_subject_first == by_subject_second


@requires_model_1
class TestTC001ShippedBundleGrammarBound:
    """TC-001 — the shipped ten-family bundle is grammar-bound (Grammar 1.0.0)."""

    def test_ten_families_grammar_statuses_and_interim_bindings(self) -> None:
        bundle = load_bundle_strict(_GRAMMAR)
        assert sorted(bundle.families) == sorted(
            ["initiative", "spec", "arch", "db", "td", "ch", "ci", "issue", "dec", "ev"]
        )
        grammar_statuses = {
            entity["id"].rsplit("/", 1)[1]
            for entity in _GRAMMAR.iter_entities()
            if entity["id"].startswith("lg:statuses/")
        }
        for family in bundle.families:
            assert set(bundle.statuses_for(family)) <= grammar_statuses, family

        interim_bindings = {
            "initiative": {"draft", "in_progress", "concluded"},
            "spec": {"draft", "proposed", "approved", "superseded", "rejected"},
            "arch": {"draft", "proposed", "approved", "superseded", "rejected"},
            "db": {"draft", "candidate", "approved", "superseded", "rejected"},
            "td": {"draft", "proposed", "approved", "superseded", "rejected"},
            "ch": {"draft", "proposed", "ready", "addressed", "rejected", "superseded"},
            "ci": {"draft", "candidate", "approved", "verified", "rejected", "superseded"},
            "issue": {"new", "needs_info", "accepted", "deferred", "resolved", "rejected"},
            "dec": {"draft", "approved", "superseded"},
            "ev": {"draft", "approved", "superseded"},
        }
        for family, expected in interim_bindings.items():
            assert set(bundle.statuses_for(family)) == expected, family


@requires_model_1
class TestTC002ShippedTenFamilies:
    """TC-002 — an undeclared transition blocks in every one of the ten families."""

    def test_undeclared_transition_blocks_everywhere(self) -> None:
        bundle = load_bundle_strict(_GRAMMAR)
        gates = gates_from_grammar(_GRAMMAR)
        view = InMemoryStateView()
        probes = {
            "initiative": ("concluded", "draft"),
            "spec": ("approved", "draft"),
            "arch": ("approved", "draft"),
            "db": ("approved", "draft"),
            "td": ("approved", "draft"),
            "ch": ("addressed", "draft"),
            "ci": ("verified", "draft"),
            "issue": ("resolved", "new"),
            "dec": ("superseded", "draft"),
            "ev": ("superseded", "draft"),
        }
        assert set(probes) == set(bundle.families)
        for family, (from_status, to_status) in probes.items():
            outcome = evaluate_transition(bundle, gates, view, family, from_status, to_status, "X-1")
            assert outcome.get("blocked") is True, family
            assert any(r["code"] == "undeclared_transition" for r in outcome["reasons"]), family


@requires_model_1
class TestTC003ShippedMultiConstraint:
    """TC-003 — one shipped-declaration transition failing several constraints at once."""

    def test_single_outcome_names_every_failed_constraint(self) -> None:
        bundle = load_bundle_strict(_GRAMMAR)
        gates = gates_from_grammar(_GRAMMAR)
        view = InMemoryStateView(
            slot_members={
                ("CH-77", "upstream_tds"): (),
                ("CH-77", "upstream_specs"): (RelatedRef("SPEC-0001", "spec", "proposed"),),
                ("CH-77", "upstream_archs"): (RelatedRef("ARCH-0001", "arch", "approved"),),
            },
        )
        outcome = evaluate_transition(bundle, gates, view, "ch", "proposed", "ready", "CH-77")
        codes = [r["code"] for r in outcome["reasons"]]
        details = "\n".join(r["detail"] for r in outcome["reasons"])
        assert codes.count("state_constraint") == 2 and codes.count("gate_evidence") == 1
        assert "upstream_tds" in details and "upstream_specs" in details and "GT-110" in details


@requires_model_1
class TestTC004ShippedCrossArtifact:
    """TC-004 — the interim workspace rules fire from the shipped declarations."""

    def _bundle_and_gates(self):
        return load_bundle_strict(_GRAMMAR), gates_from_grammar(_GRAMMAR)

    def test_ch_readiness_without_approved_td(self) -> None:
        bundle, gates = self._bundle_and_gates()
        view = InMemoryStateView(
            slot_members={
                ("CH-77", "upstream_specs"): (RelatedRef("SPEC-0001", "spec", "approved"),),
                ("CH-77", "upstream_archs"): (RelatedRef("ARCH-0001", "arch", "approved"),),
                ("CH-77", "upstream_tds"): (),
            },
            decisions=approved_gate_record("gt_110", "CH-77"),
        )
        outcome = evaluate_transition(bundle, gates, view, "ch", "proposed", "ready", "CH-77")
        assert [r["code"] for r in outcome["reasons"]] == ["state_constraint"]
        assert "upstream_tds" in outcome["reasons"][0]["detail"]

    def test_ci_approval_against_non_approved_db(self) -> None:
        bundle, gates = self._bundle_and_gates()
        view = InMemoryStateView(
            slot_members={
                ("CI-77", "change_intent"): (RelatedRef("CH-77", "ch", "ready"),),
                ("CI-77", "design_baseline"): (RelatedRef("DB-77", "db", "candidate"),),
            },
            decisions=approved_gate_record("gt_120", "CI-77"),
        )
        outcome = evaluate_transition(bundle, gates, view, "ci", "candidate", "approved", "CI-77")
        assert [r["code"] for r in outcome["reasons"]] == ["state_constraint"]
        assert "design_baseline" in outcome["reasons"][0]["detail"]

    def test_gate_decision_citing_no_evidence(self) -> None:
        bundle, gates = self._bundle_and_gates()
        view = InMemoryStateView(
            slot_members={
                ("CH-77", "upstream_specs"): (RelatedRef("SPEC-0001", "spec", "approved"),),
                ("CH-77", "upstream_archs"): (RelatedRef("ARCH-0001", "arch", "approved"),),
                ("CH-77", "upstream_tds"): (RelatedRef("TD-0001", "td", "approved"),),
            },
            decisions={("CH-77", "gt_110"): (GateRecord("DEC-77", "approved", evidence_statuses=()),)},
        )
        outcome = evaluate_transition(bundle, gates, view, "ch", "proposed", "ready", "CH-77")
        assert [r["code"] for r in outcome["reasons"]] == ["gate_evidence"]
        assert "GT-110" in outcome["reasons"][0]["detail"]

    def test_satisfied_shipped_declarations_are_eligible(self) -> None:
        bundle, gates = self._bundle_and_gates()
        view = InMemoryStateView(
            slot_members={
                ("CH-77", "upstream_specs"): (RelatedRef("SPEC-0001", "spec", "approved"),),
                ("CH-77", "upstream_archs"): (RelatedRef("ARCH-0001", "arch", "approved"),),
                ("CH-77", "upstream_tds"): (RelatedRef("TD-0001", "td", "approved"),),
            },
            decisions=approved_gate_record("gt_110", "CH-77"),
        )
        outcome = evaluate_transition(bundle, gates, view, "ch", "proposed", "ready", "CH-77")
        assert outcome.get("eligible") is True
