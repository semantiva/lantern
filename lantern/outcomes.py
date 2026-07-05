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

"""The standard blocked-outcome payload (DB-0002 D6).

One blocked shape across the resolution surface: an ineligible or unservable
request yields a first-class payload — never an exception — enumerating each
failed constraint by name (REQ-0003). Producers: the context-policy layer and
the lifecycle eligibility evaluator.
"""

from __future__ import annotations

from typing import Any

BLOCKED_OUTCOME_SCHEMA_ID = "lantern.blocked_outcome.v1"


def blocked_outcome(
    *,
    pattern: dict[str, str],
    reasons: list[dict[str, str]],
    subject: str | None = None,
) -> dict[str, Any]:
    """Build the standard blocked payload: pattern, named reasons, optional subject."""
    payload: dict[str, Any] = {
        "schema_id": BLOCKED_OUTCOME_SCHEMA_ID,
        "blocked": True,
        "pattern": pattern,
        "reasons": reasons,
    }
    if subject is not None:
        payload["subject"] = subject
    return payload
