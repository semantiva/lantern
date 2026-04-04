# Lantern workflow gate definitions

This document is normative for Lantern workflow gate execution requirements, required evidence posture, and the intended state transitions around the gates.

## GT-030 — Design Input Pack Lock
Purpose:
- establish a DIP baseline as an upstream anchor.

Inputs:
- Draft DIP
Evidence/Decision:
- EV + DEC
Output posture:
- DIP approved or blocked; SPEC/ARCH drafting may begin on PASS.

## GT-050 — Architecture Definition Readiness
Purpose:
- approve ARCH as a reusable baseline for downstream change work.

Required inputs:
- Approved DIP
- Draft ARCH
- Derivation and coherence evidence for the current DIP/SPEC/ARCH draft set
Evidence/Decision:
- EV + DEC
Output posture:
- ARCH Approved or blocked.

## GT-060 — Requirements Specification Readiness
Purpose:
- approve SPEC as a reusable baseline for downstream change work.

Required inputs:
- Approved DIP
- Draft SPEC
- Derivation and coherence evidence for the current DIP/SPEC/ARCH draft set
Evidence/Decision:
- EV + DEC
Output posture:
- SPEC Approved or blocked.

## GT-110 — Input Kit Readiness
Purpose:
- determine whether a proposed CH has sufficient approved upstream inputs, including approved test-definition coverage, to proceed to design selection.

Required inputs:
- Proposed CH
- Approved TD set referenced by the CH
- Approved SPEC and Approved ARCH for the governed scope

Evidence/Decision:
- At least one EV and one DEC for the gate run.
- EV MUST show non-placeholder TD coverage. EV MUST NOT rely on aspirational runnable-command examples as the readiness truth.

Pass posture:
- CH becomes `Ready`.
- Referenced TD artifacts remain or become `Approved`.

Fail posture:
- CH remains `Proposed`.
- Missing or shallow TD coverage is STOP, not deferrable by rationale.

## GT-115 — Design Baseline Selection
Purpose:
- select one design candidate and approve one authoritative design baseline before implementation selection.

Required inputs:
- Ready CH
- Approved TD set
- Approved SPEC
- Approved ARCH
- One or more Candidate DC artifacts

Evidence/Decision:
- At least one EV and one DEC for the gate run.
- EV SHOULD compare candidates against CH criteria, DB-governed scope, compatibility posture, and TD traceability.

Pass posture:
- One DC becomes `Selected`.
- Remaining DCs become `Rejected`.
- One DB becomes `Approved`.
- CH remains `Ready`.

Fail posture:
- No DB is approved.
- Candidate pool remains unresolved or blocked.

## GT-120 — Change Increment Selection
Purpose:
- select exactly one implementation candidate against a locked CH + DB + TD envelope.

Required inputs:
- Ready CH
- Approved DB
- Approved TD set
- One or more Candidate CI artifacts

Evidence/Decision:
- At least one EV and one DEC for the gate run.
- GT-120 remains mandatory even if only one CI candidate exists.

Pass posture:
- One CI becomes `Selected`.
- Any non-selected CI artifacts become `Rejected`.

Fail posture:
- No CI becomes `Selected`.

## GT-130 — Integration Verification
Purpose:
- verify the selected CI against the locked CH, DB, and TD baseline.

Required inputs:
- Ready CH
- Approved DB
- Approved TD set
- Selected CI

Evidence/Decision:
- At least one EV and one DEC for the gate run.
- EV MUST include real verification evidence tied to the selected CI and the approved TD set.

Pass posture:
- CI becomes `Verified`.
- CH becomes `Addressed`.

Fail posture:
- CI remains `Selected` or is administratively demoted per decision.
- CH remains `Ready`.
