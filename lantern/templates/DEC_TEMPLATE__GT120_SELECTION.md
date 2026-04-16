```yaml
# DEC_HEADER (REQUIRED)
dec_id: "DEC-####"
applies_to_ch: "CH-####"
date_utc: "2026-01-22"
decision_type: "gate"
status: "Active|Superseded"
supersedes: []
references:
  cis: ["CI-####-<UUID>", "CI-####-<UUID>"]
  evidence: ["EV-####"]
```

## Decision

Gate: GT-120  
Outcome: PASS | FAIL

Selected CI (if PASS): CI-####-<UUID>

Candidate pool (ordered):
- CI-####-<UUID>
- CI-####-<UUID>

Rationale (max 1 paragraph): <fill>

See EV-#### for the GT-120 selection report and structured findings ledger.
