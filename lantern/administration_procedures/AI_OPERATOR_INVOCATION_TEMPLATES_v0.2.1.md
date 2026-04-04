# AI operator invocation templates — v0.2.1


Status: AUTHORITATIVE — Procedure
Date (UTC): 2026-03-15
Supersedes: v0.2.0

Purpose:
- Provide stable operator-to-assistant invocation patterns that reliably trigger the intended gate procedure without scope creep.
- Preserve the rich template posture from `v0.2.0` while updating it for the active `TD / DC / DB / GT-115` downstream contract.

These templates are designed for manual-but-structured execution (Mode 1) where:
- the assistant uses the authoritative guides and templates in `Lantern/`,
- the human reviews the outputs before administrative finalization, or explicitly authorizes finalization.

Normative anchors:
- `lantern/authoring_contracts/dip_authoring_guide_v0.1.0.md`
- `lantern/authoring_contracts/change_intention_refinement_guide_v0.2.1.md`
- `lantern/authoring_contracts/test_definition_authoring_guide_v0.1.0.md`
- `lantern/authoring_contracts/design_candidate_authoring_guide_v0.1.0.md`
- `lantern/authoring_contracts/design_baseline_authoring_guide_v0.1.0.md`
- `lantern/authoring_contracts/change_increment_authoring_guide_v0.2.1.md`
- `lantern/authoring_contracts/change_increment_selection_guide_v0.2.1.md`
- `lantern/administration_procedures/GT-030__DIP_LOCK_ADMINISTRATION_v0.1.0.md`
- `lantern/administration_procedures/GT-050_GT-060__BASELINE_READINESS_ADMINISTRATION_v0.1.0.md`
- `lantern/administration_procedures/GT-115__DESIGN_BASELINE_SELECTION_v0.1.0.md`
- `lantern/administration_procedures/GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md`
- `lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION_v0.1.0.md`

## Global invocation rules (normative)

An operator invocation MUST state:
- target artifact id or scope anchor (`INI`, `DIP`, `SPEC`, `ARCH`, `CH`, `TD`, `DC`, `DB`, `CI` as applicable),
- target gate id (for example `GT-110`, `GT-115`, `GT-120`),
- scope boundary (what is in / out),
- authorization boundary (`you are authorized to proceed through ...`),
- stop condition (`stop after ...`),
- required output artifacts (`EV`, `DEC`, registry updates, status updates),
- whether the assistant is authorized to perform administration steps or only analysis.

An operator invocation SHOULD state:
- `governance_root` or workspace root when the assistant needs repo-local path resolution,
- binding posture (commit SHA available vs release id only),
- the governing authoring contract when the task creates `DC` or `CI` artifacts.

When the task creates new Lantern artifacts, the invocation SHOULD require use of the Lantern allocator tool:
- `python tools/allocate_lantern_id.py --artifact <ARTIFACT> --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact CI --ch CH-#### --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DC --ch CH-#### --repo <path-to-ssot-repo>`

When the task creates downstream candidate artifacts, the invocation SHOULD lock the governing contract explicitly:
- DC work -> `lantern/authoring_contracts/design_candidate_authoring_guide_v0.1.0.md`
- CI work -> `lantern/authoring_contracts/change_increment_authoring_guide_v0.2.1.md`

## Template 0 — Create Initiative + initial DIP draft

```text
We are starting a new Initiative.

Your task is to create one Initiative record and its initial DIP draft.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- source_bundle: <authoritative source set or pointer>

Scope:
- In scope: allocate `INI`, allocate `DIP`, author the Initiative in `Draft`, author a DIP draft that captures the authoritative source inventory and planning intent.
- Out of scope: GT-030 execution, SPEC/ARCH drafting, CH authoring, implementation work.

Authorization:
- You are authorized to create the Initiative and DIP files and update any required local registries.

Stop condition:
- Stop after the Initiative and DIP draft exist and both are ready for GT-030 review.

Deliverables:
- New `INI-####.md` (allocated with `python tools/allocate_lantern_id.py --artifact INI --repo <governance_root>`)
- New `DIP-####.md` (allocated with `python tools/allocate_lantern_id.py --artifact DIP --repo <governance_root>`)
```

## Template 0A — Advance Initiative to `Ready`

```text
We are working on Initiative INI-####.

Your task is to make the Initiative operationally `Ready`.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- initiative_id: INI-####
- dip_id: DIP-####
- spec_id: SPEC-####
- arch_id: ARCH-####

Scope:
- In scope: complete upstream intake and baseline approval using GT-030, GT-050, and GT-060, carrying the required derivation/coherence evidence into the baseline-readiness review; update the Initiative references and readiness conditions.
- Out of scope: GT-110, GT-115, GT-120, GT-130, candidate authoring, implementation work.

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

```text
We are working on Initiative INI-####.

Your task is to derive the first bounded Change Intent from this Initiative.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- initiative_id: INI-####

Scope:
- In scope: allocate one CH id, author one bounded CH slice linked through `initiative_refs`, and prepare it for later GT-110 execution.
- Out of scope: GT-110 execution, GT-115, GT-120, GT-130, candidate authoring, implementation work.

Authorization:
- You are authorized to create the CH file and update registry entries.

Stop condition:
- Stop after one bounded CH exists in `Proposed` state and the Initiative references are synchronized.

Deliverables:
- New `CH-####.md`
- Updated `INI-####.md` candidate CH list
- Updated `Lantern/change/INDEX.md`
```

## Template A — Execute GT-110 (CH + TD refinement to Ready)

```text
We are working on CH-####.

Your task is to execute `GT-110: Input Kit Readiness (Entry Gate)` for CH-####.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- ch_id: CH-####
- td_scope: <existing TD ids or "allocate required TDs">

Scope:
- In scope: update the CH, author or refine the required `TD` set, create the required EV record(s), create the GT-110 DEC record, and update `Lantern/change/INDEX.md`.
- Out of scope: authoring DC candidates, GT-115, GT-120, GT-130, or any implementation work in product repositories.

Authorization:
- You are authorized to perform the complete GT-110 procedure, including TD authoring/refinement and administration steps (status + registry updates).

Stop condition:
- Stop after GT-110 is recorded as PASS or FAIL and all required administration artifacts are completed.

Deliverables:
- Updated `CH-####.md`
- New or updated `TD-####.md` artifacts as required
- New `EV-####.md` (GT-110 evidence; id allocated with `python tools/allocate_lantern_id.py`)
- New `DEC-####.md` (GT-110 decision; id allocated with `python tools/allocate_lantern_id.py`)
- Updated `Lantern/change/INDEX.md`
```

## Template A1 — Author DC candidates for a Ready CH (no GT-115 administration)

```text
We are working on CH-####.

Your task is to author one or more Design Candidate artifacts for CH-#### using `Lantern/design_candidate_authoring_guide_v0.1.0.md`.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- ch_id: CH-####
- spec_ids: [SPEC-####, ...]
- arch_ids: [ARCH-####, ...]
- td_ids: [TD-####, ...]

Scope:
- In scope: allocate DC ids, author one or more `DC` artifacts in `Candidate` or justified `Draft` status, and update `Lantern/change/INDEX.md`.
- Out of scope: GT-115 selection administration, DB authoring, GT-120, GT-130, or implementation work.

Authorization:
- You are authorized to create `DC` files and update registry entries.

Stop condition:
- Stop after the candidate DC set exists and registry entries are synchronized.

Deliverables:
- New `DC-<CH_NUM>-<UUID>.md` candidate files
- Updated `Lantern/change/INDEX.md`
```

## Template A2 — Execute GT-115 selection (analysis only; no administration)

```text
We are working on CH-####.

Your task is to execute `GT-115: Design Baseline Selection` for the DC candidates for CH-#### using `Lantern/design_candidate_selection_guide_v0.1.0.md`.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- ch_id: CH-####
- dc_ids: [DC-<CH_NUM>-<UUID>, ...]
- spec_ids: [SPEC-####, ...]
- arch_ids: [ARCH-####, ...]
- td_ids: [TD-####, ...]

Scope:
- In scope: run the selection analysis from `Lantern/design_candidate_selection_guide_v0.1.0.md` against the candidate DC set (comparing against CH criteria, SPEC/ARCH baseline, TD traceability, governed scope, and compatibility posture) and produce a GT-115 selection report.
- Out of scope: status changes, DB authoring, registry updates, GT-120, GT-130, and implementation work.

Authorization:
- You are authorized to complete the selection analysis and produce the EV selection report only.
- You are NOT authorized to perform administration steps.

Stop condition:
- Stop after producing the EV selection report and clearly stating the recommended selected DC id with rationale.

Deliverables:
- New `EV-####.md` (GT-115 selection report; allocate id with `python tools/allocate_lantern_id.py` and use `lantern/templates/EV_TEMPLATE__GT115_SELECTION_REPORT.md`)
```

## Template A3 — Execute GT-115 selection + administration (full gate completion)

```text
We are working on CH-####.

Your task is to execute `GT-115: Design Baseline Selection` for the DC candidates for CH-#### and complete administration using `lantern/administration_procedures/GT-115__DESIGN_BASELINE_SELECTION_v0.1.0.md`.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- ch_id: CH-####
- dc_ids: [DC-<CH_NUM>-<UUID>, ...]
- spec_ids: [SPEC-####, ...]
- arch_ids: [ARCH-####, ...]
- td_ids: [TD-####, ...]

Scope:
- In scope: selection analysis, EV selection report, DEC selection decision, DC status updates, DB authoring, and `Lantern/change/INDEX.md` updates.
- Out of scope: GT-120, GT-130, and implementation work.

Authorization:
- You are authorized to proceed with the entire GT-115 process, including administration steps, and then stop.

Stop condition:
- Stop after:
  - exactly one DC is marked `Selected`,
  - non-selected candidates are marked `Rejected`,
  - one `DB-####.md` is authored in `Approved` status,
  - EV and DEC are created,
  - registry is updated.

Deliverables:
- New `EV-####.md` (GT-115 selection report; id allocated with `python tools/allocate_lantern_id.py`)
- New `DEC-####.md` (GT-115 decision; id allocated with `python tools/allocate_lantern_id.py`)
- Updated DC candidate files (statuses)
- New `DB-####.md`
- Updated `Lantern/change/INDEX.md`
```

## Template B — Execute GT-120 selection (analysis only; no administration)

```text
We are working on CH-####.

Your task is to execute `GT-120: Change Increment Selection (Selection Gate)` for the CI candidates for CH-####.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- ch_id: CH-####
- db_id: DB-####
- td_ids: [TD-####, ...]

Scope:
- In scope: read all CI candidates for CH-####, compare only structurally complete `Candidate` CIs against the locked `CH + DB + TD` envelope, and produce a GT-120 selection report (EV).
- Out of scope: status changes, registry updates, GT-130, and implementation work.

Authorization:
- You are authorized to complete the selection analysis and produce the EV selection report.
- You are NOT authorized to perform administration steps.

Stop condition:
- Stop after producing the EV selection report and clearly stating the selected CI id and rationale.

Deliverables:
- New `EV-####.md` (GT-120 selection report; allocate id with `python tools/allocate_lantern_id.py` and use `lantern/templates/EV_TEMPLATE__GT120_SELECTION_REPORT.md`)
```

## Template C — Execute GT-120 selection + administration (full gate completion)

```text
We are working on CH-####.

Your task is to execute `GT-120: Change Increment Selection (Selection Gate)` for the CI candidates for CH-#### and complete administration using `lantern/administration_procedures/GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md`.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- ch_id: CH-####
- db_id: DB-####
- td_ids: [TD-####, ...]

Scope:
- In scope: selection analysis, EV selection report, DEC selection decision, CI status updates, CH updates, and `Lantern/change/INDEX.md` updates.
- Out of scope: GT-130 verification and any implementation work.

Authorization:
- You are authorized to proceed with the entire GT-120 process, including administration steps, and then stop.

Stop condition:
- Stop after:
  - exactly one CI is marked `Selected`,
  - all non-selected candidates are marked `Rejected`,
  - EV and DEC are created,
  - CH is updated with references,
  - registry is updated.

Deliverables:
- New `EV-####.md` (GT-120 selection report; id allocated with `python tools/allocate_lantern_id.py`)
- New `DEC-####.md` (GT-120 decision; id allocated with `python tools/allocate_lantern_id.py`)
- Updated CI candidate files (statuses)
- Updated `CH-####.md` (references to selected CI + EV/DEC)
- Updated `Lantern/change/INDEX.md`
```

## Template D — Execute GT-030 (DIP lock)

```text
We are working on DIP-####.

Your task is to execute `GT-030: Design Input Pack Lock (DIP baseline lock)`.

Required fields:
- governance_root: <path-to-lantern-workflow-ssot-repo-root>
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
- Updated `Lantern/change/INDEX.md`
```

## Template E — Prepare SPEC/ARCH derivation packet for GT-050 and GT-060

```text
We are working on DIP-#### with derived SPEC-#### and ARCH-#### drafts.

Your task is to prepare the derivation packet that GT-050 and GT-060 will review.

Required fields:
- governance_root: <path-to-lantern-workflow-ssot-repo-root>
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

```text
We are working on DIP-####, SPEC-####, and ARCH-####.

Your task is to review the cross-artifact coherence that GT-050 and GT-060 will rely on.

Required fields:
- governance_root: <path-to-lantern-workflow-ssot-repo-root>
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

```text
We are working on ARCH-#### and SPEC-#### baselines.

Your task is to execute:
- `GT-050: Architecture Definition Readiness (ARCH baseline readiness)`
- `GT-060: Requirements Specification Readiness (SPEC baseline readiness)`

Required fields:
- governance_root: <path-to-lantern-workflow-ssot-repo-root>
- dip_id: DIP-####
- arch_id: ARCH-####
- spec_id: SPEC-####

Scope:
- In scope: completeness checks, derivation/coherence evidence review, acceptance criteria checks (SPEC), baseline locator or waiver handling, supersession handling, review summary capture, DEC outcomes.
- Out of scope: GT-110, GT-115, GT-120, GT-130, and implementation work.

Authorization:
- You are authorized to create EV/DEC records, update artifact statuses on PASS, and update registry entries.

Stop condition:
- Stop after both GT-050 and GT-060 have explicit PASS/FAIL DEC outcomes and administration is complete.

Deliverables:
- New `EV-####.md` + `DEC-####.md` for GT-050 (allocate ids with `python tools/allocate_lantern_id.py`)
- New `EV-####.md` + `DEC-####.md` for GT-060 (allocate ids with `python tools/allocate_lantern_id.py`)
- Updated ARCH/SPEC statuses (Draft -> Approved on PASS)
- Updated `Lantern/change/INDEX.md`
```

## Template H — Execute GT-130 (integration verification + administration)

```text
We are working on CH-####.

Your task is to execute `GT-130: Integration Verification` for CH-#### and complete administration using `lantern/administration_procedures/GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION_v0.1.0.md`.

Required fields:
- governance_root: <path-to-ssot-repo-root>
- product_repo_root: <path-to-product-repo-root>
- ch_id: CH-####
- ci_id: CI-<CH_NUM>-<UUID>
- db_id: DB-####
- td_ids: [TD-####, ...]
- product_repo_commit: <commit-hash-or-tag>

Scope:
- In scope: execute the CI verification plan against the product repo, collect evidence, create EV and DEC records, update CI and CH statuses on PASS, and update `Lantern/change/INDEX.md`.
- Out of scope: any new implementation, CI authoring, GT-115/GT-120 re-execution, or changes to product repo content.

Authorization:
- You are authorized to run the verification commands declared in the Selected CI's Verification Plan.
- You are authorized to proceed with the complete GT-130 administration, including CI and CH status transitions on PASS.

Stop condition:
- Stop after:
  - EV and DEC are created,
  - CI status is updated (Verified on PASS; or per-human disposition on FAIL),
  - CH status is updated to Addressed (on PASS only),
  - registry is updated.

Deliverables:
- New `EV-####.md` (GT-130 verification report; id allocated with `python tools/allocate_lantern_id.py`)
- New `DEC-####.md` (GT-130 decision; id allocated with `python tools/allocate_lantern_id.py`)
- Updated `CI-<CH_NUM>-<UUID>.md` (status: Verified on PASS)
- Updated `CH-####.md` (status: Addressed on PASS only)
- Updated `Lantern/change/INDEX.md`
```
