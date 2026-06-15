```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.ci_authoring
title: CI Authoring Charter
workbench_ref: ci_authoring
gate_refs:
  - GT-120
artifact_families:
  - CI
layers:
  - layer: authoring
    label: CI authoring
    transaction_moment: draft
    transaction_posture: analysis_only
    required_inputs:
      - Ready CH with Approved TD
      - Approved DB
    scope_boundary: >
      Author one or more Change Increment (CI) candidate records for a Ready CH,
      grounded in the locked CH + DB + TD envelope. Each CI is an implementation-only
      candidate: it may not redefine design truth, test truth, or CH problem statement.
      The CI covers the full declared change surface with paste-ready drop-ins.
    stop_condition: >
      At least one CI with status Candidate exists; every CI has complete required
      sections and drop-in coverage for its full allowed_change_surface; no
      placeholders in required fields; verification plan contains runnable commands
      with binary expected signals.
    deliverables:
      - CI record(s) with status Candidate (ci/CI-<CH_NUM>-<UUID>.md)
    forbidden_actions:
      - Redefine CH assessment criteria, DB design commitments, or TD oracle conditions
      - Leave allowed_change_surface entries without concrete drop-in coverage
      - Use aspirational or non-binary verification signals
    template_refs:
      - lantern/templates/TEMPLATE__CI.md

context_slots:
  - slot_id: design_baseline_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context from design_selection workbench: the Approved DB fixed
      commitments and downstream latitude that constrain CI authoring.
  - slot_id: ci_selection_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the ci_selection workbench that compares these CI
      candidates at GT-120.
```

# CI Authoring Charter

## Routing & applicability

This workbench covers the lifecycle span from GT-115 PASS to GT-120. Use it to
author CI candidate records that will be compared at GT-120.

**When to use this workbench:**
- Authoring a new CI for a Ready CH with an Approved DB.
- Iterating on an existing Draft CI to make it Candidate-eligible.

**Hard stops:**
- The governing CH must be Ready (GT-110 PASS) and the DB must be Approved (GT-115
  PASS) before CI authoring begins. Do not author CIs before GT-115.
- Posture constraint: `requires_approved_db`.

## Authoring layer — CI authoring

Produce an execution-grade CI inside the locked CH + DB + TD envelope.

1. Allocate the CI id: `python tools/allocate_lantern_id.py --artifact CI --ch
   CH-#### --repo <path>`. Create `ci/CI-<CH_NUM>-<UUID>.md`.
2. Set `design_baseline_ref` to the Approved DB id. Set `test_definition_refs` to
   the Approved TD set.
3. Declare `allowed_change_surface` as an explicit, bounded list. Include
   `__init__.py` only when it exposes/preserves the package surface for files already
   in scope; record `change_surface_justifications` for each such path.
4. Copy CH assessment criteria verbatim into `## Assessment Criteria Alignment`.
5. Copy CH constraints verbatim into `## Constraints`.
6. In `## Design Baseline Alignment`: confirm every fixed DB commitment is addressed
   and every prohibited deviation is absent.
7. In `## Drop-In Pack (REQUIRED)`: provide a coverage table mapping every change-
   surface entry to a drop-in (FULL-FILE, PATCH, REMOVE, or MECHANICAL-RULE).
   Include the full drop-in payloads; no "implement as needed" patterns.
8. In `## Commit Message (REQUIRED)`: provide a paste-ready commit message referencing
   both CH and CI ids.
9. In `## Verification Plan`: provide runnable commands with binary expected signals.
   Placeholder or aspirational signals are invalid.
10. Set `status: "Candidate"` when the package is complete and deterministic.
    Use `status: "Draft"` with `## Blocking Items` otherwise.
11. Ensure CI appears in INDEX.md and is referenced in the CH `related_cis` field.
