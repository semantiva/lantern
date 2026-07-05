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

"""Format-level tests for the lifecycle layer (DB-0002 D1, D3, D4, D6).

Fail-closed whole-bundle refusal, gate-spec derivation from the grammar, the
vocabulary bridge into the context-policy layer, and the standardized
blocked-outcome payload shared by both layers.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from lantern_grammar import Grammar

from lantern.context_policy import BLOCKED_SCHEMA_ID
from lantern.lifecycle import (
    InMemoryStateView,
    LifecycleBundleError,
    evaluate_transition,
    gates_from_grammar,
    load_bundle,
    load_bundle_strict,
)
from lantern.outcomes import BLOCKED_OUTCOME_SCHEMA_ID

from test_lifecycle_td0002 import FIXTURE_GATES, write_fixture_bundle

_GRAMMAR = Grammar.load()
_MODEL = _GRAMMAR.manifest()["model_version"]

requires_model_1 = pytest.mark.skipif(
    _MODEL != "1.0.0",
    reason=f"shipped lifecycle bundle binds to grammar model 1.0.0; installed model is {_MODEL}",
)


class TestFailClosedBundle:
    def test_unknown_status_refuses_whole_bundle(self, tmp_path: Path) -> None:
        root = write_fixture_bundle(tmp_path)
        spec = root / "spec.yaml"
        spec.write_text(
            spec.read_text(encoding="utf-8").replace("lg:statuses/proposed", "lg:statuses/nonexistent"),
            encoding="utf-8",
        )
        bundle = load_bundle(_GRAMMAR, root)
        assert not bundle.is_healthy
        assert any("nonexistent" in d.message for d in bundle.defects)
        assert bundle.families == ()

        # Any transition — even in an unaffected family — refuses to serve.
        outcome = evaluate_transition(bundle, FIXTURE_GATES, InMemoryStateView(), "td", "draft", "proposed", "TD-1")
        assert outcome["schema_id"] == BLOCKED_OUTCOME_SCHEMA_ID
        assert all(r["code"] == "bundle_invalid" for r in outcome["reasons"])

        with pytest.raises(LifecycleBundleError) as exc:
            load_bundle_strict(_GRAMMAR, root)
        assert "nonexistent" in str(exc.value)

    def test_missing_manifest_is_a_defect(self, tmp_path: Path) -> None:
        bundle = load_bundle(_GRAMMAR, tmp_path)
        assert not bundle.is_healthy
        assert any("manifest" in d.render() for d in bundle.defects)

    def test_undeclared_family_and_status_block(self, tmp_path: Path) -> None:
        bundle = load_bundle_strict(_GRAMMAR, write_fixture_bundle(tmp_path))
        view = InMemoryStateView()
        no_family = evaluate_transition(bundle, FIXTURE_GATES, view, "issue", "new", "accepted", "IS-1")
        assert [r["code"] for r in no_family["reasons"]] == ["undeclared_family"]
        no_status = evaluate_transition(bundle, FIXTURE_GATES, view, "spec", "draft", "verified", "SPEC-1")
        assert [r["code"] for r in no_status["reasons"]] == ["undeclared_status"]


class TestBlockedOutcomeStandardization:
    def test_one_blocked_schema_across_layers(self) -> None:
        assert BLOCKED_SCHEMA_ID == BLOCKED_OUTCOME_SCHEMA_ID == "lantern.blocked_outcome.v1"


class TestGateDerivation:
    def test_gate_specs_parse_from_any_model(self) -> None:
        gates = gates_from_grammar(_GRAMMAR)
        assert gates, "grammar declares gate entities"
        for spec in gates:
            assert spec.subject_family and spec.outcome_status, spec.gate

    @requires_model_1
    def test_six_outcome_locked_gates(self) -> None:
        gates = gates_from_grammar(_GRAMMAR)
        locks = {(s.label, s.subject_family, s.outcome_status) for s in gates}
        assert locks == {
            ("GT-050", "spec", "approved"),
            ("GT-060", "arch", "approved"),
            ("GT-110", "ch", "ready"),
            ("GT-115", "db", "approved"),
            ("GT-120", "ci", "approved"),
            ("GT-130", "ci", "verified"),
        }
        assert all(s.requires_dec and s.requires_ev for s in gates)


@requires_model_1
class TestVocabularyBridge:
    def test_shipped_bundle_feeds_context_policy_vocabulary(self) -> None:
        bundle = load_bundle_strict(_GRAMMAR)
        vocabulary = bundle.vocabulary()
        assert len(vocabulary.families) == 10
        assert len(vocabulary.statuses) == 16
        assert {"ch", "dec", "ev"} <= vocabulary.families
        assert {"ready", "needs_info", "superseded"} <= vocabulary.statuses
        assert "selected" not in vocabulary.statuses
