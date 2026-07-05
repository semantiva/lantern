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

"""TD-0001 acceptance — context-policy unit format and projection verification.

One test per TD-0001 case (TC-001 … TC-005), against the lantern.context_policy
public API. Governance: CH-0001 / DB-0001 / CI-0001.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lantern.context_policy import (
    BLOCKED_SCHEMA_ID,
    CONTRACT_SCHEMA_ID,
    PolicyLoadError,
    ViewDriftError,
    assert_views_derived,
    assert_views_derived_strict,
    expected_views,
    load_corpus,
    load_corpus_strict,
    resolve,
    resolve_bytes,
    write_derived_views,
)

VALID_UNIT = """```yaml
schema_id: lantern.context_policy.unit.v1
unit_id: cp.ch.draft--proposed
version: "1"
title: "Change-intent authoring: draft -> proposed"
pattern:
  family: ch
  from_status: draft
  to_status: proposed
components:
  - kind: artifact_contract
    required_header_keys: [id, title, status]
    required_sections: ["Problem", "Scope"]
    obligations:
      - "Scope states its boundary and exclusions."
  - kind: authoring_instructions
    required_inputs:
      - "The motivating initiative or issue"
    scope_boundary: "Author the change-intent body only."
    stop_condition: "Every required section is non-placeholder."
    deliverables:
      - "Change intent at proposed"
    forbidden_actions:
      - "Do not administer gates from this transition."
  - kind: evidence_expectations
    expectations:
      - "Cited upstream baselines exist and are approved."
  - kind: decision_posture
    authority: explicit_human_approval
  - kind: verification_posture
    retention: "Acceptance evidence is retained with the increment record."
```

## authoring_instructions

Derive the problem statement from the motivating input; state scope and
exclusions; keep every constraint checkable.
"""


def make_root(tmp_path: Path) -> Path:
    root = tmp_path / "policy"
    (root / "units").mkdir(parents=True)
    return root


def write_unit(root: Path, name: str = "cp.ch.draft--proposed.md", text: str = VALID_UNIT) -> None:
    (root / "units" / name).write_text(text, encoding="utf-8")


class TestTC001MalformedUnitsFailClosed:
    """TC-001 — a schema-violating unit refuses to serve, naming the defect."""

    def test_missing_required_header_field(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root, text=VALID_UNIT.replace('title: "Change-intent authoring: draft -> proposed"\n', ""))
        corpus = load_corpus(root)

        assert any(d.rule == "unit.header.title" for d in corpus.defects)
        outcome = resolve(corpus, "ch", "draft", "proposed")
        assert outcome["schema_id"] == BLOCKED_SCHEMA_ID and outcome["blocked"] is True
        assert any(r["code"] == "unit_invalid" and "title" in r["detail"] for r in outcome["reasons"])
        # No degraded or partial contract: the blocked outcome carries no contract content.
        assert "components" not in outcome and "views" not in outcome and "unit" not in outcome

        with pytest.raises(PolicyLoadError) as exc:
            load_corpus_strict(root)
        assert "unit.header.title" in str(exc.value)

    def test_undeclared_component_kind_reference(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root, text=VALID_UNIT + "\n## rogue_kind\n\nProse belonging to no declared component.\n")
        corpus = load_corpus(root)

        assert any(d.rule == "unit.body.undeclared_component" and "rogue_kind" in d.detail for d in corpus.defects)
        outcome = resolve(corpus, "ch", "draft", "proposed")
        assert outcome["schema_id"] == BLOCKED_SCHEMA_ID
        assert any("rogue_kind" in r["detail"] for r in outcome["reasons"])


class TestTC002ProjectionIsDeterministic:
    """TC-002 — same transition, fixed sources: byte-identical contracts (REQ-0004)."""

    def test_repeated_resolution_is_byte_identical(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)

        first = resolve_bytes(load_corpus(root), "ch", "draft", "proposed")
        second = resolve_bytes(load_corpus(root), "ch", "draft", "proposed")
        assert first == second

        corpus = load_corpus(root)
        assert resolve_bytes(corpus, "ch", "draft", "proposed") == first
        assert first.startswith(b'{"components":')


class TestTC003DerivedViewsAreAssertedDerived:
    """TC-003 — views regenerate identically; a manual edit fails validation (REQ-0009)."""

    def test_regenerated_views_match_and_manual_edit_fails(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        corpus = load_corpus_strict(root)
        out_dir = tmp_path / "delivered"

        written = write_derived_views(corpus, out_dir)
        assert written == [
            "cp.ch.draft--proposed.task_card.json",
            "cp.ch.draft--proposed.template.md",
            "cp.ch.draft--proposed.validation_rules.json",
        ]
        # Regenerated views match the delivered views byte for byte.
        for name, content in expected_views(corpus).items():
            assert (out_dir / name).read_bytes() == content
        assert assert_views_derived(corpus, out_dir) == ()

        # A manual edit into a delivered view fails validation mechanically.
        template = out_dir / "cp.ch.draft--proposed.template.md"
        template.write_text(template.read_text(encoding="utf-8") + "\nManually added guidance.\n", encoding="utf-8")
        findings = assert_views_derived(corpus, out_dir)
        assert len(findings) == 1
        assert "drifted view" in findings[0] and "cp.ch.draft--proposed.template.md" in findings[0]
        with pytest.raises(ViewDriftError):
            assert_views_derived_strict(corpus, out_dir)


class TestTC004OneUnitOwnsOnePattern:
    """TC-004 — a second unit on the same pattern fails loading; neither serves (REQ-0008)."""

    def test_pattern_collision_refuses_both_units(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        write_unit(
            root,
            name="cp.ch.alternate.md",
            text=VALID_UNIT.replace("unit_id: cp.ch.draft--proposed", "unit_id: cp.ch.alternate"),
        )
        corpus = load_corpus(root)

        collision = [d for d in corpus.defects if d.rule == "unit.pattern.collision"]
        assert len(collision) == 1
        assert "cp.ch.draft--proposed.md" in collision[0].detail and "cp.ch.alternate.md" in collision[0].detail

        # Neither unit serves: the pattern is refused, not silently won.
        assert ("ch", "draft", "proposed") not in corpus.units_by_pattern
        outcome = resolve(corpus, "ch", "draft", "proposed")
        assert outcome["schema_id"] == BLOCKED_SCHEMA_ID
        assert any(r["code"] == "pattern_collision" for r in outcome["reasons"])

        with pytest.raises(PolicyLoadError) as exc:
            load_corpus_strict(root)
        assert "unit.pattern.collision" in str(exc.value)


class TestTC005SingleCoveredTransitionIsOperableAlone:
    """TC-005 — one covered pattern gives full resolution behavior (REQ-0005)."""

    def test_single_unit_corpus_full_behavior(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)

        # Loading demands nothing beyond the one unit: no vocabulary, no
        # groupings, no coverage of any other family or transition.
        corpus = load_corpus(root)
        assert corpus.is_healthy and len(corpus.units_by_pattern) == 1

        # Contract delivery on the covered transition.
        contract = resolve(corpus, "ch", "draft", "proposed")
        assert contract["schema_id"] == CONTRACT_SCHEMA_ID
        assert contract["unit"]["unit_id"] == "cp.ch.draft--proposed"
        assert [c["kind"] for c in contract["components"]] == [
            "artifact_contract",
            "authoring_instructions",
            "evidence_expectations",
            "decision_posture",
            "verification_posture",
        ]
        views = contract["views"]
        assert views["task_card"]["view_schema_id"] == "lantern.context_policy.view.task_card.v1"
        assert views["validation_rules"]["rules"]["required_sections"] == ["Problem", "Scope"]
        assert views["human_template"].startswith("<!-- derived view:")

        # Blocked outcome on an uncovered transition: first-class, named reason.
        blocked = resolve(corpus, "spec", "draft", "proposed")
        assert blocked["schema_id"] == BLOCKED_SCHEMA_ID and blocked["blocked"] is True
        assert blocked["reasons"] == [
            {"code": "uncovered_pattern", "detail": "no context-policy unit covers pattern (spec: draft -> proposed)"}
        ]
