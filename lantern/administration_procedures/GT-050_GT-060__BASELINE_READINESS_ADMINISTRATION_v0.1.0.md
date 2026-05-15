# GT-050/GT-060 Administration Guide — v0.1.0


Status: **AUTHORITATIVE — Procedure**
Date (UTC): 2026-03-15

Purpose: approve a Requirements Specification (SPEC) at GT-050 and an Architecture Definition (ARCH) at GT-060 as reusable baselines that anchor downstream change work.

These two gates share a procedure structure and are typically run in the same session after the SPEC and ARCH drafts are derived and the required derivation/coherence evidence has been assembled. They are documented together to avoid duplication but are independent gates: GT-050 PASS and GT-060 PASS are separate decisions recorded in separate DEC artifacts.

Normative anchors:
- `dip_authoring_guide_v0.1.0.md` (DIP record shape; ARCH and SPEC must derive from an Approved DIP)
- `lantern/preservation/EPISTEMIC_FRAME.md` (record invariants)
- `lantern/preservation/GATES.md` (GT-050 and GT-060 requirements)
- `lantern/preservation/WORKSPACE_TOPOLOGY.md` (multi-repo posture)

---

### 0. Preconditions (before running GT-050/GT-060)

1) Upstream gate posture:
- An Approved DIP exists for the governed scope (GT-030 PASS).
- Derivation linkage evidence is present for the SPEC and ARCH being reviewed.
- DIP/SPEC/ARCH coherence evidence is present for the current draft set.
- If any of the above inputs are missing, GT-050/GT-060 are blocked.

2) Artifacts in `Draft`:
- `spec/SPEC-####.md` exists and has `Status: Draft`.
- `arch/ARCH-####.md` exists and has `Status: Draft`.

3) Stability:
- Do not make substantive changes to SPEC or ARCH during GT-050/GT-060 evaluation. If a material gap is found, pause, update the artifact, refresh the derivation/coherence evidence, and then re-evaluate GT-050/GT-060.

---

## Definitions (for this procedure)

- "Derivation linkage": a traceable relationship between a SPEC or ARCH section and a specific source entry in the governing Approved DIP.
- "Acceptance criterion (AC)": a checkable claim in the SPEC that defines what must be true for the governed scope to be considered complete.
- "Baseline locator": an immutable reference (commit SHA or tag) to the SPEC or ARCH artifact at the point of approval.
- "Reusable baseline": a SPEC or ARCH with `Status: Approved` that may be referenced as an authoritative input by multiple CH records without re-derivation.

---

## Inputs (required)

- `SPEC_ID` (e.g., `SPEC-0001`) and `ARCH_ID` (e.g., `ARCH-0001`)
- `DIP_ID` — the governing Approved DIP
- Derivation linkage and coherence evidence supporting the current SPEC/ARCH draft set
- The full SPEC and ARCH texts as authored
- Human-approved outcomes: `PASS` or `FAIL` for each gate independently
- Baseline locators (commit SHA or tag) for each artifact, or explicit waivers

Note: GT-050 and GT-060 produce separate EV and DEC records. The procedure steps below apply independently to each artifact; where steps differ, this is noted explicitly.

---

## Outputs (what "done" means)

### PASS outcome (per gate)

A) Artifact status is correct
- GT-050 PASS: `SPEC_ID` has `Status: Approved`.
- GT-060 PASS: `ARCH_ID` has `Status: Approved`.
- If this SPEC/ARCH supersedes a prior one, the prior artifact has `Status: Superseded`.

B) Audit trail exists (stored under canonical paths)
- GT-050: one `EV-####.md` and one `DEC-####.md` in `ev/` and `dec/` respectively.
- GT-060: one `EV-####.md` and one `DEC-####.md` (separate ids from GT-050 records).

### FAIL outcome (per gate)

A) Artifact status unchanged
- The SPEC or ARCH remains `Status: Draft`.

B) Audit trail exists
- One `EV-####.md` and one `DEC-####.md` per failing gate.

---

## Procedure — GT-050 (SPEC Baseline Readiness)

### GT-050 Step 1 — Evaluate SPEC completeness (STOP if violated)

**S1) Header completeness**
- `Status` is `Draft`.
- `Derived from DIP` field exists and references an Approved DIP.
- `Supersedes` field exists (may be `None`).
- `Timestamp` is a valid ISO 8601 date.

**S2) Summary is substantive**
- `## Summary` non-empty; describes requirements scope without requiring DIP access for core semantics.

**S3) Scope is bounded**
- `## Scope` contains explicit "In scope" and "Out of scope" sub-lists.
- Each entry is a specific, bounded statement — not a sentiment.

**S4) Acceptance criteria are checkable**
- `## Acceptance criteria` is non-empty with at least one `AC-###` entry.
- Each AC is a checkable, binary claim (a reviewer can determine compliance without running code).
- Invalid: "AC-001: The system should work well." | Placeholder ACs.

**S5) Derivation linkage exists**
- At least one AC or scope statement is traceable to a specific DIP source entry or DIP constraint.
- The SPEC does not introduce scope that cannot be traced to the DIP.

**S6) Questions are resolved or non-blocking**
- All questions with `Blocking: YES` are `Status: Resolved`, OR carry an explicit waiver with rationale.

**S7) SPEC does not contain architectural decisions**
- No `## Key decisions` or explicit architectural choices.
- A SPEC that reads like an ARCH has overstepped and must be refactored.

**S8) Supersession is handled correctly (if applicable)**
- If `Supersedes` is non-empty, the referenced prior SPEC exists and is currently `Approved`.
- The SPEC body records the scope change.

**S9) Validation target signals are coherent (if present)**
- If `## Validation target signal definition` is present, each entry has a non-placeholder command and a binary expected signal.
- Aspirational signals (e.g., "expected signal: looks correct") are invalid.

### GT-050 Step 2 — Confirm or record baseline locator (SPEC)

Same as GT-030 Step 2 (commit SHA, tag, or explicit waiver with rationale).

### GT-050 Step 3 — Allocate EV and DEC ids (GT-050)

- `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`

### GT-050 Step 4 — Create EV record (GT-050)

Create: `ev/EV-####.md`

Use template: `lantern/templates/EV_TEMPLATE.md` (with gate-specific adaptations)

Header:
- `evidence_type` SHOULD be `spec_readiness_assessment`
- `artifacts` MUST include:
  - `kind: "path"` for the SPEC file
  - `kind: "path"` for the governing DIP file
  - `kind: "path"` for any derivation/coherence evidence artifact or review note used in the readiness session
  - `kind: "commit"` with repo name and baseline locator (or waiver)

Body (minimum coverage):

- **E1 — Completeness checklist**: outcome for each item S1–S9. For each FAIL, name the section and the specific deficiency.
- **E2 — Derivation linkage summary**: one line per key SPEC section stating which DIP source or constraint it traces to.
- **E3 — Baseline locator**: the SPEC baseline locator (commit SHA / tag / waiver rationale).
- **E4 — Derivation/coherence evidence references**: locators or identifiers for the supporting evidence confirming the current drafts remain derivable from the approved DIP and mutually coherent.
- **Human approval**: outcome (PASS/FAIL), approver, UTC timestamp.

### GT-050 Step 5 — Create DEC record (GT-050)

Gate: `GT-050`
Body structure same as GT-030 Step 5.

### GT-050 Step 6 — Update SPEC status (PASS action only)

- PASS: set `SPEC_ID` `Status: Approved`. If supersession occurred, update the prior SPEC to `Status: Superseded`.
- FAIL: leave `SPEC_ID` `Status: Draft`.

---

## Procedure — GT-060 (ARCH Baseline Readiness)

### GT-060 Step 1 — Evaluate ARCH completeness (STOP if violated)

**A1) Header completeness**
- `Status` is `Draft`.
- `Derived from DIP` field exists and references an Approved DIP.
- `Supersedes` field exists (may be `None`).
- `Timestamp` is a valid ISO 8601 date.

**A2) Summary is substantive**
- `## Summary` is non-empty.
- The summary describes the architecture scope, system boundary, and primary concerns without requiring the reader to open the DIP.

**A3) Architecture scope and intent**
- `## Architecture scope and intent` section is present and non-empty.
- System boundary and primary concerns are explicitly declared.

**A4) Key decisions are explicit**
- `## Key decisions` is non-empty with at least one recorded decision.
- Each decision is a substantive architectural choice, not a placeholder.
- Invalid: "DECISION-001: TBD." | Empty decision list.

**A5) Constraints and boundaries are checkable**
- `## Constraints and boundaries` is non-empty, OR explicitly states that no constraints apply with a rationale.
- Each constraint is checkable and coherent with the DIP's `## Constraints and non-goals`.

**A6) Derivation linkage exists**
- At least one `## Key decisions` entry or section is traceable to a specific DIP source entry or DIP constraint.
- The ARCH does not introduce scope that cannot be traced to the DIP.

**A7) Questions are resolved or non-blocking**
- All questions with `Blocking: YES` are `Status: Resolved`, OR carry an explicit waiver with rationale.

**A8) ARCH does not contain requirements**
- No acceptance criteria or SPEC-domain content embedded in the ARCH body.
- An ARCH that reads like a SPEC has overstepped and must be refactored.

**A9) Supersession is handled correctly (if applicable)**
- If `Supersedes` is non-empty, the referenced prior ARCH exists and is currently `Approved`.
- The ARCH body records the scope change.

### GT-060 Step 2 — Confirm or record baseline locator (ARCH)

Same as GT-030 Step 2.

### GT-060 Step 3 — Allocate EV and DEC ids (GT-060)

Allocate separately from GT-050 ids.

### GT-060 Step 4 — Create EV record (GT-060)

Same structure as GT-050 Step 4, adapted for ARCH:
- `evidence_type` SHOULD be `arch_readiness_assessment`
- `artifacts` reference the ARCH file instead of the SPEC file
- Body covers A1–A9 checklist items and key-decisions coverage summary

### GT-060 Step 5 — Create DEC record (GT-060)

Gate: `GT-060`

### GT-060 Step 6 — Update ARCH status (PASS action only)

Same as GT-050 Step 6, adapted for ARCH.

---

## Joint Step — Consistency checks (required; apply after both gates)

Before considering GT-050 and GT-060 closed, verify:

- `SPEC_ID` header `Status` is `Approved` (GT-050 PASS) or `Draft` (FAIL).
- `ARCH_ID` header `Status` is `Approved` (GT-060 PASS) or `Draft` (FAIL).
- If supersession occurred for either artifact, the prior artifact has `Status: Superseded`.
- EV and DEC records for both gates exist with correct gate ids.
- Baseline locators or waivers are recorded in both EV records.
- No blocking questions remain unresolved in either SPEC or ARCH.

If any check fails, treat the affected gate as incomplete.

---

## Back-pressure notes

| Failure condition | Recovery path |
|---|---|
| Acceptance criteria non-checkable | Refine SPEC ACs to be binary and specific; re-run GT-050 |
| Missing derivation linkage | Trace ARCH/SPEC sections to DIP; refactor scope if untraceable; refresh derivation evidence; re-run GT-050/060 |
| ARCH/SPEC contains out-of-scope content | Refactor into correct artifact; refresh coherence evidence; re-run GT-050/060 |
| Blocking question unresolved | Resolve and update artifact; re-run GT-050/060 |
| Drafts fail coherence review | Resolve contradictions, refresh coherence evidence, and re-run GT-050/060 |

---

## After GT-050/GT-060 PASS — what comes next

Approved SPEC and ARCH are now available as reusable baselines for CH authoring.

1. Derive one or more bounded CH slices from the approved baselines using `guides/INITIATIVE__DECOMPOSITION_AND_CH_SIZING_v0.1.0.md`.
2. Author CH records and run GT-110 (CH + TD readiness) using `change_intention_refinement_guide_v0.2.1.md` and `test_definition_authoring_guide_v0.1.0.md`.
