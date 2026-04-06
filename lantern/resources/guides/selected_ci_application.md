```yaml
workbench_id: selected_ci_application
guide_role: authoritative
provenance_type: lantern_authored_projection
provenance_refs:
- path: lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION_v0.1.0.md
  relocation_entry_id: AP-007
```

# Selected CI Application — authoritative Lantern guide

## Purpose
Stabilizes the post-GT-120, pre-GT-130 product-application posture and keeps it distinct from both authoring and verification.

## Stable workflow-facing rules
- Workbench id: `selected_ci_application`.
- Instruction resource: `lantern/resources/instructions/selected_ci_application.md`.
- This guide is the stable Lantern-authored workflow-facing surface for runtime delivery and maintainer inspection.
- The preserved source corpus remains input evidence only; this file is the workflow-facing authority for the workbench.

## Bound Lantern-local resources
- `lantern/administration_procedures/GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md`
- `lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION_v0.1.0.md`

## Provenance
This guide is a Lantern-authored projection over reviewed Lantern-local source material. The provenance block above records the reviewed inputs and relocation-manifest entry identifiers used for auditability.


## Post-application posture
- A successful `selected_ci_application` commit MUST emit runtime-managed `application_handoff` metadata.
- The handoff records the applied CI id, contract ref, effective change surface, affected product paths, actor, timestamp, and the Lantern-local next-step anchors that govern GT-130 preparation.
- Product bootstrap hygiene is runtime-managed and limited to a deterministic Python/test/cache `.gitignore` block when the target repository lacks the required ignore coverage.
- The handoff posture is `awaiting_gt130`; it is not a new CI status and it does not create a new SSOT artifact family.

