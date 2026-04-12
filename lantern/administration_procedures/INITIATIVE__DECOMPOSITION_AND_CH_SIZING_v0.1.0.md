# Initiative decomposition and CH sizing — v0.1.0

Status: AUTHORITATIVE — Guidance  
Date (UTC): 2026-03-07

Purpose:
- Provide a bounded, repeatable way to decompose an **Initiative** into one or more Change Intents (CH).
- Help operators size CHs so they can be refined to `Ready` (GT-110) and then authored as Change Increment (CI) candidates for GT-120 selection.

Normative anchors (must not contradict):
- `change_increment_authoring_guide.md`
- `change_intention_refinement_guide_v0.2.1.md`
- `lantern/preservation/EPISTEMIC_FRAME.md`
- `lantern/preservation/GATES.md`
- `lantern/preservation/LANTERN_MODEL_BINDING.md`

## Initiative posture

Lantern model defines **Initiative** as the planning object above `CH`.

This guide does **not** define gate machinery for Initiative status changes.
It defines only how to use Initiative as a practical planning and decomposition aid in real projects.

Recommended Initiative status labels:
- `Proposed`
- `Ready`
- `In Progress`
- `Concluded`

If a project chooses to keep Initiative records in SSOT, use stable repo-local references or repo-relative paths. No allocator namespace is required by this guide.

## Core rules

1) Each Initiative intended for execution SHOULD decompose into one or more `CH-####` items.
2) A CH SHOULD represent a bounded vertical slice of one Initiative.
3) If a CH is derived from an Initiative, the CH SHOULD record that linkage in `initiative_refs:`.
4) A CH MUST remain the execution-grade requirement anchor; Initiative does not replace CH in GT-110 / GT-120 / GT-130.
5) If an Initiative cannot be decomposed into bounded CHs, the Initiative is not ready for active execution planning.
6) Execution MAY begin as soon as one bounded CH derived from the Initiative can proceed to GT-110 refinement; a complete CH inventory is not required up front.

## Minimum Initiative content

A usable Initiative record SHOULD contain:
- Title
- Status
- Objective / intended outcome
- Scope boundary (in / out)
- Decomposition notes
- Candidate CH list
- Sizing notes / rationale
- Inputs / evidence pointers

Use `lantern/templates/TEMPLATE__INITIATIVE.md` as the starting point.

## Decomposition intent

Decompose an Initiative so that each resulting CH:
- has a clear problem statement,
- can carry explicit constraints and acceptance criteria,
- can declare a bounded validation target,
- can be implemented by one or more CI candidates without redefining the Initiative.

## Deterministic sizing checks

Sizing is a compromise:
- CHs that are too small create excessive gate and administration overhead.
- CHs that are too large exceed what a capable LLM can safely and reliably deliver in a single coding session with one prompt.

Use the checks below to stay between those two failure modes.

Apply these checks before promoting a CH to active GT-110 refinement.

C1) Scope bullet count
- In the CH `## 2. Scope` section, count bullet items under **In scope**.
- If the count is greater than 5, STOP and split the CH.

C2) Input sufficiency assessment present
- The CH contains `## 0. GT-110 Input Sufficiency Assessment (STOP/GO)`.
- The section includes tests/docs posture lines (`Included` vs `Deferred (with rationale)`).

C3) Validation target exists
- The CH header contains a non-empty `validation_target` list.

C4) Behavior change implies tests included
- If the CH introduces or changes behavior, tests MUST be `Included` unless explicitly deferred with rationale in the sufficiency assessment.

C5) Initiative slice is singular
- The CH addresses one coherent Initiative slice.
- If the CH mixes multiple independent primary outcomes, STOP and split it.

C6) Change surface stays bounded
- The intended `allowed_change_surface` for downstream CI authoring is plausibly bounded.
- If the expected implementation surface is broad or crosses multiple unrelated areas, STOP and split the CH.

## Tests and documentation posture

Default posture:
- tests are included unless explicitly deferred, and
- documentation changes are included when user-facing or operator-facing behavior changes.

Initiative decomposition rule:
- do not plan a feature CH followed by separate tests CH and docs CH for the same feature slice.
- if a feature cannot carry tests/docs within one CH, split the feature into smaller vertical slices.

If tests or docs are deferred:
- record the deferral and rationale in the CH sufficiency assessment, and
- create a follow-on CH for the deferred work, linked via `depends_on_ch` or explicit waiver rationale.

## Common split patterns

- Split by capability slice: one coherent user/operator-visible outcome per CH.
- Split by contract boundary: separate schema/marker/CLI contract changes when they affect multiple components.
- Split by verification: separate work when different parts require different binary validation signals.
- Exception (cross-cutting enablement): a tests/contracts-only CH is allowed when it introduces shared infrastructure used by multiple CHs.
- Exception (cross-cutting docs): a docs/runbooks-only CH is allowed when it is not specific to a single feature slice.

## Failure modes

- Treating Initiative as directly executable work instead of decomposing to CH.
- Creating oversized CHs that bundle unrelated slices.
- Omitting `initiative_refs:` in CHs that clearly come from an Initiative.
- Using Initiative status as a substitute for GT-110 / GT-120 / GT-130 outcomes.
