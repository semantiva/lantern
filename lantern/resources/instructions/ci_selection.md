Operator instruction resource for workbench ci_selection.

## Workbench
Display name: CI Selection
Lifecycle kind: covered_gates

## Artifacts in scope
CI, EV, DEC

## Key actions
- Read and follow Lantern-local guidance in lantern/authoring_contracts/change_increment_selection_guide_v0.2.1.md.
- Use companion guidance in lantern/administration_procedures/GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md when the workbench crosses a gate boundary.
- Keep all emitted references inside the approved Lantern-local corpus.

## MCP usage
- Load the gate context before comparing candidates.
- Use the approved selection guide and evidence format.
- Do not widen the selected change surface during selection.

## Constraints
- Respect posture constraints: requires_execution_grade_candidate.
- Do not emit references outside Lantern-local paths.
- Keep the workbench guidance inside the approved CH-0007 change surface.

Referenced Lantern-local guides:
- lantern/authoring_contracts/change_increment_selection_guide_v0.2.1.md
- lantern/administration_procedures/GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md
