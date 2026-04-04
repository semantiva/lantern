```yaml
ch_id: "CH-####"
ci_id: "CI-<CH_NUM>-<UUID>"
status: "Draft|Candidate|Selected|Rejected|Verified"
title: "<concise title>"

design_baseline_ref: "DB-####"
test_definition_refs:
  - "TD-####"

ssot:
  code: "<repo-or-archive-pointer>@<commit-or-tag>"
  docs: ["<path>"]
  schemas: ["<path>"]
  tools: ["<path>"]
  glossary: "<path-or-empty>"

baseline:
  product_repo: "<repo-name>"
  branch_or_commit: "<main|branch|commit>"
  rationale: "<required when not mainline>"

allowed_change_surface:
  - "<path-or-module-glob>"

verification:
  required_evidence:
    - kind: "test|artifact|report|command"
      command: "<exact command when applicable>"
      path: "<exact path when applicable>"
      expected_signal: "<binary expected result>"

blocked_by: []  # required when status = Draft
```

# CI-<CH_NUM>-<UUID> — <short title>

## Intent

<Describe the implementation intent within the CH+DB+TD envelope.>

## Assessment Criteria Alignment (verbatim from CH)

<Verbatim from CH.>

## Constraints (verbatim from CH)

<Verbatim from CH.>

## Design Baseline Alignment

<Alignment with DB-####.>

## Test Definition Alignment

<Alignment with TD set.>

## Allowed Change Surface

- `<path-or-module-glob>`

## Drop-In Pack (REQUIRED)

| Path | Drop-in type | Drop-in anchor |
|---|---|---|
| `<path>` | PATCH | `DROP-IN: PATCH <path>` |

### DROP-IN: PATCH <path>

```
<patch content>
```

## Commit Message (REQUIRED)

```text
feat: <short summary>

CH: CH-####
CI: CI-<CH_NUM>-<UUID>

<optional rationale>
```

## Verification Plan

- Command: `<exact command>` → expected: exit code 0

## Definition of Done (binary)

- <Binary: all verification commands exit 0 and all required artifacts exist.>
