# Design Candidate authoring guide — v0.1.0


Status: AUTHORITATIVE — Normative
Date (UTC): 2026-03-15

Applies to:
- Lantern workflow SSOT container repositories in a multi-repository workspace
- AI-assisted execution under a locked `CH + SPEC + ARCH + TD` upstream envelope before GT-115

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
A CH is the stable problem definition and assessment anchor for downstream work.

CH id format (required): `CH-####`

### 1.2 Requirements Specification (SPEC)
A SPEC is the approved requirements baseline for the governed scope.

SPEC id format (required): `SPEC-####`

### 1.3 Architecture Definition (ARCH)
An ARCH is the approved architecture baseline for the governed scope.

ARCH id format (required): `ARCH-####`

### 1.4 Test Definition (TD)
A TD is the approved test-definition baseline that candidate designs must satisfy.

TD id format (required): `TD-####`

### 1.5 Design Candidate (DC)
A DC is a candidate design compared at GT-115.
It is design truth for comparison only until selected or rejected.

DC id format (required): `DC-<CH_NUM>-<UUID>`, where `CH_NUM` equals the numeric suffix of the governing `CH-####`.
DC statuses (required): `Draft`, `Candidate`, `Selected`, `Rejected`

Allocation rule (normative): DC ids MUST be generated using the Lantern allocator tool in DC mode:
- `python tools/allocate_lantern_id.py --artifact DC --ch CH-#### --repo <path-to-ssot-root>`

### 1.6 Design Baseline (DB)
A DB is the authoritative selected design artifact approved at GT-115.

DB id format (required): `DB-####`

---

## 2. DC lifecycle semantics (normative)

- `Candidate` is the default status for a complete design package eligible for GT-115 comparison.
- `Draft` is exceptional and is allowed only when the design package is still blocked.
- `Selected` and `Rejected` are GT-115 outcomes only.

Authoring workflow (normative):
1. Author the full DC package using all required header fields and sections in this guide.
2. Keep the package inside the locked `CH + SPEC + ARCH + TD` envelope.
3. Ensure the design is complete enough to compare on technical merit, governed scope, compatibility posture, and TD traceability.
4. Set `status: "Candidate"` if the package is complete.
5. If completion is blocked, set `status: "Draft"` and include `## Blocking Items`.
6. Ensure the DC is listed in `Lantern/change/INDEX.md`.

Eligibility rule:
- A DC MUST NOT be compared at GT-115 unless it has `status: "Candidate"`.

---

## 3. Non-negotiable boundaries

### 3.1 Boundary between CH, SPEC, ARCH, TD, and DC
- CH defines what must become true and the assessment anchor.
- SPEC defines the approved requirements baseline.
- ARCH defines the approved architecture baseline.
- TD defines the approved test-definition baseline.
- DC defines a candidate design inside those upstream constraints.

Hard rule:
- A DC MUST NOT redefine CH, SPEC, ARCH, or TD truth.
- If a DC uncovers a problem in upstream truth, reopen the upstream gate or artifact rather than silently repairing it in the DC.

### 3.2 Boundary between design and implementation
A DC is not an implementation package.

A DC MUST NOT contain:
- commit messages,
- implementation drop-in packs,
- patch payloads for product repos,
- instructions that delegate unresolved design decisions to CI authoring.

Hard rule:
- A DC that behaves like a CI is invalid.

### 3.3 Governed scope boundary
Every DC MUST declare a `governed_scope`.

Hard rule:
- The governed scope must be explicit and bounded.
- Anything outside that scope remains outside the design commitment unless the DC says otherwise.

### 3.4 Implementation latitude boundary
Every DC MUST state what downstream CI candidates may vary without reopening GT-115.

Hard rule:
- If the DC does not separate fixed design commitments from downstream latitude, it is incomplete.

---

## 4. SSOT storage locations and registry (normative)

Canonical locations:
- `ch/CH-####.md`
- `dc/DC-<CH_NUM>-<UUID>.md`
- `db/DB-####.md`
- `ev/EV-####.md`
- `dec/DEC-####.md`
- `Lantern/change/INDEX.md`

Registry rules:
- Every DC MUST appear exactly once under `## Design Candidates` in `Lantern/change/INDEX.md`.
- The DC header and registry status MUST match.
- GT-115 Evidence and Decision records MUST refer to the actual candidate pool.

---

## 5. Required DC header (normative)

File: `dc/DC-<CH_NUM>-<UUID>.md`

Every DC MUST include a machine-readable header block with at least:

```yaml
dc_id: "DC-<CH_NUM>-<UUID>"
ch_id: "CH-####"
status: "Draft|Candidate|Selected|Rejected"
title: "<concise title>"

spec_refs:
  - "SPEC-####"
arch_refs:
  - "ARCH-####"
test_definition_refs:
  - "TD-####"

origin:
  baseline: "<repo-or-archive-pointer>@<commit-or-tag>"
  rationale: "<why this design candidate exists>"

governed_scope:
  - "<module-or-surface>"

compatibility_posture:
  assumptions:
    - "<compatibility assumption>"
  constraints:
    - "<compatibility constraint>"
  non_goals:
    - "<explicit non-goal>"

blocked_by: []  # required when status = Draft
```

Header rules:
- `spec_refs`, `arch_refs`, and `test_definition_refs` MUST be explicit and non-empty.
- `governed_scope` MUST be explicit and non-empty.
- `blocked_by` MUST be empty unless `status: "Draft"`.

---

## 6. Required DC body sections (normative)

Every DC MUST contain these top-level sections:

1. `# <dc_id> — <short title>`
2. `## Problem Framing`
3. `## Assessment Criteria Alignment (verbatim from CH)`
4. `## Constraints (verbatim from CH)`
5. `## Upstream Baseline Alignment`
6. `## Proposed Design`
7. `## Tradeoffs and Rejected Local Alternatives`
8. `## Compatibility Posture`
9. `## Governed Scope`
10. `## Interfaces / Public Surface Impact`
11. `## Implementation Latitude`
12. `## Comparison Notes for GT-115`

Required only when blocked:
- `## Blocking Items`

Recommended additional sections:
- `## Risks / Failure Modes`
- `## Migration / Cutover Notes`
- `## Deferred Design Questions`

---

## 7. DC authoring contract (design-grade)

### 7.1 Upstream-first posture
Every DC MUST ground its design in the approved upstream baseline.

If the DC cannot point to the governing SPEC, ARCH, TD, or CH truth, it MUST block rather than invent.

### 7.2 Design completeness over vagueness
A DC may be blocked, but it must never be vague.

Invalid patterns:
- `follow existing patterns`
- `implementation should decide`
- `details TBD`
- compatibility implications left unstated

### 7.3 Explicit comparison posture
The DC MUST make GT-115 comparison possible without side-channel assumptions.

At minimum it MUST state:
- what this design fixes,
- what technical tradeoffs it accepts,
- what compatibility constraints it preserves or breaks,
- what downstream implementation freedom remains.

### 7.4 Design-only artifact
The DC defines design truth for comparison, not implementation instructions.

Hard rule:
- If the document starts telling an implementer exactly what patch to apply, it has crossed into CI territory and is invalid as a DC.

---

## 8. Implementation latitude contract (normative)

Every DC MUST explicitly separate:
- design commitments fixed by this candidate,
- downstream choices left open to CI authoring,
- changes that would require reopening GT-115 if altered later.

Minimum expectation:
- one short list of fixed commitments,
- one short list of downstream latitude,
- one short list of reopen conditions.

If these are missing, the DC is incomplete even if the design narrative is otherwise strong.

---

## 9. Gate-driven lifecycle implications

### GT-110
- A DC MUST NOT be authored as `Candidate` until the governing CH is `Ready` and the required TD set is Approved.

### GT-115
- A DC MUST contain enough design substance to compare candidates on technical merit, governed scope, compatibility posture, and TD traceability.
- The candidate pool MUST remain stable during comparison.

### GT-120
- A selected DC becomes the source for the Approved DB, which then constrains CI authoring.
- A DC MUST therefore state enough design truth to support later implementation selection without reopening design by accident.

---

## 10. Common failure modes (avoid)

- DC mutates upstream CH, SPEC, ARCH, or TD truth instead of consuming it.
- DC is really a CI in disguise.
- Governed scope is vague or unbounded.
- Compatibility posture is missing.
- Tradeoffs are omitted, making GT-115 comparison impressionistic.
- Implementation latitude is omitted, causing CI drift or unnecessary GT-115 reopenings.
- Public interface impact is left implicit.
