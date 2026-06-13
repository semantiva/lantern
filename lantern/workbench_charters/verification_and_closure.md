```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.verification_and_closure
title: Verification and Closure Charter
workbench_ref: verification_and_closure
gate_refs:
  - GT-130
artifact_families:
  - CI
  - EV
  - DEC
layers:
  - layer: authoring
    label: GT-130 verification evidence authoring
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Selected CI (status Selected) with applied product changes
      - Approved DB
      - Approved TD
      - Product repo at committed baseline (known SHA)
    scope_boundary: >
      Execute integration verification for the Selected CI and author the GT-130 EV
      record: run declared verification commands, capture actual outputs, evaluate
      PASS/FAIL per TD case, populate the EV record with real (non-aspirational)
      evidence. Applies the GT-130 expectation-to-delivery review checklist.
    stop_condition: >
      EV record is authored with real command output, TD case coverage table (all cases
      PASS or explicitly FAIL), delivered artifacts list, expectation-to-delivery review
      (initiative objective, requirements satisfaction, architectural fit,
      reproducibility), and human approval block ready for GT-130 PASS.
    deliverables:
      - EV record draft (ev/EV-####.md)
    forbidden_actions:
      - Use aspirational or fabricated evidence
      - Close GT-130 against an uncommitted dirty worktree
      - Modify the Selected CI, DB, or TD records
    template_refs:
      - lantern/templates/EV_TEMPLATE__GT130_VERIFICATION_REPORT.md

  - layer: administrative
    label: GT-130 integration verification administration
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - Completed EV record with real verification evidence
      - Human-approved GT-130 outcome (PASS or FAIL)
      - Product repo committed SHA
    scope_boundary: >
      Administer GT-130 outcomes: allocate DEC id, create DEC record, update CI
      status to Verified (PASS) or manage demotion (FAIL), update CH status to
      Addressed (PASS), update INDEX.md and binding record with the committed
      product SHA.
    stop_condition: >
      CI status is Verified (PASS) or demoted per human direction (FAIL); CH status
      is Addressed (PASS) or remains Ready (FAIL); DEC record references the EV;
      INDEX.md and binding record reflect the committed product SHA.
    deliverables:
      - CI with status Verified (ci/CI-<CH_NUM>-<UUID>.md)
      - CH with status Addressed (ch/CH-####.md)
      - DEC record for GT-130 (dec/DEC-####.md)
      - INDEX.md updated with CI, CH, EV, DEC statuses
      - binding_record.md updated with committed product SHA
    forbidden_actions:
      - Set CH to Addressed when GT-130 outcome is FAIL
      - Record GT-130 PASS without real verification evidence in the EV
      - Skip the binding record update
    template_refs:
      - lantern/templates/DEC_TEMPLATE__GT130_VERIFICATION.md

context_slots:
  - slot_id: ci_application_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context from selected_ci_application workbench: the committed
      product SHA and any bounded GT-130 extension paths identified during
      application.
```

# Verification and Closure Charter

## Routing & applicability

This workbench covers GT-130 (Integration Verification). Use it to execute
verification against the Selected CI and administer the GT-130 gate decision,
transitioning the CI to Verified and the CH to Addressed.

**When to use this workbench:**
- Running GT-130 verification commands against the committed product baseline (authoring layer).
- Authoring the EV record with real verification evidence.
- Administering GT-130 outcomes: status updates, DEC record, INDEX update (administrative layer).

**Hard stops:**
- Exactly one CI must have `status: Selected` and its changes must be applied to the
  product repo before GT-130 verification begins.
- Aspirational evidence is invalid. Real command output must appear in the EV record.
- Do not close GT-130 against an uncommitted dirty worktree.
- Posture constraint: `requires_selected_ci`.

## Authoring layer — GT-130 verification evidence authoring

Execute verification and populate the EV record.

1. Confirm preconditions (§0 of GT-130 Administration Guide): Selected CI exists,
   Approved DB and TD exist, product repo is at the committed baseline from
   `selected_ci_application`.
2. For each item in the CI `## Verification Plan`: run the declared command exactly,
   capture actual output, compare to expected signal, record PASS/FAIL.
3. For each TD case in the Approved TD set: map to verification evidence, confirm the
   oracle is satisfied, record PASS/FAIL per case.
4. Apply the GT-130 expectation-to-delivery review checklist:
   - Initiative objective: which initiative objective does this CH satisfy?
   - Roadmap role: what role does this CH play in the current roadmap?
   - Requirements satisfaction: which SPEC ACs and TD requirements are satisfied?
   - Architectural fit: does the delivered result align with the Approved ARCH?
   - Reproducibility: what clean-state evidence proves the result is repeatable?
5. If a GT-130 bounded extension was registered during application, include a section
   listing extra paths, blocking rationale, and confirming DB/TD remain unchanged.
6. Write `ev/EV-####.md` with all real evidence. Include the TD case coverage table
   and the human approval block.

## Administrative layer — GT-130 integration verification administration

Run this layer after human approval of the GT-130 outcome.

1. Allocate the DEC id using the allocator tool.
2. Create `dec/DEC-####.md` with gate GT-130, outcome PASS/FAIL, verified CI id,
   rationale grounded in the EV.
3. On PASS: set CI `status: "Verified"`; set CH `status: "Addressed"`.
4. On FAIL: leave CI at `status: "Selected"` (default) or demote per human direction
   (Candidate for GT-120 re-run; Rejected if retired). Leave CH at `status: "Ready"`.
5. Update `INDEX.md`: CI status, CH status, EV entry, DEC entry.
6. Update `binding_record.md` with the committed product SHA used for verification.
7. Run GT-130 consistency checks (§9) before closing.
