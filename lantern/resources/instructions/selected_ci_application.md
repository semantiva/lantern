Operator instruction resource for workbench selected_ci_application.

## Workbench
Display name: Selected CI Application
Lifecycle kind: lifecycle_span

## Artifacts in scope
CI

## Key actions
- Read and follow Lantern-local guidance in lantern/preservation/WORKSPACE_TOPOLOGY.md.
- Use companion guidance in lantern/preservation/WORKBENCH_MAP.md when the workbench crosses a gate boundary.
- Keep all emitted references inside the approved Lantern-local corpus.

## MCP usage
- Inspect the selected change increment before changing product files.
- Apply only the approved Lantern-local change surface.
- Collect executable verification evidence for closure preparation.

## Constraints
- Respect posture constraints: product_writes_permitted.
- Do not emit references outside Lantern-local paths.
- Keep the workbench guidance inside the approved CH-0007 change surface.

Referenced Lantern-local guides:
- lantern/preservation/WORKSPACE_TOPOLOGY.md
- lantern/preservation/WORKBENCH_MAP.md


## Post-application administration
- Inspect the selected CI change surface before writing product files.
- Treat `.gitignore` hygiene as runtime-managed; do not author `.gitignore` mutations in the operator payload.
- After commit, capture the emitted `application_handoff` metadata and use its next-step anchors to prepare GT-130 verification.
