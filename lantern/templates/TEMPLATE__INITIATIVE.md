```yaml
initiative_id: "INI-####"
status: "Draft|Proposed|Ready|In Progress|Concluded"
title: "<short, specific title>"
owner: "<name/role or TBD>"
created: "YYYY-MM-DD"
last_updated: "YYYY-MM-DD"

inputs:
	dips: []
	specs: []
	arch: []
	issues: []
	questions: []

candidate_ch_refs: []
```

# INI-#### — <short, specific title>

## Objective
<Describe the intended strategic or program-level outcome.>

## Scope

In scope:
- <fill>

Out of scope:
- <fill>

## Decomposition notes
<Explain how this Initiative is expected to decompose into bounded CH slices.>

## Candidate Change Intents
- CH-#### — <short title or TBD>
- CH-#### — <short title or TBD>

## Sizing rationale
<Explain why the proposed CH slices are bounded, independently refinable, and suitable for GT-110. Explicitly address the compromise between gate-overhead from overly small CHs and LLM/session risk from overly large CHs.>

## Readiness conditions
- Initiative-owned DIP is Approved (GT-030 PASS)
- Initiative-owned SPEC is Approved (GT-060 with derivation/coherence evidence satisfied)
- Initiative-owned ARCH is Approved (GT-050 with derivation/coherence evidence satisfied)
- At least one bounded CH slice is identified and can proceed to GT-110 refinement

## Inputs / evidence
- <pointer 1>
- <pointer 2>

## Notes
- Initiative status changes are not gate-defined by a separate Initiative gate family.
- CH/CI execution still occurs through standard Lantern workflow gates.
