# Change Increment Selection Guide (v0.2.1)


Status: AUTHORITATIVE — Guide (selection analysis; must not conflict with SSOT specs or authoring contract)
Date (UTC): 2026-03-15
Supersedes: v0.2.0
Gate: GT-120 (Change Increment Selection)

Note: This guide assumes the multi-repo workspace posture defined in `lantern/preservation/WORKSPACE_TOPOLOGY.md`.
Semantic identifiers (statuses, gate ids) are bound via `lantern/preservation/LANTERN_MODEL_BINDING.md`.

CH_ID: `CH-####`

Revision note (2026-01-23)
- Added a deterministic “many-candidate mode” output structure for 8+ candidate pools.

You are performing a grounded Change Increment (CI) candidate comparison for `CH_ID` at gate **GT-120** against a locked `CH + DB + TD` envelope.

I will provide:
- the authoritative Change Intent (CH) record for `CH_ID`,
- the authoritative approved Design Baseline (DB) for `CH_ID`,
- the authoritative approved Test Definition set for `CH_ID`, and
- 1+ candidate Change Increments (CI) that claim to implement that CH (same `ch_id`).

Preconditions:
- All provided CIs MUST have CI header `status: "Candidate"` (eligible for GT-120 comparison).
- If a provided CI is still `Draft`, either promote it to `Candidate` before running selection (per the authoring guide), or exclude it and document the exclusion in the GT-120 decision record.

Your job is to recommend which CI should be selected for integration (**CI status → `Selected`**) or declare that none is acceptable. You must also produce a concise list of high-priority issues (selection blockers and integration risks).

Scope: selection only.

After the selection report is produced and a human approves the chosen candidate, GT-120 status administration MUST be completed using:
- `lantern/administration_procedures/GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md`

Until that point, do not update CI statuses and do not create DEC/EV records.

- Do NOT assess or implement the candidates in the repository.
- Do NOT apply patches, run commands, or update SSOT registries/statuses.
- Do NOT create or update DEC/EV records in this step.

## SSOT (must use; do not substitute)

- `lantern/preservation/EPISTEMIC_FRAME.md` (objects, IDs, statuses, anchoring)
- `lantern/preservation/GATES.md` (GT-110/120/130 decision logic and GT-120 output semantics)
- `Lantern/change_increment_authoring_guide_v0.2.1.md` (normative CI/CH record shape; required CI sections)
- The provided CH file for `CH_ID`: `ch/CH-####.md` (authoritative assessment criteria, constraints, validation target)
- The provided DB file for `CH_ID`: `db/DB-####.md` (authoritative design commitments and implementation latitude)
- The provided TD files for `CH_ID`: `td/TD-####.md` (authoritative test-definition coverage)

This guide is intentionally paired with:
- `change_intention_refinement_guide_v0.2.1.md` (how CH becomes `Ready` at GT-110 with approved TD coverage)
- `change_increment_authoring_guide_v0.2.1.md` (what a CI must contain to be selection-eligible)

## Hard anti-drift rules (apply regardless of stage)

- Treat the CH as the requirement anchor. A CI MUST NOT redefine the CH problem statement, constraints, assessment criteria, or validation target.
- Do not invent file paths, commands, flags, or contracts. Only accept references that exist in the repo snapshot you can read, or are explicitly pinned in the CI/CH records.
- Redaction protocol: treat any ellipsized / truncated excerpt (e.g., `...`) as non-authoritative; do not claim presence/absence based on truncated text.
- Do not “fix” candidates in your response. You may propose minimal remediation steps, but do not rewrite CI content.
- Treat placeholders in required CI content (e.g., `TBD`, empty required fields, “fill in later”) as FAIL for selection.

## Goal (what “best CI” means at GT-120)

Select the candidate that is most CH-aligned, DB-conformant, TD-traceable, and execution-grade for the next step (**integration**), with the lowest drift and contract risk.

Because GT-120 happens before integration, your judgment must be based on what is explicitly specified in the CI package:
- CH alignment and scope lock
- conformance to the approved DB
- conformance to the approved TD set
- bounded allowed change surface
- deterministic, paste-ready drop-ins
- contract/seams preservation posture
- verification plan and binary definition of done

## Inputs I will provide

- CH record: full text of `CH-####.md` (for `CH_ID`)
- Approved DB record: full text of `DB-####.md`
- Approved TD set: full text of the referenced `TD-####.md` files
- Candidate CI A..N: full text of each `CI-....md`
- (Optional) Repo snapshot pointer (zip/commit) if any CI references repo paths or contracts that need verification

## Mode selection (small vs many-candidate)

If the candidate pool contains **8 or more** CIs, you MUST use **Many-candidate mode** output (Section “Many-candidate mode (8+)”).

If the candidate pool contains **1–7** CIs, you MAY use either mode. Default posture: use Standard mode unless the pool is expected to grow.

Note: a pool of exactly **1** CI is valid (GT-120 remains mandatory). For a single-candidate pool, the head-to-head comparison step is omitted; the recommendation is either `Selected` (if the single CI passes all classes A–E) or `NONE ACCEPTABLE` (if it fails).

## Method (must follow exactly)

### 1) Pre-flight eligibility (BLOCK if violated)

#### 1A) Verify CH eligibility for GT-120

BLOCK selection if any of the following are false:

- CH header exists and parses as YAML.
- `ch_id` matches `CH_ID`.
- `status` is `Ready`.
- CH includes non-empty:
  - `assessment_criteria`
  - `validation_target`
- CH includes the constraints containers (they may be empty but MUST exist):
  - `constraints.must_not_change`
  - `constraints.out_of_scope`
- CH references GT-110 completion artifacts (existence checks are allowed only if you can read the repo snapshot):
  - `required_evidence_for_gt110` exists (non-empty)
  - `required_decisions` exists (non-empty)

#### 1A.1) Verify DB and TD envelope eligibility

BLOCK selection if any of the following are false:

- Exactly one Approved `DB-####` is provided for `CH_ID`.
- The DB declares `applies_to_ch: CH-####`.
- At least one Approved `TD-####` is provided for `CH_ID`.
- The provided TD set covers the CH assessment criteria relevant to the candidate pool.

If the envelope is ineligible, output:

`BLOCKED: CH not eligible for GT-120`

...and list each missing or invalid DB/TD element precisely.

If CH is ineligible, output:

`BLOCKED: CH not eligible for GT-120`

…and list each missing/invalid element precisely.

#### 1B) Verify each candidate CI is anchored and selection-eligible

For each CI candidate:

- CI header exists and parses as YAML.
- `ch_id` equals `CH_ID`.
- `ci_id` format matches `CI-<CH_NUM>-<UUID>`, where `CH_NUM` equals the numeric suffix of `CH_ID`.
- `status` is a CI status defined by `lantern/preservation/EPISTEMIC_FRAME.md`.

Hard rule:
- A CI MUST NOT be compared/selected at GT-120 unless its status is `Candidate`.

If anchoring is wrong, the CI is **ineligible** (FAIL) and must not be considered in head-to-head ranking.

### 2) Reconstruct the baseline (CH + DB + TD grounded; no assumptions)

From the CH, DB, and TD records, restate as a concise checklist:

- Assessment criteria (as written)
- Constraints (as written)
  - must_not_change
  - out_of_scope
- Validation target (as written)
- Fixed design commitments from the Approved DB
- Implementation latitude explicitly left open by the Approved DB
- TD coverage expectations relevant to the candidate pool

This locked envelope is the only basis for judging candidates.

### 3) Candidate-by-candidate evaluation (PASS/FAIL per class; evidence required)

For each candidate CI, mark PASS/FAIL with short evidence excerpts (quote only what you need).

Use the same classes for every candidate:

#### A) CH Alignment & Scope Lock

PASS requires:
- CI contains `## Assessment Criteria Alignment (verbatim from CH)` and the listed criteria match the CH `assessment_criteria` verbatim.
- CI contains `## Constraints (verbatim from CH)` and the `must_not_change` and `out_of_scope` lists match the CH constraints verbatim.
- CI does not introduce new requirements, constraints, or validation targets that expand or shift the CH.

#### B) DB / TD Conformance & Record Validity

PASS requires:
- CI has a valid `CI_HEADER` with required fields (at minimum):
  - `ch_id`, `ci_id`, `status`
  - `design_baseline_ref`
  - `test_definition_refs`
  - `ssot` (with a pinned `code` pointer)
  - `allowed_change_surface` (non-empty)
  - `verification` (must exist; at minimum `required_evidence` list may be empty but must exist)
- `design_baseline_ref` matches the provided Approved `DB_ID`.
- `test_definition_refs` are explicit and sufficient for the CI to be judged against the approved TD envelope.
- CI does not contradict fixed commitments in the Approved DB or assume latitude the DB does not permit.
- All referenced SSOT paths are concrete and verifiable from the provided snapshot (or explicitly pinned by pointer).
- No placeholders in required fields/required sections.

#### C) Contracts / Seams Inventory & Safety Posture

PASS requires:
- CI explicitly states what is contract-frozen (public signatures, CLI flags, schemas, file formats) for the touched surface.
- If the CI proposes contract changes, it enumerates them and states compatibility posture; otherwise it explicitly states contracts are preserved.
- CI does not conflict with CH `must_not_change` constraints.

#### D) Implementation Determinism (Drop-Ins + Coverage)

PASS requires:
- CI contains `## Drop-In Pack (REQUIRED)` and `## Commit Message (REQUIRED)`.
- Drop-ins are paste-ready and bounded (no “implement as needed”, no unbounded refactors).
- Drop-in coverage matches the `allowed_change_surface` (every entry has a concrete drop-in or a bounded mechanical rule with a binary verification gate).

#### E) Verification & Drift Resistance

PASS requires:
- CI contains `## Verification Plan` with runnable commands and expected signals and/or explicit artifact expectations.
- CI contains `## Definition of Done (binary)` that is testable and aligned to the CH `validation_target`.
- Verification does not depend on out-of-scope work or unpinned prerequisites unless the CH explicitly permits it.
- CI calls out key drift traps and how the integration step must avoid exceeding scope.

### 4) Selection logic

- If exactly one eligible candidate passes all classes A–E: recommend it as **Selected**.
- If multiple eligible candidates pass all classes A–E: rank them by (highest priority first):
  1) tightest scope lock (least ambiguity; strongest out-of-scope adherence),
  2) strongest DB conformance and lowest design-reopen risk,
  3) strongest TD traceability and evidence posture,
  4) strongest contract/seams inventory posture,
  5) smallest allowed change surface (least invasive),
  6) strongest determinism and verification posture.
- If none pass: declare `NONE ACCEPTABLE`, identify the best near-miss, and list the minimal remediation required for it to reach PASS (specific missing sections/fields and exact insertion points).

### Many-candidate mode (8+) (reporting rules; must follow exactly)

This mode preserves the same evaluation standards, but produces a compact report surface.

#### M1) Eligibility filter (reporting)

Partition the pool into three sets:

1) **Ineligible (exclude from ranking)**
   - fails anchoring in Step 1B (bad YAML header, wrong `ch_id`, bad `ci_id`, numeric anchor mismatch)

2) **Eligible but NOT ranking-eligible**
   - passes anchoring, but FAILS Class B (SSOT compliance / record validity)

3) **Ranking-eligible**
   - passes anchoring and PASSES Class B

Only **ranking-eligible** candidates may be selected.

#### M2) One comparison table (all eligible candidates)

Output exactly one markdown table with one row per **eligible** candidate (sets 2+3 above) using these columns:

| CI | Rank? | A | B | C | D | E | Top blockers (max 12 words) | Notes (max 12 words) |
|---|---|---|---|---|---|---|---|---|

Rules:
- `Rank?` MUST be `YES` only for ranking-eligible candidates, otherwise `NO`.
- For candidates that fail Class B, set A/C/D/E to `N/A (fails B)`.
- Keep “Top blockers” and “Notes” within the stated word caps.

#### M3) Fixed-size candidate capsules (all eligible candidates)

After the table, produce one capsule per **eligible** candidate using this exact template and caps:

**<CI_ID>**
- Rank eligible: YES | NO
- Class results: A=<PASS|FAIL|N/A>, B=<PASS|FAIL>, C=<PASS|FAIL|N/A>, D=<PASS|FAIL|N/A>, E=<PASS|FAIL|N/A>
- Blockers (max 2):
  - <...>
  - <...>
- Strengths (max 2):
  - <...>
  - <...>
- Minimal remediation (max 2):
  - <...>
  - <...>

Do not exceed the caps. If fewer than 2 items exist for a list, include only what exists.

#### M4) Recommendation and tie-break

If multiple ranking-eligible candidates pass all classes A–E, use the tie-break priority list from Section 4, and state the top 1–3 decisive reasons.

## Output (use the matching structure exactly)

### Standard mode output (1–7 candidates)

- Eligibility Summary
  - CH: ELIGIBLE | BLOCKED (+ reasons)
  - Candidate list: eligible vs ineligible (anchoring/record errors)

- Baseline Checklist (from CH)
  - Assessment criteria
  - Constraints (must_not_change, out_of_scope)
  - Validation target
  - Fixed design commitments from DB
  - TD coverage expectations

- Candidate Scorecards
  - Candidate A: PASS/FAIL per class (A–E) + evidence excerpts
    - High-priority issues (BLOCKER/HIGH)
  - Candidate B: PASS/FAIL per class (A–E) + evidence excerpts
    - High-priority issues (BLOCKER/HIGH)
  - (Candidate C/D if provided)

- Head-to-Head Comparison
  - Only among candidates that pass class B (SSOT Compliance & Record Validity)

- Recommendation
  - Selected candidate (A/B/C/…) OR NONE
  - Rationale (1–3 decisive reasons)
  - Minimal remediation required (if any), with exact insertion points (section names and/or header fields)

- Handoff Notes (GT-120 → GT-130)
  - What integration must preserve (CH baseline, contracts/seams, allowed change surface)
  - Evidence expectations for GT-130 (tests + artifacts) as declared in the selected CI
  - Known ambiguity hotspots to resolve before integration (if any)

### Many-candidate mode output (8+ candidates)

- Eligibility Summary
  - CH: ELIGIBLE | BLOCKED (+ reasons)
  - Ineligible CIs (exclude from ranking): list CI ids + 1-line reason each
  - Eligible CIs count: <N>
  - Ranking-eligible CIs count: <N>

- Baseline Checklist (from CH)
  - Assessment criteria
  - Constraints (must_not_change, out_of_scope)
  - Validation target
  - Fixed design commitments from DB
  - TD coverage expectations

- Candidate Comparison Table (all eligible CIs)
  - (single table as defined in M2)

- Candidate Capsules (all eligible CIs)
  - (capsules as defined in M3)

- Recommendation
  - Selected CI id OR NONE
  - Rationale (1–3 decisive reasons)
  - Minimal remediation required (if NONE), with exact insertion points (section names and/or header fields)

- Handoff Notes (GT-120 → GT-130)
  - What integration must preserve (CH baseline, contracts/seams, allowed change surface)
  - Evidence expectations for GT-130 (tests + artifacts) as declared in the selected CI
  - Known ambiguity hotspots to resolve before integration (if any)

## Evidence requirements

- Every PASS/FAIL must be justified with a short excerpt from the candidate/CH (or with a verifiable pointer in the repo snapshot you can read).
- If you claim something is missing, name it precisely (e.g., missing required section, missing CI_HEADER field, missing drop-in coverage for a specific `allowed_change_surface` entry).

## Close-out requirements

- Do NOT update `Lantern/change/INDEX.md`, CH status, CI statuses, or create DEC/EV records in this step.
- Do NOT apply changes or run integration. This step produces only a selection recommendation and issues list.
