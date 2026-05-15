# Lantern model binding for Lantern workflow

This document maps workflow terms and gates to Lantern model semantic identifiers.

## Artifact family bindings

| Workflow term | Lantern model id |
|---|---|
| Change Intent (CH) | `lg:artifacts/ch` |
| Change Increment (CI) | `lg:artifacts/ci` |
| Test Definition (TD) | `lg:artifacts/td` |
| Design Candidate (DC) | `lg:artifacts/dc` |
| Design Baseline (DB) | `lg:artifacts/db` |
| Architecture Definition (ARCH) | `lg:artifacts/arch` |
| Requirements Specification (SPEC) | `lg:artifacts/spec` |
| Design Input Pack (DIP) | `lg:artifacts/dip` |
| Initiative | `lg:artifacts/initiative` |
| Evidence | `lg:records/ev` |
| Decision | `lg:records/dec` |

## Gate bindings

| Workflow gate | Lantern model id |
|---|---|
| GT-030 | `lg:gates/gt_030` |
| GT-050 | `lg:gates/gt_050` |
| GT-060 | `lg:gates/gt_060` |
| GT-110 | `lg:gates/gt_110` |
| GT-115 | `lg:gates/gt_115` |
| GT-120 | `lg:gates/gt_120` |
| GT-130 | `lg:gates/gt_130` |

## Status bindings used by the workflow

- `Draft` (DIP/SPEC/ARCH/TD/DB) -> `lg:statuses/draft`
- `Approved` -> `lg:statuses/approved`
- `Superseded` -> `lg:statuses/superseded`
- `Proposed` (CH) -> `lg:statuses/proposed`
- `Ready` (CH) -> `lg:statuses/ready`
- `Addressed` (CH) -> `lg:statuses/addressed`
- `Candidate` -> `lg:statuses/candidate`
- `Selected` -> `lg:statuses/selected`
- `Rejected` -> `lg:statuses/rejected`
- `Verified` -> `lg:statuses/verified`
- `Draft` (Initiative) -> `lg:statuses/draft`
- `Proposed` (Initiative) -> `lg:statuses/proposed`
- `Ready` (Initiative) -> `lg:statuses/ready`
- `In Progress` (Initiative/CH) -> `lg:statuses/in_progress`
- `Concluded` (Initiative) -> `lg:statuses/concluded`

## Binding rule

If workflow guidance conflicts with these mapped Lantern model identifiers or their semantic surface, Lantern model is authoritative for semantics and workflow guidance must be amended.
