# AI operator invocation templates — v0.2.0


Status: SUPERSEDED — Historical
Superseded by: `AI_OPERATOR_INVOCATION_TEMPLATES_v0.2.1.md`

Purpose:
- Provide stable “operator-to-assistant” invocation patterns that reliably trigger the intended gate procedure without scope creep.

These templates are designed for manual-but-structured execution (Mode 1) where:
- the assistant uses the authoritative guides and templates in `Lantern/`,
- the human reviews the outputs before administrative finalization (or explicitly authorizes finalization).

## Global invocation rules (normative)

An operator invocation MUST state:
- Target CH id (e.g., `CH-0018`)
- Target gate id (e.g., `GT-120`)
- Scope boundary (what is in / out)
- Authorization boundary (“you are authorized to proceed through …”)
- Stop condition (“stop after …”)
- Required output artifacts (EV/DEC, registry updates, status updates)
- Whether the assistant is authorized to perform administration steps (status updates + index changes) or only analysis

An operator invocation SHOULD state:
- Workspace root (when the assistant needs cross-repo access)
- Binding posture (commit SHA available vs release id only)

When the task creates new Lantern artifacts, the invocation SHOULD require use of the Lantern allocator tool:
- `python tools/allocate_lantern_id.py --artifact <ARTIFACT> --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact CI --ch CH-####`

## Template 0 — Create Initiative + initial DIP draft

```
We are starting a new Initiative.

Your task is to create one Initiative record and its initial DIP draft.

Required fields:
- ssot_root: <path-to-ssot-repo-root>
- source_bundle: <authoritative source set or pointer>

Scope:
- In scope: allocate `INI`, allocate `DIP`, author the Initiative in `Draft`, author a DIP draft that captures the authoritative source inventory and planning intent.
- Out of scope: GT-030 execution, SPEC/ARCH drafting, CH authoring, implementation work.

Authorization:
- You are authorized to create the Initiative and DIP files and update any required local registries.

Stop condition:
- Stop after the Initiative and DIP draft exist and both are ready for GT-030 review.

Deliverables:
- New `INI-####.md` (allocated with `python tools/allocate_lantern_id.py --artifact INI --repo <ssot_root>`)
- New `DIP-####.md` (allocated with `python tools/allocate_lantern_id.py --artifact DIP --repo <ssot_root>`)
```

## Template 0A — Advance Initiative to `Ready`

```
We are working on Initiative INI-####.

Your task is to make the Initiative operationally `Ready`.

Required fields:
- ssot_root: <path-to-ssot-repo-root>
- initiative_id: INI-####
- dip_id: DIP-####
- spec_id: SPEC-####
- arch_id: ARCH-####

Scope:
- In scope: complete upstream intake and baseline approval using GT-030, GT-050, and GT-060, carrying the required derivation/coherence evidence into the baseline-readiness review; update the Initiative references and readiness conditions.
- Out of scope: GT-110, GT-120, GT-130, CI authoring, implementation work.

Authorization:
- You are authorized to create EV/DEC records, update DIP/SPEC/ARCH statuses on PASS, and update the Initiative to `Ready` once all readiness conditions are satisfied.

Stop condition:
- Stop after the Initiative is either updated to `Ready` or explicitly blocked with the missing conditions listed.

Deliverables:
- Updated `INI-####.md`
- Required `EV-####.md` / `DEC-####.md` records for GT-030/050/060
- Updated DIP/SPEC/ARCH artifacts and registry entries
```

## Template 0B — Derive first CH from a Ready Initiative

```
We are working on Initiative INI-####.

Your task is to derive the first bounded Change Intent from this Initiative.

Required fields:
- ssot_root: <path-to-ssot-repo-root>
- initiative_id: INI-####

Scope:
- In scope: allocate one CH id, author one bounded CH slice linked through `initiative_refs`, and prepare it for later GT-110 execution.
- Out of scope: GT-110 execution, CI authoring, implementation work.

Authorization:
- You are authorized to create the CH file and update registry entries.

Stop condition:
- Stop after one bounded CH exists in `Proposed` state and the Initiative references are synchronized.

Deliverables:
- New `CH-####.md`
- Updated `INI-####.md` candidate CH list
- Updated `INDEX.md` (governance repository root)
```

## Template A — Execute GT-110 (CH refinement to Ready)

```
We are working on CH-####.

Your task is to execute `GT-110: Input Kit Readiness (Entry Gate)` for CH-####.

Scope:
- In scope: update the CH, create the required EV record(s), create the GT-110 DEC record, and update `INDEX.md` (governance repository root).
- Out of scope: drafting CI candidates, GT-120, GT-130, or any implementation work in product repositories.

Authorization:
- You are authorized to perform the complete GT-110 procedure, including administration steps (status + registry updates).

Stop condition:
- Stop after GT-110 is recorded as PASS or FAIL and all required administration artifacts are completed.

Deliverables:
- Updated `CH-####.md`
- New `EV-####.md` (GT-110 evidence; id allocated with `python tools/allocate_lantern_id.py`)
- New `DEC-####.md` (GT-110 decision; id allocated with `python tools/allocate_lantern_id.py`)
- Updated `INDEX.md` (governance repository root)
```

## Template B — Execute GT-120 selection (analysis only; no administration)

```
We are working on CH-####.

Your task is to execute `GT-120: Change Increment Selection (Selection Gate)` for the CI candidates for CH-####.

Scope:
- In scope: read all CI candidates for CH-####, select the single best candidate, and produce a GT-120 selection report (EV).
- Out of scope: status changes, registry updates, GT-130, and any implementation work.

Authorization:
- You are authorized to complete the selection analysis and produce the EV selection report.
- You are NOT authorized to perform administration steps.

Stop condition:
- Stop after producing the EV selection report and clearly stating the selected CI id and rationale.

Deliverables:
- New `EV-####.md` (GT-120 selection report; allocate id with `python tools/allocate_lantern_id.py` and use `lantern/templates/EV_TEMPLATE__GT120_SELECTION_REPORT.md`)
```

## Template C — Execute GT-120 selection + administration (full gate completion)

```
We are working on CH-####.

Your task is to execute `GT-120: Change Increment Selection (Selection Gate)` for the CI candidates for CH-#### and complete administration.

Scope:
- In scope: selection analysis, EV selection report, DEC selection decision, CI status updates, CH updates, and `INDEX.md` (governance repository root) updates.
- Out of scope: GT-130 verification and any implementation work.

Authorization:
- You are authorized to proceed with the entire GT-120 process, including administration steps, and then stop.

Stop condition:
- Stop after:
  - exactly one CI is marked Selected,
  - all non-selected candidates are marked Rejected (with rationale),
  - EV and DEC are created,
  - CH is updated with references,
  - registry is updated.

Deliverables:
- New `EV-####.md` (GT-120 selection report; id allocated with `python tools/allocate_lantern_id.py`)
- New `DEC-####.md` (GT-120 decision; id allocated with `python tools/allocate_lantern_id.py`)
- Updated CI candidate files (statuses)
- Updated `CH-####.md` (references to selected CI + EV/DEC)
- Updated `INDEX.md` (governance repository root)
```

## Template D — Execute GT-030 (DIP lock)

```
We are working on DIP-####.

Your task is to execute `GT-030: Design Input Pack Lock (DIP baseline lock)`.

Required fields:
- ssot_root: <path-to-lantern-workflow-ssot-repo-root>
- dip_id: DIP-####

Scope:
- In scope: review DIP completeness, source inventory, baseline locator/waiver handling, supersession declaration (if present), and referenced Questions handling.
- Out of scope: SPEC/ARCH drafting, GT-050/060, CH authoring.

Authorization:
- You are authorized to create EV and DEC records for GT-030 and update registry entries.

Stop condition:
- Stop after GT-030 PASS/FAIL is recorded with EV+DEC references and status administration is complete.

Deliverables:
- New `EV-####.md` (GT-030 evidence; id allocated with `python tools/allocate_lantern_id.py`)
- New `DEC-####.md` (GT-030 decision; id allocated with `python tools/allocate_lantern_id.py`)
- Updated DIP status (Draft -> Approved on PASS)
- Updated `INDEX.md` (governance repository root)
```

## Template E — Prepare SPEC/ARCH derivation packet for GT-050 and GT-060

```
We are working on DIP-#### with derived SPEC-#### and ARCH-#### drafts.

Your task is to prepare the derivation packet that GT-050 and GT-060 will review.

Required fields:
- ssot_root: <path-to-lantern-workflow-ssot-repo-root>
- dip_id: DIP-####
- spec_id: SPEC-####
- arch_id: ARCH-####

Scope:
- In scope: derivation linkage checks, structural completeness checks, and any draft updates needed so SPEC and ARCH are ready for GT-050 / GT-060 review.
- Out of scope: baseline-readiness decisions and CH authoring.

Authorization:
- You are authorized to update the drafts and prepare the derivation notes that will be cited in GT-050 / GT-060 evidence.

Stop condition:
- Stop after the derivation packet is ready for the baseline-readiness review.

Deliverables:
- Updated `SPEC-####.md` and/or `ARCH-####.md` as needed
- One concise derivation evidence packet or checklist ready to be cited in GT-050 / GT-060 EV records
```

## Template F — Review DIP/SPEC/ARCH coherence for GT-050 and GT-060

```
We are working on DIP-####, SPEC-####, and ARCH-####.

Your task is to review the cross-artifact coherence that GT-050 and GT-060 will rely on.

Required fields:
- ssot_root: <path-to-lantern-workflow-ssot-repo-root>
- dip_id: DIP-####
- spec_id: SPEC-####
- arch_id: ARCH-####

Scope:
- In scope: contradiction/coherence analysis across DIP constraints/non-goals, SPEC scope, ARCH scope, and Questions alignment, plus any draft updates or review notes needed to resolve contradictions before baseline readiness.
- Out of scope: baseline-readiness decisions and CH authoring.

Authorization:
- You are authorized to update the drafts and produce the coherence notes that will be cited in GT-050 / GT-060 evidence.

Stop condition:
- Stop after the coherence packet is ready for GT-050 / GT-060 review, or after the remaining blockers are listed explicitly.

Deliverables:
- Updated `SPEC-####.md` and/or `ARCH-####.md` as needed
- One concise coherence evidence packet or checklist ready to be cited in GT-050 / GT-060 EV records
```

## Template G — Execute GT-050 and GT-060 (baseline readiness)

```
We are working on SPEC-#### and ARCH-#### baselines.

Your task is to execute:
- `GT-050: Requirements Specification Readiness (SPEC baseline readiness)`
- `GT-060: Architecture Definition Readiness (ARCH baseline readiness)`

Required fields:
- ssot_root: <path-to-lantern-workflow-ssot-repo-root>
- spec_id: SPEC-####
- arch_id: ARCH-####

Scope:
- In scope: completeness checks, acceptance criteria checks (SPEC), baseline locator or waiver handling, supersession handling, review summary capture, DEC outcomes.
- Out of scope: GT-110/120 and any implementation work.

Authorization:
- You are authorized to create EV/DEC records, update artifact statuses on PASS, and update registry entries.

Stop condition:
- Stop after both GT-050 and GT-060 have explicit PASS/FAIL DEC outcomes and administration is complete.

Deliverables:
- New `EV-####.md` + `DEC-####.md` for GT-050 (allocate ids with `python tools/allocate_lantern_id.py`)
- New `EV-####.md` + `DEC-####.md` for GT-060 (allocate ids with `python tools/allocate_lantern_id.py`)
- Updated ARCH/SPEC statuses (Draft -> Approved on PASS)
- Updated `INDEX.md` (governance repository root)
```
