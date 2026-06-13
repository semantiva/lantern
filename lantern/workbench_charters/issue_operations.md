```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.issue_operations
title: Issue Operations Charter
workbench_ref: issue_operations
gate_refs: []
artifact_families:
  - IS
layers:
  - layer: authoring
    label: Issue intake and triage
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Observed friction, defect, inconsistency, or risk
    scope_boundary: >
      Create an IS record and perform triage: assess the observed issue, determine
      the triage outcome (ACCEPTED, DEFERRED, REJECTED, NEEDS_INFO), and if accepted,
      create a linked CH record. The intake is factual; do not embed implementation
      plans in the IS file.
    stop_condition: >
      IS record exists with non-placeholder observation, evidence pointers, and an
      explicit triage decision with rationale. If ACCEPTED: a linked CH exists.
    deliverables:
      - IS record (is/IS-####.md) with triage decision
      - CH record (ch/CH-####.md) if triage outcome is ACCEPTED
    forbidden_actions:
      - Embed implementation plans in IS records
      - Bypass CH creation for accepted issues
      - Set IS to RESOLVED before CH/CI/EV resolution evidence is available
    template_refs:
      - lantern/templates/TEMPLATE__IS.md
      - lantern/templates/CH_TEMPLATE.md

  - layer: administrative
    label: Issue resolution administration
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - ACCEPTED IS record with linked CH
      - Completed CH/CI workflow (GT-130 PASS for the resolving CH)
    scope_boundary: >
      Administer issue resolution: update IS status to RESOLVED, add links to the
      resolving CH, CI, EV, and DEC records. Also covers DEFERRED and REJECTED
      status administration: record rationale and re-entry conditions.
    stop_condition: >
      IS status reflects the closure decision (RESOLVED, DEFERRED, or REJECTED)
      with explicit rationale and evidence links; INDEX.md or issue record updated.
    deliverables:
      - IS record with RESOLVED, DEFERRED, or REJECTED status (is/IS-####.md)
    forbidden_actions:
      - Mark IS RESOLVED without CH/CI/EV resolution evidence links
      - Rewrite the historical Observation or Triage sections (use ordered notes)
    template_refs: []

context_slots:
  - slot_id: ch_execution_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the CH execution workbenches (ch_and_td_readiness and
      downstream) that resolve an ACCEPTED issue. Injected when the resolving CH
      is active.
```

# Issue Operations Charter

## Routing & applicability

This workbench covers the full issue lifecycle from intake through resolution or
rejection. It is lifecycle-independent — issues may arise at any point.

**When to use this workbench:**
- Intake: creating a new IS record for any observed problem or risk.
- Triage: deciding what happens to an open issue (ACCEPTED, DEFERRED, REJECTED, NEEDS_INFO).
- Resolution: updating IS status to RESOLVED after CH/CI/EV evidence is available.

**Hard stops:**
- Accepted issues must generate a CH. Do not bypass CH creation.
- Do not embed implementation plans in IS files — keep them factual and link-driven.
- For regressions: file an IS record first before any fix (posture constraint:
  `issue_first_for_regressions`).

## Authoring layer — Issue intake and triage

**Intake steps:**
1. Allocate the IS id: `python tools/allocate_lantern_id.py --artifact IS --repo
   <path>`. Create `is/IS-####.md` from the IS template.
2. Fill required minimum fields: ID, Status (NEW), Created, Reporter, Owner.
   Summary, Observation (factual, not speculative), Expected behavior, Impact/Risk,
   Evidence pointers.
3. Set `Status: NEW`.

**Triage steps:**
1. Review issue facts and evidence. Decide: NEEDS_INFO, ACCEPTED, DEFERRED, REJECTED.
2. Record triage decision, date, decider, rationale, and next action.
3. If NEEDS_INFO: list the explicit missing items.
4. If ACCEPTED: create a CH (use `ch_and_td_readiness` workbench for GT-110) and link
   the CH id in the IS record under the Links section.
5. If new mitigation context must be added while the issue remains open, append
   it under `## Ordered notes` as a new timestamped entry — do not rewrite the
   historical Observation or Triage sections.

## Administrative layer — Issue resolution administration

**Resolution steps (ACCEPTED issues):**
1. After the resolving CH reaches GT-130 PASS, gather the CH, CI (Verified), EV,
   and DEC ids.
2. Update IS `Status: RESOLVED` in the YAML header.
3. Add links to all resolution artifacts (CH, CI, EV, DEC) in the Links section.

**Deferred issues:**
- Keep rationale and explicit re-entry condition or date.

**Rejected issues:**
- Keep concise rejection rationale. REJECTED is terminal.
