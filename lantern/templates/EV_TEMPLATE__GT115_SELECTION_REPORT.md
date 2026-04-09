```yaml
# EV_HEADER (REQUIRED)
ev_id: "EV-####"
applies_to_initiative: "INI-####"
applies_to_ch: "CH-####"
gate_id: "GT-115"
date_utc: "YYYY-MM-DD"
evidence_type: "selection_report"
title: "GT-115 selection report for CH-####"
references:
  ch: ["CH-####"]
  td: ["TD-####"]
  spec: ["SPEC-####"]
  arch: ["ARCH-####"]
  dcs: ["DC-<CH_NUM>-<UUID>", "DC-<CH_NUM>-<UUID>"]
  issues: ["IS-####"]
  artifacts: ["DB-####", "DEC-####"]
artifacts:
  - kind: "path"
    path: "ch/CH-####.md"
  - kind: "path"
    path: "dc/DC-<CH_NUM>-<UUID>.md"
  - kind: "path"
    path: "dc/DC-<CH_NUM>-<UUID>.md"
  - kind: "path"
    path: "lantern/authoring_contracts/design_candidate_selection_guide_v0.1.0.md"
  - kind: "path"
    path: "spec/SPEC-####.md"
  - kind: "path"
    path: "arch/ARCH-####.md"
  - kind: "path"
    path: "td/TD-####.md"
```

> Path semantics: governed-artifact paths in this template are relative to the governance repo root.

## Selection report (verbatim)

<!--
Paste the assistant-produced selection report here (unaltered).

For 8+ candidate pools, the selection guide defines a compact report surface:
  - one comparison table across all eligible candidates
  - fixed-size candidate capsules (bounded length)
See: `lantern/authoring_contracts/design_candidate_selection_guide_v0.1.0.md`
-->

<paste the assistant-produced selection report here>

## Human approval

Approved selection: DC-<CH_NUM>-<UUID> | NONE  
Approver: <name/team>  
Approved at (UTC): YYYY-MM-DDTHH:MM:SSZ
