```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.upstream_intake_and_baselines
title: Upstream Intake and Baselines Charter
workbench_ref: upstream_intake_and_baselines
gate_refs:
  - GT-030
  - GT-050
  - GT-060
artifact_families:
  - DIP
  - SPEC
  - ARCH
  - INI
layers:
  - layer: authoring
    label: SPEC/ARCH derivation
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Approved DIP
    scope_boundary: >
      Derive SPEC and ARCH drafts from an Approved DIP. The operator translates
      DIP source inventory, constraints, and non-goals into checkable acceptance
      criteria (SPEC) and durable architectural decisions (ARCH). DIP content is
      not restated; it is the derivation basis.
    stop_condition: >
      SPEC draft and ARCH draft both exist with non-empty content traceable to the
      Approved DIP, no blocking questions open, and derivation/coherence evidence
      assembled for GT-050/GT-060.
    deliverables:
      - SPEC draft (spec/SPEC-####.md)
      - ARCH draft (arch/ARCH-####.md)
      - Derivation/coherence evidence notes
    forbidden_actions:
      - Restate DIP source inventory as architecture without tracing it to a DIP constraint
      - Embed acceptance criteria inside ARCH
      - Embed architectural decisions inside SPEC
    template_refs:
      - lantern/templates/SPEC_TEMPLATE.md
      - lantern/templates/ARCH_TEMPLATE.md

  - layer: validation
    label: DIP/SPEC/ARCH coherence review
    transaction_moment: validate
    transaction_posture: analysis_only
    required_inputs:
      - Approved DIP
      - SPEC draft
      - ARCH draft
      - Derivation and coherence evidence
    scope_boundary: >
      Verify that SPEC and ARCH remain mutually coherent and jointly derivable from
      the Approved DIP. The operator checks derivation linkage (each SPEC AC and ARCH
      decision traces to a DIP source entry or constraint) and coherence (SPEC and ARCH
      do not contradict each other).
    stop_condition: >
      Derivation linkage confirmed for all SPEC ACs and ARCH key decisions; no
      SPEC-ARCH contradictions; coherence evidence ready for GT-050/GT-060.
    deliverables:
      - Coherence assessment notes
    forbidden_actions:
      - Approve SPEC or ARCH in this layer (approval requires GT-050/GT-060 DEC)
    template_refs: []

  - layer: administrative
    label: GT-030 DIP lock
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - DIP in Draft with all blocking questions resolved
      - Human-approved GT-030 outcome
    scope_boundary: >
      Lock a DIP at GT-030: update DIP status to Approved, allocate EV and DEC ids,
      create EV record with completeness assessment (S1-S8), create DEC record for
      GT-030 PASS/FAIL, update INDEX.md. Precedes SPEC/ARCH derivation.
    stop_condition: >
      DIP status is Approved; EV and DEC records exist in canonical paths;
      DEC references the EV; INDEX.md reflects Approved status.
    deliverables:
      - DIP with status Approved (dip/DIP-####.md)
      - EV record (ev/EV-####.md)
      - DEC record for GT-030 (dec/DEC-####.md)
      - INDEX.md updated
    forbidden_actions:
      - Change DIP content beyond the status field
      - Skip EV record even for FAIL outcomes
    template_refs:
      - lantern/templates/EV_TEMPLATE.md
      - lantern/templates/DEC_TEMPLATE.md

  - layer: administrative
    label: Initiative to Ready
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - Initiative in Draft with at least one referenced CH in Ready
      - Objective, boundary, and decomposition posture established
    scope_boundary: >
      Move an Initiative from Draft to Ready: confirm objective and boundary are
      explicit, at least one derived CH is Ready (GT-110 evidence present), referenced
      product baselines are not owned by the Initiative, update Initiative status,
      update INDEX.md.
    stop_condition: >
      Initiative status is Ready; at least one linked CH is Ready; INDEX.md reflects
      Ready status.
    deliverables:
      - Initiative with status Ready (ini/INI-####.md)
      - INDEX.md updated
    forbidden_actions:
      - Assign DIP/SPEC/ARCH ownership to the Initiative record
      - Set Initiative to Ready without a linked Ready CH
    template_refs:
      - lantern/templates/TEMPLATE__INITIATIVE.md

  - layer: administrative
    label: GT-050/GT-060 SPEC and ARCH baseline readiness
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - SPEC draft and ARCH draft
      - Derivation/coherence evidence
      - Human-approved GT-050 and GT-060 outcomes
    scope_boundary: >
      Approve SPEC at GT-050 and ARCH at GT-060: evaluate completeness checklists
      (S1-S9 for SPEC; A1-A9 for ARCH), confirm baseline locators, allocate EV and
      DEC ids for each gate, create EV and DEC records, update SPEC and ARCH statuses
      to Approved, update INDEX.md. GT-050 and GT-060 are separate decisions recorded
      in separate DEC artifacts.
    stop_condition: >
      SPEC status is Approved; ARCH status is Approved; EV and DEC records exist for
      both gates; baseline locators recorded; INDEX.md reflects both Approved statuses.
    deliverables:
      - SPEC with status Approved (spec/SPEC-####.md)
      - ARCH with status Approved (arch/ARCH-####.md)
      - EV record for GT-050 (ev/EV-####.md)
      - DEC record for GT-050 (dec/DEC-####.md)
      - EV record for GT-060 (ev/EV-####.md)
      - DEC record for GT-060 (dec/DEC-####.md)
      - INDEX.md updated
    forbidden_actions:
      - Approve SPEC and ARCH in a single DEC record
      - Skip the completeness checklist for either artifact
    template_refs:
      - lantern/templates/EV_TEMPLATE.md
      - lantern/templates/DEC_TEMPLATE.md

context_slots:
  - slot_id: downstream_ch_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the CH-authoring and GT-110 workbench that consumes these
      Approved baselines. Injected when the downstream workbench is active.
```

# Upstream Intake and Baselines Charter

## Routing & applicability

This workbench covers DIP intake and the upstream baseline gates (GT-030, GT-050,
GT-060). It is the entry point for all governance work that requires new or updated
DIP, SPEC, or ARCH baselines, and for advancing an Initiative to Ready.

**When to use this workbench:**
- Authoring a new DIP or superseding an existing one (proceeds to GT-030).
- Deriving SPEC and ARCH drafts from an Approved DIP (authoring layer).
- Running coherence validation on a SPEC/ARCH draft set (validation layer).
- Administering GT-030 (DIP lock), GT-050 (SPEC readiness), or GT-060 (ARCH readiness).
- Advancing an Initiative to Ready status.

**Hard stops:**
- Do not begin SPEC/ARCH authoring before the DIP is Approved (GT-030 PASS required).
- Do not run GT-050/GT-060 without prior derivation and coherence evidence.
- Posture constraint: `requires_governance_workspace`, `startup_validated`.

## Authoring layer — SPEC/ARCH derivation

Derive SPEC and ARCH drafts from an Approved DIP.

**SPEC derivation steps:**
1. Open the Approved DIP. Identify every source entry in `## Source inventory` and
   every constraint and non-goal in `## Constraints and non-goals`.
2. Translate DIP scope into checkable acceptance criteria (AC-###). Each AC must be
   a binary, verifiable claim tied to observable product behavior. Aspirational or
   placeholder ACs are invalid.
3. Declare `## Scope` with explicit "In scope" and "Out of scope" sub-lists bounded
   by the DIP constraints and non-goals.
4. Do not include architectural decisions in SPEC. If an architectural choice is
   needed to complete an AC, record it in ARCH and cross-reference.
5. If a required semantic is absent from the DIP, return to DIP governance rather
   than inventing SPEC scope.

**ARCH derivation steps:**
1. Open the Approved DIP and the relevant SPEC draft. Identify all constraints and
   non-goals that constrain system structure.
2. Record each architectural decision in `## Key decisions`. Every decision must
   trace to a DIP source entry, DIP constraint, or SPEC AC that motivates it.
3. State decisions in timeless present tense. Do not narrate supersession, migration
   events, or transitional rules in ARCH. Transitional rules belong in the CH.
4. Do not restate SPEC acceptance criteria as architecture. Do not embed requirements
   in ARCH.
5. ARCH scope is determined by architectural coherence, not by CH execution convenience.

**Coherence check before proceeding:**
- Each SPEC AC is traceable to a DIP source or constraint.
- Each ARCH key decision is traceable to a DIP source, DIP constraint, or SPEC AC.
- SPEC and ARCH do not contradict each other on any shared claim.

## Validation layer — DIP/SPEC/ARCH coherence review

Perform the coherence review before GT-050/GT-060 administration.

1. For each SPEC acceptance criterion, confirm a traceable link to a DIP source
   entry or constraint exists. Record the linkage summary.
2. For each ARCH key decision, confirm a traceable link to a DIP source, DIP
   constraint, or SPEC AC exists.
3. Check for SPEC/ARCH contradictions: if any SPEC AC implies a structural
   requirement that conflicts with an ARCH decision, the contradiction must be
   resolved (refactor one or both) before GT-050/GT-060.
4. Confirm no out-of-scope expansions: SPEC must not introduce scope untraceable
   to DIP; ARCH must not introduce architectural claims untraceable to DIP or SPEC.
5. If all checks pass, assemble derivation/coherence evidence notes for the EV
   record (used at GT-050/GT-060).

## Administrative layer — GT-030 DIP lock

Run this layer when a human has approved a GT-030 outcome.

1. Confirm preconditions (§0 of the GT-030 Administration Guide): DIP is Draft,
   source inventory complete, no unresolved blocking questions, DIP stable.
2. Allocate EV and DEC ids using the allocator tool.
3. Create `ev/EV-####.md` covering items E1 (S1-S8 completeness checklist), E2
   (baseline locator), E3 (questions resolution), E4 (supersession if applicable).
4. Create `dec/DEC-####.md` with gate GT-030, outcome PASS/FAIL, rationale grounded
   in the EV assessment.
5. On PASS: set DIP `Status: Approved`; update INDEX.md.
6. On FAIL: leave DIP `Status: Draft`; record deficiencies in EV.
7. Run the §8 consistency checks before closing GT-030.

## Administrative layer — Initiative to Ready

Run this layer when advancing an Initiative to Ready status.

1. Confirm the Initiative record exists in `ini/INI-####.md` with non-empty
   objective, scope boundary, and decomposition notes.
2. Confirm at least one referenced CH is in `Ready` status (GT-110 PASS).
3. Confirm no product baselines (DIP/SPEC/ARCH) are listed as owned by the Initiative.
   They may be referenced but not owned.
4. Set Initiative `status: "Ready"` in the YAML header.
5. Update INDEX.md to reflect the Ready status.
6. Apply the bounds from `INITIATIVE__DECOMPOSITION_AND_CH_SIZING.md` sizing checks
   (C1-C6) to any new CH slices added to the Initiative.

## Administrative layer — GT-050/GT-060 SPEC and ARCH baseline readiness

Run this layer when a human has approved GT-050 and GT-060 outcomes.

1. Confirm preconditions: Approved DIP, SPEC and ARCH in Draft, derivation/coherence
   evidence assembled, no unresolved blocking questions.
2. For GT-050 (SPEC): evaluate S1-S9 completeness checklist. Allocate EV/DEC ids.
   Create `ev/EV-####.md` covering E1 (S1-S9), E2 (derivation summary), E3 (baseline
   locator), E4 (coherence evidence references). Create `dec/DEC-####.md` gate GT-050.
   On PASS: set SPEC `Status: Approved`.
3. For GT-060 (ARCH): evaluate A1-A9 checklist. Allocate separate EV/DEC ids.
   Create separate EV and DEC records. On PASS: set ARCH `Status: Approved`.
4. GT-050 and GT-060 are independent decisions in separate DEC artifacts. Do not
   combine them into a single DEC.
5. Update INDEX.md to reflect Approved statuses for both artifacts.
6. Apply the joint consistency checks before closing both gates.
