```yaml
workbench_id: governance_onboarding
guide_role: authoritative
provenance_type: lantern_authored_projection
provenance_refs:
- path: lantern/administration_procedures/SSOT_BLOB_INGESTION_v0.2.0.md
  relocation_entry_id: AP-011
- path: lantern/administration_procedures/INITIATIVE__DECOMPOSITION_AND_CH_SIZING_v0.1.0.md
  relocation_entry_id: AP-009
```

# Governance Onboarding — authoritative Lantern guide

## Purpose
Stabilizes onboarding and bootstrap guidance for governance workspaces before normal governed execution begins.

## Stable workflow-facing rules
## External bootstrap boundary
- The governed workspace is the product root plus the governance root; Lantern runtime assets remain owned by the executing Lantern install or source checkout.
- A governed product repository must not vendor or mirror the Lantern runtime tree as a bootstrap prerequisite.
- Minimal product-local bootstrap files are limited to identity/contract files, bounded launcher scripts, and ignored local MCP wiring.

- Workbench id: `governance_onboarding`.
- Instruction resource: `lantern/resources/instructions/governance_onboarding.md`.
- This guide is the stable Lantern-authored workflow-facing surface for runtime delivery and maintainer inspection.
- The preserved source corpus remains input evidence only; this file is the workflow-facing authority for the workbench.

## Bound Lantern-local resources
- `lantern/administration_procedures/SSOT_BLOB_INGESTION_v0.2.0.md`
- `lantern/administration_procedures/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md`
- `lantern/administration_procedures/INITIATIVE__DECOMPOSITION_AND_CH_SIZING_v0.1.0.md`

## Provenance
This guide is a Lantern-authored projection over reviewed Lantern-local source material. The provenance block above records the reviewed inputs and relocation-manifest entry identifiers used for auditability.

