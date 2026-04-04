# Change Increment authoring guide — v0.2.1


Status: AUTHORITATIVE — Normative
Date (UTC): 2026-03-15
Supersedes: v0.2.0

Applies to:
- Lantern workflow SSOT container repositories in a multi-repository workspace
- AI-assisted execution under a locked `CH + DB + TD` downstream envelope

Correction note:
- This guide restores the rich authoring posture of `v0.2.0` while incorporating the active `TD / DB / GT-115` downstream contract that was introduced after `v0.2.0`.

Normative anchors:
- `lantern/preservation/EPISTEMIC_FRAME.md`
- `lantern/preservation/GATES.md`
- `lantern/preservation/WORKSPACE_TOPOLOGY.md`
- `lantern/preservation/LANTERN_MODEL_BINDING.md`
- `lantern/preservation/ARTIFACT_ID_ALLOCATION.md`
- `lantern/preservation/UPSTREAM_INPUT_ARTIFACTS.md`

---

## 1. Definitions (normative)

### 1.1 Change Intent (CH)
A CH is the stable problem definition and assessment anchor.

CH id format (required): `CH-####`
CH statuses used by this guide: `Proposed`, `Ready`, `Addressed`

### 1.2 Test Definition (TD)
A TD is the authoritative test-definition baseline for GT-110 and downstream execution.

TD id format (required): `TD-####`
TD statuses used by this guide: `Draft`, `Approved`, `Superseded`

### 1.3 Design Baseline (DB)
A DB is the authoritative selected design artifact approved at GT-115.

DB id format (required): `DB-####`
DB statuses used by this guide: `Draft`, `Approved`, `Superseded`

### 1.4 Change Increment (CI)
A CI is an implementation-only candidate solution package authored against a locked `CH + DB + TD` envelope.
It MUST NOT redefine design truth or test truth.

CI id format (required): `CI-<CH_NUM>-<UUID>`, where `CH_NUM` equals the numeric suffix of the governing `CH-####`.
CI statuses (required): `Draft`, `Candidate`, `Selected`, `Rejected`, `Verified`

Allocation rule (normative): CI ids MUST be generated using the Lantern allocator tool in CI mode:
- `python tools/allocate_lantern_id.py --artifact CI --ch CH-#### --repo <path-to-ssot-root>`

### 1.5 Evidence and Decisions
Evidence supports gate outcomes. Decisions record gate outcomes or supersession.
Evidence and Decisions do not redefine CH, TD, or DB semantics.

---

## 2. CI lifecycle semantics (normative)

- `Candidate` is the default status for a complete execution-grade CI package produced by an AI assistant or human operator.
- `Draft` is exceptional and is allowed only when the CI cannot yet be made deterministic or complete.
- `Selected` and `Rejected` are GT-120 outcomes only.
- `Verified` is a GT-130 outcome only.

AI authoring workflow (normative):
1. Author the full CI package using all required header fields and sections in this guide.
2. Ensure the CI is implementation-only and remains inside the locked `CH + DB + TD` envelope.
3. Ensure the CI is deterministic: no placeholders, no unstated branch assumptions, no delegated design decisions.
4. Set `status: "Candidate"` if the package is complete.
5. If completion is blocked, set `status: "Draft"` and include `## Blocking Items`.
6. Ensure the CI is listed in `Lantern/change/INDEX.md` and linked from the governing CH.

Eligibility rule:
- A CI MUST NOT be compared at GT-120 unless it has `status: "Candidate"`.

---

## 3. Non-negotiable boundaries

### 3.1 Boundary between CH, TD, DB, and CI
- CH defines what must become true and how success is judged at the change level.
- TD defines what must be tested and what evidence counts as success.
- DB defines the authoritative selected design and the governed scope it locks.
- CI defines only how the approved design is implemented inside a bounded change surface.

Hard rule:
- If CI authoring reveals CH truth is wrong or incomplete, reopen CH governance rather than silently repairing it in the CI.
- If CI authoring reveals TD truth is wrong or insufficient, reopen GT-110.
- If CI authoring reveals the selected design is wrong or incomplete, reopen GT-115.

### 3.2 Boundary of CI change surface
Every CI MUST declare an `allowed_change_surface`.

Hard rule:
- Anything outside the declared change surface is out of scope.
- If execution requires edits outside the declared surface, the CI is blocked until the CI or DB is explicitly revised.

### 3.3 Boundary between design and implementation
A CI MUST NOT contain:
- alternative design comparison as authoritative truth,
- changes to compatibility posture that contradict the approved DB,
- requests for the implementer to make design decisions during execution.

Hard rule:
- A CI that says "choose one of these designs during implementation" is invalid.

### 3.4 Branch and baseline posture
A CI SHOULD target the governed product repository mainline unless a branch-specific baseline is required.

If branch-specific context is required, the CI MUST:
- name the branch or commit baseline explicitly,
- state why the context is required,
- keep the scope bound to that baseline.

---

## 4. SSOT storage locations and registry (normative)

Canonical locations:
- `ch/CH-####.md`
- `ci/CI-<CH_NUM>-<UUID>.md`
- `db/DB-####.md`
- `ev/EV-####.md`
- `dec/DEC-####.md`
- `Lantern/change/INDEX.md`

Registry rules:
- Every CI MUST appear exactly once under `## Change Increments` in `Lantern/change/INDEX.md`.
- Every CI MUST be referenced by its governing CH in the CH header `related_cis` list, if that header field exists in the local CH shape.
- The CI header and registry status MUST match.

---

## 5. Required CI header (normative)

File: `ci/CI-<CH_NUM>-<UUID>.md`

Every CI MUST include a machine-readable header block with at least:

```yaml
ch_id: "CH-####"
ci_id: "CI-<CH_NUM>-<UUID>"
status: "Draft|Candidate|Selected|Rejected|Verified"
title: "<concise title>"

design_baseline_ref: "DB-####"
test_definition_refs:
  - "TD-####"

ssot:
  code: "<repo-or-archive-pointer>@<commit-or-tag>"
  docs: ["<path>"]
  schemas: ["<path>"]
  tools: ["<path>"]
  glossary: "<path-or-empty>"

baseline:
  product_repo: "<repo-name>"
  branch_or_commit: "<main|branch|commit>"
  rationale: "<required when not mainline>"

allowed_change_surface:
  - "<path-or-module-glob>"

verification:
  required_evidence:
    - kind: "test|artifact|report|command"
      command: "<exact command when applicable>"
      path: "<exact path when applicable>"
      expected_signal: "<binary expected result>"

blocked_by: []  # required when status = Draft
```

Header rules:
- `design_baseline_ref` MUST reference exactly one Approved DB.
- `test_definition_refs` MUST contain every TD needed to judge the CI.
- `allowed_change_surface` MUST be explicit and non-empty.
- `blocked_by` MUST be empty unless `status: "Draft"`.

---

## 6. Required CI body sections (normative)

Every CI MUST contain these top-level sections:

1. `# <ci_id> — <short title>`
2. `## Intent`
3. `## Assessment Criteria Alignment (verbatim from CH)`
4. `## Constraints (verbatim from CH)`
5. `## Design Baseline Alignment`
6. `## Test Definition Alignment`
7. `## Allowed Change Surface`
8. `## Drop-In Pack (REQUIRED)`
9. `## Commit Message (REQUIRED)`
10. `## Verification Plan`
11. `## Definition of Done (binary)`

Required only when blocked:
- `## Blocking Items`

Recommended additional sections:
- `## Extracted Evidence (SSOT reads)`
- `## Public Signatures Frozen`
- `## Risks / Failure Modes`

Hard rule:
- A CI is invalid unless it contains both `## Drop-In Pack (REQUIRED)` and `## Commit Message (REQUIRED)`.

---

## 7. CI authoring contract (execution-grade)

### 7.1 SSOT-first posture
Every CI MUST list the SSOT references it relies on.

If the CI cannot ground a requirement, interface, or term in SSOT or a locked upstream artifact, it MUST block rather than invent.

### 7.2 Determinism over completeness
A CI may be blocked, but it must never be ambiguous.

Invalid patterns:
- `TBD`
- `implement as appropriate`
- `follow existing patterns` without exact scope and expected effect
- hidden dependence on undocumented files, flags, or repo layout

### 7.3 Contracts are frozen by default
Public payload boundaries, schemas, CLI contracts, and integration semantics are frozen unless the CI explicitly states a permitted change already authorized by the DB and CH.

### 7.4 CI is an implementation artifact
The CI is not a brainstorming note.

Hard rules:
- The CI MUST carry paste-ready drop-ins or precise bounded patch instructions.
- The CI MUST carry a paste-ready commit message template.
- The CI MUST make implementation decisions explicit enough that the implementer is not asked to design while coding.

---

## 8. Drop-In sufficiency standard (normative)

A CI MUST fully cover its allowed change surface using only:
1. `FULL-FILE`
2. `PATCH`
3. `REMOVE`
4. `MECHANICAL-RULE`

If a required change cannot be expressed with one of these, the CI MUST block.

### 8.1 Required Drop-In Pack contents
Every CI MUST include a coverage table mapping every declared change-surface entry to a drop-in.

Minimum format:

```text
Path | Drop-in type | Drop-in anchor
<path> | PATCH | "DROP-IN: PATCH <path>"
```

Then include the drop-in payloads themselves using these anchors:
- `### DROP-IN: FULL-FILE <path>`
- `### DROP-IN: PATCH <path>`
- `### DROP-IN: REMOVE <path>`
- `### DROP-IN: MECHANICAL-RULE <short name>`

### 8.2 Mechanical rule requirements
Every `MECHANICAL-RULE` drop-in MUST include:
- exact match condition,
- edit action,
- bounded scope,
- safety constraint,
- at least one binary verification gate.

### 8.3 Blocking posture for incomplete drop-ins
If drop-in coverage is incomplete, the CI MUST include `## Blocking Items` with:
- what is missing,
- why it could not be made deterministic,
- exact SSOT references required to proceed.

---

## 9. Commit Message (normative)

Every CI MUST include `## Commit Message (REQUIRED)`.

Hard rules:
- The commit message MUST be paste-ready.
- The commit message MUST reference both CH and CI ids.
- Repo-specific conventions MUST be followed or explicitly called out.

Minimum template:

```text
<type>: <short summary>

CH: CH-####
CI: CI-<CH_NUM>-<UUID>

<optional rationale>
```

---

## 10. Verification requirements (normative)

The `## Verification Plan` section MUST contain real, binary checks.

Rules:
- Commands MUST be exact and runnable.
- Expected signals MUST be explicit.
- Artifact checks MUST name exact files or outputs.
- Placeholder verification is invalid.

Examples of valid signals:
- `exit code 0`
- `specific file exists`
- `named test passes`
- `validator prints VALIDATION OK`

Examples of invalid signals:
- `looks good`
- `review output`
- `no obvious issues`

---

## 11. Gate-driven lifecycle implications

### GT-110
- CI authoring MUST NOT begin until the target CH is `Ready` and the required TD set is Approved.

### GT-115
- CI authoring MUST use an Approved DB and MUST NOT reopen design choice inside the CI.

### GT-120
- A CI MUST contain explicit CH, DB, and TD alignment so the candidate can be compared without inventing evaluation criteria.

### GT-130
- A CI MUST specify the verification evidence expected after integration so the selected candidate can be verified mechanically.

---

## 12. Common failure modes (avoid)

- CI redefines design or test truth instead of consuming DB and TD.
- CI widens the allowed change surface implicitly.
- CI lacks full drop-in coverage for the declared surface.
- CI verification is aspirational or non-binary.
- CI hides required branch or baseline context.
- CI leaves public-surface changes implicit.
- CI asks the implementer to make unresolved design choices during execution.
