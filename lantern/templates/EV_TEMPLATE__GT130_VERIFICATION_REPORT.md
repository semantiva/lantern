```yaml
# EV_HEADER (REQUIRED)
ev_id: "EV-####"
applies_to_ch: "CH-####"
date_utc: "YYYY-MM-DD"
evidence_type: "verification_report"
references:
  ci: "CI-<CH_NUM>-<UUID>"
artifacts:
  - kind: "path"
    path: "ch/CH-####.md"
  - kind: "path"
    path: "ci/CI-<CH_NUM>-<UUID>.md"
  - kind: "path"
    path: "db/DB-####.md"
  - kind: "path"
    path: "td/TD-####.md"
  - kind: "commit"
    repo: "<product-repo-name>"
    ref: "<commit-hash-or-tag>"

# Optional for a bounded GT-130 extension
gt130_extension:
  allowed_paths:
    - "path/to/file"
  rationale: "why integration was blocked without these paths"
  discovered_during_gt130: true
  bounded_integration_gap: true
  no_spec_changes: true
  no_test_changes: true
  no_design_baseline_changes: true
  no_architectural_baseline_changes: true
```

## Verification run

<!--
Record the actual verification execution here.

Required content:
- exact commands run (as declared in the Selected CI's Verification Plan)
- actual output for each command
- PASS/FAIL per verification item
-->

<paste verification execution evidence here>

## Bounded integration-surface extension (optional)

List the extra paths admitted at GT-130, why the integration was blocked without them, and why the approved change truth remains unchanged.

## TD case coverage

| TD case id | Oracle | Actual result | PASS/FAIL |
|---|---|---|---|
| TD-####-C01 | \<oracle from TD\> | \<actual observed\> | PASS \| FAIL |

## Human approval

Outcome: PASS | FAIL
CI disposition (if FAIL): Selected | Candidate | Rejected
Approver: \<name/team\>
Approved at (UTC): YYYY-MM-DDTHH:MM:SSZ


## Expectation-to-delivery review

| Review anchor | Evidence | PASS/FAIL |
|---|---|---|
| Initiative objective | <why this CH exists in the roadmap> | PASS / FAIL |
| Roadmap role | <execution-order role for the CH> | PASS / FAIL |
| Requirements satisfaction | <SPEC / TD alignment evidence> | PASS / FAIL |
| Architectural fit | <ARCH alignment evidence> | PASS / FAIL |
| Clean-state and reproducibility | <clean-state + rerun evidence> | PASS / FAIL |
