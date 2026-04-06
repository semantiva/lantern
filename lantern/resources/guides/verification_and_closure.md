```yaml
workbench_id: verification_and_closure
guide_role: authoritative
provenance_type: lantern_authored_projection
provenance_refs:
- path: lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION_v0.1.0.md
  relocation_entry_id: AP-007
```

# Verification and Closure — authoritative Lantern guide

## Purpose
Stabilizes GT-130 verification and closure posture so verification evidence and quarantine semantics remain explicit.

## Stable workflow-facing rules
- Workbench id: `verification_and_closure`.
- Instruction resource: `lantern/resources/instructions/verification_and_closure.md`.
- This guide is the stable Lantern-authored workflow-facing surface for runtime delivery and maintainer inspection.
- The preserved source corpus remains input evidence only; this file is the workflow-facing authority for the workbench.

## Bound Lantern-local resources
- `lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION_v0.1.0.md`

## Provenance
This guide is a Lantern-authored projection over reviewed Lantern-local source material. The provenance block above records the reviewed inputs and relocation-manifest entry identifiers used for auditability.


## Expectation-to-delivery review
A GT-130 PASS for MVP slices requires all of the following review anchors to be explicit in the evidence packet:
- initiative objective and roadmap role for the governing CH
- requirements satisfaction against the approved SPEC / TD envelope
- architectural fit against the approved ARCH baseline
- local verification execution, clean-state evidence, and reproducibility evidence
- workflow-maintainer guidance that makes the review checklist explicit rather than optional

