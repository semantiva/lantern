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

"""TD-0029 proxy tests for CH-0029: Grammar 0.5.0 issue lifecycle compatibility."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_POLICY_DIR = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "lifecycle-policy"
LIFECYCLE_POLICY_MANIFEST = LIFECYCLE_POLICY_DIR / "manifest.yaml"
STATUS_CONTRACT_PATH = PRODUCT_ROOT / "lantern" / "workflow" / "definitions" / "artifact_status_contract.json"

ISSUE_STATUS_MAPPING = {
    "NEW": "lg:statuses/new",
    "NEEDS_INFO": "lg:statuses/needs_info",
    "ACCEPTED": "lg:statuses/accepted",
    "DEFERRED": "lg:statuses/deferred",
    "REJECTED": "lg:statuses/rejected",
    "RESOLVED": "lg:statuses/resolved",
}

ISSUE_TRANSITIONS = {
    ("NEW", "NEEDS_INFO"),
    ("NEW", "ACCEPTED"),
    ("NEW", "DEFERRED"),
    ("NEW", "REJECTED"),
    ("NEEDS_INFO", "NEW"),
    ("NEEDS_INFO", "ACCEPTED"),
    ("NEEDS_INFO", "DEFERRED"),
    ("NEEDS_INFO", "REJECTED"),
    ("ACCEPTED", "RESOLVED"),
    ("DEFERRED", "ACCEPTED"),
    ("DEFERRED", "REJECTED"),
}


def test_runtime_accepts_grammar_050() -> None:
    from lantern._compat import check_grammar_compatibility
    from lantern.workflow import load_workflow_layer

    result = check_grammar_compatibility()
    assert result["status"] == "ok", result
    assert result["supported_range"] == ">=0.5.0,<0.6.0"
    assert result["installed_package_version"].startswith("0.5.")
    assert result["installed_model_version"].startswith("0.5.")

    wl = load_workflow_layer()
    assert wl.grammar_version.startswith("0.5.")
    assert wl.grammar_package_version.startswith("0.5.")


def test_issue_lifecycle_declared_in_bundle_and_validates() -> None:
    from lantern_grammar import Grammar, Lifecycle

    manifest = yaml.safe_load(LIFECYCLE_POLICY_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["grammar_compatibility"]["min_model_version"] == "0.5.0"
    assert "issue.yaml" in manifest["families"]

    grammar = Grammar.load()
    for status_id in ISSUE_STATUS_MAPPING.values():
        assert grammar.get_entity(status_id) is not None

    lc = Lifecycle.from_manifest(grammar, LIFECYCLE_POLICY_MANIFEST)
    result = lc.validate()
    assert result.ok, [f"{i.path}: {i.message}" for i in result.issues]
    assert "lg:artifacts/issue" in set(lc.artifact_families())


def test_issue_status_contract_is_grammar_semantic_projection() -> None:
    contract = json.loads(STATUS_CONTRACT_PATH.read_text(encoding="utf-8"))
    issue = contract["families"]["IS"]

    assert issue["ownership"] == "grammar_semantic"
    assert issue["canonical_statuses"] == list(ISSUE_STATUS_MAPPING)
    assert issue["grammar_mapping"] == ISSUE_STATUS_MAPPING
    assert {(t["from"], t["to"]) for t in issue["transitions"]} == ISSUE_TRANSITIONS
    assert issue["normal_path_policy"] == "reject_alias"


def test_issue_lifecycle_projection_parity_is_enforced() -> None:
    from lantern.workflow.loader import _verify_lifecycle_projection_consistency

    _verify_lifecycle_projection_consistency(LIFECYCLE_POLICY_MANIFEST, status_contract_path=STATUS_CONTRACT_PATH)
