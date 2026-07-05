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

"""Deterministic resolution of a transition pattern to its operating contract (DB-0001 D4).

Resolution is a pure function of the loaded unit file bytes. A covered, healthy
pattern yields the operating contract (components plus derived views); an
uncovered, defective, or collided pattern yields a first-class blocked outcome
enumerating each reason by name — never an exception, never a partial contract.
"""

from __future__ import annotations

import json
from typing import Any

from lantern.outcomes import blocked_outcome

from .model import CONTRACT_SCHEMA_ID, PolicyCorpus
from .views import human_template, task_card, validation_rules

REASON_UNCOVERED = "uncovered_pattern"
REASON_UNIT_INVALID = "unit_invalid"
REASON_COLLISION = "pattern_collision"


def canonical_json(payload: dict[str, Any]) -> bytes:
    """Canonical byte serialization: sorted keys, fixed separators, UTF-8."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def resolve(corpus: PolicyCorpus, family: str, from_status: str, to_status: str) -> dict[str, Any]:
    """Resolve one transition pattern to its operating contract or blocked outcome."""
    key = (family, from_status, to_status)
    pattern_payload = {"family": family, "from_status": from_status, "to_status": to_status}

    unit = corpus.units_by_pattern.get(key)
    if unit is not None:
        return {
            "schema_id": CONTRACT_SCHEMA_ID,
            "pattern": pattern_payload,
            "unit": {
                "unit_id": unit.unit_id,
                "version": unit.version,
                "title": unit.title,
                "content_digest": unit.content_digest,
            },
            "components": [
                {"kind": comp.kind, "payload": dict(comp.payload), "body": comp.body} for comp in unit.components
            ],
            "views": {
                "task_card": task_card(unit),
                "validation_rules": validation_rules(unit),
                "human_template": human_template(unit),
            },
        }

    reasons: list[dict[str, str]] = []
    for defect in corpus.refused_patterns.get(key, ()):
        code = REASON_COLLISION if defect.rule == "unit.pattern.collision" else REASON_UNIT_INVALID
        reasons.append({"code": code, "detail": defect.render()})
    if not reasons:
        label = f"{family}: {from_status} -> {to_status}"
        reasons.append({"code": REASON_UNCOVERED, "detail": f"no context-policy unit covers pattern ({label})"})

    return blocked_outcome(pattern=pattern_payload, reasons=reasons)


def resolve_bytes(corpus: PolicyCorpus, family: str, from_status: str, to_status: str) -> bytes:
    """Canonical bytes of ``resolve`` — the byte-identical determinism surface (REQ-0004)."""
    return canonical_json(resolve(corpus, family, from_status, to_status))
