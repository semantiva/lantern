# Lantern workflow epistemic frame

This document is normative for what each Lantern workflow artifact class is allowed to claim.

## Core rule

- Semantics are authoritative in Lantern model.
- Workflow artifacts and guides are authoritative for operational execution only.
- Evidence supports decisions. Evidence does not redefine semantics.

## Artifact families

### Change Intent (CH)
A CH states what must become true, why it matters, what constraints apply, and what evidence/decision posture is required to move forward.

### Test Definition (TD)
A TD states what must be tested and how success is judged before design or implementation selection.
A TD is behavioral truth, not an implementation patch.

### Design Candidate (DC)
A DC is a candidate design compared at GT-115.
A DC may describe a possible solution shape, compatibility posture, and bounded change surface. It is not authoritative once rejected.

### Design Baseline (DB)
A DB is the authoritative selected design artifact approved at GT-115.
A DB governs only its declared governed scope.

### Change Increment (CI)
A CI is an implementation-only candidate package authored against a locked CH + DB + TD envelope.
A CI MUST NOT redefine design or test strategy.
If a CI needs to change design or testing truth, the workflow MUST reopen GT-115 or GT-110 respectively.

### Evidence (EV)
EV captures verifiable evidence for gate execution.

### Decision (DEC)
DEC records gate outcomes, selections, or supersession decisions.

## Invariants

- Missing TD coverage blocks GT-110.
- Missing DB blocks GT-120 and GT-130.
- Rejected DC artifacts remain historical but are non-authoritative.
- The active design corpus is the set of Approved, non-superseded DB artifacts.
