# ARCH authoring guide

Status: AUTHORITATIVE - Normative
Date (UTC): 2026-06-05

Applies to:
- Lantern governance repositories that derive architecture baselines from an Approved DIP and compatible SPEC baseline.
- AI-assisted baseline authoring before GT-060.

Normative anchors:
- `lantern/authoring_contracts/dip_authoring_guide.md`
- `lantern/authoring_contracts/spec_authoring_guide.md`
- `lantern/administration_procedures/GT-050_GT-060__BASELINE_READINESS_ADMINISTRATION.md`

---

## 1. Purpose

An ARCH is the authoritative architecture baseline derived from an Approved DIP and the relevant SPEC baseline. It records system structure, component boundaries, interfaces, invariants, operational constraints, and architectural decisions.

An ARCH is not intake truth, product requirements, a CI, or an implementation checklist.

## 2. Lifecycle semantics

ARCH id format: `ARCH-####`
ARCH statuses: `Draft`, `Approved`, `Superseded`

An ARCH may move to `Approved` only through GT-060 PASS. A Superseded ARCH must not anchor new CH work except as historical context.

## 3. Boundary with DIP

The DIP owns intake constraints and source context. ARCH owns the derived architectural decisions that satisfy those constraints.

Hard rules:
- Do not use ARCH to reopen the DIP source envelope.
- Do not record source inventory as architecture unless it becomes an architectural constraint or decision.
- If the architecture requires a scope expansion, return to DIP/SPEC governance rather than hiding the expansion in ARCH.
- An ARCH must not depend on raw source blobs for semantics missing from the DIP or SPEC. If a needed semantic is absent from both, revise the DIP or SPEC through its gate; do not reach back into the original source material to supply ARCH meaning.

## 4. Boundary with SPEC

SPEC states what the product must do. ARCH states how the system is structured to satisfy those requirements.

Hard rules:
- Do not restate SPEC acceptance criteria as architecture.
- Do not introduce behavior requirements in ARCH unless they trace to SPEC.
- Every architectural decision that constrains implementation latitude should identify the requirement, constraint, or risk it addresses.

## 5. Granularity rule

ARCH scope is determined by architectural coherence: decisions that must remain jointly consistent should live in the same architecture baseline.

ARCH scope must not be determined by CH size, implementation effort, execution sequencing, or parallelization convenience.

A split ARCH is valid only when each resulting baseline can stand alone without hiding a shared invariant that implementers must reconstruct from multiple files.

## 6. Relationship to CH and CI

CH slices consume the Approved ARCH baseline. GT-110 verifies that the selected ARCH coverage is sufficient for the CH slice.

CI authors must stay inside the implementation latitude allowed by the ARCH and the selected DB. A CI must not replace ARCH decisions unless a new or superseding ARCH has been approved.

Hard rules (ARCH content is execution-free):
- An ARCH MUST NOT state the value delivered by an execution slice, delivery sequencing, decomposition consequences, CH sizing, or which agent works which slice. That framing is DIP intake authority and CH/INI execution authority.
- "Product refinement framing" as defined for DIP authoring (intake-slice value and sequencing) MUST NOT appear in an ARCH. An ARCH records durable structure and decisions that remain true independent of any execution plan.
- A structural rule that is only true while a migration is in progress is not an ARCH decision. Transitional rules belong to the CH that performs the transition and are void on its closure.
- An ARCH states the durable end-state in timeless present tense. It MUST NOT use diachronic or transitional language (for example "becomes", "no longer", "is now", "is retained", "is removed", "will"), and MUST NOT narrate supersession, migration, coordination, or approval events. State what is structurally true, not what changed or will change.
- An ARCH MUST NOT narrate changes to another baseline (for example "SPEC-X is superseded by ..."). Cross-baseline conflicts are reconciled in decision records; an ARCH states only its own durable structure.
- An ARCH MUST NOT contain storytelling: motivational essays, scenario walkthroughs, analogies, or rationale that will stale. Every statement is objective and minimal.

## 7. Required ARCH content

An ARCH must contain:
1. Summary of the architecture baseline.
2. Decision motivation (optional, minimal): at most one or two objective sentences naming the durable problem the decisions address (see §6). Omit when the decisions are self-evident. No narrative, scenarios, analogies, or transitional language.
3. Architecture scope and intent.
4. Key decisions.
5. Constraints and boundaries.
6. Referenced questions, even when empty.
7. Pinning pointers or notes when needed for auditability.

## 8. Common failure modes

- Scoping ARCH by CH execution convenience.
- Mixing requirements and architectural decisions without traceability.
- Treating implementation tasks as architecture decisions.
- Leaving shared invariants split across records without an explicit integration decision.
- Using ARCH approval as permission to implement without a Ready CH and selected CI.
- Importing DIP-style slice framing ("delivered value in this slice", sequencing or decomposition consequences) into ARCH content. That is intake and CH authority and corrupts the ARCH's durability.
- Recording a structural rule that is only valid during a migration. Transitional discipline belongs in the CH that performs it, not in an ARCH.
- Diachronic or transitional language ("becomes", "no longer", supersession or migration narration). An ARCH describes the durable end-state.
- Narrating another baseline's change inside an ARCH. Cross-baseline reconciliation belongs in decision records.
- Storytelling, analogies, or motivational prose that will stale. ARCH content is objective and minimal.
