```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.design_selection
title: Design Selection Charter
workbench_ref: design_selection
gate_refs:
  - GT-115
artifact_families:
  - DC
  - DB
  - EV
  - DEC
layers:
  - layer: authoring
    label: GT-115 design candidate selection analysis
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Ready CH with Approved TD
      - Approved SPEC
      - Approved ARCH
      - One or more DC candidates with status Candidate
    scope_boundary: >
      Perform the GT-115 selection analysis: evaluate each Candidate DC against
      the locked CH + SPEC + ARCH + TD envelope using comparison classes A-E,
      produce the selection recommendation and structured findings ledger. This
      analysis layer produces a recommendation only — no statuses are updated,
      no DEC or EV records are created, and no DB is authored at this step.
    stop_condition: >
      Selection report exists with: eligibility summary, baseline checklist,
      candidate scorecards (PASS/FAIL per class A-E), recommendation (selected DC
      id or NONE), and GT-115 → DB/GT-120 handoff notes. Human has approved the
      chosen candidate.
    deliverables:
      - GT-115 selection report (chat output or draft file)
    forbidden_actions:
      - Update DC statuses in this layer
      - Create EV, DEC, or DB records in this layer
      - Apply changes to the repository
    template_refs: []

  - layer: administrative
    label: GT-115 design baseline selection administration
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - Completed GT-115 selection report
      - Human-approved selected DC id (or NONE)
      - Approved SPEC, ARCH, TD
    scope_boundary: >
      Administer GT-115 outcomes: freeze the candidate pool (set DCs to Candidate),
      allocate EV/DEC/DB ids, create EV record with selection report, create DEC
      record for GT-115, update DC statuses (Selected/Rejected), author the Approved
      DB from the selected DC, update INDEX.md.
    stop_condition: >
      Exactly one DC has status Selected (or outcome is FAIL/NONE); all other candidate
      DCs have status Rejected; one DB with status Approved exists for the CH;
      EV and DEC records exist; INDEX.md updated.
    deliverables:
      - DC with status Selected (dc/DC-<CH_NUM>-<UUID>.md)
      - All other candidate DCs with status Rejected
      - DB with status Approved (db/DB-####.md)
      - EV record for GT-115 selection report (ev/EV-####.md)
      - DEC record for GT-115 (dec/DEC-####.md)
      - INDEX.md updated
    forbidden_actions:
      - Change DC content beyond the YAML status field
      - Change CH status (CH remains Ready through GT-115)
      - Author DB before a DC is formally Selected
      - Introduce design decisions in DB not present in the Selected DC
    template_refs:
      - lantern/templates/EV_TEMPLATE__GT115_SELECTION_REPORT.md
      - lantern/templates/DEC_TEMPLATE__GT115_SELECTION.md
      - lantern/templates/TEMPLATE__DB.md

context_slots:
  - slot_id: candidate_authoring_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context from design_candidate_authoring: the candidate DC records
      that will be compared at GT-115.
  - slot_id: ci_authoring_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the ci_authoring workbench that follows GT-115 PASS.
      Injected when CI authoring is the next step.
```

# Design Selection Charter

## Routing & applicability

This workbench covers GT-115 (Design Baseline Selection). Use it to analyze competing
DC candidates and administer the GT-115 decision, including authoring the Approved DB.

**When to use this workbench:**
- Running the GT-115 selection analysis against a pool of Candidate DCs (authoring layer).
- Administering GT-115 outcomes: updating DC/DB statuses, creating EV/DEC records (administrative layer).

**Hard stops:**
- All DCs in the comparison pool must have `status: Candidate` before selection begins.
- The SPEC, ARCH, and TD envelope must be Approved before GT-115.
- Do not update DC statuses or create records during the analysis layer.
- Posture constraint: `requires_candidate_comparison`.

## Authoring layer — GT-115 design candidate selection analysis

Produce the GT-115 selection report.

1. Pre-flight (block if violated): confirm CH is Ready with non-empty assessment
   criteria and validation target; confirm Approved SPEC, ARCH, and TD exist; confirm
   all provided DCs have `status: Candidate`.
2. Reconstruct the locked baseline as a checklist from CH + SPEC + ARCH + TD: assessment
   criteria, constraints (must_not_change, out_of_scope), validation target,
   TD coverage expectations.
3. For each Candidate DC, evaluate PASS/FAIL for classes A-E with evidence:
   - A: CH alignment and scope lock (verbatim criteria/constraints match, no expansion)
   - B: Upstream baseline conformance and record validity (SPEC/ARCH/TD coherence,
     required header fields, no placeholders)
   - C: Compatibility posture explicit (what is frozen, what changes, constraints preserved)
   - D: Design completeness (implementation latitude sub-lists present, no delegation)
   - E: GT-115 comparison posture (comparison notes, tradeoffs explicit, no CI artifacts)
4. Record all material findings in one structured findings ledger (finding ID, DC id,
   claim, evidence, governing rule, blocker class, severity, confidence, remediation,
   outcome effect, disposition).
5. Apply selection logic: if one DC passes all classes → recommend it; if multiple pass
   → rank by tightest scope lock, strongest SPEC/ARCH conformance, strongest TD
   traceability; if none pass → NONE ACCEPTABLE with minimal remediation list.
6. Include a `GT-115 → DB/GT-120` handoff section.

## Administrative layer — GT-115 design baseline selection administration

Run this layer after human approval of the selection outcome.

1. Freeze the candidate pool: set any Draft DC to Candidate (status field only).
2. Allocate EV, DEC, and DB ids using the allocator tool.
3. Create `ev/EV-####.md` from the GT-115 selection report template, including the
   full selection report and a `GT-115 → DB/GT-120` handoff section.
4. Create `dec/DEC-####.md` with gate GT-115, outcome PASS/FAIL, selected DC id,
   Approved DB id (when PASS), rationale grounded in the selection report.
5. On PASS: set selected DC to `status: Selected`; set all other candidate DCs to
   `status: Rejected`; author the DB from the Selected DC using the DB authoring guide
   (extract fixed commitments, downstream latitude, and reopen conditions; do not
   introduce design decisions not present in the Selected DC).
6. Set DB `status: Approved` only when all required fields are complete and
   non-placeholder.
7. Update INDEX.md for DCs, DB, EV, and DEC.
8. Run GT-115 consistency checks (§8) before closing.
