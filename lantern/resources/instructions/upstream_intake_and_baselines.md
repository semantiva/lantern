Operator instruction resource for workbench upstream_intake_and_baselines.

## Workbench
Display name: Upstream Intake and Baselines
Lifecycle kind: covered_gates
Transaction posture: inspect, draft, commit, validate

## Artifacts in scope
DIP, SPEC, ARCH, INI

## Bound resource roles
Consult, via MCP, the resources the workflow layer binds to this workbench. Route to them; do not restate their content. This workbench binds:
- administration guides (authoring contracts and administration procedures bound to this workbench)
- artifact templates for the families in scope

## Hard stops
- Each gate requires explicit human approval by default. Bounded multi-gate authorization applies only when the human names the authorized scope; it stops at any blocker, ambiguity, failed check, dirty worktree, or scope change.
- Operate within the workspace boundary defined in AGENTS.md: write governed records only in the governance workspace.
- Emit references only to resources delivered through this workbench's bound roles.
- Respect posture constraint: requires_governance_workspace.
- Respect posture constraint: startup_validated.
