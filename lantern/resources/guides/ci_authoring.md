```yaml
workbench_id: ci_authoring
guide_role: authoritative
provenance_type: lantern_authored_projection
provenance_refs:
- path: lantern/authoring_contracts/change_increment_authoring_guide.md
  relocation_entry_id: AC-001
- path: lantern/authoring_contracts/allowed_change_surface_flexibilization.md
  relocation_entry_id: AC-009
```

# CI Authoring — authoritative Lantern guide

## Purpose
Stabilizes the post-GT-115 implementation-candidate authoring surface so GT-120 compares real execution-grade CI packages.

## Stable workflow-facing rules
- Workbench id: `ci_authoring`.
- Instruction resource: `lantern/resources/instructions/ci_authoring.md`.
- This guide is the stable Lantern-authored workflow-facing surface for runtime delivery and maintainer inspection.
- The preserved source corpus remains input evidence only; this file is the workflow-facing authority for the workbench.
- Active CI records that include `__init__.py` in `allowed_change_surface` must justify the package-surface reason for that file explicitly.

## Bound Lantern-local resources
- `lantern/authoring_contracts/change_increment_authoring_guide.md`
- `lantern/authoring_contracts/allowed_change_surface_flexibilization.md`

## Provenance
This guide is a Lantern-authored projection over reviewed Lantern-local source material. The provenance block above records the reviewed inputs and relocation-manifest entry identifiers used for auditability.

