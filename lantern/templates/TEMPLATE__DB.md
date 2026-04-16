```yaml
db_id: "DB-####"
status: "Draft|Approved"
title: "<concise title>"
source_dc_id: "DC-<CH_NUM>-<UUID>"
applies_to_ch: "CH-####"
test_definition_refs:
  - "TD-####"
governed_scope:
  - "<module-or-surface>"
supersedes: []  # historical lineage only, or empty
superseded_by: ""  # historical lineage only, or empty
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
  - Commitment: <fixed design commitment>
    Source: <selected DC section or clause>
- Downstream latitude:
  - Latitude: <allowed implementation freedom>
    Source: <selected DC section or clause>
- Reopen GT-115 if:
  - Condition: <reopen trigger>
    Source: <selected DC section or clause>
