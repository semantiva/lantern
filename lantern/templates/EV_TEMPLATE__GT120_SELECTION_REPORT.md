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
Paste the assistant-produced selection report here (unaltered).

For 8+ candidate pools, the selection guide defines a compact report surface:
  - one comparison table across all eligible candidates
  - fixed-size candidate capsules (bounded length)
See: `lantern/authoring_contracts/change_increment_selection_guide_v0.2.1.md` (Lantern Runtime packaged resource)
-->

<paste the assistant-produced selection report here>

## Human approval

Approved selection: CI-####-<UUID> | NONE  
Approver: <name/team>  
Approved at (UTC): 2026-01-22T00:00:00Z
