```yaml
# EV_HEADER (REQUIRED)
ev_id: "EV-####"
applies_to_ch: "CH-####"
date_utc: "2026-01-23"
evidence_type: "selection_report"
references:
  cis: ["CI-####-<UUID>", "CI-####-<UUID>"]
artifacts:
  - kind: "path"
    path: "ch/CH-####.md"
  - kind: "path"
    path: "ci/CI-####-<UUID>.md"
  - kind: "path"
    path: "ci/CI-####-<UUID>.md"
  - kind: "path"
    path: "lantern/authoring_contracts/change_increment_selection_guide_v0.2.1.md"
```

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

The report must also include a bounded handoff section labeled `GT-120 → GT-130`.
-->

## Eligibility Summary

<paste>

## Baseline Checklist

<paste>

## Structured Findings Ledger

| finding_id | candidate_id | claim | evidence | governing_rule_or_artifact | classification | severity | confidence | required_remediation_before_promotion | outcome_effect | final_disposition_rationale |
|---|---|---|---|---|---|---|---|---|---|---|
| F-001 | CI-####-<UUID> | <claim> | <evidence> | <rule> | <blocking/non-blocking> | <severity> | <confidence> | <remediation or N/A> | <excluded from ranking/comparative only/handoff-only> | <disposition> |

## Recommendation

<paste>

## GT-120 → GT-130

- Integration must preserve: <scope lock or contract>
- GT-130 must verify: <test or artifact expectation>

## Human approval

Approved selection: CI-####-<UUID> | NONE  
Approver: <name/team>  
Approved at (UTC): 2026-01-22T00:00:00Z
