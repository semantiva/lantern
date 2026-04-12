# Allowed Change Surface Flexibilization


Status: AUTHORITATIVE — Normative
Date (UTC): 2026-04-12

Purpose:
- keep `allowed_change_surface` strict while admitting two bounded cases that otherwise create avoidable implementation distortion or blocked integration closeout.

## 1. CI authoring posture

- `allowed_change_surface` remains the implementation boundary for a CI.
- CI authoring may include a module `__init__.py` only when that file exposes or preserves the package surface for module files already inside the CI scope.
- The CI MUST record that rationale explicitly for each such `__init__.py` path.
- If the package-surface edit is foreseeable during CI authoring, it MUST be carried by the CI rather than deferred to GT-130.

## 2. GT-130 bounded extension posture

- GT-130 may register a bounded extension only when integration is blocked by a late-discovered workflow-integration consistency gap.
- The extension MUST be minimal, enumerated path-by-path, and recorded in the GT-130 EV and DEC records.
- The Selected CI, TD, and DB remain locked during GT-130. The extension is recorded as gate evidence and decision authority; it is not written back into the Selected CI.
- This mechanism MUST NOT modify specifications, tests, design baselines, or architectural baselines.