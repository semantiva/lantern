```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.ci_selection
title: CI Selection Charter
workbench_ref: ci_selection
gate_refs:
  - GT-120
artifact_families:
  - CI
  - EV
  - DEC
layers:
  - layer: authoring
    label: GT-120 CI selection analysis
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Ready CH with Approved TD
      - Approved DB
      - One or more CI candidates with status Candidate
    scope_boundary: >
      Perform the GT-120 CI selection analysis: evaluate each Candidate CI against
      the locked CH + DB + TD envelope using comparison classes A-E, produce the
      selection recommendation and structured findings ledger. This analysis layer
      produces a recommendation only — no statuses are updated, no DEC or EV
      records are created at this step.
    stop_condition: >
      Selection report exists with: eligibility summary, baseline checklist,
      candidate scorecards (PASS/FAIL per class A-E), recommendation (selected CI
      id or NONE), and GT-120 → GT-130 handoff notes. Human has approved the
      chosen candidate.
    deliverables:
      - GT-120 selection report (chat output or draft file)
    forbidden_actions:
      - Update CI statuses in this layer
      - Create EV or DEC records in this layer
      - Apply changes to the repository
    template_refs: []

  - layer: administrative
    label: GT-120 CI selection administration
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - Completed GT-120 selection report
      - Human-approved selected CI id (or NONE)
      - Approved DB, Approved TD
    scope_boundary: >
      Administer GT-120 outcomes: freeze the candidate pool (set CIs to Candidate),
      allocate EV/DEC ids, create EV record with selection report, create DEC record
      for GT-120, update CI statuses (Selected/Rejected), update INDEX.md.
    stop_condition: >
      Exactly one CI has status Selected (or outcome is FAIL/NONE); all other
      candidate CIs have status Rejected; EV and DEC records exist; INDEX.md updated.
    deliverables:
      - CI with status Selected (ci/CI-<CH_NUM>-<UUID>.md)
      - All other candidate CIs with status Rejected
      - EV record for GT-120 selection report (ev/EV-####.md)
      - DEC record for GT-120 (dec/DEC-####.md)
      - INDEX.md updated
    forbidden_actions:
      - Change CI content beyond the YAML status field
      - Change CH or DB status (CH remains Ready, DB remains Approved)
      - Skip authority-model replacement posture check (Step 0)
    template_refs:
      - lantern/templates/EV_TEMPLATE.md
      - lantern/templates/DEC_TEMPLATE.md

context_slots:
  - slot_id: ci_authoring_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context from ci_authoring workbench: the CI candidate records
      that will be compared at GT-120.
  - slot_id: selected_ci_application_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the selected_ci_application workbench that follows
      GT-120 PASS. Injected when CI application is the next step.
```

# CI Selection Charter

## Routing & applicability

This workbench covers GT-120 (CI Selection). Use it to analyze competing CI candidates
and administer the GT-120 decision.

**When to use this workbench:**
- Running the GT-120 selection analysis against a pool of Candidate CIs (authoring layer).
- Administering GT-120 outcomes: updating CI statuses, creating EV/DEC records (administrative layer).

**Hard stops:**
- All CIs in the comparison pool must have `status: Candidate` before selection begins.
- The Approved DB and Approved TD must exist before GT-120.
- A pool of exactly one CI is valid; GT-120 remains mandatory.
- Do not update CI statuses or create records during the analysis layer.
- Posture constraint: `requires_execution_grade_candidate`.

## Authoring layer — GT-120 CI selection analysis

Produce the GT-120 selection report.

1. Pre-flight (block if violated): confirm CH is Ready with non-empty assessment
   criteria and validation target; confirm Approved DB and TD exist; confirm all
   provided CIs have `status: Candidate`.
2. Step 0 — authority-model replacement check: if any CI replaces an authority model,
   confirm it identifies the replacement type, removes superseded runtime definitions,
   and addresses tests tied to superseded authority.
3. Reconstruct the locked baseline from CH + DB + TD: assessment criteria, constraints,
   validation target, fixed DB design commitments, implementation latitude, TD expectations.
4. For each Candidate CI, evaluate PASS/FAIL for classes A-E with evidence:
   - A: CH alignment (verbatim criteria/constraints, no expansion)
   - B: DB/TD conformance and record validity (required headers, design_baseline_ref,
     test_definition_refs, no placeholders)
   - C: Contract/seams inventory (what is frozen, what changes, compatibility posture)
   - D: Implementation determinism (drop-in pack covers full allowed_change_surface;
     commit message present)
   - E: Verification plan (runnable commands, binary signals, drift resistance posture)
5. Record material findings in one structured findings ledger. Include `GT-120 → GT-130`
   handoff notes.
6. Select the CI with tightest scope lock and strongest DB conformance; use the full
   ranking criteria if multiple pass. Declare NONE ACCEPTABLE if none pass.

## Administrative layer — GT-120 CI selection administration

Run this layer after human approval of the selection outcome.

1. Freeze the candidate pool: set any Draft CI to Candidate (status field only).
2. Allocate EV and DEC ids using the allocator tool.
3. Create `ev/EV-####.md` including the full selection report and `GT-120 → GT-130`
   handoff notes.
4. Create `dec/DEC-####.md` with gate GT-120, outcome PASS/FAIL, selected CI id,
   rationale grounded in the selection report.
5. On PASS: set selected CI to `status: Selected`; set all other candidate CIs to
   `status: Rejected`.
6. Update INDEX.md for CIs, EV, and DEC. Confirm selected CI is in CH `related_cis`.
7. Run GT-120 consistency checks (§7) before closing.
