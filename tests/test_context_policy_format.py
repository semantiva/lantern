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

"""Format-level tests for the context-policy unit schema, groupings, and vocabulary seam.

Complements the TD-0001 acceptance suite with per-rule coverage of the unit
header schema, known component-kind payloads, the body-binding discipline,
grouping validation, and the injected-vocabulary seam (DB-0001 D1–D3, D6).
"""

from __future__ import annotations

from pathlib import Path

from lantern.context_policy import (
    BLOCKED_SCHEMA_ID,
    CONTRACT_SCHEMA_ID,
    Vocabulary,
    assert_views_derived,
    load_corpus,
    resolve,
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

VALID_GROUPING = """schema_id: lantern.context_policy.grouping.v1
grouping_id: authoring-desk
title: "Authoring desk"
patterns:
  - family: ch
    from_status: draft
    to_status: proposed
"""


def make_root(tmp_path: Path) -> Path:
    root = tmp_path / "policy"
    (root / "units").mkdir(parents=True)
    return root


def write_unit(root: Path, name: str = "cp.ch.draft--proposed.md", text: str = VALID_UNIT) -> None:
    (root / "units" / name).write_text(text, encoding="utf-8")


def write_grouping(root: Path, name: str = "authoring-desk.yaml", text: str = VALID_GROUPING) -> None:
    groupings = root / "groupings"
    groupings.mkdir(exist_ok=True)
    (groupings / name).write_text(text, encoding="utf-8")


def rules_for(root: Path) -> set[str]:
    return {d.rule for d in load_corpus(root).defects}


class TestUnitHeaderSchema:
    def test_unknown_top_level_field_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root, text=VALID_UNIT.replace("components:", "workbench: legacy\ncomponents:"))
        assert "unit.header.unknown_field" in rules_for(root)

    def test_wrong_schema_id_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(
            root, text=VALID_UNIT.replace("lantern.context_policy.unit.v1", "lantern.operator.workbench_charter.v1")
        )
        assert "unit.header.schema_id" in rules_for(root)

    def test_pattern_field_syntax_enforced(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root, text=VALID_UNIT.replace("family: ch", "family: CH"))
        assert "unit.pattern.field" in rules_for(root)

    def test_pattern_unknown_field_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root, text=VALID_UNIT.replace("  family: ch", "  workbench: intake\n  family: ch"))
        assert "unit.pattern.unknown_field" in rules_for(root)

    def test_filename_must_match_unit_id(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root, name="misnamed.md")
        assert "unit.filename" in rules_for(root)

    def test_stray_body_content_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(
            root, text=VALID_UNIT.replace("\n## authoring_instructions", "\nStray prose.\n\n## authoring_instructions")
        )
        assert "unit.body.stray_content" in rules_for(root)

    def test_duplicate_component_kind_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        extra = '  - kind: evidence_expectations\n    expectations:\n      - "Twice."\n'
        write_unit(root, text=VALID_UNIT.replace("  - kind: decision_posture", extra + "  - kind: decision_posture"))
        assert "unit.component.duplicate_kind" in rules_for(root)

    def test_non_json_payload_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(
            root,
            text=VALID_UNIT.replace(
                "  - kind: decision_posture\n    authority: explicit_human_approval\n",
                "  - kind: review_window\n    opens_on: 2026-07-05\n",
            ),
        )
        assert "unit.component.payload_not_json" in rules_for(root)


class TestKnownComponentKinds:
    def test_authoring_instructions_body_required(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root, text=VALID_UNIT.split("\n## authoring_instructions")[0] + "\n")
        assert "unit.component.body_required" in rules_for(root)

    def test_artifact_contract_unknown_field_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(
            root,
            text=VALID_UNIT.replace(
                "    required_header_keys:", "    downstream_gate_behavior: enforce\n    required_header_keys:"
            ),
        )
        assert "unit.component.unknown_field" in rules_for(root)

    def test_artifact_contract_must_state_something(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        text = VALID_UNIT.replace(
            """  - kind: artifact_contract
    required_header_keys: [id, title, status]
    required_sections: ["Problem", "Scope"]
    obligations:
      - "Scope states its boundary and exclusions."
""",
            "  - kind: artifact_contract\n",
        )
        write_unit(root, text=text)
        assert "unit.component.empty_contract" in rules_for(root)

    def test_evidence_expectations_must_be_non_empty(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        text = VALID_UNIT.replace(
            '    expectations:\n      - "Cited upstream baselines exist and are approved."\n',
            "    expectations: []\n",
        )
        write_unit(root, text=text)
        assert "unit.component.field" in rules_for(root)

    def test_bounded_authorization_requires_scope_and_stop_conditions(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(
            root, text=VALID_UNIT.replace("authority: explicit_human_approval", "authority: bounded_authorization")
        )
        corpus = load_corpus(root)
        details = [d.detail for d in corpus.defects if d.rule == "unit.component.field"]
        assert any("'scope'" in d for d in details) and any("'stop_conditions'" in d for d in details)

    def test_bounded_authorization_with_scope_and_stop_conditions_is_healthy(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        bounded = (
            "authority: bounded_authorization\n"
            '    scope: "Administer this gate outcome for the cited subject only."\n'
            "    stop_conditions:\n"
            '      - "Any validation failure."\n'
        )
        write_unit(root, text=VALID_UNIT.replace("authority: explicit_human_approval", bounded))
        assert load_corpus(root).is_healthy

    def test_explicit_approval_forbids_bounded_fields(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(
            root,
            text=VALID_UNIT.replace(
                "authority: explicit_human_approval",
                'authority: explicit_human_approval\n    scope: "Not applicable."',
            ),
        )
        assert "unit.component.authority" in rules_for(root)

    def test_verification_posture_requires_retention(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(
            root,
            text=VALID_UNIT.replace(
                '    retention: "Acceptance evidence is retained with the increment record."',
                '    replacement_discipline:\n      - "Replaced tests are named in the increment."',
            ),
        )
        assert "unit.component.field" in rules_for(root)

    def test_open_kind_accepted_with_free_payload_and_body(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        text = VALID_UNIT.replace(
            "```\n\n## authoring_instructions",
            '  - kind: escalation_paths\n    contacts:\n      - "governance owner"\n```\n\n## escalation_paths\n\nEscalate on any authority ambiguity.\n\n## authoring_instructions',
        )
        write_unit(root, text=text)
        corpus = load_corpus(root)
        assert corpus.is_healthy
        contract = resolve(corpus, "ch", "draft", "proposed")
        assert contract["schema_id"] == CONTRACT_SCHEMA_ID
        open_components = [c for c in contract["components"] if c["kind"] == "escalation_paths"]
        assert open_components == [
            {
                "kind": "escalation_paths",
                "payload": {"contacts": ["governance owner"]},
                "body": "Escalate on any authority ambiguity.",
            }
        ]
        assert "escalation_paths" in contract["views"]["task_card"]["component_kinds"]


class TestVocabularySeam:
    def test_vocabulary_membership_enforced_when_supplied(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        vocabulary = Vocabulary(families=frozenset({"spec"}), statuses=frozenset({"draft"}))
        corpus = load_corpus(root, vocabulary)
        rules = {d.rule for d in corpus.defects}
        assert "unit.pattern.unknown_family" in rules and "unit.pattern.unknown_status" in rules
        assert resolve(corpus, "ch", "draft", "proposed")["schema_id"] == BLOCKED_SCHEMA_ID

    def test_matching_vocabulary_is_healthy(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        vocabulary = Vocabulary(families=frozenset({"ch"}), statuses=frozenset({"draft", "proposed"}))
        assert load_corpus(root, vocabulary).is_healthy


class TestGroupings:
    def test_valid_grouping_loads_with_references_only(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        write_grouping(root)
        corpus = load_corpus(root)
        assert corpus.is_healthy and len(corpus.groupings) == 1
        grouping = corpus.groupings[0]
        assert grouping.grouping_id == "authoring-desk"
        assert [p.key for p in grouping.patterns] == [("ch", "draft", "proposed")]

    def test_grouping_contract_content_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        write_grouping(root, text=VALID_GROUPING + 'stop_condition: "Groupings must not carry contract content."\n')
        corpus = load_corpus(root)
        assert any(d.rule == "grouping.unknown_field" for d in corpus.defects)
        assert corpus.groupings == ()
        # A grouping defect refuses the grouping, not the referenced pattern.
        assert resolve(corpus, "ch", "draft", "proposed")["schema_id"] == CONTRACT_SCHEMA_ID

    def test_grouping_dangling_pattern_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        write_grouping(root, text=VALID_GROUPING.replace("family: ch", "family: spec"))
        corpus = load_corpus(root)
        assert any(d.rule == "grouping.dangling_pattern" for d in corpus.defects)
        assert corpus.groupings == ()

    def test_grouping_duplicate_pattern_rejected(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        duplicate = VALID_GROUPING + "  - family: ch\n    from_status: draft\n    to_status: proposed\n"
        write_grouping(root, text=duplicate)
        corpus = load_corpus(root)
        assert any(d.rule == "grouping.duplicate_pattern" for d in corpus.defects)


class TestCorpusShapes:
    def test_empty_corpus_is_healthy_and_uncovered(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        corpus = load_corpus(root)
        assert corpus.is_healthy and corpus.units_by_pattern == {}
        outcome = resolve(corpus, "ch", "draft", "proposed")
        assert outcome["schema_id"] == BLOCKED_SCHEMA_ID
        assert outcome["reasons"][0]["code"] == "uncovered_pattern"

    def test_missing_root_is_a_defect(self, tmp_path: Path) -> None:
        corpus = load_corpus(tmp_path / "nowhere")
        assert [d.rule for d in corpus.defects] == ["root.missing"]

    def test_unexpected_delivered_file_is_a_drift_finding(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        corpus = load_corpus(root)
        out_dir = tmp_path / "delivered"
        write_derived_views(corpus, out_dir)
        (out_dir / "hand_authored_extra.md").write_text("Independent authority.\n", encoding="utf-8")
        findings = assert_views_derived(corpus, out_dir)
        assert findings == ("unexpected file not derived from any unit: hand_authored_extra.md",)

    def test_template_view_shape(self, tmp_path: Path) -> None:
        root = make_root(tmp_path)
        write_unit(root)
        corpus = load_corpus(root)
        template = resolve(corpus, "ch", "draft", "proposed")["views"]["human_template"]
        assert "```yaml" in template and "id: <id>" in template
        assert "## Problem" in template and "## Scope" in template
        assert "> - Scope states its boundary and exclusions." in template
