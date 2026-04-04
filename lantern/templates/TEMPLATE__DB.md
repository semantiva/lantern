```yaml
db_id: "DB-####"
status: "Draft|Approved|Superseded"
title: "<concise title>"
source_dc_id: "DC-<CH_NUM>-<UUID>"
applies_to_ch: "CH-####"
test_definition_refs:
  - "TD-####"
governed_scope:
  - "<module-or-surface>"
supersedes: []  # list of superseded DB ids, or empty
superseded_by: ""  # id of the superseding DB, or empty
```

# DB-#### — <short title>

## Selected Design
Describe the selected design that is authoritative for the governed scope.

## Selection Rationale
- Summarize why this DC was selected at GT-115.

## Governed Scope
- <module-or-surface>

## Supersession Posture
- <none|supersedes DB-####|partial supersession explanation>

## Implementation Latitude
- Fixed commitments:
- Downstream latitude:
- Reopen GT-115 if:
