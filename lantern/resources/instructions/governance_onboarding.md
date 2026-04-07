Operator instruction resource for workbench governance_onboarding.

## Workbench
Display name: Governance Onboarding
Lifecycle kind: lifecycle-independent

## Artifacts in scope
INI, CH, TD

## Key actions
- Read and follow Lantern-local guidance in lantern/administration_procedures/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md.
- Use companion guidance in lantern/administration_procedures/SSOT_BLOB_INGESTION_v0.2.0.md when the workbench crosses a gate boundary.
- Keep all emitted references inside the approved Lantern-local corpus.
- Keep product bootstrap tracked files minimal: managed `AGENTS.md`, product `README.md`, bounded launcher/ignore files, and ignored local MCP wiring only.

## MCP usage
- Check runtime posture before bootstrapping.
- Use the onboarding and initiative procedures to establish the first governed slice.
- Keep all emitted references inside Lantern-local paths.

## Constraints
- Respect posture constraints: supports_bootstrap_without_product_writes.
- Do not emit references outside Lantern-local paths.
- Do not instruct operators to vendor or copy the Lantern runtime into the governed product repository.
- Keep the workbench guidance inside the approved CH-0007 change surface.

Referenced Lantern-local guides:
- lantern/administration_procedures/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md
- lantern/administration_procedures/SSOT_BLOB_INGESTION_v0.2.0.md
