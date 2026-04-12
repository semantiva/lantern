```yaml
dec_id: "DEC-####"
applies_to_ch: "CH-####"
date_utc: "YYYY-MM-DD"
decision_type: "gate"
status: "Active"
references:
  ci: "CI-<CH_NUM>-<UUID>"
  evidence: ["EV-####"]

# Optional for a bounded GT-130 extension
gt130_extension:
  evidence_ref: "EV-####"
  approved_paths:
    - "path/to/file"
```

# GT-130 Decision

Gate: GT-130
Decision: PASS | FAIL
Verified CI: `CI-<CH_NUM>-<UUID>`


## Expectation-to-delivery rationale
Summarize initiative objective, roadmap role, requirements satisfaction, architectural fit, and clean-state / reproducibility posture before declaring PASS.
