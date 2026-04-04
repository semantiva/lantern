# GT-120 Administration Guide — v0.2.1


Status: **AUTHORITATIVE — Procedure**
Date (UTC): 2026-03-15
Supersedes: v0.2.0

Purpose: complete the required administration tasks for a GT-120 selection decision, in a way that is reproducible and mechanically checkable.

Normative anchors:
- `change_increment_authoring_guide_v0.2.1.md` (record shapes + directory structure)
- `lantern/preservation/EPISTEMIC_FRAME.md` (record invariants)
- `lantern/preservation/GATES.md` (GT-120 requirements)
- `lantern/preservation/WORKSPACE_TOPOLOGY.md` (multi-repo posture)

### 0. Preconditions (before running GT-120)

These are administrative requirements, not evaluation criteria.

1) Candidate pool eligibility:
- Each CI that will be compared at GT-120 MUST have CI header `status: "Candidate"`.
- If any CI is still `Draft`, promote it to `Candidate` (Draft → Candidate promotion is a status-only administrative step; it MUST NOT change the technical substance of the CI).

1A) Envelope lock:
- GT-120 administration assumes one Approved DB for the governing `CH-####`.
- GT-120 administration assumes an Approved TD set for the governing `CH-####`.
- If the DB or TD envelope is missing, GT-120 is blocked before status administration begins.

2) Registry alignment:
- Each Candidate CI MUST appear in `Lantern/change/INDEX.md` with status `Candidate` before the selection report is approved.

3) Stability:
- Do not add/remove Candidate CIs during evaluation. If a Candidate becomes invalid, record an explicit exclusion rationale in the GT-120 decision record.


---

## Definitions (for this procedure)

- “Candidate pool”: the set of CI ids actively considered at GT-120 for a given `CH-####`.
- “Selection report”: the human-readable evaluation output produced by running `Lantern/change_increment_selection_guide_v0.2.1.md`.

This procedure assumes the selection report already exists (as chat output or a draft file) and a human has approved the chosen candidate (or explicitly overridden the assistant’s recommendation).

---

## Inputs (required)

- `CH_ID` (e.g., `CH-0001`)
- `DB_ID` (e.g., `DB-0001`)
- Approved `TD` ids anchored to `CH_ID`
- Candidate pool CI ids (1+), all anchored to `CH_ID`
- Human-approved selected CI id (one of the candidate pool ids), OR an explicit "NONE" outcome

Note: GT-120 remains mandatory even if only one CI candidate exists. For a single-candidate pool, the selection procedure is identical; the head-to-head comparison step produces a single scorecard.
- The selection report text (as produced by the selection guide)

---

## Outputs (what “done” means)

GT-120 administration is complete only when ALL are true:

A) SSOT statuses are coherent
- Exactly one CI in the candidate pool has `status: "Selected"` OR the Decision outcome is “FAIL / NONE SELECTED”.
- All non-selected CIs in the candidate pool have `status: "Rejected"` (if a CI is explicitly rejected).
- No CI outside the candidate pool is accidentally modified.

B) Audit trail exists (stored under canonical paths)
- One Evidence record exists for the selection report: `ev/EV-####.md`
- One Decision record exists for the GT-120 outcome: `dec/DEC-####.md`
- `Lantern/change/INDEX.md` links both records and reflects updated CI statuses.

C) No CH status drift
- The CH status MUST remain `Ready` after GT-120. (CH becomes `Addressed` only at GT-130.)

---

## Procedure (deterministic)

### Step 1 — Freeze the candidate pool (status hygiene)

For each CI in the candidate pool:

1) Open `ci/<CI_ID>.md`.
2) In the YAML header, set:
   - `status: "Candidate"` (only if it is currently `Draft`).

Do NOT change anything else in CI files at this step.

Rationale: `Candidate` is the explicit “submitted for selection” status in `lantern/preservation/EPISTEMIC_FRAME.md`. It makes the GT-120 decision auditable even if selection is delayed.

### Step 2 — Allocate new EV/DEC ids

Use the authoritative Lantern allocator tool from the Lantern workflow product repository:

- `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`

Normative rule:
- manual directory scanning MUST NOT be used when the allocator tool is available.
- ids are sequential, zero-padded (`EV-####`, `DEC-####`), and are allocated only from their canonical directories.

### Step 3 — Create EV record for the selection report (required)

Create: `ev/EV-####.md`

Header requirements:
- `applies_to_ch` MUST equal `CH_ID`
- `references.cis` MUST list the full candidate pool CI ids (in stable order)
- `evidence_type` SHOULD be `selection_report`
- `artifacts` MUST include at least:
  - `kind: "path"` pointing to the CH file path
  - `kind: "path"` pointing to each CI file path (candidate pool)
  - `kind: "path"` pointing to `Lantern/change_increment_selection_guide_v0.2.1.md`
  - `kind: "path"` pointing to the Approved DB file
  - `kind: "path"` pointing to each Approved TD file used for the gate

Body requirements:
- Paste the selection report in full (or a faithful, unedited copy of it).
- Add a short “Human approval” line that states:
  - approved selected CI id, OR approved “NONE”
  - approver identity (name/team) if available
  - approval date/time in UTC

### Step 4 — Create DEC record for GT-120 (required)

Create: `dec/DEC-####.md`

Header requirements:
- `applies_to_ch` MUST equal `CH_ID`
- `decision_type` MUST be `gate`
- `references.evidence` MUST include the EV id created in Step 3
- `references.cis` MUST include:
  - all candidate pool CI ids, AND
  - the selected CI id first (if one is selected)

Body requirements:
- Gate: `GT-120`
- Outcome:
  - `PASS` if a CI is selected
  - `FAIL` if “NONE” is approved
- Rationale: 1 paragraph max, grounded in the selection report

### Step 5 — Update CI statuses (finalize the selection)

If Outcome is `PASS` (a CI is selected):

- In the selected CI file header: set `status: "Selected"`.
- In every other candidate pool CI file header: set `status: "Rejected"`.

If Outcome is `FAIL` (none selected):

- Keep candidate pool statuses as `Candidate` (or `Draft`) and do NOT mark any CI as `Selected`.
- Optionally mark clearly-invalid candidates as `Rejected` only if the human explicitly wants them retired from future consideration.

Rule: status changes must be limited to the YAML `status:` field only.

### Step 6 — Update `Lantern/change/INDEX.md` (registry update)

Update three sections:

1) “Change Increments (CI)”
- Ensure each candidate pool CI entry’s “Status:” matches the CI header (`Selected` / `Rejected` / `Candidate` / `Draft`).

2) “Decisions”
- Add the new `DEC-####` entry (GT-120 selection decision).

3) “Evidence”
- Add the new `EV-####` entry (GT-120 selection report evidence).

### Step 7 — Consistency checks (required)

Before considering GT-120 closed, verify:

- The selected CI id (if any) is in the CH’s `related_cis` list.
- The selected CI `design_baseline_ref` matches `DB_ID`.
- The selected CI `test_definition_refs` are coherent with the Approved TD set used for the gate.
- Exactly one CI for `CH_ID` has `status: "Selected"` (if Outcome is `PASS`).
- All file links in `Lantern/change/INDEX.md` resolve and point to existing files.

If any check fails, treat GT-120 as incomplete and do not proceed to GT-130.

---

## AI assistant administrative prompt (optional; paste-ready)

Use this when you want an assistant to generate the exact file edits (without evaluating candidates again):

1) Provide the assistant:
- the `CH_ID`
- the candidate pool CI ids
- the human-approved selected CI id (or “NONE”)
- the complete selection report text

2) Ask the assistant:

“Produce a GT-120 Administration Patch Pack:
- the full contents for EV-#### and DEC-#### (allocate ids using `python tools/allocate_lantern_id.py`)
- unified diffs for CI header `status` updates (candidate → selected/rejected)
- a unified diff patch for `Lantern/change/INDEX.md` updates

Hard rules:
- Do not change any CI content outside the YAML `status:` field.
- Do not change the CH status.”
