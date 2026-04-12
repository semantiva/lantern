# Change Intent refinement guide — GT-110 (Proposed → Ready) — v0.2.1


Status: **Guide** (execution guidance; MUST NOT conflict with the authoring contract)  
Date (UTC): 2026-03-01  
Supersedes: `change_intention_refinement_guide_v0.2.0.md`

## Purpose

This guide standardizes how to refine a Change Intent (CH) from `Proposed` to `Ready` by satisfying **GT-110: Input Kit Readiness (Entry Gate)** with explicit approved `TD` coverage plus:
- Evidence record(s) (EV), and
- a gate Decision record (DEC).

This guide is designed for **AI-assisted execution** with human review.

## Normative anchors

- `change_increment_authoring_guide.md` (record shapes + storage locations + boundaries)
- `lantern/preservation/EPISTEMIC_FRAME.md` (record invariants)
- `lantern/preservation/GATES.md` (GT-110 gate expectations)
- `lantern/preservation/WORKSPACE_TOPOLOGY.md` (multi-repo posture)
- `lantern/preservation/LANTERN_MODEL_BINDING.md` (canonical statuses + gate ids)
- `lantern/preservation/UPSTREAM_INPUT_ARTIFACTS.md` (TD posture)

## Scope

In scope:
- create/update CH records
- create/update the required TD artifacts referenced by the CH
- create EV record(s) required for GT-110
- create a DEC record to record the GT-110 outcome
- update `INDEX.md` (governance repository root) registry
- set CH status to `Ready` when GT-110 is satisfied

Out of scope:
- drafting DC candidates (starts after CH is `Ready`)
- drafting CI candidates (starts only after GT-115 has produced an Approved DB)
- implementing repo changes
- integration work / GT-130 verification

## Outputs (definition of done)

A CH is GT-110-ready when ALL are true:
1) the CH file is complete (header + body)
2) an approved TD set exists and covers the CH assessment criteria
3) required EV record(s) exist and are referenced by the CH header
4) a GT-110 DEC record exists and is referenced by the CH header
5) `INDEX.md` (governance repository root) reflects the updated CH status

## Procedure (deterministic)

### Step 0 — Gather pinned inputs (STOP if missing)

A CH MUST NOT become `Ready` if required upstream inputs are missing or unpinned.

Identify and pin (as applicable):
- Initiative(s) / planning anchor(s), if the CH is derived from an Initiative
- DIP(s): `dip/DIP-####.md`
- SPEC(s): `spec/SPEC-####.md`
- ARCH(s): `arch/ARCH-####.md`
- TD(s): `td/TD-####.md`
- Issue(s) / legacy SSOT references (paths or external ids)
- Blocking Questions (must be `Resolved` or explicitly waived in the DEC)

If upstream inputs do not exist yet, create them first (see `guides/SSOT_BLOB_INGESTION_v0.2.0.md`).

### Step 1 — Create or update the CH record

Location:
- `ch/CH-####.md`

If a new CH is being created, allocate the identifier using the authoritative allocator tool:
- `python tools/allocate_lantern_id.py --artifact CH --repo <path-to-ssot-repo>`

Rules:
- keep status `Proposed` until GT-110 evidence and decision exist
- if the problem statement changes materially, record a supersession Decision (DEC) or create a new CH
- if the CH is derived from an Initiative, ensure the CH is a bounded slice of that Initiative using `guides/INITIATIVE__DECOMPOSITION_AND_CH_SIZING_v0.1.0.md`

Dependency rule:
- If the CH depends on other CHs, declare them in the CH header field:
  - `depends_on_ch: ["CH-####", ...]`
- Default posture: unmet dependencies ⇒ CH MUST NOT be set to `Ready`
- Waiver posture: if proceeding despite unmet dependencies, the GT-110 EV and DEC MUST document the waiver and rationale.

Minimum CH body sections (recommended):
- Problem statement
- Scope (in / out)
- Constraints
- Assessment criteria (checkable)
- Validation target (TD-backed behavioral success statement)
- Inputs referenced (DIP/SPEC/ARCH/issues)
- Initiative linkage (if applicable)
- Gate expectations (GT-115 design posture; GT-120 selection posture; GT-130 validation expectations)

### Step 1A — GT-110 input sufficiency assessment (STOP/GO) (required)

Before producing GT-110 EV and DEC, you MUST complete the input sufficiency assessment section in the CH.

- Use the section `## 0. GT-110 Input Sufficiency Assessment (STOP/GO)` (see `lantern/templates/CH_TEMPLATE.md`).
- Apply this checklist (deterministic):

S1) Scope completeness
- `In scope` and `Out of scope` are non-empty lists.

S2) Constraints enumerated
- Constraints exist and contain no placeholders (no “TBD”, “…”, empty bullets).

S3) Assessment criteria are checkable and tied to product behavior
- Each criterion MUST be a checkable claim tied to observable, deterministic behavior (e.g., "Canonicalization yields deterministic CPSV1"), not subjective adjectives (e.g., "canonicalization is good").
- Criteria should reference concrete product surfaces (code, tests, configuration, artifacts) that implementers can validate.

S4) Validation target is concrete and TD-backed
- MUST define the behavioral success condition that the CH expects, expressed in terms that can be traced into TD cases.
- Runnable commands MAY appear later in downstream verification, but they are not the readiness truth at GT-110.
- If the only available validation language is aspirational or placeholder, the sufficiency decision is STOP.

S5) TD coverage exists and is non-shallow
- Each CH assessment criterion MUST be covered by at least one TD case.
- TD coverage MUST include criterion, preconditions, stimulus, observable, oracle, and failure condition.
- Missing or shallow TD coverage is STOP.

S6) Upstream inputs are pinned
- Every referenced DIP/SPEC/ARCH includes a baseline locator (path + immutable reference), OR the CH explicitly records a waiver posture to proceed without it.

S7) Dependencies are handled
- If `depends_on_ch` is non-empty: each dependency CH is already `Addressed`, OR a waiver is explicitly documented.

S8) No blocking Questions
- Any blocking Questions listed in the CH header are `Resolved`, OR explicitly waived with rationale.

S9) Technical substance — Problem statement must address a genuine technical need
- The problem statement MUST articulate a real product technical problem, defect, or capability gap that the CH will address.
- **Reject administrative-only CHs** (e.g., "Retrospective mapping of historical work to Lantern governance") as insufficient without corresponding technical substance.
- For retrospective CHs that extend an already-authoritative baseline (e.g., continuity Initiatives), upstream DIPs MUST carry self-contained technical intake summaries translated from legacy SSOT, not just source locators.

Stop/go rule:
- If any checklist item fails, set the sufficiency decision to `STOP`, keep CH status as `Proposed`, and do not record GT-110 as PASS.

### Step 2 — Produce GT-110 Evidence (EV)

Location:
- `ev/EV-####.md`

Allocate the EV identifier using the authoritative allocator tool:
- `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`

Minimum evidence coverage for GT-110 MUST include:

EV1) **Baseline locators for upstream inputs**
- For each referenced DIP/SPEC/ARCH: record path + immutable reference (commit SHA preferred; tag allowed), OR a waiver rationale.

EV1b) **TD coverage inventory**
- Record every TD used for the CH, its status, and the criteria it covers.
- Explicitly note any assessment criterion that lacks sufficient TD coverage.

EV2) **GT-110 sufficiency assessment summary**
- Copy the CH STOP/GO determination into the EV as a short summary, including what is still missing if `STOP`.

EV3) **Validation target check definition**
- Record the CH validation target and the corresponding TD-backed behavioral checks.
- If runnable commands are listed, mark them as downstream verification context rather than GT-110 readiness truth.

EV4) **Dependency handling evidence**
- If `depends_on_ch` is non-empty: record dependency statuses or waiver rationale.

Recommended: include an “Inputs inventory” list that enumerates every source document used.

### Step 3 — Record the GT-110 Decision (DEC)

Location:
- `dec/DEC-####.md`

Allocate the DEC identifier using the authoritative allocator tool:
- `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`

The GT-110 DEC MUST:
- declare `gate: GT-110`
- declare an outcome: `PASS` or `FAIL`
- reference the EV ids used
- record any waivers explicitly (including proceeding with Draft/Superseded upstream inputs)

Outcome rules:
- `PASS` ⇒ CH MAY transition to `Ready`
- `FAIL` ⇒ CH MUST remain `Proposed`

### Step 4 — Update CH header and registry

Update CH header fields:
- `required_evidence_for_gt110: ["EV-####", ...]`
- `required_decisions: ["DEC-####", ...]`
- `status: "Ready"` only when the DEC records `PASS`

Update the registry:
- `INDEX.md` (governance repository root) MUST list the CH and its current status, and MUST list the referenced EV/DEC ids under their sections.

## Common failure modes (avoid)

- Marking CH `Ready` without EV/DEC links.
- Marking CH `Ready` without approved, non-shallow TD coverage.
- Using unpinned upstream inputs (no baseline locator) without an explicit waiver.
- Treating aspirational runnable commands as the GT-110 readiness truth.
- Inventing acceptance criteria at DC or CI selection time (criteria must already exist in CH and TD).
- Mixing implementation instructions into the CH (belongs to CI).
- **Validation targets that are placeholders** (for example `TBD` or `Assume test will be written`). Use STOP posture instead.
