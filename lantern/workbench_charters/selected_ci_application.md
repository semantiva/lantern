```yaml
schema_id: lantern.operator.workbench_charter.v1
charter_id: charter.selected_ci_application
title: Selected CI Application Charter
workbench_ref: selected_ci_application
gate_refs:
  - GT-130
artifact_families:
  - CI
layers:
  - layer: administrative
    label: Selected CI application
    transaction_moment: commit
    transaction_posture: administration_authorized
    required_inputs:
      - Selected CI (status Selected)
      - Approved DB
      - Approved TD
      - GT-120 PASS DEC
    scope_boundary: >
      Apply the Selected CI's changes to the product repository against the declared
      baseline branch/commit. This layer covers applying changes, running any
      integration steps needed to produce a committed product state, and staging the
      product repo for GT-130 verification. The Selected CI, DB, and TD remain locked
      throughout; no design or test truth is modified.
    stop_condition: >
      The Selected CI's intended changes are applied to the product repository and
      committed; the product repo state is clean and the commit SHA is known; the
      state is ready for GT-130 verification execution.
    deliverables:
      - Committed product repository revision with Selected CI changes applied
    forbidden_actions:
      - Modify the Selected CI content (status field only is allowed later)
      - Modify DB or TD records
      - Perform GT-130 verification evidence collection in this layer
      - Widen the allowed_change_surface beyond what is declared in the Selected CI
    template_refs: []

context_slots:
  - slot_id: ci_selection_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context from ci_selection workbench: the GT-120 selection report
      and handoff notes for the Selected CI.
  - slot_id: verification_context
    injected_by: context-injection engine (deferred)
    description: >
      Adjacent context for the verification_and_closure workbench that follows.
      Injected when GT-130 verification is the next step.
```

# Selected CI Application Charter

## Routing & applicability

This workbench covers the lifecycle span from GT-120 PASS to GT-130. Use it to apply
the Selected CI to the product repository in preparation for GT-130 verification.

**When to use this workbench:**
- Applying the Selected CI's changes to the product repo (administrative layer).
- Resolving product-repo integration issues discovered during application.

**Hard stops:**
- Exactly one CI for the governing CH must have `status: Selected` before this
  workbench is active. If no CI is Selected, return to GT-120.
- Do not perform GT-130 verification evidence collection here; that belongs to
  `verification_and_closure`.
- Posture constraint: `product_writes_permitted`.

## Administrative layer — Selected CI application

Apply the Selected CI and prepare the product repository for GT-130 verification.

1. Confirm preconditions: Selected CI exists, Approved DB exists, Approved TD exists,
   product repo is at the baseline declared in `baseline.branch_or_commit`.
2. Apply the Selected CI's changes as specified in its `## Drop-In Pack (REQUIRED)`.
   Follow drop-in instructions exactly — do not improvise implementation beyond
   the drop-in pack.
3. If the application surfaces a late integration gap that prevents a clean landing
   (a GT-130 bounded extension scenario), document it immediately and check the
   extension conditions:
   - The gap was discovered during application, not anticipated.
   - Extra paths are enumerated explicitly.
   - The extension closes only the integration-consistency gap.
   - Specifications, tests, DB, and TD remain unchanged.
   If conditions are met, proceed; the extension will be recorded in GT-130 EV/DEC.
4. Commit the product repo changes. The commit SHA will be recorded at GT-130.
5. Run a preliminary check (e.g., `python -m pytest tests/ -q`) to catch obvious
   failures before formal GT-130 verification. Address any pre-verification failures
   within the allowed_change_surface before proceeding.
6. Stage the product repo for GT-130 verification: clean worktree, known commit SHA.
