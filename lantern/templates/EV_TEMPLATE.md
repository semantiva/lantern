```yaml
# EV_HEADER (REQUIRED)
ev_id: "EV-####"
applies_to_ch: "CH-####"
date_utc: "2026-01-21"
evidence_type: "report"
references:
  cis: []
artifacts:
  - kind: "path"
    path: "inputs/arch/ARCH-####.md"
  - kind: "path"
    path: "inputs/specs/SPEC-####.md"
  - kind: "path"
    path: "inputs/dips/DIP-####.md"
  - kind: "path"
    path: "<product-repo-relative-artifact-path>"
  - kind: "command"
    command: "<verification-command>"
    expected_signal: "<expected-signal>"
```

## Evidence coverage summary

- E1 (required inputs verified for gate): <fill>
- E2 (baseline locator(s) and immutable identifiers recorded): <fill>
- E3 (decision-relevant checks and outcomes captured): <fill>
- E4 (verification signals and/or waiver rationale recorded): <fill>
