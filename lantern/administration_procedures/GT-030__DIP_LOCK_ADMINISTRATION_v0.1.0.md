# GT-030 Administration Guide — v0.1.0


Status: **AUTHORITATIVE — Procedure**
Date (UTC): 2026-03-15

Purpose: lock a Design Input Pack (DIP) at GT-030, producing the Approved baseline that authorizes SPEC and ARCH derivation.

GT-030 is the entry gate for the upstream artifact family. A PASS at GT-030 transitions the DIP from `Draft` to `Approved` and unlocks SPEC/ARCH drafting plus the derivation/coherence evidence that will be carried into GT-050 and GT-060.

Normative anchors:
- `dip_authoring_guide_v0.1.0.md` (DIP record shape + authoring contract)
- `lantern/preservation/EPISTEMIC_FRAME.md` (record invariants)
- `lantern/preservation/GATES.md` (GT-030 requirements)
- `lantern/preservation/WORKSPACE_TOPOLOGY.md` (multi-repo posture)

---

### 0. Preconditions (before running GT-030)

1) DIP exists in `Draft`:
- `dip/DIP-####.md` exists and has `Status: Draft`.
- If no DIP exists yet, author one using `dip_authoring_guide_v0.1.0.md` before proceeding.

2) Source inventory is complete:
- `## Source inventory` is non-empty and each source has a stable identifier, type, and locator.

3) Questions posture:
- All questions marked `Blocking: YES` are `Status: Resolved`, OR the DIP explicitly records a waiver with rationale.
- Unresolved blocking questions MUST block GT-030.

4) Stability:
- Do not make substantive changes to the DIP after starting GT-030 evaluation. If a material gap is found during evaluation, pause, update the DIP, then re-evaluate from Step 1.

---

## Definitions (for this procedure)

- "Baseline locator": an immutable reference to the DIP artifact at a specific point in time (commit SHA preferred; tag allowed).
- "Waiver": an explicit recorded rationale for accepting a known gap or proceeding with an unresolved non-blocking question.
- "Source completeness": the DIP's `## Source inventory` accounts for all authoritative sources that materially shape scope, constraints, or non-goals.

---

## Inputs (required)

- `DIP_ID` (e.g., `DIP-0001`)
- The full DIP text as authored
- Human-approved outcome: `PASS` or `FAIL`
- Baseline locator (commit SHA or tag), or an explicit waiver if an immutable reference is not yet available
- Resolution evidence for any blocking questions, or waiver rationale

---

## Outputs (what "done" means)

GT-030 administration is complete only when ALL are true:

### PASS outcome

A) DIP status is correct
- `DIP_ID` has `Status: Approved`.
- If this DIP supersedes a prior DIP, the prior DIP has `Status: Superseded`.

B) Audit trail exists (stored under canonical paths)
- One Evidence record with the completeness assessment: `ev/EV-####.md`
- One Decision record for the GT-030 outcome: `dec/DEC-####.md`

### FAIL outcome

A) DIP status is unchanged
- `DIP_ID` remains `Status: Draft`.

B) Audit trail exists
- One Evidence record with the failure assessment: `ev/EV-####.md`
- One Decision record: `dec/DEC-####.md`

---

## Procedure (deterministic)

### Step 1 — Evaluate DIP completeness (STOP if violated)

Apply this checklist. A single FAIL means the outcome is `FAIL`; do not proceed to PASS unless all items are satisfied.

**S1) Header completeness**
- `Status` field exists and is `Draft`.
- `Supersedes` field exists (may be `None`).
- `Timestamp` field exists and is a valid ISO 8601 date.

**S2) Summary is substantive**
- `## Summary` is non-empty.
- The summary describes the scope and intent of the intake without requiring the reader to open the original source material.
- Invalid: "Summary to be written." | "See source document." | Empty.

**S3) Source inventory is traceable**
- `## Source inventory` is non-empty.
- Every entry has a `Source ID`, `Type`, and `Locator` (or opaque token with documented real locator).
- At least one source is traceable to a substantive downstream scope or constraint claim.
- Invalid: bulk archive listed with no decomposition; sources with no derivation linkage.

**S4) Constraints and non-goals are checkable and explicit**
- `## Constraints and non-goals` is non-empty, OR it explicitly states "No constraints apply" / "No scope exclusions are required" with a brief rationale.
- Each constraint is a checkable claim, not a sentiment.
- Each non-goal is an explicit exclusion that bounds downstream scope.

**S5) DIP does not contain requirements or architectural decisions**
- No `## Acceptance criteria` section or equivalent.
- No explicit solution choices framed as mandatory design decisions.

**S6) Questions are resolved or non-blocking**
- All questions with `Blocking: YES` are `Status: Resolved`, OR carry an explicit waiver with rationale.
- No placeholder questions (e.g., `Q-001: TBD`).

**S7) Self-contained intake**
- Core scope and constraint semantics are present in the DIP body; they do not reside only in an external source document.
- External source references are provenance, not semantic dependencies.

**S8) Supersession is handled correctly (if applicable)**
- If `Supersedes` is non-empty, the referenced prior DIP exists and is currently `Approved`.
- The DIP body records what changed and whether the supersession is total or partial.

### Step 2 — Confirm or record baseline locator

For a GT-030 PASS, an immutable baseline locator MUST be established or explicitly waived.

Options:
- **Preferred**: record a commit SHA or tag for the DIP file at its current state.
- **Acceptable waiver**: if no commit SHA is available, record an explicit waiver with rationale (e.g., "DIP authored in SSOT repo; commit SHA will be captured at time of EV creation").

This locator MUST appear in the EV record.

### Step 3 — Allocate EV and DEC ids

Use the authoritative Lantern allocator tool:

- `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`

Normative rule:
- Manual directory scanning MUST NOT be used when the allocator tool is available.

### Step 4 — Create EV record (required)

Create: `ev/EV-####.md`

Use template: `lantern/templates/EV_TEMPLATE.md` (with gate-specific adaptations below)

Header requirements:
- `applies_to_ch` is not applicable for upstream gates; set it to the governing Initiative id or omit if not supported by the template.
- `evidence_type` SHOULD be `dip_lock_assessment`
- `artifacts` MUST include at least:
  - `kind: "path"` pointing to the DIP file path
  - `kind: "commit"` with the repo name and the commit SHA or tag used as the baseline locator (or `kind: "waiver"` with a brief rationale if no immutable ref exists)

Body requirements (minimum coverage):

- **E1 — Input completeness**: record the checklist outcome for each item in Step 1 (S1–S8). For each FAIL, name the section and the specific deficiency.
- **E2 — Baseline locator**: record the DIP baseline locator (commit SHA / tag / waiver rationale).
- **E3 — Questions resolution**: for each blocking question, record status and resolution evidence or waiver.
- **E4 — Supersession handling** (if applicable): record the prior DIP id and confirm its status was updated or will be updated.

Body MUST include a short "Human approval" section:
- outcome: PASS or FAIL
- approver identity (name/team) if available
- approval date/time in UTC

### Step 5 — Create DEC record (required)

Create: `dec/DEC-####.md`

Use template: `lantern/templates/DEC_TEMPLATE.md`

Header requirements:
- `decision_type` MUST be `gate`
- `references.evidence` MUST include the EV id created in Step 4

Body requirements:
- Gate: `GT-030`
- Outcome: `PASS` or `FAIL`
- Rationale: 1 paragraph max, grounded in the EV completeness assessment

### Step 6 — Update DIP status (PASS action only)

**If Outcome is PASS:**
- In `dip/<DIP_ID>.md`, set `Status: Approved`.
- If this DIP supersedes a prior DIP, set the prior DIP `Status: Superseded`.

**If Outcome is FAIL:**
- Leave `DIP_ID` `Status: Draft`. Do NOT change it.
- The DIP should be revised to address the identified deficiencies before re-running GT-030.

Rule: status changes MUST be limited to the `Status:` header field only.

### Step 7 — Update Initiative record (PASS action)

If the DIP belongs to a governing Initiative (`ini/INI-####.md`):
- Confirm the DIP is listed under `inputs.dips` in the Initiative header.
- Update the Initiative's DIP reference to reflect Approved status if the Initiative record tracks per-artifact status.

### Step 8 — Consistency checks (required)

Before considering GT-030 closed, verify:

- `DIP_ID` header `Status` is `Approved` (PASS) or `Draft` (FAIL).
- If PASS and supersession occurred: prior DIP has `Status: Superseded`.
- EV record references a valid baseline locator or explicit waiver.
- DEC record references the EV id.
- No questions marked `Blocking: YES` and `Status: Open` remain in the DIP (if PASS).

If any check fails, treat GT-030 as incomplete.

---

## Back-pressure notes

| Failure condition | Recovery path |
|---|---|
| Blocking question unresolved | Resolve the question; update the DIP; re-run GT-030 |
| Source inventory incomplete | Add missing sources; establish derivation linkage; re-run GT-030 |
| DIP contains acceptance criteria / architectural decisions | Refactor into SPEC/ARCH scope; re-run GT-030 |
| External dependency not translated into DIP body | Translate or summarize; re-run GT-030 |
| Baseline locator not available | Obtain commit SHA / tag; or record explicit waiver with rationale |

---

## After GT-030 PASS — what comes next

1. Author SPEC draft from the Approved DIP.
2. Author ARCH draft from the Approved DIP.
3. Record the derivation and coherence evidence that GT-050 and GT-060 will review.
4. Run GT-050 (SPEC baseline readiness) and GT-060 (ARCH baseline readiness).

These steps are covered by:
- `guides/GT-050_GT-060__BASELINE_READINESS_ADMINISTRATION_v0.1.0.md`
- Operator templates E and F plus template G in `guides/AI_OPERATOR_INVOCATION_TEMPLATES_v0.2.1.md`
