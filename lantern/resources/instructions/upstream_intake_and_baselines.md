Operator instruction resource for workbench upstream_intake_and_baselines.

## Workbench
Display name: Upstream Intake and Baselines
Lifecycle kind: covered_gates

## Artifacts in scope
DIP, SPEC, ARCH, INI

## Key actions
- Read and follow Lantern-local guidance in lantern/administration_procedures/SSOT_BLOB_INGESTION_v0.2.0.md.
- Use companion guidance in lantern/administration_procedures/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md when the workbench crosses a gate boundary.
- Keep all emitted references inside the approved Lantern-local corpus.

## MCP usage
- Inspect runtime posture before any write.
- Use the ingestion and validation flow for upstream baselines.
- Keep references inside the Lantern-local corpus.

## Constraints
- Respect posture constraints: requires_governance_workspace, startup_validated.
- Do not emit references outside Lantern-local paths.
- Keep the workbench guidance inside the approved CH-0007 change surface.

Referenced Lantern-local guides:
- lantern/administration_procedures/SSOT_BLOB_INGESTION_v0.2.0.md
- lantern/administration_procedures/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md
