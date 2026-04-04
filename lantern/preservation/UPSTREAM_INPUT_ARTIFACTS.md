# Upstream input artifacts

This document is normative for the upstream artifact families that may feed Lantern workflow.

## Canonical upstream families

- `DIP` — intake baseline
- `SPEC` — requirements baseline
- `ARCH` — architecture baseline
- `TD` — test-definition baseline

## TD posture

A TD is required for GT-110 readiness.
A TD must improve on shallow command-only placeholders by defining:
- stable case identifiers,
- traced criterion or requirement anchor,
- preconditions,
- stimulus,
- observable/oracle,
- failure condition,
- evidence expectation.

A TD is not executable code and is not required to embed final runnable commands at GT-110.
Runnable verification commands belong in downstream implementation verification evidence.
