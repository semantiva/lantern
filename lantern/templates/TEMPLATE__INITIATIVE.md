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
- Initiative is bounded with a coherent decomposition posture.
- At least one decomposed or referenced CH is Ready. GT-110 readiness carries the upstream DIP/SPEC/ARCH sufficiency check for that CH.
- Upstream DIP/SPEC/ARCH baselines are referenced where applicable; the Initiative does not own them.

## Inputs / evidence
- <pointer 1>
- <pointer 2>

## Notes
- Initiative status changes are not gate-defined by a separate Initiative gate family.
- CH/CI execution still occurs through standard Lantern workflow gates.
