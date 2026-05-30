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

"""TD-0028 tests for CH-0028: CH and TD lifecycle bundle extensions for rejection,
backward transitions, and supersession (IS-0033)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_POLICY_DIR = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "lifecycle-policy"
CH_YAML_PATH = LIFECYCLE_POLICY_DIR / "ch.yaml"
TD_YAML_PATH = LIFECYCLE_POLICY_DIR / "td.yaml"

# Pre-CH-0028 baselines (the additive-extension property requires these to remain admitted).
PRE_CH_0028_CH_STATUS_IDS = frozenset(
    {
        "lg:statuses/proposed",
        "lg:statuses/ready",
        "lg:statuses/in_progress",
        "lg:statuses/addressed",
    }
)
PRE_CH_0028_CH_TRANSITIONS = frozenset(
    {
        ("lg:statuses/proposed", "lg:statuses/ready"),
        ("lg:statuses/ready", "lg:statuses/in_progress"),
        ("lg:statuses/in_progress", "lg:statuses/addressed"),
        ("lg:statuses/ready", "lg:statuses/addressed"),
    }
)
PRE_CH_0028_TD_STATUS_IDS = frozenset(
    {
        "lg:statuses/draft",
        "lg:statuses/approved",
    }
)
PRE_CH_0028_TD_TRANSITIONS = frozenset(
    {
        ("lg:statuses/draft", "lg:statuses/approved"),
    }
)

# Expected post-CH-0028 additions.
CH_NEW_STATUS_IDS = frozenset({"lg:statuses/rejected"})
CH_NEW_TRANSITIONS = frozenset(
    {
        # Backward — demotion for adaptation
        ("lg:statuses/ready", "lg:statuses/proposed"),
        ("lg:statuses/in_progress", "lg:statuses/ready"),
        # Rejection
        ("lg:statuses/proposed", "lg:statuses/rejected"),
        ("lg:statuses/ready", "lg:statuses/rejected"),
        ("lg:statuses/in_progress", "lg:statuses/rejected"),
        # Resurrection from Rejected — via Proposed only (Rejected→Ready excluded to preserve GT-110 gate discipline)
        ("lg:statuses/rejected", "lg:statuses/proposed"),
    }
)
TD_NEW_STATUS_IDS = frozenset({"lg:statuses/superseded"})
TD_NEW_TRANSITIONS = frozenset(
    {
        ("lg:statuses/approved", "lg:statuses/superseded"),
    }
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _status_id_set(doc: dict) -> frozenset[str]:
    return frozenset(s["id"] for s in doc["statuses"])


def _status_label_map(doc: dict) -> dict[str, str]:
    return {s["id"]: s["label"] for s in doc["statuses"]}


def _transition_set(doc: dict) -> frozenset[tuple[str, str]]:
    return frozenset((t["from"], t["to"]) for t in doc["transitions"])


def _grammar_status_ids() -> frozenset[str]:
    from lantern_grammar import Grammar

    g = Grammar.load()
    return frozenset(e["id"] for e in g.iter_entities(prefix="lg:statuses/"))


# ── TD-0028 cases ────────────────────────────────────────────────────────────


def test_c01_ch_admits_rejected_status() -> None:
    """C01: CH lifecycle admits Rejected status using existing Grammar entity."""
    ch_doc = _load_yaml(CH_YAML_PATH)
    status_ids = _status_id_set(ch_doc)
    label_map = _status_label_map(ch_doc)
    expected_ids = PRE_CH_0028_CH_STATUS_IDS | CH_NEW_STATUS_IDS

    assert (
        status_ids == expected_ids
    ), f"CH status set mismatch.\n  got:      {sorted(status_ids)}\n  expected: {sorted(expected_ids)}"
    assert label_map["lg:statuses/rejected"] == "Rejected"
    assert "lg:statuses/rejected" in _grammar_status_ids(), "lg:statuses/rejected must exist in lantern-grammar"


def test_c02_ch_admits_required_transitions() -> None:
    """C02: CH lifecycle admits backward + rejection + resurrection transitions; no original removed."""
    ch_doc = _load_yaml(CH_YAML_PATH)
    transitions = _transition_set(ch_doc)
    expected = PRE_CH_0028_CH_TRANSITIONS | CH_NEW_TRANSITIONS

    assert transitions == expected, (
        f"CH transition set mismatch.\n"
        f"  missing: {sorted(expected - transitions)}\n"
        f"  extra:   {sorted(transitions - expected)}"
    )


def test_c03_td_admits_superseded_status() -> None:
    """C03: TD lifecycle admits Superseded status using existing Grammar entity."""
    td_doc = _load_yaml(TD_YAML_PATH)
    status_ids = _status_id_set(td_doc)
    label_map = _status_label_map(td_doc)
    expected_ids = PRE_CH_0028_TD_STATUS_IDS | TD_NEW_STATUS_IDS

    assert (
        status_ids == expected_ids
    ), f"TD status set mismatch.\n  got:      {sorted(status_ids)}\n  expected: {sorted(expected_ids)}"
    assert label_map["lg:statuses/superseded"] == "Superseded"
    assert "lg:statuses/superseded" in _grammar_status_ids(), "lg:statuses/superseded must exist in lantern-grammar"


def test_c04_td_admits_approved_to_superseded() -> None:
    """C04: TD lifecycle admits Approved → Superseded transition; pre-existing transition retained."""
    td_doc = _load_yaml(TD_YAML_PATH)
    transitions = _transition_set(td_doc)
    expected = PRE_CH_0028_TD_TRANSITIONS | TD_NEW_TRANSITIONS

    assert transitions == expected, (
        f"TD transition set mismatch.\n"
        f"  missing: {sorted(expected - transitions)}\n"
        f"  extra:   {sorted(transitions - expected)}"
    )


def test_c05_extended_bundle_validates_against_grammar_schema() -> None:
    """C05: Extended ch.yaml and td.yaml validate against gscld-family-1.0.schema.json."""
    jsonschema = __import__("jsonschema")
    # Locate the grammar-published schema by walking the lantern_grammar package install.
    import lantern_grammar  # noqa: F401

    pkg_dir = Path(__import__("lantern_grammar").__file__).resolve().parent
    schema_path = pkg_dir / "_schemas" / "gscld-family-1.0.schema.json"
    assert schema_path.exists(), f"grammar family schema not found at {schema_path}"

    schema = json.loads(schema_path.read_text())
    for name, path in (("ch.yaml", CH_YAML_PATH), ("td.yaml", TD_YAML_PATH)):
        doc = _load_yaml(path)
        try:
            jsonschema.validate(doc, schema)
        except jsonschema.ValidationError as e:
            raise AssertionError(f"{name} fails grammar family schema: {e.message}") from e


def test_c06_ch_extension_is_additive_for_statuses() -> None:
    """C06: Every pre-CH-0028 CH status remains admitted by the extended lifecycle."""
    ch_doc = _load_yaml(CH_YAML_PATH)
    status_ids = _status_id_set(ch_doc)
    missing = PRE_CH_0028_CH_STATUS_IDS - status_ids
    assert not missing, f"CH lifecycle removed pre-existing statuses: {sorted(missing)}"


def test_c07_td_extension_is_additive_for_statuses() -> None:
    """C07: Every pre-CH-0028 TD status remains admitted by the extended lifecycle."""
    td_doc = _load_yaml(TD_YAML_PATH)
    status_ids = _status_id_set(td_doc)
    missing = PRE_CH_0028_TD_STATUS_IDS - status_ids
    assert not missing, f"TD lifecycle removed pre-existing statuses: {sorted(missing)}"


def test_c08_workflow_loader_accepts_extended_bundle() -> None:
    """C08: load_workflow_layer() succeeds against the extended bundle."""
    from lantern.workflow import load_workflow_layer

    wl = load_workflow_layer()
    # The loader must return a workflow-layer object without raising. Verify the
    # extended families are reachable through the loader's lifecycle-bundle surface.
    # We probe both ways the loader may expose lifecycle data (object attribute or
    # mapping); whichever is present, the data must reflect the extension.
    for attr in ("lifecycles", "lifecycle_bundle", "lifecycle_families"):
        bundle = getattr(wl, attr, None)
        if bundle is not None:
            # We do not assert on bundle internals beyond loader success; the
            # status-set and transition-set assertions are covered by C01..C04.
            break
    # If the loader does not expose a lifecycle bundle attribute by name, the
    # successful return value still proves the loader did not reject the
    # extended bundle on parse or schema grounds (which is the C08 contract).
    assert wl is not None, "load_workflow_layer() returned None"


def test_c09_round_trip_ready_to_proposed_admitted() -> None:
    """C09: The transition Ready → Proposed is present in the CH lifecycle transition set."""
    ch_doc = _load_yaml(CH_YAML_PATH)
    transitions = _transition_set(ch_doc)
    assert ("lg:statuses/ready", "lg:statuses/proposed") in transitions


def test_c10_round_trip_approved_to_superseded_admitted() -> None:
    """C10: The transition Approved → Superseded is present in the TD lifecycle transition set."""
    td_doc = _load_yaml(TD_YAML_PATH)
    transitions = _transition_set(td_doc)
    assert ("lg:statuses/approved", "lg:statuses/superseded") in transitions


def test_c11_rejected_to_ready_not_admitted() -> None:
    """C11: Rejected → Ready is NOT in the CH lifecycle; resurrection goes via Proposed only."""
    ch_doc = _load_yaml(CH_YAML_PATH)
    transitions = _transition_set(ch_doc)
    assert (
        "lg:statuses/rejected",
        "lg:statuses/ready",
    ) not in transitions, (
        "Rejected → Ready must not be admitted; resurrection path is Rejected → Proposed → (GT-110) → Ready"
    )
