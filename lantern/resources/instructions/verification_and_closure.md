Operator instruction resource for workbench verification_and_closure.

## Workbench
Display name: Verification and Closure
Lifecycle kind: covered_gates

## Artifacts in scope
CI, EV, DEC

## Key actions
- Read and follow Lantern-local guidance in lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION.md.
- Keep all emitted references inside the approved Lantern-local corpus.

## MCP usage
- Resolve the verification packet before gate execution.
- Run the declared verification commands against the product repo.
- Record Lantern-local evidence and decision references only.

## Constraints
- Respect posture constraints: requires_selected_ci.
- Do not emit references outside Lantern-local paths.
- Keep the workbench guidance inside the approved CH-0007 change surface.

Referenced Lantern-local guides:
- lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION.md


## Required GT-130 review anchors
- Record initiative objective and roadmap role before judging local test output.
- Map each approved TD case to actual verification evidence.
- Confirm architectural fit against the approved ARCH baseline.
- Capture clean-state and reproducibility evidence together with command output.
- Treat local test passage alone as insufficient for GT-130 PASS.
