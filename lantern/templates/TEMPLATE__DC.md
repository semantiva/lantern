```yaml
dc_id: "DC-<CH_NUM>-<UUID>"
ch_id: "CH-####"
status: "Draft|Candidate|Selected|Rejected"
title: "<concise title>"
spec_refs:
  - "SPEC-####"
arch_refs:
  - "ARCH-####"
test_definition_refs:
  - "TD-####"
origin:
  baseline: "<repo-or-archive-pointer>@<commit-or-tag>"
  rationale: "<why this design candidate exists>"
governed_scope:
  - "<module-or-surface>"
compatibility_posture:
  assumptions:
    - "<compatibility assumption>"
  constraints:
    - "<compatibility constraint>"
  non_goals:
    - "<explicit non-goal>"
blocked_by: []
```

# DC-<CH_NUM>-<UUID> — <short title>

## Problem Framing
Describe the problem slice this design candidate addresses.

## Assessment Criteria Alignment (verbatim from CH)
Paste the governing CH assessment criteria verbatim.

## Constraints (verbatim from CH)
Paste the governing CH constraints verbatim.

## Upstream Baseline Alignment
- SPEC anchors:
- ARCH anchors:
- TD anchors:

## Proposed Design
Describe the proposed design shape.

## Tradeoffs and Rejected Local Alternatives
List tradeoffs and rejected local alternatives.

## Compatibility Posture
- Assumptions:
- Constraints:
- Non-goals:

## Governed Scope
- <path-or-module>

## Interfaces / Public Surface Impact
- <public contract impact or none>

## Implementation Latitude
- Fixed commitments:
- Downstream latitude:
- Reopen GT-115 if:

## Comparison Notes for GT-115
- Why this candidate is preferable or riskier than alternatives.

## Blocking Items
- Required only when `status: "Draft"`.
