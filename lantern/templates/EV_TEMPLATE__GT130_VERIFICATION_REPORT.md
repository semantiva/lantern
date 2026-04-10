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
