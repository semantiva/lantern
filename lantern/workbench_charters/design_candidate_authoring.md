```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.design_candidate_authoring
title: Design Candidate Authoring Charter
workbench_ref: design_candidate_authoring
gate_refs:
  - GT-115
artifact_families:
  - DC
layers:
  - layer: authoring
    label: DC authoring
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Ready CH with Approved TD
      - Approved SPEC
      - Approved ARCH
    scope_boundary: >
      Author one or more Design Candidate (DC) records for a Ready CH, grounded in
      the approved CH + SPEC + ARCH + TD envelope. Each DC proposes a design that
      can be compared at GT-115. The DC is design truth for comparison only — not
      an implementation package.
    stop_condition: >
      At least one DC with status Candidate exists for the governing CH; each DC
      has complete required sections, no placeholders, and an explicit implementation
      latitude separation (fixed commitments vs downstream choices vs reopen conditions).
    deliverables:
      - DC record(s) with status Candidate (dc/DC-<CH_NUM>-<UUID>.md)
    forbidden_actions:
      - Include commit messages, drop-in packs, or patch payloads in a DC
      - Redefine CH assessment criteria, SPEC requirements, or ARCH decisions
      - Set DC to Candidate while any required section contains TBD or placeholders
    template_refs:
      - lantern/templates/TEMPLATE__DC.md

context_slots:
  - slot_id: ch_and_td_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context from ch_and_td_readiness workbench: the Ready CH problem
      statement, assessment criteria, constraints, and validated TD cases.
  - slot_id: design_selection_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the design_selection workbench that consumes the
      DC candidates. Injected when GT-115 selection is the next step.
```

# Design Candidate Authoring Charter

## Routing & applicability

This workbench covers the lifecycle span from GT-110 PASS to GT-115. Use it to
author DC records that will be compared at GT-115 design selection.

**When to use this workbench:**
- Authoring a new DC for a Ready CH.
- Iterating on an existing Draft DC to make it Candidate-eligible.
- Authoring multiple competing DC candidates for the same CH.

**Hard stops:**
- The governing CH must be Ready (GT-110 PASS) before DC authoring begins.
- The approved TD set must exist before a DC can claim Candidate status.
- Posture constraint: `requires_ready_ch`.

## Authoring layer — DC authoring

Produce a design candidate inside the locked CH + SPEC + ARCH + TD envelope.

1. Allocate the DC id using `python tools/allocate_lantern_id.py --artifact DC
   --ch CH-#### --repo <path>`. Create `dc/DC-<CH_NUM>-<UUID>.md`.
2. Write `## Problem Framing`: restate the CH problem in design terms without
   redefining CH assessment criteria.
3. Copy CH assessment criteria verbatim into `## Assessment Criteria Alignment`.
4. Copy CH constraints verbatim into `## Constraints`.
5. In `## Proposed Design`: describe the design clearly enough for GT-115 comparison
   on technical merit, governed scope, compatibility posture, and TD traceability.
   Never leave design choices delegated to CI authoring.
6. In `## Implementation Latitude`: provide three explicit sub-lists —
   (a) fixed commitments CI candidates must implement exactly,
   (b) downstream choices CI candidates may vary freely,
   (c) changes that would require reopening GT-115.
7. In `## Tradeoffs and Rejected Local Alternatives`: explain what was considered
   and ruled out for this candidate.
8. In `## Compatibility Posture`: state all compatibility constraints and non-goals
   explicitly.
9. Set `status: "Candidate"` when all required sections are complete and
   non-placeholder. Use `status: "Draft"` with `## Blocking Items` otherwise.
10. Ensure the DC appears in INDEX.md.
