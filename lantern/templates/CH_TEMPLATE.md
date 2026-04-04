```yaml
ch_id: "CH-####"
status: "Proposed"
title: "<concise title>"
origin: "<stable source description>"

inputs:
  dips: []
  specs: []
  arch: []
  issues: []
  questions: []

gates:
  entry: "GT-110"
  design: "GT-115"
  selection: "GT-120"
  exit: "GT-130"

assessment_criteria:
  - "<criterion>"

validation_target:
  - "TD-backed behavioral success statement"

constraints:
  must_not_change: []
  out_of_scope: []

depends_on_ch: []
required_evidence_for_gt110: []
required_decisions: []
related_cis: []
test_definition_refs: []
design_candidate_refs: []
design_baseline_ref: ""
```

# CH-#### — <short title>

## 0. GT-110 Input Sufficiency Assessment

Decision: GO | NO-GO

Rationale:
- <state whether approved TD coverage exists>

## 1. Problem statement

<fill>

## 2. Scope

In scope:
- <fill>

Out of scope:
- <fill>

## 3. Inputs required to reach `Ready`

- Approved SPEC
- Approved ARCH
- Approved TD set

## 4. Gate expectations

GT-115 design selection posture:
- Design selection happens only after GT-110 has passed.

GT-120 implementation posture:
- CI comparison happens against locked DB + TD inputs.
