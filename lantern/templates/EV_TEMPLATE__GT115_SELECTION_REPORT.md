```yaml
# EV_HEADER (REQUIRED)
ev_id: "EV-####"
applies_to_initiative: "INI-####"
applies_to_ch: "CH-####"
gate_id: "GT-115"
date_utc: "YYYY-MM-DD"
evidence_type: "selection_report"
title: "GT-115 selection report for CH-####"
references:
  ch: ["CH-####"]
  td: ["TD-####"]
  spec: ["SPEC-####"]
  arch: ["ARCH-####"]
  dcs: ["DC-<CH_NUM>-<UUID>", "DC-<CH_NUM>-<UUID>"]
  issues: ["IS-####"]
  artifacts: ["DB-####", "DEC-####"]
artifacts:
  - kind: "path"
    path: "ch/CH-####.md"
  - kind: "path"
    path: "dc/DC-<CH_NUM>-<UUID>.md"
  - kind: "path"
    path: "dc/DC-<CH_NUM>-<UUID>.md"
  - kind: "path"
    path: "lantern/authoring_contracts/design_candidate_selection_guide_v0.1.0.md"
  - kind: "path"
    path: "spec/SPEC-####.md"
  - kind: "path"
    path: "arch/ARCH-####.md"
  - kind: "path"
    path: "td/TD-####.md"
```

> Path semantics: governed-artifact paths in this template are relative to the governance repo root.

## Selection report (verbatim)

<!--
Paste the assistant-produced selection report here as one structured single-review findings report.

Required findings ledger fields for every material finding:
- `finding_id`
- `candidate_id`
- `claim`
- `evidence`
- `governing_rule_or_artifact`
- `classification`
- `severity`
- `confidence`
- `required_remediation_before_promotion`
- `outcome_effect`
- `final_disposition_rationale`

The report must also include a bounded handoff section labeled `GT-115 → DB/GT-120`.
-->

## Eligibility Summary

<paste>

## Baseline Checklist

<paste>

## Structured Findings Ledger

| finding_id | candidate_id | claim | evidence | governing_rule_or_artifact | classification | severity | confidence | required_remediation_before_promotion | outcome_effect | final_disposition_rationale |
|---|---|---|---|---|---|---|---|---|---|---|
| F-001 | DC-<CH_NUM>-<UUID> | <claim> | <evidence> | <rule> | <blocking/non-blocking> | <severity> | <confidence> | <remediation or N/A> | <excluded from ranking/comparative only/handoff-only> | <disposition> |

## Recommendation

<paste>

## GT-115 → DB/GT-120

- DB extraction must preserve: <fixed design commitment or scope lock>
- GT-120 must preserve: <downstream continuity note>

## Human approval

Approved selection: DC-<CH_NUM>-<UUID> | NONE  
Approver: <name/team>  
Approved at (UTC): YYYY-MM-DDTHH:MM:SSZ
