# DIP authoring guide — v0.1.0


Status: AUTHORITATIVE — Normative
Date (UTC): 2026-03-15

Applies to:
- Lantern workflow SSOT container repositories in a multi-repository workspace
- AI-assisted execution at and before GT-030

Normative anchors:
- `lantern/preservation/EPISTEMIC_FRAME.md`
- `lantern/preservation/GATES.md`
- `lantern/preservation/WORKSPACE_TOPOLOGY.md`
- `lantern/preservation/LANTERN_MODEL_BINDING.md`
- `lantern/preservation/ARTIFACT_ID_ALLOCATION.md`

---

## 1. Definitions (normative)

### 1.1 Design Input Pack (DIP)
A DIP is the authoritative intake baseline for a feature, initiative, or change scope. It documents the source inventory, planning intent, constraints, non-goals, and open questions that downstream SPEC and ARCH artifacts must derive from.

A DIP is not a requirements specification and is not an architecture definition. It is the locked intake that makes those downstream artifacts derivable without requiring operators to re-open original source material.

DIP id format (required): `DIP-####`
DIP statuses (required): `Draft`, `Approved`, `Superseded`

Allocation rule (normative): DIP ids MUST be generated using the Lantern allocator tool:
- `python tools/allocate_lantern_id.py --artifact DIP --repo <path-to-ssot-root>`

### 1.2 Initiative (INI)
An Initiative is the planning container that owns one DIP and one or more derived SPEC/ARCH artifacts.

INI id format (required): `INI-####`

### 1.3 Requirements Specification (SPEC)
A SPEC is derived from an Approved DIP and is the authoritative requirements baseline.

SPEC id format (required): `SPEC-####`

### 1.4 Architecture Definition (ARCH)
An ARCH is derived from an Approved DIP and is the authoritative architecture baseline.

ARCH id format (required): `ARCH-####`

---

## 2. DIP lifecycle semantics (normative)

- `Approved` is the required status for a DIP to unlock SPEC/ARCH drafting, baseline-readiness review, and downstream change work.
- `Draft` is the authoring state. A DIP in `Draft` may be iteratively refined before GT-030.
- `Superseded` applies when a DIP has been replaced by a newer Approved DIP covering the same or expanded scope.

Authoring workflow (normative):
1. Identify and inventory the authoritative source material for the Initiative.
2. Translate, adapt, or summarize source material into the DIP. External references may remain as provenance, but MUST NOT remain required semantic dependencies.
3. Enumerate constraints and non-goals explicitly; do not leave them implicit.
4. Record all blocking questions by reference; unresolved blocking questions prevent GT-030 PASS.
5. Set `status: "Approved"` only after GT-030 PASS; before that, keep `Draft`.
6. Ensure the DIP is listed in the SSOT registry.

Eligibility rules:
- A DIP MUST be `Approved` before SPEC and ARCH derivation may begin.
- A `Draft` DIP may be iterated during GT-030 execution but MUST be promoted to `Approved` before the GT-030 DEC is recorded as PASS.
- A `Superseded` DIP MUST NOT anchor new SPEC/ARCH derivations; it may only be referenced as historical context.

---

## 3. Non-negotiable boundaries

### 3.1 DIP is intake truth, not requirements or architecture
A DIP captures what is known at intake: source inventory, scope intent, constraints, non-goals, and open questions. It is not a SPEC and is not an ARCH.

Hard rule:
- A DIP MUST NOT contain acceptance criteria (those belong in SPEC).
- A DIP MUST NOT contain architectural decisions (those belong in ARCH).
- A DIP that reads like a SPEC or ARCH has overstepped its scope and is invalid as a DIP.

### 3.2 Self-contained intake discipline
A DIP MUST be understandable without requiring the reader to open the original source material for core semantics.

Hard rule:
- Relevant facts from blobs, legacy SSOT bundles, planning archives, or external documents MUST be translated, adapted, or summarized into the DIP body.
- Source locators remain as provenance pointers but MUST NOT remain the only place where the authoritative intake content lives.
- If a source is private or sensitive, use an opaque token in the source inventory and document the real locator outside any public projection.

### 3.3 Constraints and non-goals are first-class content
A DIP without explicit constraints and non-goals is incomplete. Vague or aspirational constraints are invalid.

Hard rule:
- `## Constraints and non-goals` MUST be non-empty.
- Each constraint MUST be a checkable claim (e.g., "must not change the public API surface") not a sentiment (e.g., "should be good quality").
- Non-goals MUST be explicit and bounded: they define the scope exclusions that prevent SPEC and ARCH from expanding beyond intent.

### 3.4 Supersession protocol
A DIP MUST NOT be superseded by direct edit to an Approved DIP. Supersession requires a new GT-030 run.

Hard rule:
- Authoring a new DIP that supersedes a prior one requires updating the old DIP's `status` to `Superseded` as part of GT-030 administration.
- The new DIP MUST list the superseded DIP id in the header `supersedes` field.
- Any SPEC/ARCH derived from the superseded DIP must be re-evaluated for derivation validity against the new DIP.

### 3.5 Questions discipline
Blocking questions MUST be resolved before GT-030 PASS.

Hard rule:
- A question marked `Blocking: YES` and `Status: Open` in the DIP header MUST block GT-030.
- Non-blocking questions (`Blocking: NO`) are informative and do not block GT-030 but MUST still be listed so downstream authors are aware of them.
- A DIP MUST NOT have a non-empty questions list with blank or placeholder entries; each question must be substantive.

---

## 4. SSOT storage locations and registry (normative)

Canonical locations:
- `dip/DIP-####.md`
- `INDEX.md` (governance repository root, via Initiative record)

Registry rules:
- Every DIP MUST appear in its governing Initiative record under the `inputs.dips` header list.
- When a DIP is superseded, both the old DIP (updated to `Superseded`) and the new DIP (`Approved`) MUST be reflected in the Initiative record and any relevant registry entries.

---

## 5. Required DIP header (normative)

File: `dip/DIP-####.md`

Every DIP MUST include a header preamble with at least:

```markdown
# DIP-#### — <concise title>

Status: Draft | Approved | Superseded
Supersedes: DIP-#### | None
Timestamp: YYYY-MM-DDTHH:MM:SSZ
```

Header rules:
- `Status` MUST be updated to `Approved` only as part of GT-030 administration.
- `Supersedes` MUST be `None` unless this DIP explicitly replaces a prior Approved DIP.
- `Timestamp` SHOULD be the ISO 8601 date of last substantive revision.

---

## 6. Required DIP body sections (normative)

Every DIP MUST contain these top-level sections:

1. `## Summary`
2. `## Product refinement framing (required)`
3. `## Source inventory (required)`
4. `## Constraints and non-goals (required)`
5. `## Questions referenced (required; may be empty)`

Recommended additional sections:
- `## Pinning pointers` (informative; baseline locator evidence is formally captured at GT-030 EV)
- `## Notes`

---

## 7. DIP authoring contract (intake-grade)

### 7.1 Source inventory completeness
Every substantive source that shapes scope, constraints, or design must appear in `## Source inventory`.

Rules:
- Each source MUST have a stable identifier (`SRC-###`), a type (`file`, `url`, `archive`, `private-token`), and a locator.
- Sources MUST be traceable to specific downstream SPEC/ARCH derivations; a source that cannot be traced to any downstream artifact is dead weight and should be omitted.
- If a source is private, use an opaque token and document the real locator externally.

Invalid patterns:
- "see attached" with no stable locator,
- bulk import of a source archive as a single entry with no decomposition of what it contributes,
- sources that are "included for completeness" with no derivation linkage.

### 7.2 Constraints and non-goals discipline
Constraints define what the downstream SPEC/ARCH and implementation MUST preserve or avoid.
Non-goals define what is explicitly out of scope regardless of feasibility.

Rules:
- Each constraint MUST be checkable: a reviewer must be able to determine compliance from the downstream artifacts without additional interpretation.
- Non-goals MUST be explicit exclusions, not implicit assumptions.
- Both lists MUST be non-empty unless there are genuinely no constraints and no non-goals, in which case this MUST be stated explicitly ("No constraints apply to this intake" / "No scope exclusions are required").

### 7.3 Questions discipline
A DIP question is a formal record of a known uncertainty that affects scope, constraints, or downstream derivation.

Rules:
- Questions MUST be identified as blocking or non-blocking.
- A blocking question MUST be resolved before GT-030 can PASS.
- Questions MUST NOT be placeholders (e.g., "Q-001: TBD").
- Resolution of a blocking question MUST be documented in the DIP or in a referenced Decision record.

### 7.4 Product refinement framing
A DIP MUST force the author to explain why this slice exists now and what complexity is intentionally being held back.

Rules:
- `## Product refinement framing (required)` MUST be non-empty.
- The framing MUST state the real bottleneck that justifies the slice.
- The framing MUST state the value being delivered in this slice.
- The framing MUST state the complexity being avoided or deferred.
- The framing MUST state any decomposition or sequencing consequence created by that deferral.

### 7.5 DIP is intake, not design
A DIP captures what is known at intake and what is intentionally out of scope. It does not make design choices.

Hard rules:
- The DIP MUST NOT prescribe solution approaches; it may identify constraints that rule out certain approaches.
- The DIP MUST NOT enumerate acceptance criteria; it may state scope requirements that acceptance criteria will later need to satisfy.
- A DIP that contains detailed technical solutions has overstepped and must be split or refactored.

---

## 8. Supersession authoring rules (normative)

When authoring a DIP that supersedes a prior DIP:
1. Set `Supersedes: DIP-####` for each superseded DIP.
2. In `## Notes`, explicitly state what scope the new DIP assumes, what changed from the prior DIP, and whether the supersession is total or partial.
3. Update the superseded DIP header `Status: Superseded` as part of GT-030 administration.
4. Re-evaluate any SPEC/ARCH derived from the superseded DIP during the next GT-050 / GT-060 readiness review against the new DIP baseline.

Hard rule:
- Setting `Status: Superseded` on a DIP without a corresponding new Approved DIP is invalid.
- Any SPEC/ARCH derived from a superseded DIP remains valid only until explicitly re-evaluated.

---

## 9. Gate-driven lifecycle implications

### GT-030
- DIP authoring happens before and during GT-030 execution.
- A DIP MUST be `Approved` before GT-030 PASS is recorded; before that it MUST remain `Draft`.
- GT-030 EV MUST capture: source inventory completeness assessment, baseline locator or waiver, blocking questions resolution, and constraints/non-goals completeness determination.

### GT-050/GT-060
- These approve ARCH and SPEC respectively as reusable baselines.
- Derivation linkage and DIP/SPEC/ARCH coherence evidence are reviewed inside these readiness gates rather than through standalone preflight gates.
- A DIP that is not self-contained or that propagates contradictions into SPEC/ARCH will fail GT-050 / GT-060 because the derivation/coherence evidence cannot be substantiated.
- Approved SPEC and ARCH are required inputs for GT-110 (CH readiness).

---

## 10. Common failure modes (avoid)

- DIP summary is aspirational ("we will build a great pipeline") rather than factual ("this DIP captures the intake for scope X from source Y").
- Source inventory is a file dump with no derivation notes; downstream SPEC/ARCH authors cannot tell which sources drive which requirements.
- Constraints are stated as preferences ("should be fast") rather than checkable bounds ("latency under 100 ms for the nominal path").
- Non-goals are omitted; SPEC authors expand scope into territory the DIP owner intended to exclude.
- Blocking questions are left open at GT-030; the gate is recorded as PASS anyway.
- DIP contains detailed solution choices (architecture in disguise); ARCH then repeats them, creating redundancy and drift risk.
- Superseded DIP left in `Approved` state alongside a new DIP covering the same scope.
- External source is referenced but not translated; a reader must open the original source to understand the DIP's core scope.
