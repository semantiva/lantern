# ISSUE workflow (Intake → Triage → Resolution/Rejection) v0.2.0

Scope
- Define a low-overhead workflow for issues from intake through resolution or rejection.
- Accepted issues must be addressed via the existing Change Intent (CH) and Change Increment (CI) workflow.

Out of scope
- Investigating or fixing any specific issue.
- Changing the CH/CI workflow itself.

## Core principle

An Issue is a factual report of an observed problem or risk.
If the issue is accepted, the unit of work becomes a Change Intent (CH).
The issue remains as the origin record.

Ordered notes are append-only timestamped issue comments captured inside the issue artifact. They document mitigation posture and incremental observations without changing the lifecycle model.

## Artifacts

- Issue file: `is/IS-####.md`
- Template: `lantern/templates/TEMPLATE__IS.md`
- This guide: `lantern/administration_procedures/ISSUE__INTAKE_TRIAGE_RESOLUTION_v0.2.0.md`

No additional registers are required.

## Status model

- `NEW`: recorded, not triaged
- `NEEDS_INFO`: triage cannot decide; missing context listed explicitly
- `ACCEPTED`: valid issue; convert to CH
- `DEFERRED`: valid but postponed (condition/date recorded)
- `REJECTED`: not accepted (rationale recorded)
- `RESOLVED`: resolved via CH/CI/evidence linkage

Allowed transitions:
- `NEW` → `NEEDS_INFO | ACCEPTED | DEFERRED | REJECTED`
- `NEEDS_INFO` → `NEW | ACCEPTED | DEFERRED | REJECTED`
- `ACCEPTED` → `RESOLVED | DEFERRED`
- `DEFERRED` → `ACCEPTED | REJECTED`
- `REJECTED` and `RESOLVED` are terminal

## Step 1 — Intake

Trigger
- Any observed friction, defect, inconsistency, or risk during intake or gate execution.

Procedure
1. Allocate the next issue identifier using the authoritative allocator tool and create `is/IS-####.md` from `lantern/templates/TEMPLATE__IS.md`.
   - Command: `python tools/allocate_lantern_id.py --artifact IS --repo <path-to-ssot-repo>`
2. Fill required minimum fields:
   - ID, Status, Created, Reporter, Owner
   - Summary, Observation, Expected, Impact/Risk
   - Evidence pointers (or explicitly "not available")
3. Set `Status: NEW`.

Intake completion criteria
- Observation is factual (no speculative solutioning).
- Evidence section has actionable pointers.

## Step 2 — Triage

Goal
- Decide what happens next: NEEDS_INFO, ACCEPTED, DEFERRED, or REJECTED.

Procedure
1. Review issue facts and evidence.
2. Record triage decision, date, decider, rationale, and next action.
3. If `NEEDS_INFO`, list explicit missing items.
4. If `ACCEPTED`, create `CH-####` and link it in the issue file.
5. If new mitigation context or validation posture must be recorded while the issue remains open, append it under `## Ordered notes` as a new timestamped entry rather than rewriting the historical Observation or Triage sections.

Triage completion criteria
- Decision and rationale are explicit and auditable.
- Next action is unambiguous.

## Step 3 — Resolution / Closure

For `ACCEPTED` issues:
1. Execute CH→CI workflow under normal gates.
2. When resolved, update issue status to `RESOLVED`.
3. Add links to CH, CI, and EV/DEC evidence proving closure.

For `DEFERRED` issues:
- Keep rationale plus re-entry condition/date.

For `REJECTED` issues:
- Keep concise rejection rationale.

Ordered note rules
- Use append-only timestamped ordered notes for mitigation-in-place context, reviewer observations, and validation updates.
- Ordered notes do not add a new issue state and do not change the meaning of `NEW`, `NEEDS_INFO`, `ACCEPTED`, `DEFERRED`, `REJECTED`, or `RESOLVED`.
- When an issue remains open after a bounded mitigation lands, record that posture in ordered notes instead of marking the issue resolved early.

## Quality guardrails

- Do not embed implementation plans in issue files.
- Do not bypass CH creation for accepted issues.
- Keep issue records short, factual, and link-driven.
