Operator instruction resource for workbench governance_onboarding.

## Workbench
Display name: Governance Onboarding
Lifecycle kind: lifecycle-independent
Transaction posture: inspect, draft, validate

## Artifacts in scope
INI, CH, TD

## Bound resource roles
Consult, via MCP, the resources the workflow layer binds to this workbench. Route to them; do not restate their content. This workbench binds:
- administration guides (authoring contracts and administration procedures bound to this workbench)
- artifact templates for the families in scope

## Hard stops
- Each gate requires explicit human approval by default. Bounded multi-gate authorization applies only when the human names the authorized scope; it stops at any blocker, ambiguity, failed check, dirty worktree, or scope change.
- Operate within the workspace boundary defined in AGENTS.md: write governed records only in the governance workspace.
- Do not instruct operators to vendor or copy the Lantern runtime; the product consumes it as an external package.
- Emit references only to resources delivered through this workbench's bound roles.
- Respect posture constraint: supports_bootstrap_without_product_writes.
