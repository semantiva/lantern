# GT-115 Administration Guide — v0.1.0


Status: **AUTHORITATIVE — Procedure**
Date (UTC): 2026-03-15
Revision note: expands the earlier skeletal GT-115 administration draft into a full deterministic procedure.

Purpose: complete the required administration tasks for a GT-115 design baseline selection decision, in a way that is reproducible and mechanically checkable.

Normative anchors:
- `design_candidate_authoring_guide_v0.1.0.md` (DC record shapes + directory structure)
- `design_baseline_authoring_guide_v0.1.0.md` (DB record shape + extraction discipline)
- `lantern/preservation/EPISTEMIC_FRAME.md` (record invariants)
- `lantern/preservation/GATES.md` (GT-115 requirements)
- `lantern/preservation/WORKSPACE_TOPOLOGY.md` (multi-repo posture)

---

### 0. Preconditions (before running GT-115 administration)

These are administrative requirements, not evaluation criteria.

1) Upstream envelope lock:
- GT-115 administration requires at least one Approved SPEC for the governed scope.
- GT-115 administration requires at least one Approved ARCH for the governed scope.
- GT-115 administration requires an Approved TD set for the governing `CH-####`.
- If the SPEC, ARCH, or TD envelope is missing or not `Approved`, GT-115 is blocked before administration begins.

2) Candidate pool eligibility:
- Each DC that will be compared at GT-115 MUST have DC header `status: "Candidate"`.
- If any DC is still `Draft`, promote it to `Candidate` (Draft → Candidate promotion is a status-only administrative step; it MUST NOT change the technical substance of the DC) or exclude it with an explicit rationale in the DEC.

3) Registry alignment:
- Each Candidate DC MUST appear in `INDEX.md` at the governance repo root with status `Candidate` before the selection report is approved.

4) Selection report exists:
- This procedure assumes the selection analysis report already exists (as chat output or a draft file), produced by running `lantern/authoring_contracts/design_candidate_selection_guide_v0.1.0.md`.
- A human has approved the chosen candidate (or explicitly overridden the assistant's recommendation).

5) Stability:
- Do not add or remove Candidate DCs during evaluation. If a Candidate becomes invalid, record an explicit exclusion rationale in the GT-115 decision record.

---

## Definitions (for this procedure)

- "Candidate pool": the set of DC ids actively considered at GT-115 for a given `CH-####`.
- "Selection report": the human-readable evaluation output produced by running `lantern/authoring_contracts/design_candidate_selection_guide_v0.1.0.md`.

---

## Inputs (required)

- `CH_ID` (e.g., `CH-0001`)
- `SPEC_ID(s)` — the Approved SPEC(s) governing the scope
- `ARCH_ID(s)` — the Approved ARCH(s) governing the scope
- Approved `TD` ids anchored to `CH_ID`
- Candidate pool DC ids (1+), all anchored to `CH_ID`
- Human-approved selected DC id (one of the candidate pool ids), OR an explicit "NONE" outcome
- The selection report text (as produced by the selection guide)

Note: GT-115 requires a minimum of one Candidate DC. A pool of one DC is valid (mandatory gate still applies).

---

## Outputs (what "done" means)

GT-115 administration is complete only when ALL are true:

A) SSOT statuses are coherent
- Exactly one DC in the candidate pool has `status: "Selected"` OR the Decision outcome is "FAIL / NONE SELECTED".
- All non-selected DCs in the candidate pool have `status: "Rejected"`.
- No DC outside the candidate pool is accidentally modified.
- Exactly one DB with `status: "Approved"` exists for `CH_ID` (if Outcome is PASS).

B) Audit trail exists (stored under canonical paths)
- One Evidence record exists for the selection report: `ev/EV-####.md`
- One Decision record exists for the GT-115 outcome: `dec/DEC-####.md`
- `INDEX.md` at the governance repo root links both records and reflects updated DC and DB statuses.

C) No CH status drift
- The CH status MUST remain `Ready` after GT-115. (CH becomes `Addressed` only at GT-130.)

---

## Procedure (deterministic)

### Step 1 — Freeze the candidate pool (status hygiene)

For each DC in the candidate pool:

1) Open `dc/<DC_ID>.md`.
2) In the YAML header, set:
   - `status: "Candidate"` (only if it is currently `Draft`).

Do NOT change anything else in DC files at this step.

Rationale: `Candidate` is the explicit "submitted for selection" status in `lantern/preservation/EPISTEMIC_FRAME.md`. It makes the GT-115 decision auditable even if selection is delayed.

### Step 2 — Allocate new EV, DEC, and DB ids

Use the authoritative Lantern allocator tool from the Lantern workflow product repository:

- `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DB --repo <path-to-ssot-repo>`

Normative rule:
- Manual directory scanning MUST NOT be used when the allocator tool is available.
- IDs are sequential, zero-padded (`EV-####`, `DEC-####`, `DB-####`), and are allocated only from their canonical directories.

### Step 3 — Create EV record for the selection report (required)

Create: `ev/EV-####.md`

Use template: `lantern/templates/EV_TEMPLATE__GT115_SELECTION_REPORT.md`

Header requirements:
- `applies_to_ch` MUST equal `CH_ID`
- `evidence_type` SHOULD be `selection_report`
- `references.dcs` MUST list the full candidate pool DC ids (in stable order)
- `artifacts` MUST include at least:
  - `kind: "path"` pointing to the CH file path
  - `kind: "path"` pointing to each DC file path (candidate pool)
  - `kind: "path"` pointing to `lantern/authoring_contracts/design_candidate_selection_guide_v0.1.0.md`
  - `kind: "path"` pointing to each Approved SPEC file used for the gate
  - `kind: "path"` pointing to each Approved ARCH file used for the gate
  - `kind: "path"` pointing to each Approved TD file used for the gate

Body requirements:
- Paste the selection report in full (or a faithful, unedited copy of it).
- Add a short "Human approval" line that states:
  - approved selected DC id, OR approved "NONE"
  - approver identity (name/team) if available
  - approval date/time in UTC

### Step 4 — Create DEC record for GT-115 (required)

Create: `dec/DEC-####.md`

Use template: `lantern/templates/DEC_TEMPLATE__GT115_SELECTION.md`

Header requirements:
- `applies_to_initiative` MUST match the CH `initiative_refs` field
- `applies_to_ch` MUST equal `CH_ID`
- `gate_id` MUST be `GT-115`
- `decision_type` MUST be `gate`
- `status` MUST be `Active`
- `outcome` MUST be `PASS` if a DC is selected and a DB is approved, otherwise `FAIL`
- `title` MUST be `GT-115 PASS for CH-####` or `GT-115 FAIL for CH-####` as applicable
- `references.evidence` MUST include the EV id created in Step 3
- `references.db` MUST include the approved DB id when the outcome is PASS
- `references.ch` MUST include `CH_ID`
- `references.td` MUST include the Approved TD ids used for the gate
- `references.spec` MUST include the Approved SPEC ids used for the gate
- `references.arch` MUST include the Approved ARCH ids used for the gate
- `references.dcs` MUST include all candidate pool DC ids and may list the selected DC first
- `references.issues` SHOULD include the issue ids routed into the CH

Body requirements:
- Keep the `# GT-115 Decision` heading for template compatibility.
- Include a `## Decision` section.
- Include the lines:
  - `Decision: PASS | FAIL`
  - `Outcome: PASS | FAIL`
  - `Gate: GT-115`
  - `Selected DC: <dc-id> | NONE`
  - `Approved DB: <db-id>` when PASS
- Add a `## Decision rationale` section grounded in the selection report.

### Step 5 — Update DC statuses (finalize the selection)

If Outcome is `PASS` (a DC is selected):

- In the selected DC file header: set `status: "Selected"`.
- In every other candidate pool DC file header: set `status: "Rejected"`.

If Outcome is `FAIL` (none selected):

- Keep candidate pool statuses as `Candidate` (or `Draft`) and do NOT mark any DC as `Selected`.
- Optionally mark clearly-invalid candidates as `Rejected` only if the human explicitly wants them retired from future consideration.

Rule: status changes MUST be limited to the YAML `status:` field only.

### Step 6 — Author the Approved DB (required if Outcome is PASS)

Create: `db/DB-####.md`

Use the DB id allocated in Step 2.

Authoring rules (follow `design_baseline_authoring_guide_v0.1.0.md` in full):

- `db_id` MUST equal the allocated DB id.
- `source_dc_id` MUST reference the Selected DC id.
- `applies_to_ch` MUST equal `CH_ID`.
- `test_definition_refs` MUST list the same Approved TD set used at GT-115.
- `governed_scope` MUST match or be bounded by the Selected DC's `governed_scope`.
- `## Implementation Latitude` MUST contain:
  - non-empty fixed commitments list
  - non-empty downstream latitude list
  - non-empty reopen GT-115 conditions list
- Set `status: "Approved"` only when all required fields are complete and non-placeholder.

If the Selected DC is ambiguous on any required design commitment:
- Set `status: "Draft"` and add `## Blocking Items` referencing the exact DC section that needs clarification.
- GT-120 remains blocked until the DB is promoted to `Approved`.

### Step 7 — Update `INDEX.md` at the governance repo root (registry update)

Update four sections:

1) "Design Candidates (DC)"
- Ensure each candidate pool DC entry's "Status:" matches the DC header (`Selected` / `Rejected` / `Candidate` / `Draft`).

2) "Design Baselines (DB)"
- Add the new `DB-####` entry (if PASS) with status `Approved`.
- If this DB supersedes a prior DB, update the prior DB entry to `Superseded`.

3) "Decisions"
- Add the new `DEC-####` entry (GT-115 selection decision).

4) "Evidence"
- Add the new `EV-####` entry (GT-115 selection report evidence).

### Step 8 — Consistency checks (required)

Before considering GT-115 closed, verify:

- The selected DC id (if any) remains anchored to `CH_ID` and the CH `initiative_refs` field is propagated into the EV/DEC headers.
- The approved DB `source_dc_id` matches the selected DC id.
- The approved DB `applies_to_ch` matches `CH_ID`.
- The approved DB `test_definition_refs` are coherent with the Approved TD set used for the gate.
- Exactly one DC for `CH_ID` has `status: "Selected"` (if Outcome is PASS).
- Exactly one DB for `CH_ID` has `status: "Approved"` (if Outcome is PASS).
- All file links in `INDEX.md` at the governance repo root resolve and point to existing files.
- No prior Approved DB for the same scope remains in `Approved` state (if a supersession occurred).

If any check fails, treat GT-115 as incomplete and do not proceed to GT-120.

---

## AI assistant administrative prompt (optional; paste-ready)

Use this when you want an assistant to generate the exact file edits (without re-evaluating candidates):

1) Provide the assistant:
- the `CH_ID`
- the candidate pool DC ids
- the human-approved selected DC id (or "NONE")
- the complete selection report text

2) Ask the assistant:

"Produce a GT-115 Administration Patch Pack:
- the full contents for EV-#### and DEC-#### (allocate ids using `python tools/allocate_lantern_id.py`)
- the full contents for DB-#### (allocate id using `python tools/allocate_lantern_id.py`; author using `design_baseline_authoring_guide_v0.1.0.md`)
- unified diffs for DC header `status` updates (candidate → selected/rejected)
- a unified diff patch for `INDEX.md` updates at the governance repo root

Hard rules:
- Do not change any DC content outside the YAML `status:` field.
- Do not change the CH status.
- Set DB `status: 'Approved'` only if all required DB fields are non-placeholder; otherwise set `Draft` with `## Blocking Items`."
