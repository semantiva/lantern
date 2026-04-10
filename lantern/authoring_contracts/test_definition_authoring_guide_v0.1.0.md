# Test Definition authoring guide — v0.1.0


Status: AUTHORITATIVE — Normative
Date (UTC): 2026-03-15

Applies to:
- Lantern workflow SSOT container repositories in a multi-repository workspace
- AI-assisted execution under a locked `CH` upstream envelope at and before GT-110

Normative anchors:
- `lantern/preservation/EPISTEMIC_FRAME.md`
- `lantern/preservation/GATES.md`
- `lantern/preservation/UPSTREAM_INPUT_ARTIFACTS.md`
- `lantern/preservation/LANTERN_MODEL_BINDING.md`
- `lantern/preservation/ARTIFACT_ID_ALLOCATION.md`

---

## 1. Definitions (normative)

### 1.1 Change Intent (CH)
A CH is the stable problem definition and assessment anchor for downstream work.

CH id format (required): `CH-####`

### 1.2 Test Definition (TD)
A TD is the authoritative test-definition baseline that governs what must be tested and how success is judged before design or implementation selection.

A TD is behavioral truth. It states test cases in terms of criteria, preconditions, stimulus, observables, oracle, and failure condition. It is not executable code and MUST NOT embed final runnable commands as the oracle.

TD id format (required): `TD-####`
TD statuses (required): `Draft`, `Approved`, `Superseded`

Allocation rule (normative): TD ids MUST be generated using the Lantern allocator tool:
- `python tools/allocate_lantern_id.py --artifact TD --repo <path-to-ssot-root>`

### 1.3 Requirements Specification (SPEC)
A SPEC is the approved requirements baseline for the governed scope.

SPEC id format (required): `SPEC-####`

### 1.4 Architecture Definition (ARCH)
An ARCH is the approved architecture baseline for the governed scope.

ARCH id format (required): `ARCH-####`

---

## 2. TD lifecycle semantics (normative)

- `Approved` is the required status for a TD to satisfy GT-110 readiness.
- `Draft` is allowed only when the TD is still being authored or is blocked.
- `Superseded` applies when a TD has been replaced by a newer TD that covers the same or expanded criterion scope.

Authoring workflow (normative):
1. Identify the CH `assessment_criteria` entries to be covered.
2. Author TD cases that cover every criterion with non-shallow, structured case content.
3. Set `status: "Approved"` when all required fields are non-empty and coverage is complete per Section 8.
4. If authoring is blocked, set `status: "Draft"` and include `## Blocking Items`.
5. Ensure the TD is listed in `INDEX.md` (governance repository root).

Eligibility rules:
- A TD MUST be `Approved` to satisfy GT-110 readiness.
- A `Draft` TD may exist during GT-110 iteration but MUST be promoted to `Approved` before the GT-110 DEC is recorded as PASS.
- A `Superseded` TD MUST NOT be used as new GT-110 evidence; it may only be referenced as historical context.

---

## 3. Non-negotiable boundaries

### 3.1 Boundary between CH and TD
- CH defines what must become true and why.
- TD defines what must be tested and how success is judged before design selection.

Hard rule:
- A TD MUST NOT redefine the CH problem statement, scope, or constraints.
- If a TD uncovers a problem in CH truth (e.g., a criterion is untestable or under-specified), reopen CH governance rather than silently patching it in the TD.

### 3.2 TD is behavioral truth, not executable code
A TD is not a test script, test file, or runnable command set.

A TD MUST NOT contain:
- pytest code, unit test implementations, or CI script fragments,
- runnable commands presented as the oracle (the oracle must be expressed in behavioral terms),
- dependencies on specific code paths, file names, or line numbers that may change during implementation.

Hard rule:
- A TD that reads like a test implementation has crossed into CI territory and is invalid as a TD.

### 3.3 Binary oracle discipline
Every TD case MUST have a binary oracle: a statement of the exact expected outcome that constitutes pass versus fail. The oracle must be evaluable by a human reviewer without running code.

### 3.4 Traceability discipline
Every TD case MUST trace to at least one CH assessment criterion by id or exact wording.

Hard rule:
- A TD case that does not trace to a CH criterion is unmaintained noise and MUST be removed or explicitly linked before the TD is set to `Approved`.

### 3.5 Boundary between TD and downstream artifacts
- TD is upstream truth that DCs, DBs, and CIs must comply with.
- A DC may not introduce untraceable new behavior without updating the TD set and reopening GT-110.
- A CI may not substitute its own test plan for the approved TD set.

---

## 4. SSOT storage locations and registry (normative)

Canonical locations:
- `td/TD-####.md`
- `INDEX.md` (governance repository root)

Registry rules:
- Every TD MUST appear exactly once under `## Test Definitions` in `INDEX.md` (governance repository root).
- The TD header status and registry status MUST match.
- When a TD is superseded, both the old TD (updated to `Superseded`) and the new TD (new file, `Approved`) MUST be reflected in the registry.

---

## 5. Required TD header (normative)

File: `td/TD-####.md`

Every TD MUST include a machine-readable header block with at least:

```yaml
td_id: "TD-####"
status: "Draft|Approved|Superseded"
title: "<concise title>"
applies_to_ch: "CH-####"
origin:
  baseline: "<source description or upstream artifact pointer>"
  rationale: "<why this TD exists>"
governed_scope:
  - "<module-or-surface>"
supersedes: []  # list of superseded TD ids, or empty
superseded_by: ""  # id of the superseding TD, or empty
```

Header rules:
- `applies_to_ch` MUST reference exactly one CH id.
- `governed_scope` MUST be explicit and non-empty.
- `supersedes` MUST be an explicit list (may be empty).
- `superseded_by` MUST be empty until this TD is itself superseded.
- `status: "Approved"` MUST NOT be set while any required field is a placeholder.

---

## 6. Required TD body sections (normative)

Every TD MUST contain these top-level sections:

1. `# TD-#### — <short title>`
2. `## Purpose`
3. `## Coverage Matrix`
4. `## Evidence Expectations`

Required only when blocked:
- `## Blocking Items`

Recommended additional sections:
- `## Assumptions`
- `## Out of Scope`
- `## Supersession Notes` (required when `supersedes` is non-empty)

---

## 7. TD authoring contract (behavioral-grade)

### 7.1 CH-first posture
Every TD MUST ground its coverage in the CH assessment criteria.

If the TD cannot point to a specific CH criterion for a case, it MUST block rather than author speculative coverage.

### 7.2 Non-shallow coverage over aspirational breadth
A TD MUST contain complete case entries. An incomplete coverage matrix with non-shallow cases is better than a wide matrix of shallow cases.

Invalid patterns:
- `criterion: "see CH"` (non-specific; must quote or reference the exact criterion)
- `oracle: "should work"` (non-binary)
- `observable: "output looks correct"` (non-verifiable)
- `preconditions: "standard state"` (non-specific)
- `failure_condition: "unexpected behavior"` (non-checkable)
- Cases missing any of the six required fields

### 7.3 Binary oracle discipline
The `oracle` field MUST be a specific, deterministic expected outcome.

Valid oracle examples:
- `"Returns exactly one object with canonical_id matching the input pattern"`
- `"Pipeline execution completes with exit code 0 and produces the artifact at the declared output path"`
- `"Raises SemantivaTypeError with a message containing 'incompatible type'"`

Invalid oracle examples:
- `"works correctly"`
- `"produces expected output"`
- `"no errors observed"`

### 7.4 TD is test design, not implementation
The TD defines what to test and how to judge it. The implementer decides how to automate the verification.

Hard rules:
- The TD MUST NOT prescribe the test file path, test function name, or pytest fixture layout.
- The TD MUST NOT be a copy-paste of existing test code.
- The TD SHOULD use natural language for the oracle and failure condition, even if the eventual verification will be automated.

---

## 8. Coverage requirement contract (normative)

A TD is coverage-complete for a CH if and only if ALL of the following are true:

1. Every CH `assessment_criteria` entry has at least one TD case in the `## Coverage Matrix`.
2. Every TD case in the `## Coverage Matrix` has all six required fields non-empty:
   - `criterion` (traces to a specific CH assessment criterion)
   - `preconditions`
   - `stimulus`
   - `observable`
   - `oracle`
   - `failure_condition`
3. No required field contains a placeholder (`TBD`, `…`, `see above`, empty string).
4. The `governed_scope` in the TD header matches the scope implied by the covered criteria.

Coverage-completeness is a binary gate: a TD is either coverage-complete or it is not. Partial coverage MUST result in `status: "Draft"`.

---

## 9. Coverage Matrix format (normative)

Every TD case MUST follow this structure inside the `## Coverage Matrix` section:

```yaml
- case_id: TD-####-C01
  criterion: "<verbatim CH assessment criterion or exact reference>"
  preconditions: "<state, fixture, or setup assumption — not 'standard state'>"
  stimulus: "<operation, event, or input that triggers the test>"
  observable: "<what is observed — measurable, not 'see output'>"
  oracle: "<expected outcome — binary pass condition>"
  failure_condition: "<what constitutes failure — must be checkable>"
```

Rules:
- `case_id` MUST be unique within the TD and follow the `TD-####-C##` format (two-digit sequential counter, zero-padded).
- `criterion` MUST reference a specific CH criterion, not just "general coverage".
- Multiple cases may cover the same criterion (different preconditions or stimuli).
- Every field MUST be a non-empty string.
- Cases MAY include an optional `notes` field for reviewer context (not a substitute for any required field).

---

## 10. Evidence Expectations section (normative)

Every TD MUST include `## Evidence Expectations` declaring:

- the intended test level (`unit`, `integration`, `system`, or `other`)
- the intended evidence mode (`report`, `trace`, `command_output`, `review_note`, or `other`)
- any constraints on when evidence may be collected (e.g., "requires running product repo; evidence collected at GT-130")

This section is informative for downstream CI authoring and integration but MUST be present and non-empty.

---

## 11. Gate-driven lifecycle implications

### GT-110
- TD authoring SHOULD happen in parallel with or immediately before the GT-110 readiness assessment.
- A TD MUST be `Approved` before the GT-110 DEC is recorded as PASS.
- A CH MUST NOT become `Ready` until all referenced TDs are `Approved` and coverage-complete per Section 8.
- A GT-110 EV MUST include a TD coverage inventory (which TD covers which criterion, and any criterion gaps).

### GT-115
- Candidate DCs MUST reference the Approved TD set in `test_definition_refs`.
- A DC MUST demonstrate that the proposed design is compatible with the TD coverage expectations (behavioral cases can be satisfied by the design).
- If a DC reveals that a TD is missing or incorrect, GT-110 MUST be reopened rather than silently adjusting the DC.

### GT-120
- Candidate CIs MUST reference the Approved TD set in `test_definition_refs`.
- If CI authoring reveals a TD is missing or shallow, GT-110 MUST be reopened; the CI MUST NOT invent substitute coverage.

### GT-130
- Verification evidence MUST demonstrate that the Approved TD cases pass against the integrated implementation.

---

## 12. Common failure modes (avoid)

- TD cases trace to "general quality" rather than a specific CH assessment criterion.
- Oracle is aspirational or non-binary (`"should work"`, `"no errors"`).
- Preconditions are vague (`"standard environment"`, `"normal state"`).
- TD is really a test script fragment with pytest imports and fixtures.
- `case_id` values are not unique or not formatted as `TD-####-C##`.
- Coverage matrix has placeholder entries yet TD status is set to `Approved`.
- TD governs a scope not matching the CH's scope.
- TD is authored before the CH is `Proposed` (no criterion anchor exists yet).
- TD supersession is not tracked: old TD left `Approved` alongside the new one.
- TD cases are authored by analogy from existing tests rather than from CH criteria.
- `failure_condition` is identical to the negation of `oracle` with no additional specificity (acceptable only if genuinely binary; otherwise must be stated explicitly).
