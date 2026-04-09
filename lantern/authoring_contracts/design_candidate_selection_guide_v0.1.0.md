# Design Candidate Selection Guide (v0.1.0)


Status: AUTHORITATIVE — Guide (selection analysis; must not conflict with SSOT specs or authoring contract)
Date (UTC): 2026-03-15
Gate: GT-115 (Design Baseline Selection)

Note: This guide assumes the multi-repo workspace posture defined in `lantern/preservation/WORKSPACE_TOPOLOGY.md`.
Semantic identifiers (statuses, gate ids) are bound via `lantern/preservation/LANTERN_MODEL_BINDING.md`.

CH_ID: `CH-####`

You are performing a grounded Design Candidate (DC) comparison for `CH_ID` at gate **GT-115** against a locked `CH + SPEC + ARCH + TD` upstream envelope.

I will provide:
- the authoritative Change Intent (CH) record for `CH_ID`,
- the authoritative approved SPEC for the governed scope,
- the authoritative approved ARCH for the governed scope,
- the authoritative approved Test Definition set for `CH_ID`, and
- 1+ candidate Design Candidates (DC) that propose designs addressing that CH (same `ch_id`).

Preconditions:
- All provided DCs MUST have DC header `status: "Candidate"` (eligible for GT-115 comparison).
- If a provided DC is still `Draft`, either promote it to `Candidate` before running selection (per the DC authoring guide), or exclude it and document the exclusion in the GT-115 decision record.

Your job is to recommend which DC should be selected for baseline approval (**DC status → `Selected`**) or declare that none is acceptable. You must also produce a concise list of high-priority issues (selection blockers and design risks).

Scope: selection analysis only.

After the selection report is produced and a human approves the chosen candidate, GT-115 status administration MUST be completed using:
- `lantern/administration_procedures/GT-115__DESIGN_BASELINE_SELECTION_v0.1.0.md`

Until that point, do not update DC statuses and do not create DEC/EV records.

- Do NOT implement or apply candidate designs in the repository.
- Do NOT apply patches, run commands, or update SSOT registries/statuses.
- Do NOT create or update DEC/EV records in this step.
- Do NOT author the DB record in this step.

## SSOT (must use; do not substitute)

- `lantern/preservation/EPISTEMIC_FRAME.md` (objects, IDs, statuses, anchoring)
- `lantern/preservation/GATES.md` (GT-110/115/120 decision logic and GT-115 output semantics)
- `lantern/authoring_contracts/design_candidate_authoring_guide_v0.1.0.md` (normative DC/CH record shape; required DC sections)
- The provided CH file for `CH_ID`: `ch/CH-####.md` (authoritative assessment criteria, constraints, validation target)
- The provided SPEC file(s): (authoritative requirements baseline)
- The provided ARCH file(s): (authoritative architecture baseline)
- The provided TD files for `CH_ID`: `td/TD-####.md` (authoritative test-definition coverage)

This guide is intentionally paired with:
- `change_intention_refinement_guide_v0.2.1.md` (how CH becomes `Ready` at GT-110 with approved TD coverage)
- `design_candidate_authoring_guide_v0.1.0.md` (what a DC must contain to be selection-eligible)
- `lantern/administration_procedures/GT-115__DESIGN_BASELINE_SELECTION_v0.1.0.md` (how to administer the gate after the recommendation)
- `design_baseline_authoring_guide_v0.1.0.md` (what the Approved DB must contain after DC selection)

## Hard anti-drift rules (apply regardless of stage)

- Treat the CH as the requirement anchor. A DC MUST NOT redefine the CH problem statement, constraints, assessment criteria, or validation target.
- Do not invent file paths, commands, flags, or contracts. Only accept references that exist in the repo snapshot you can read, or are explicitly pinned in the DC/CH records.
- Redaction protocol: treat any ellipsized / truncated excerpt (e.g., `...`) as non-authoritative; do not claim presence/absence based on truncated text.
- Do not "fix" candidates in your response. You may propose minimal remediation steps, but do not rewrite DC content.
- Treat placeholders in required DC content (e.g., `TBD`, empty required fields, `"follow existing patterns"`) as FAIL for selection.
- A DC that behaves like a CI is invalid: it MUST NOT contain commit messages, implementation drop-in packs, or patch instructions.

## Goal (what "best DC" means at GT-115)

Select the candidate that is most CH-aligned, upstream-conformant (SPEC/ARCH), TD-traceable, and design-complete for the next step (**implementation via CI authoring**), with the lowest design-reopen risk.

Because GT-115 happens before implementation, your judgment must be based on what is explicitly specified in the DC package:
- CH alignment and scope lock
- conformance to the approved SPEC and ARCH baselines
- TD traceability and coverage correspondence
- explicit governed scope
- explicit compatibility posture and surface impact
- explicit implementation latitude (what CI authoring may vary without reopening GT-115)
- design completeness sufficient to anchor multiple CI candidates without re-opening design

## Inputs I will provide

- CH record: full text of `CH-####.md` (for `CH_ID`)
- Approved SPEC record(s): full text of `SPEC-####.md`
- Approved ARCH record(s): full text of `ARCH-####.md`
- Approved TD set: full text of the referenced `TD-####.md` files
- Candidate DC A..N: full text of each `DC-<CH_NUM>-<UUID>.md`
- (Optional) Repo snapshot pointer (zip/commit) if any DC references repo paths or contracts that need verification

## Mode selection (small vs many-candidate)

If the candidate pool contains **8 or more** DCs, you MUST use **Many-candidate mode** output (Section "Many-candidate mode (8+)").

If the candidate pool contains **1–7** DCs, you MAY use either mode. Default posture: use Standard mode unless the pool is expected to grow.

Note: a pool of exactly **1** DC is valid (GT-115 remains mandatory). For a single-candidate pool, the head-to-head comparison step is omitted; the recommendation is either `Selected` (if the single DC passes all classes A–E) or `NONE ACCEPTABLE` (if it fails).

## Method (must follow exactly)

### 1) Pre-flight eligibility (BLOCK if violated)

#### 1A) Verify CH eligibility for GT-115

BLOCK selection if any of the following are false:

- CH header exists and parses as YAML.
- `ch_id` matches `CH_ID`.
- `status` is `Ready`.
- CH includes non-empty:
  - `assessment_criteria`
  - `validation_target`
- CH includes non-empty:
  - `constraints`
  - `allowed_change_surface`

If CH is ineligible, output:

`BLOCKED: CH not eligible for GT-115`

…and list each missing/invalid element precisely.

#### 1A.1) Verify SPEC, ARCH, TD envelope eligibility

BLOCK selection if any of the following are false:

- At least one Approved `SPEC-####` is provided for the governed scope.
- At least one Approved `ARCH-####` is provided for the governed scope.
- At least one Approved `TD-####` is provided for `CH_ID`.
- The provided TD set covers the CH assessment criteria relevant to the candidate pool.

If the envelope is ineligible, output:

`BLOCKED: Upstream envelope not eligible for GT-115`

…and list each missing or invalid SPEC/ARCH/TD element precisely.

#### 1B) Verify each candidate DC is anchored and selection-eligible

For each DC candidate:

- DC header exists and parses as YAML.
- `ch_id` equals `CH_ID`.
- `dc_id` format matches `DC-<CH_NUM>-<UUID>`, where `CH_NUM` equals the numeric suffix of `CH_ID`.
- `status` is a DC status defined by `lantern/preservation/EPISTEMIC_FRAME.md`.

Hard rule:
- A DC MUST NOT be compared/selected at GT-115 unless its status is `Candidate`.

If anchoring is wrong, the DC is **ineligible** (FAIL) and must not be considered in head-to-head ranking.

### 2) Reconstruct the upstream envelope (CH + SPEC + ARCH + TD grounded; no assumptions)

From the CH, SPEC, ARCH, and TD records, restate as a concise checklist:

- Assessment criteria (as written in CH)
- Constraints (as written in CH)
- Allowed change surface (as written in CH)
- Validation target (as written in CH)
- Key SPEC requirements relevant to the candidate pool
- Key ARCH constraints relevant to the candidate pool
- TD coverage expectations (what behavioral cases must be satisfiable by the design)

This locked envelope is the only basis for judging candidates.

### 3) Candidate-by-candidate evaluation (PASS/FAIL per class; evidence required)

For each candidate DC, mark PASS/FAIL with short evidence excerpts (quote only what you need).

Use the same classes for every candidate:

#### A) CH Alignment & Scope Lock

PASS requires:
- DC contains `## Assessment Criteria Alignment (verbatim from CH)` and the listed criteria match the CH `assessment_criteria` verbatim.
- DC contains `## Constraints (verbatim from CH)` and the text matches the CH `constraints` field verbatim.
- DC contains `## Allowed Change Surface (verbatim from CH)` and the text matches the CH `allowed_change_surface` field verbatim.
- DC does not introduce new requirements, constraints, or validation targets that expand or shift the CH.

#### B) Upstream Baseline Conformance & Record Validity

PASS requires:
- DC has a valid YAML header with required fields (at minimum):
  - `dc_id`, `ch_id`, `status`, `title`
  - `spec_refs` (non-empty; must reference the provided Approved SPEC(s))
  - `arch_refs` (non-empty; must reference the provided Approved ARCH(s))
  - `test_definition_refs` (non-empty; must reference the provided Approved TD set)
  - `origin` (with `baseline` and `rationale`)
  - `governed_scope` (non-empty)
  - `compatibility_posture` (with `assumptions`, `constraints`, `non_goals`)
- `spec_refs` matches the provided Approved SPEC(s).
- `arch_refs` matches the provided Approved ARCH(s).
- `test_definition_refs` are explicit and sufficient for the DC to be judged against the approved TD envelope.
- DC contains `## Upstream Baseline Alignment` section with substantive content (not a placeholder).
- No placeholders in required fields/required sections.

#### C) Governed Scope & Compatibility Posture

PASS requires:
- DC declares an explicit, bounded `governed_scope` in the header and in `## Governed Scope`.
- DC contains `## Compatibility Posture` that explicitly states compatibility assumptions, constraints, and non-goals (each sub-list non-empty or explicitly declared empty with rationale).
- DC contains `## Interfaces / Public Surface Impact` with substantive content (must not be empty or aspirational).
- Declared compatibility posture does not contradict the CH `constraints` field or exceed the CH `allowed_change_surface`.
- The governed scope is coherent with the scope implied by the CH assessment criteria.

#### D) Design Completeness & Comparison Readiness

PASS requires:
- DC contains `## Proposed Design` with substantive technical content (not vague, aspirational, or a forward-reference to implementation).
- DC contains `## Tradeoffs and Rejected Local Alternatives` with at least one explicit tradeoff (makes GT-115 comparison possible without side-channel assumptions).
- DC contains `## Comparison Notes for GT-115` with substantive content.
- DC does not behave like a CI: no commit messages, no implementation drop-in packs, no patch instructions, no requests for the implementer to make design decisions during execution.
- No invalid patterns: `"follow existing patterns"`, `"implementation should decide"`, `"details TBD"`.

#### E) TD Traceability & Implementation Latitude

PASS requires:
- DC contains `## Implementation Latitude` with:
  - non-empty list of fixed design commitments,
  - non-empty list of downstream latitude (what CI candidates may vary without reopening GT-115),
  - non-empty list of reopen GT-115 conditions.
- The DC's proposed design is traceable to the TD coverage expectations: the governed scope and design claims must correspond to at least one TD case from the approved TD set.
- Implementation latitude does not leave design decisions unresolved in a way that would cause unpredictable CI scope drift.

### 4) Selection logic

- If exactly one eligible candidate passes all classes A–E: recommend it as **Selected**.
- If multiple eligible candidates pass all classes A–E: rank them by (highest priority first):
  1) tightest scope lock (least CH expansion risk; exact constraint match),
  2) strongest upstream conformance (SPEC/ARCH/TD) and lowest design-reopen risk,
  3) strongest TD traceability and coverage correspondence,
  4) most explicit implementation latitude (minimizes future GT-115 reopenings and CI drift),
  5) clearest governed scope and compatibility posture (least ambiguity for CI authoring),
  6) most comprehensive tradeoff documentation (strongest GT-115 comparison evidence posture).
- If none pass: declare `NONE ACCEPTABLE`, identify the best near-miss, and list the minimal remediation required for it to reach PASS (specific missing sections/fields and exact insertion points).

### Many-candidate mode (8+) (reporting rules; must follow exactly)

This mode preserves the same evaluation standards, but produces a compact report surface.

#### M1) Eligibility filter (reporting)

Partition the pool into three sets:

1) **Ineligible (exclude from ranking)**
   - fails anchoring in Step 1B (bad YAML header, wrong `ch_id`, bad `dc_id`, numeric anchor mismatch)

2) **Eligible but NOT ranking-eligible**
   - passes anchoring, but FAILS Class B (upstream baseline conformance / record validity)

3) **Ranking-eligible**
   - passes anchoring and PASSES Class B

Only **ranking-eligible** candidates may be selected.

#### M2) One comparison table (all eligible candidates)

Output exactly one markdown table with one row per **eligible** candidate (sets 2+3 above) using these columns:

| DC | Rank? | A | B | C | D | E | Top blockers (max 12 words) | Notes (max 12 words) |
|---|---|---|---|---|---|---|---|---|

Rules:
- `Rank?` MUST be `YES` only for ranking-eligible candidates, otherwise `NO`.
- For candidates that fail Class B, set A/C/D/E to `N/A (fails B)`.
- Keep "Top blockers" and "Notes" within the stated word caps.

#### M3) Fixed-size candidate capsules (all eligible candidates)

After the table, produce one capsule per **eligible** candidate using this exact template and caps:

**<DC_ID>**
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
  - Upstream envelope (SPEC/ARCH/TD): ELIGIBLE | BLOCKED (+ reasons)
  - Candidate list: eligible vs ineligible (anchoring/record errors)

- Baseline Checklist (from CH + SPEC + ARCH + TD)
  - Assessment criteria
  - Constraints
  - Allowed change surface
  - Validation target
  - Key SPEC requirements relevant to the pool
  - Key ARCH constraints relevant to the pool
  - TD coverage expectations

- Candidate Scorecards
  - Candidate A: PASS/FAIL per class (A–E) + evidence excerpts
    - High-priority issues (BLOCKER/HIGH)
  - Candidate B: PASS/FAIL per class (A–E) + evidence excerpts
    - High-priority issues (BLOCKER/HIGH)
  - (Candidate C/D if provided)

- Head-to-Head Comparison
  - Only among candidates that pass class B (record validity)

- Recommendation
  - Selected candidate (A/B/C/…) OR NONE
  - Rationale (1–3 decisive reasons)
  - Minimal remediation required (if any), with exact insertion points (section names and/or header fields)

- Handoff Notes (GT-115 → DB authoring → GT-120)
  - What DB authoring must preserve from the Selected DC (fixed commitments, governed scope, compatibility posture)
  - What implementation latitude the DB must state for CI authoring
  - Known design ambiguities or open latitude questions to resolve before DB approval (if any)

### Many-candidate mode output (8+ candidates)

- Eligibility Summary
  - CH: ELIGIBLE | BLOCKED (+ reasons)
  - Upstream envelope (SPEC/ARCH/TD): ELIGIBLE | BLOCKED (+ reasons)
  - Ineligible DCs (exclude from ranking): list DC ids + 1-line reason each
  - Eligible DCs count: <N>
  - Ranking-eligible DCs count: <N>

- Baseline Checklist (from CH + SPEC + ARCH + TD)
  - Assessment criteria
  - Constraints
  - Allowed change surface
  - Validation target
  - Key SPEC/ARCH requirements
  - TD coverage expectations

- Candidate Comparison Table (all eligible DCs)
  - (single table as defined in M2)

- Candidate Capsules (all eligible DCs)
  - (capsules as defined in M3)

- Recommendation
  - Selected DC id OR NONE
  - Rationale (1–3 decisive reasons)
  - Minimal remediation required (if NONE), with exact insertion points (section names and/or header fields)

- Handoff Notes (GT-115 → DB authoring → GT-120)
  - What DB authoring must preserve
  - What implementation latitude the DB must state
  - Known ambiguities to resolve before DB approval (if any)

## Evidence requirements

- Every PASS/FAIL must be justified with a short excerpt from the candidate/CH (or with a verifiable pointer in the repo snapshot you can read).
- If you claim something is missing, name it precisely (e.g., missing required section, missing DC header field, missing TD traceability for a specific assessment criterion).

## Close-out requirements

- Do NOT update `INDEX.md` at the governance repo root, CH status, DC statuses, or create DEC/EV records in this step.
- Do NOT apply changes or author the DB record. This step produces only a selection recommendation and issues list.
