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

"""Lifecycle layer: declarative per-family policy and transition eligibility.

Public API for the lifecycle bundle (authored in the grammar's published
lifecycle-declaration format, loaded fail-closed through the grammar's
``Lifecycle`` API), grammar-derived gate specifications, and the pure
eligibility evaluator with the standard blocked-outcome payload. Design
baseline DB-0002; architecture ARCH-0001/ARCH-0002.
"""

from .bundle import (
    BundleDefect,
    CardinalityRule,
    LifecycleBundle,
    LifecycleBundleError,
    SlotConstraint,
    default_bundle_root,
    load_bundle,
    load_bundle_strict,
    short_name,
)
from .evaluate import (
    ELIGIBLE_SCHEMA_ID,
    REASON_BUNDLE_INVALID,
    REASON_GATE_EVIDENCE,
    REASON_STATE_CONSTRAINT,
    REASON_UNDECLARED_FAMILY,
    REASON_UNDECLARED_STATUS,
    REASON_UNDECLARED_TRANSITION,
    evaluate_transition,
)
from .gates import GateSpec, gates_by_outcome, gates_from_grammar
from .view import GateRecord, InMemoryStateView, RelatedRef, StateView

__all__ = [
    "ELIGIBLE_SCHEMA_ID",
    "REASON_BUNDLE_INVALID",
    "REASON_GATE_EVIDENCE",
    "REASON_STATE_CONSTRAINT",
    "REASON_UNDECLARED_FAMILY",
    "REASON_UNDECLARED_STATUS",
    "REASON_UNDECLARED_TRANSITION",
    "BundleDefect",
    "CardinalityRule",
    "GateRecord",
    "GateSpec",
    "InMemoryStateView",
    "LifecycleBundle",
    "LifecycleBundleError",
    "RelatedRef",
    "SlotConstraint",
    "StateView",
    "default_bundle_root",
    "evaluate_transition",
    "gates_by_outcome",
    "gates_from_grammar",
    "load_bundle",
    "load_bundle_strict",
    "short_name",
]
