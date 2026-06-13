```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.ch_and_td_readiness
title: CH and TD Readiness Charter
workbench_ref: ch_and_td_readiness
gate_refs:
  - GT-110
artifact_families:
  - CH
  - TD
  - EV
  - DEC
layers:
  - layer: authoring
    label: CH authoring and TD authoring
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Approved upstream baselines (DIP/SPEC/ARCH) or explicit waiver
      - Initiative record (if CH is derived from an Initiative)
    scope_boundary: >
      Author a CH from Proposed toward Ready: define problem statement, scope,
      constraints, assessment criteria, and validation target. Author the TD covering
      all CH assessment criteria. Applies to initial authoring and to iterative
      refinement before GT-110 PASS.
    stop_condition: >
      CH body is complete (all required sections non-placeholder); TD is Approved with
      non-shallow coverage of every CH assessment criterion; GT-110 input sufficiency
      checks S1-S9 all pass.
    deliverables:
      - CH record (ch/CH-####.md) with complete body
      - TD record (td/TD-####.md) with status Approved
    forbidden_actions:
      - Author CI or DC candidates before GT-110 PASS
      - Set CH to Ready without an Approved TD
      - Use aspirational or placeholder validation targets
    template_refs:
      - lantern/templates/CH_TEMPLATE.md
      - lantern/templates/TD_TEMPLATE.md

  - layer: administrative
    label: GT-110 entry gate administration
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - CH with complete body and Approved TD
      - Human-approved GT-110 outcome
    scope_boundary: >
      Administer GT-110: confirm input-sufficiency checks S1-S9 pass, allocate EV and
      DEC ids, create EV record, create DEC record, update CH status to Ready on PASS,
      update INDEX.md.
    stop_condition: >
      CH status is Ready (PASS) or remains Proposed (FAIL); EV and DEC records exist;
      DEC references the EV; CH header lists EV and DEC ids; INDEX.md updated.
    deliverables:
      - CH with status Ready (ch/CH-####.md)
      - EV record (ev/EV-####.md)
      - DEC record for GT-110 (dec/DEC-####.md)
      - INDEX.md updated
    forbidden_actions:
      - Set CH to Ready without recording a GT-110 PASS DEC
      - Skip the TD coverage check in the EV
    template_refs:
      - lantern/templates/EV_TEMPLATE.md
      - lantern/templates/DEC_TEMPLATE.md

context_slots:
  - slot_id: upstream_baseline_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the upstream intake workbench that produced the baselines
      this workbench consumes. Injected when upstream baseline state is relevant.
  - slot_id: downstream_design_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the design_candidate_authoring workbench that follows
      GT-110 PASS. Injected when design candidate authoring is the next step.
```

# CH and TD Readiness Charter

## Routing & applicability

This workbench covers GT-110 (CH + TD Input Kit Readiness). It is the entry gate for
all change execution. Use this workbench to author or refine a CH, author its TD, and
administer the GT-110 gate decision.

**When to use this workbench:**
- Authoring a new CH from scratch (draft layer).
- Refining an existing Proposed CH to address sufficiency gaps.
- Authoring or updating the TD set for a CH.
- Running GT-110 administration after human approval (administrative layer).

**Hard stops:**
- Upstream baselines (DIP/SPEC/ARCH) must be Approved before CH reaches Ready,
  unless an explicit waiver with rationale is recorded in the GT-110 EV and DEC.
- TD must be Approved before GT-110 PASS is recorded.
- Posture constraint: `requires_upstream_baselines`.

## Authoring layer — CH authoring and TD authoring

**CH authoring steps:**
1. Allocate the CH id using the allocator tool. Create `ch/CH-####.md` from the
   CH template. Set `status: "Proposed"` until GT-110 is satisfied.
2. Write a non-placeholder problem statement: articulate the real product technical
   problem, defect, or capability gap the CH addresses.
3. Declare `## Scope` with explicit "In scope" and "Out of scope" sub-lists.
4. Write checkable `assessment_criteria`: each criterion is a binary verifiable claim
   tied to observable product behavior — not a sentiment.
5. Write a concrete `validation_target` expressible in TD cases. Aspirational
   or TBD validation targets are invalid.
6. Run the GT-110 input sufficiency checks S1-S9 in `## 0. GT-110 Input Sufficiency
   Assessment`. If any check fails, keep CH at Proposed and address the gap.
7. Record `depends_on_ch` if this CH has upstream dependencies.

**TD authoring steps:**
1. Allocate the TD id using the allocator tool. Create `td/TD-####.md`.
2. For each CH assessment criterion, author at least one TD case covering:
   criterion, preconditions, stimulus, observable, oracle (binary), failure condition.
3. The oracle must be evaluable by a human reviewer without running code. It is
   behavioral truth, not executable code.
4. Every TD case must trace to a CH assessment criterion by id or exact wording.
5. Set `status: "Approved"` only when all cases are non-shallow and coverage is
   complete. Use `status: "Draft"` with `## Blocking Items` when authoring is blocked.
6. Ensure the TD is listed in INDEX.md.

## Administrative layer — GT-110 entry gate administration

Run this layer when a human has reviewed the CH + TD package and approved a GT-110
PASS or FAIL outcome.

1. Confirm input-sufficiency checks S1-S9 all pass (re-run the CH §0 section).
2. Allocate EV and DEC ids using the allocator tool.
3. Create `ev/EV-####.md` covering: EV1 (upstream baseline locators), EV1b (TD
   coverage inventory per criterion), EV2 (sufficiency assessment summary including
   STOP/GO), EV3 (validation target check definition), EV4 (dependency handling).
4. Create `dec/DEC-####.md` with gate GT-110, outcome PASS/FAIL, rationale
   grounded in the EV. Reference EV id.
5. On PASS: set CH `status: "Ready"`; update CH header fields
   `required_evidence_for_gt110` and `required_decisions`; update INDEX.md.
6. On FAIL: leave CH at `status: "Proposed"`. Record what must be addressed.
