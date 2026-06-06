# SPEC authoring guide

Status: AUTHORITATIVE - Normative
Date (UTC): 2026-06-05

Applies to:
- Lantern governance repositories that derive product requirements from an Approved DIP.
- AI-assisted baseline authoring before GT-050.

Normative anchors:
- `lantern/authoring_contracts/dip_authoring_guide.md`
- `lantern/authoring_contracts/arch_authoring_guide.md`
- `lantern/administration_procedures/GT-050_GT-060__BASELINE_READINESS_ADMINISTRATION.md`

---

## 1. Purpose

A SPEC is the authoritative product requirements baseline derived from an Approved DIP. It states what the product must do, what behavior is in scope, and what evidence will show that the behavior is acceptable.

A SPEC is not intake truth, architecture, execution planning, or implementation instruction.

## 2. Lifecycle semantics

SPEC id format: `SPEC-####`
SPEC statuses: `Draft`, `Approved`, `Superseded`

A SPEC may move to `Approved` only through GT-050 PASS. A Superseded SPEC must not anchor new CH work except as historical context.

## 3. Boundary with DIP

The DIP owns source inventory, scope intent, constraints, non-goals, and open questions. The SPEC owns derived product requirements and acceptance criteria.

Hard rules:
- Do not copy unresolved intake ambiguity into SPEC requirements.
- Do not put acceptance criteria in the DIP when they are product behavior criteria; move them to SPEC.
- Do not expand beyond the Approved DIP unless the DIP is superseded or another Approved DIP is added as input.
- A SPEC must not depend on raw source blobs for semantics missing from the DIP. If a needed semantic is absent from the Approved DIP, revise the DIP through its gate; do not reach back into the original source material to supply SPEC meaning.

## 4. Boundary with ARCH

SPEC states required product behavior. ARCH states the architectural decisions and invariants that make that behavior possible.

Hard rules:
- A SPEC must not prescribe component structure, module layout, storage topology, runtime framework, or migration mechanics unless those are product requirements from the DIP.
- If a statement explains how the system is structured, it belongs in ARCH.
- If a statement defines externally observable behavior, acceptance semantics, or required product capability, it belongs in SPEC.

## 5. Granularity rule

SPEC scope is determined by product or technical coherence of the requirements group.

SPEC scope must not be determined by implementation effort, execution sequencing, parallelization convenience, CH size, or which agent can work on which slice.

A SPEC may be split only when the resulting requirements baselines are independently coherent and do not force readers to reconstruct one requirement model from multiple partial records.

## 6. Relationship to CH

CH decomposition is downstream of Approved SPEC and Approved ARCH baselines. CH slices consume SPEC requirements; they do not define SPEC granularity.

A CH may reference one or more Approved SPEC records. GT-110 verifies that the selected SPEC coverage is sufficient for the CH slice.

Hard rules (SPEC content is execution-free):
- A SPEC MUST NOT state the value delivered by an execution slice, delivery sequencing, decomposition consequences, CH sizing, or which agent works which slice. That framing is DIP intake authority and CH/INI execution authority.
- "Product refinement framing" as defined for DIP authoring (intake-slice value and sequencing) MUST NOT appear in a SPEC. A SPEC records durable requirements that remain true independent of any execution plan.
- A requirement that is only true while a migration is in progress is not a SPEC requirement. Transitional rules belong to the CH that performs the transition and are void on its closure.
- A SPEC states the durable end-state in timeless present tense. It MUST NOT use diachronic or transitional language (for example "becomes", "no longer", "is now", "is retained", "is removed", "will"), and MUST NOT narrate supersession, migration, coordination, or approval events. State what is true, not what changed or will change.
- A SPEC MUST NOT narrate changes to another baseline (for example "SPEC-X is superseded by ..."). Cross-baseline conflicts are reconciled in decision records; a SPEC states only its own durable requirements.
- A SPEC MUST NOT contain storytelling: motivational essays, scenario walkthroughs, analogies, or rationale that will stale. Every statement is objective and minimal.

## 7. Required SPEC content

A SPEC must contain:
1. Summary of the requirement baseline.
2. Requirement motivation (optional, minimal): at most one or two objective sentences naming the durable problem the requirements address (see §6). Omit when the requirements are self-evident. No narrative, scenarios, analogies, or transitional language.
3. Scope.
4. Acceptance criteria (see §9).
5. Validation target signal definition when a testable target signal exists.
6. Referenced questions, even when empty.
7. Pinning pointers or notes when needed for auditability.

## 8. Acceptance criteria format

A SPEC collects its acceptance criteria in a dedicated `## Acceptance criteria` section. Each criterion carries a unique identifier in the form `AC-###`, scoped to the SPEC, starting at `AC-001`.

Rules:
- Each AC traces to one or more requirements by explicit REQ-ID reference in the heading: `### AC-### (REQ-ID[, REQ-ID])`.
- AC text states a mechanical, testable check — not requirement intent or rationale.
- The `## Acceptance criteria` section is the single owning source for each AC text. Requirements reference their AC by identifier only; they do not duplicate AC text inline.
- Every requirement must have exactly one corresponding AC, or share one with another requirement when the check is identical.
- A SPEC with no testable acceptance signal must still have an `## Acceptance criteria` section, marked "None".

## 9. Common failure modes

- Scoping a SPEC by CH size or parallel execution plan.
- Embedding architectural decisions in requirements language.
- Leaving acceptance criteria in the DIP instead of moving them to SPEC.
- Carrying unresolved questions as if they were requirements.
- Treating SPEC approval as permission to implement without a Ready CH.
- Importing DIP-style slice framing ("delivered value in this slice", sequencing or decomposition consequences) into SPEC content. That is intake and CH authority and corrupts the SPEC's durability.
- Stating a requirement that is only valid during a migration. Transitional discipline belongs in the CH that performs it, not in a SPEC.
- Diachronic or transitional language ("becomes", "no longer", supersession or migration narration). A SPEC describes the durable end-state.
- Narrating another baseline's change inside a SPEC. Cross-baseline reconciliation belongs in decision records.
- Storytelling, analogies, or motivational prose that will stale. SPEC content is objective and minimal.
