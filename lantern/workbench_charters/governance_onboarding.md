```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.governance_onboarding
title: Governance Onboarding Charter
workbench_ref: governance_onboarding
gate_refs: []
artifact_families:
  - INI
  - CH
  - TD
layers:
  - layer: authoring
    label: Initiative creation
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Planning intent or objectives for the new governance scope
    scope_boundary: >
      Bootstrap the governance workspace: create an Initiative record, define the
      objective, boundary, and candidate CH slices. Optionally author initial CH and
      TD records for the first execution slice. Does not write to the product repo;
      does not reference lantern runtime internals. The Initiative is the planning
      object above CH.
    stop_condition: >
      Initiative record exists with non-placeholder objective, scope boundary, and
      decomposition notes; at least one candidate CH slice identified; Initiative can
      proceed toward Ready once a derived CH reaches GT-110 PASS.
    deliverables:
      - Initiative record (ini/INI-####.md)
      - Initial CH record(s) if first slice authoring is included
      - Initial TD record(s) if first slice authoring is included
    forbidden_actions:
      - Assign DIP/SPEC/ARCH ownership to the Initiative record
      - Vendor or copy the Lantern runtime into the governed repository
      - Use Initiative status as a substitute for GT-110/GT-115/GT-120/GT-130 outcomes
    template_refs:
      - lantern/templates/TEMPLATE__INITIATIVE.md
      - lantern/templates/CH_TEMPLATE.md
      - lantern/templates/TD_TEMPLATE.md

context_slots:
  - slot_id: upstream_baseline_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the upstream_intake_and_baselines workbench when product
      baselines need to be established. Injected when DIP/SPEC/ARCH authoring is
      the next step.
```

# Governance Onboarding Charter

## Routing & applicability

This workbench covers governance onboarding and Initiative creation. It is
lifecycle-independent — it can be used at any time to bootstrap a new governance
scope or create a new Initiative.

**When to use this workbench:**
- Creating a new Initiative record for a planning scope.
- Decomposing an Initiative into candidate CH slices.
- Optionally authoring the first CH and TD for the first execution slice.

**Hard stops:**
- Do not instruct operators to vendor or copy the Lantern runtime; the product
  consumes it as an external package.
- Do not assign DIP/SPEC/ARCH ownership to the Initiative.
- Posture constraint: `supports_bootstrap_without_product_writes`.

## Authoring layer — Initiative creation

**Initiative authoring steps:**
1. Allocate the INI id: `python tools/allocate_lantern_id.py --artifact INI
   --repo <path>`. Create `ini/INI-####.md` from the Initiative template.
2. Write a clear objective and intended outcome (what success looks like at
   Initiative level, independent of any specific CH execution).
3. Declare the scope boundary: what is in scope and out of scope for this Initiative.
4. Write decomposition notes: how the Initiative breaks into CH slices. Apply the
   CH sizing checks (C1-C6 from INITIATIVE__DECOMPOSITION_AND_CH_SIZING.md) to
   each candidate CH slice.
5. List candidate CH slices with status `Proposed`. Reference existing product
   baselines (DIP/SPEC/ARCH) where applicable; do not assign ownership to the Initiative.
6. Set `status: "Proposed"` until at least one referenced CH is `Ready`.
7. Optionally, author the first CH slice and its TD inline (use `ch_and_td_readiness`
   workbench procedures for GT-110 readiness).
8. Ensure the Initiative is listed in INDEX.md.

**Sizing guidance for CH slices:**
- Each CH should address one coherent vertical slice of the Initiative.
- Avoid CHs that bundle unrelated primary outcomes (C5 failure mode).
- Avoid CHs with more than 5 "In scope" bullet items (C1 failure mode).
- Tests and documentation default to included; defer only with explicit rationale
  and a follow-on CH.
