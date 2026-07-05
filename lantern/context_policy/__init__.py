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

"""Context-policy layer: one authored unit per transition pattern.

Public API for the context-policy unit format (schema, fail-closed loader,
derived views, deterministic resolution, optional named groupings). Design
baseline DB-0001; architecture ARCH-0003 under ARCH-0002's engine posture.
"""

from .loader import load_corpus, load_corpus_strict
from .model import (
    BLOCKED_SCHEMA_ID,
    CONTRACT_SCHEMA_ID,
    GROUPING_SCHEMA_ID,
    KNOWN_COMPONENT_KINDS,
    UNIT_SCHEMA_ID,
    VIEW_HUMAN_TEMPLATE_SCHEMA_ID,
    VIEW_TASK_CARD_SCHEMA_ID,
    VIEW_VALIDATION_RULES_SCHEMA_ID,
    PolicyComponent,
    PolicyCorpus,
    PolicyDefect,
    PolicyGrouping,
    PolicyLoadError,
    PolicyUnit,
    TransitionPattern,
    ViewDriftError,
    Vocabulary,
)
from .resolve import REASON_COLLISION, REASON_UNCOVERED, REASON_UNIT_INVALID, canonical_json, resolve, resolve_bytes
from .views import (
    assert_views_derived,
    assert_views_derived_strict,
    expected_views,
    human_template,
    task_card,
    validation_rules,
    write_derived_views,
)

__all__ = [
    "BLOCKED_SCHEMA_ID",
    "CONTRACT_SCHEMA_ID",
    "GROUPING_SCHEMA_ID",
    "KNOWN_COMPONENT_KINDS",
    "UNIT_SCHEMA_ID",
    "VIEW_HUMAN_TEMPLATE_SCHEMA_ID",
    "VIEW_TASK_CARD_SCHEMA_ID",
    "VIEW_VALIDATION_RULES_SCHEMA_ID",
    "REASON_COLLISION",
    "REASON_UNCOVERED",
    "REASON_UNIT_INVALID",
    "PolicyComponent",
    "PolicyCorpus",
    "PolicyDefect",
    "PolicyGrouping",
    "PolicyLoadError",
    "PolicyUnit",
    "TransitionPattern",
    "ViewDriftError",
    "Vocabulary",
    "assert_views_derived",
    "assert_views_derived_strict",
    "canonical_json",
    "expected_views",
    "human_template",
    "load_corpus",
    "load_corpus_strict",
    "resolve",
    "resolve_bytes",
    "task_card",
    "validation_rules",
    "write_derived_views",
]
