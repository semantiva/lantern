```yaml
# EV_HEADER (REQUIRED)
ev_id: "EV-####"
applies_to_ch: "CH-####"
date_utc: "YYYY-MM-DD"
evidence_type: "selection_report"
references:
  dcs: ["DC-<CH_NUM>-<UUID>", "DC-<CH_NUM>-<UUID>"]
artifacts:
  - kind: "path"
    path: "ch/CH-####.md"
  - kind: "path"
    path: "dc/DC-<CH_NUM>-<UUID>.md"
  - kind: "path"
    path: "dc/DC-<CH_NUM>-<UUID>.md"
  - kind: "path"
    path: "Lantern/design_candidate_selection_guide_v0.1.0.md"
  - kind: "path"
    path: "<SPEC-####.md path>"
  - kind: "path"
    path: "<ARCH-####.md path>"
  - kind: "path"
    path: "td/TD-####.md"
```

> Path semantics: every `Lantern/...` path in this document is a logical governed-workspace path resolved relative to the governed product SSOT repository. It is not a writable local path inside the Lantern workflow product repository.

## Selection report (verbatim)

<!--
Paste the assistant-produced selection report here (unaltered).

For 8+ candidate pools, the selection guide defines a compact report surface:
  - one comparison table across all eligible candidates
  - fixed-size candidate capsules (bounded length)
See: `Lantern/design_candidate_selection_guide_v0.1.0.md`
-->

<paste the assistant-produced selection report here>

## Human approval

Approved selection: DC-<CH_NUM>-<UUID> | NONE  
Approver: <name/team>  
Approved at (UTC): YYYY-MM-DDTHH:MM:SSZ
