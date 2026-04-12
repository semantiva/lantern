# GT-130 Administration Guide — v0.1.0


Status: **AUTHORITATIVE — Procedure**
Date (UTC): 2026-03-15

Purpose: execute integration verification for the Selected CI against the locked CH + DB + TD baseline and complete required administration.

GT-130 is the final change-lifecycle gate. A PASS at GT-130 transitions the CI to `Verified` and the CH to `Addressed`.

Normative anchors:
- `change_increment_authoring_guide.md` (CI record shapes + verification plan contract)
- `allowed_change_surface_flexibilization.md` (bounded GT-130 extension posture)
- `lantern/preservation/EPISTEMIC_FRAME.md` (record invariants and status transitions)
- `lantern/preservation/GATES.md` (GT-130 requirements)
- `lantern/preservation/WORKSPACE_TOPOLOGY.md` (multi-repo posture)

---

### 0. Preconditions (before running GT-130)

These are administrative requirements, not evaluation criteria.

1) Selected CI exists:
- Exactly one CI for the governing `CH-####` must have `status: "Selected"`.
- If no CI is `Selected`, GT-130 is blocked. Return to GT-120.

2) Envelope lock:
- One Approved DB for `CH-####` must exist.
- An Approved TD set for `CH-####` must exist.
- The governing `CH-####` must have `status: "Ready"`.
- If any of these are missing, GT-130 is blocked.

3) Product repo state:
- The Selected CI's `baseline.branch_or_commit` must resolve in the target product repository.
- Verification is executed against the product repo, not the SSOT repo.
- GT-130 PASS closure requires a committed product repository revision. If verification exposed a dirty worktree, commit the product repo changes before closing GT-130 and record that commit SHA in the governance binding record.

4) Stability:
- Do not modify the Selected CI, DB, or TD records during verification. All content must remain locked as at GT-120 selection.

---

## Definitions (for this procedure)

- "Verification execution": running the commands declared in the Selected CI's `## Verification Plan` against the product repo at the declared baseline, and collecting actual outputs.
- "Verification report": the human-readable record of the verification execution, including commands run, actual outputs, and PASS/FAIL status per TD case covered by the CI.
- "Administrative demotion": a human decision to change a CI from `Selected` back to `Candidate` or to `Rejected` when GT-130 fails and the CI cannot be re-verified in its current form.
- "Blocked integration-surface gap": a late-discovered workflow-integration consistency gap that prevents closure even though the Selected CI already satisfies the approved change truth.

---

## Inputs (required)

- `CH_ID` (e.g., `CH-0001`)
- `CI_ID` — the Selected CI id (e.g., `CI-0001-<UUID>`)
- `DB_ID` (e.g., `DB-0001`)
- Approved `TD` ids anchored to `CH_ID`
- Product repo commit hash or tag against which verification was executed
- Human-approved outcome: `PASS` or `FAIL`
- The verification report text (actual execution output)

---

## Outputs (what "done" means)

GT-130 administration is complete only when ALL are true:

### PASS outcome

A) Status transitions are correct
- `CI_ID` has `status: "Verified"`.
- `CH_ID` has `status: "Addressed"`.

B) Audit trail exists (stored under canonical paths)
- One Evidence record exists with real verification evidence: `ev/EV-####.md`
- One Decision record exists for the GT-130 outcome: `dec/DEC-####.md`
- `INDEX.md` (governance repository root) reflects the updated CI and CH statuses.
- The governance binding record captures the committed product SHA used for the delivered code.

### FAIL outcome

A) Status transitions are correct
- `CI_ID` status is one of:
  - `Selected` (default; re-verification will be attempted after fixes), or
  - `Candidate` (administrative demotion; new GT-120 run required), or
  - `Rejected` (if the human decides the CI cannot be salvaged).
- `CH_ID` status remains `Ready`.

B) Audit trail exists
- One Evidence record with the failure evidence: `ev/EV-####.md`
- One Decision record: `dec/DEC-####.md`
- `INDEX.md` (governance repository root) reflects any status changes.

---

## Procedure (deterministic)

### Step 1 — Confirm pre-flight

Verify all preconditions in Section 0 before proceeding.

If any precondition fails, stop and document the blocker before returning to the appropriate upstream gate.

### Step 2 — Execute verification in the product repository

This step MUST be performed against the product repository at the baseline declared in the Selected CI's `baseline.branch_or_commit`.

For each item in the CI's `## Verification Plan`:
1. Run the declared command exactly as written.
2. Capture the actual output.
3. Compare actual output against the declared `expected_signal`.
4. Record PASS or FAIL for each verification item.

Additionally, for each TD case in the Approved TD set:
1. Map the TD case to the verification evidence.
2. Confirm the oracle is satisfied by the actual output.
3. Record PASS or FAIL per TD case.

Hard rules:
- Aspirational or placeholder evidence is invalid. Real command output, test results, or artifact paths MUST appear in the EV record.
- If the verification environment prevents a command from running, record this as a FAIL with the blocking reason; do not fabricate evidence.
- The commit hash recorded in the EV and binding record MUST identify the committed product repository revision used for the delivered code; do not close GT-130 against an uncommitted dirty worktree.
- If GT-130 discovers a blocked integration-surface gap, it may register a bounded extension only when all of the following are true: the gap was discovered during GT-130, the extra paths are enumerated explicitly, the extension closes only the integration-consistency gap, and the extension does not modify specifications, tests, design baselines, or architectural baselines.
- GT-130 extension authority is recorded in EV and DEC evidence only. Do not modify the Selected CI to register the extension.

### Step 3 — Allocate new EV and DEC ids

Use the authoritative Lantern allocator tool from the Lantern workflow product repository:

- `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`

Normative rule:
- Manual directory scanning MUST NOT be used when the allocator tool is available.
- IDs are sequential, zero-padded (`EV-####`, `DEC-####`), and are allocated only from their canonical directories.

### Step 4 — Create EV record for the verification run (required)

Create: `ev/EV-####.md`

Use template: `lantern/templates/EV_TEMPLATE__GT130_VERIFICATION_REPORT.md`

Header requirements:
- `applies_to_ch` MUST equal `CH_ID`
- `evidence_type` MUST be `verification_report`
- `references.ci` MUST equal `CI_ID`
- If GT-130 uses a bounded extension, the EV header MUST also include a `gt130_extension` block with `allowed_paths`, `rationale`, and all required guardrail booleans set to `true`.
- `artifacts` MUST include at least:
  - `kind: "path"` pointing to the CH file path
  - `kind: "path"` pointing to the CI file path
  - `kind: "path"` pointing to the Approved DB file path
  - `kind: "path"` pointing to each Approved TD file used for the gate
  - `kind: "commit"` with the product repo name and the commit hash or tag used for verification

Body requirements:
- Paste the full verification execution record (commands run, actual outputs, PASS/FAIL per verification item).
- Include an explicit TD case coverage table: TD case id → oracle → actual result → PASS/FAIL.
- If GT-130 uses a bounded extension, include a short section that lists the extra paths, explains why integration was blocked without them, and confirms that specifications, tests, design baselines, and architectural baselines remain unchanged.
- Add a short "Human approval" section that states:
  - outcome: PASS or FAIL
  - if FAIL: the human-approved CI disposition (`Selected` / `Candidate` / `Rejected`) and rationale
  - approver identity (name/team) if available
  - approval date/time in UTC

### Step 5 — Create DEC record for GT-130 (required)

Create: `dec/DEC-####.md`

Use template: `lantern/templates/DEC_TEMPLATE__GT130_VERIFICATION.md`

Header requirements:
- `applies_to_ch` MUST equal `CH_ID`
- `decision_type` MUST be `gate`
- `references.evidence` MUST include the EV id created in Step 4
- `references.ci` MUST equal `CI_ID`
- If GT-130 uses a bounded extension, the DEC header MUST also include a `gt130_extension` block with `evidence_ref` and `approved_paths`.

Body requirements:
- Gate: `GT-130`
- Outcome: `PASS` or `FAIL`
- Verified CI: `CI_ID`
- Rationale: 1 paragraph max, grounded in the verification evidence

### Step 6 — Update CI status (PASS or FAIL actions)

**If Outcome is PASS:**
- In `ci/<CI_ID>.md`, set `status: "Verified"`.

**If Outcome is FAIL (default — no demotion):**
- Leave `CI_ID` `status: "Selected"`. No change to CI file.

**If Outcome is FAIL and human approves demotion:**
- Set `status: "Candidate"` (if re-comparison at GT-120 is intended), OR
- Set `status: "Rejected"` (if the CI is retired from further consideration).

Rule: status changes MUST be limited to the YAML `status:` field only.

### Step 7 — Update CH status (PASS action only)

**If Outcome is PASS:**
- In `ch/<CH_ID>.md`, set `status: "Addressed"`.

**If Outcome is FAIL:**
- The CH status MUST remain `Ready`. Do NOT change it.

Rule: no other CH fields may be modified in this step.

### Step 8 — Update `INDEX.md` (governance repository root, registry update)

Update three sections:

1) "Change Increments (CI)"
- Update the `CI_ID` entry's "Status:" to match the CI header (`Verified` / `Selected` / `Candidate` / `Rejected`).

2) "Decisions"
- Add the new `DEC-####` entry (GT-130 verification decision).

3) "Evidence"
- Add the new `EV-####` entry (GT-130 verification report evidence).

4) "Binding record"
- Update `binding_record.md` in the governance repository with the committed product SHA used for the delivered code.
- If verification was performed against a dirty worktree, commit the product repository changes first, then record the resulting commit SHA before closing GT-130.

If CH status changed to `Addressed`, also update:

4) "Change Intents (CH)"
- Update the `CH_ID` entry's "Status:" to `Addressed`.

### Step 9 — Consistency checks (required)

Before considering GT-130 closed, verify:

- `CI_ID` header `status` matches the registry entry in `INDEX.md` (governance repository root).
- `CH_ID` header `status` matches the registry entry if a transition occurred.
- The EV record contains real (non-aspirational) verification evidence.
- The DEC record references the correct EV id.
- The binding record reflects the committed product SHA used for the delivered code.
- If PASS: exactly one CI for `CH_ID` has `status: "Verified"`.
- If PASS: `CH_ID` has `status: "Addressed"`.
- All file links in `INDEX.md` (governance repository root) resolve and point to existing files.

If any check fails, treat GT-130 as incomplete.

---

## FAIL disposition — back-pressure to upstream gates

| CI disposition after FAIL | Meaning | Next step |
|---|---|---|
| `Selected` (default) | CI will be fixed and re-verified | Fix the implementation, re-run GT-130 |
| `Candidate` (administrative demotion) | CI returned to selection pool | New GT-120 run required |
| `Rejected` | CI retired from consideration | Return to GT-120; select a different CI or author a new one |

Hard rule: if all candidate CIs for `CH_ID` are `Rejected` and GT-120 has no eligible pool, a new round of CI authoring is required before GT-120 can be re-run.

---

## AI assistant administrative prompt (optional; paste-ready)

Use this when you want an assistant to generate the exact file edits (without re-executing verification):

1) Provide the assistant:
- the `CH_ID`
- the `CI_ID` (selected CI)
- the `DB_ID`
- the approved TD ids
- the human-approved outcome: `PASS` or `FAIL`
- the complete verification execution text (actual outputs, test results)
- if FAIL: the CI disposition (`Selected` / `Candidate` / `Rejected`)

2) Ask the assistant:

"Produce a GT-130 Administration Patch Pack:
- the full contents for EV-#### and DEC-#### (allocate ids using `python tools/allocate_lantern_id.py`)
- a unified diff for CI header `status` update (Selected → Verified on PASS; Selected → Candidate/Rejected on demotion)
- a unified diff for CH header `status` update (Ready → Addressed on PASS only)
- a unified diff patch for `INDEX.md` (governance repository root) updates

Hard rules:
- Do not change any CI content outside the YAML `status:` field.
- Do not change CH content outside the YAML `status:` field.
- Do not change CH status to Addressed unless the outcome is PASS."


## Expectation-to-delivery review checklist (mandatory for MVP slices)
Before a GT-130 PASS is approved, the verification packet MUST explicitly answer all of the following:
- What initiative objective does this CH satisfy, and why does it exist in the roadmap now?
- What role does this CH play in the current execution order?
- Which approved SPEC / TD requirements are satisfied by the delivered result?
- Does the delivered result remain aligned with the approved ARCH baseline?
- What clean-state, reproducibility, and local verification evidence proves the result is repeatable?

Local test passage is necessary but not sufficient. A packet that omits this expectation-to-delivery review is incomplete for GT-130.
