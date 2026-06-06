# Initiative authoring and readying

Status: AUTHORITATIVE - Guidance
Date (UTC): 2026-06-03

Purpose:
- Define how to author an Initiative and move it to `Ready` without assigning product technical baselines to Initiative ownership.
- Preserve the hand-off from roadmap planning to CH execution through GT-110 readiness.

Normative anchors:
- `lantern/administration_procedures/INITIATIVE__DECOMPOSITION_AND_CH_SIZING.md`
- `lantern/authoring_contracts/change_intention_refinement_guide.md`
- `lantern/authoring_contracts/dip_authoring_guide.md`
- `lantern/authoring_contracts/spec_authoring_guide.md`
- `lantern/authoring_contracts/arch_authoring_guide.md`

## Scope

In scope:
- allocate and author Initiative records;
- define the Initiative objective, boundary, decomposition posture, and candidate CH slices;
- reference relevant product baselines where applicable;
- mark an Initiative `Ready` only when at least one decomposed or referenced CH is `Ready`.

Out of scope:
- assigning DIP, SPEC, or ARCH artifacts to Initiative ownership;
- replacing GT-030, GT-050, GT-060, or GT-110 evidence;
- implementation work in product repositories;
- redefining CH, CI, or lifecycle semantics.

## Canonical storage and identifiers

- Initiative records live in `ini/`.
- Initiative identifiers use the form `INI-####`.
- Allocate Initiative identifiers with `python tools/allocate_lantern_id.py --artifact INI --repo <path-to-governance-root>`.

Do not invent Initiative identifiers or use slug-only filenames in place of `INI-####.md` records.

## Initiative readiness posture

Lantern does not define a separate Initiative gate family. Initiative `Ready` is a planning readiness state, not a technical-baseline approval state.

An Initiative is `Ready` when all are true:
1. the Initiative objective and boundary are explicit;
2. the decomposition posture is coherent and bounded;
3. at least one decomposed or referenced CH is `Ready`;
4. any referenced DIP, SPEC, or ARCH baselines are product baselines, not owned by the Initiative;
5. the Initiative record links the CH slice that carries execution-grade readiness.

Upstream DIP/SPEC/ARCH sufficiency is inherited through the Ready CH's GT-110 evidence. The Initiative must not assert a direct ownership or lifecycle dependency over those baselines.

## Gate approval posture

Each gate requires explicit human approval before the operator proceeds. The human may grant bounded multi-gate authorization only by naming the authorized scope. Authorization stops at any blocker, ambiguity, failed check, dirty worktree, or scope change.

## Procedure

### Step 0 - Allocate and author the Initiative in `Draft`

Create `ini/INI-####.md` using the Initiative template. Include objective, scope, decomposition notes, candidate CH list, sizing rationale, readiness conditions, and evidence pointers.

### Step 1 - Establish or reference product baselines

If the requested work lacks Approved product baselines, run the appropriate intake and baseline procedures outside the Initiative record:
- GT-030 for DIP approval;
- GT-050 for SPEC approval;
- GT-060 for ARCH approval.

The Initiative may reference those records after they exist. It must not describe them as owned by the Initiative.

### Step 2 - Decompose into CH slices

Use `lantern/administration_procedures/INITIATIVE__DECOMPOSITION_AND_CH_SIZING.md` to identify coherent CH slices. A CH slice should be independently refinable and should carry its own approved upstream baseline references when it reaches GT-110.

### Step 3 - Execute GT-110 for at least one CH

Use `lantern/authoring_contracts/change_intention_refinement_guide.md` to move at least one CH to `Ready`. The CH GT-110 evidence is the point where DIP/SPEC/ARCH sufficiency is checked for execution.

### Step 4 - Move Initiative to `Ready`

Set Initiative status to `Ready` only after the record is bounded and at least one referenced CH is `Ready`. Update `INDEX.md` and any Initiative CH reference list in the same administration step.

## Relationship to CH execution

Initiative is the planning object above CH. CH remains the execution-grade requirement anchor. CI remains the candidate implementation unit.

Initiative status must not be used as a substitute for GT-110, GT-115, GT-120, or GT-130 outcomes.
