```yaml
td_id: "TD-####"
status: "Draft|Approved"
title: "<concise title>"
applies_to_ch: "CH-####"
origin:
  baseline: "<source description or upstream artifact pointer>"
  rationale: "<why this TD exists>"
governed_scope:
  - "<module-or-surface>"
supersedes: []  # historical lineage only, or empty
superseded_by: ""  # historical lineage only, or empty
```

# TD-#### — <short title>

## Purpose
Describe what must be tested and why.

## Coverage Matrix
- case_id: TD-####-C01
  criterion: "<traced CH criterion>"
  preconditions: "<state or fixture assumption>"
  stimulus: "<operation or event>"
  observable: "<what is observed>"
  oracle: "<expected outcome>"
  failure_condition: "<what constitutes failure>"

## Evidence Expectations
- test level: "<unit|integration|system|other>"
- evidence mode: "<report|trace|command_output|review_note>"
