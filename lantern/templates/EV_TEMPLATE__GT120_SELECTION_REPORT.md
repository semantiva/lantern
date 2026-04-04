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
    path: "Lantern/change_increment_selection_guide_v0.2.1.md"
```

> Path semantics: every `Lantern/...` path in this document is a logical governed-workspace path resolved relative to the governed product SSOT repository. It is not a writable local path inside the Lantern workflow product repository.

## Selection report (verbatim)

<!--
Paste the assistant-produced selection report here (unaltered).

For 8+ candidate pools, the selection guide defines a compact report surface:
  - one comparison table across all eligible candidates
  - fixed-size candidate capsules (bounded length)
See: `Lantern/change_increment_selection_guide_v0.2.1.md`
-->

<paste the assistant-produced selection report here>

## Human approval

Approved selection: CI-####-<UUID> | NONE  
Approver: <name/team>  
Approved at (UTC): 2026-01-22T00:00:00Z
