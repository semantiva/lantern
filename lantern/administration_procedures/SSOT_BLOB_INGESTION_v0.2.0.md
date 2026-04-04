# SSOT blob ingestion workflow — SSOT bundle → DIP → SPEC/ARCH (privacy boundary hardened) — v0.2.0


## Scope

This guide defines a safe and repeatable procedure to intake unstructured SSOT material (“blob”) and convert it into Lantern upstream input artifacts:
- DIP (Design Input Pack)
- SPEC (Requirements Specification)
- ARCH (Architecture Definition)

This guide is designed to support AI assistants (local and remote) while preserving strict privacy boundaries.

### Where outputs live (normative)

All produced artifacts MUST live in the SSOT container repository:
- DIP: `dip/`
- SPEC: `spec/`
- ARCH: `arch/`

Product repositories MUST NOT be modified as part of blob ingestion.

### Related specs

- Record contract: `lantern/preservation/EPISTEMIC_FRAME.md`
- Gate expectations: `lantern/preservation/GATES.md`
- Upstream artifact structure: `lantern/preservation/UPSTREAM_INPUT_ARTIFACTS.md`
- Multi-repo posture: `lantern/preservation/WORKSPACE_TOPOLOGY.md`

---

Purpose
- Provide deterministic, operator-friendly steps for ingesting a real-world SSOT blob into a minimal set of formal artifacts:
  - Design Input Pack (DIP) Draft → lock via GT-030
   - Derive SPEC and ARCH drafts from the locked DIP and carry derivation/coherence evidence into GT-050 / GT-060
- Serve as the upstream-artifact companion to `guides/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md` when an Initiative is being created.
- Explicitly harden the privacy boundary so private SSOT sources can be used without leaking sensitive locators or proprietary narrative to public integration agents.

Authority
- Structural requirements and gate semantics are defined by:
  - `lantern/preservation/EPISTEMIC_FRAME.md`
  - `lantern/preservation/GATES.md`
- This document is operational guidance. It does not change normative semantics.

Terminology
- “SSOT blob”: a packaged set of authoritative inputs (documents, notes, diagrams, logs, etc.).
- “Private surface”: the workspace where the SSOT blob and sensitive source locators live.
- “Public projection”: a sanitized representation suitable for external/public integration agents.

## Inputs

Required
- SSOT blob (private surface; may include sensitive content and locators)
- A repo/workspace that will host the resulting DIP/SPEC/ARCH artifacts

Optional
- A need to use external/public integration agents (e.g., CODEX) on a sanitized projection

## Outputs

Minimum
- DIP Draft created from SSOT blob (template-based)
- GT-030 decision recorded (PASS/FAIL) and, on PASS, DIP status set to Approved
- SPEC Draft and ARCH Draft derived from locked DIP (template-based)
- GT-050 / GT-060 decisions recorded (PASS/FAIL), including the required derivation/coherence evidence and any explicit waivers permitted by the gates

Optional
- Public projection of DIP/SPEC/ARCH for external agent usage, with documented redaction rules

## Authoritative artifact rule

The DIP/SPEC/ARCH artifacts produced by this workflow MUST be self-contained authoritative artifacts.

Required posture:
- copy, translate, normalize, or summarize the relevant source semantics into the authored artifacts,
- preserve external sources as provenance where useful,
- do not rely on the original blob as a required semantic dependency after intake is complete.

When translation or language adaptation makes the authoritative artifact clearer, it is preferred over blind migration.

## Procedure

Use with Initiative planning:
- When intake is being performed for a new Initiative, start with `guides/INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md`.
- This guide governs how the Initiative-owned DIP/SPEC/ARCH artifacts are created and approved.

### Step 0 — Establish boundary and identifiers

1) Assign a stable SSOT blob identifier (example: `SSOT_BLOB_2026_02_02_A`).
2) Decide whether external/public integration agents will be used.
   - If yes, you MUST plan to create a public projection (see “Public projection procedure”).
3) Decide the repository location(s) where DIP/SPEC/ARCH will live.
   - Requirement: all locators referenced in Evidence/Decisions MUST be repo-relative when possible.

### Step 1 — Create DIP Draft (iterative; no formal DEC/EV during iteration)

1) Allocate a new DIP identifier using the authoritative allocator tool and create the DIP document using `lantern/templates/TEMPLATE__DIP.md`.
   - Command: `python tools/allocate_lantern_id.py --artifact DIP --repo <path-to-ssot-repo>`
2) Populate required DIP fields per `lantern/preservation/EPISTEMIC_FRAME.md`.
3) Build the Source inventory:
   - Prefer repo-relative paths (if the sources are committed or can be referenced safely).
   - For private/sensitive sources, use opaque tokens (e.g., `PRIVATE_SOURCE_001`) and keep the real locator in a private mapping file.
4) Iterate on DIP Draft until it captures:
   - The authoritative problem framing and constraints/non-goals.
   - A stable enough source inventory to support derivation.
   - A Questions referenced list that is either resolved or ready to be explicitly waived at lock.

Rule
- During this iteration loop, do NOT generate formal Decision (DEC) or Evidence (EV) records. Keep it lightweight.

### Step 2 — Determine “ready to lock” inputs for GT-030

Before running GT-030, ensure you can produce Evidence for each required class in `lantern/preservation/GATES.md` (GT-030).

Checklist (GT-030 readiness)
- DIP Draft has the minimum required structure.
- Source inventory is recorded.
- A baseline locator can be produced:
  - repo-relative path to the DIP document, plus an immutable reference (e.g., commit hash).
  - If you cannot provide an immutable reference, prepare a waiver rationale (gate-permitted).
- If this DIP replaces a prior Approved DIP, ensure the DIP declares `supersedes: DIP-####`.
- Any blocking Questions are Resolved, or you have a waiver rationale ready to record.

### Step 3 — Run GT-030 (DIP lock)

1) Record the baseline locator evidence:
   - Capture the DIP path and an immutable reference.
   - Example commands (adapt to your environment):
     - `git rev-parse HEAD` (commit hash)
     - `git log -1 --oneline` (human-readable commit reference)
2) Allocate EV/DEC ids using the authoritative allocator tool, then create a Decision record for GT-030 documenting PASS/FAIL and referencing Evidence pointers.
   - `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`
   - `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`
3) On PASS:
   - Update DIP status Draft → Approved.
   - Ensure the Decision explicitly records any waivers and (if applicable) the supersession statement.

Evidence pointers should be metadata-only
- Use repo-relative paths and immutable references.
- Do not embed sensitive blob contents in Evidence/Decision records.

### Step 4 — Derive SPEC Draft and ARCH Draft from the locked DIP

1) Allocate a SPEC id and create SPEC Draft using `lantern/templates/TEMPLATE__SPEC.md`.
   - Command: `python tools/allocate_lantern_id.py --artifact SPEC --repo <path-to-ssot-repo>`
   - Set “Derived from DIP” to the locked DIP id.
2) Allocate an ARCH id and create ARCH Draft using `lantern/templates/TEMPLATE__ARCH.md`.
   - Command: `python tools/allocate_lantern_id.py --artifact ARCH --repo <path-to-ssot-repo>`
   - Set “Derived from DIP” to the locked DIP id.
3) Ensure SPEC/ARCH scopes and constraints align with DIP constraints/non-goals.
4) Ensure Questions referenced remain consistent across DIP/SPEC/ARCH.

### Step 5 — Prepare derivation and coherence evidence for GT-050 / GT-060

Derivation evidence must show:
- SPEC and ARCH both derive from the locked DIP
- SPEC carries required structure, explicit acceptance criteria, and validation target signal definition (or an explicit waiver/deferment rationale)
- ARCH carries required structure and minimal architectural contract surfaces (key decisions, constraints/boundaries)

Coherence evidence must show:
1) A contradiction check across:
   - DIP constraints/non-goals vs SPEC scope
   - DIP constraints/non-goals vs ARCH boundaries
   - Consistency of referenced Questions
2) Any divergence is corrected, or explicitly waived with rationale before GT-050 / GT-060 run.

### Step 6 — Run GT-050 and GT-060 (baseline readiness)

When GT-050 / GT-060 produce new EV/DEC records, allocate ids using:
- `python tools/allocate_lantern_id.py --artifact EV --repo <path-to-ssot-repo>`
- `python tools/allocate_lantern_id.py --artifact DEC --repo <path-to-ssot-repo>`

## Privacy boundary posture

### What may be exposed to public integration agents

Allowed (typical)
- The public projection of DIP/SPEC/ARCH that preserves required fields but excludes sensitive content.
- Gate outcomes and high-level rationales that do not reveal sensitive source locators.
- Sanitized evidence pointers (repo-relative paths within the public projection, or opaque tokens).

Not allowed
- Absolute filesystem paths.
- Raw SSOT blob contents that include proprietary narrative, private identifiers, or sensitive operational details.
- Private source locator mappings (token → real path/URL/person/system).

### Public projection procedure (when external agents are used)

1) Create a copy of each artifact (DIP/SPEC/ARCH) as a projection.
2) Apply redaction rules:
   - Replace private source locators with opaque tokens.
   - Remove or generalize proprietary internal references not required for the normative contract.
   - Keep IDs, statuses, “Derived from DIP”, “supersedes”, scopes, constraints, and acceptance criteria intact.
3) Apply path sanitization rules:
   - Ensure no absolute paths remain.
   - Ensure no repo-internal private paths are included unless the repository is itself the public surface.
4) Produce a projection manifest that documents (at a rule level) what was redacted.
   - Do NOT include the private mapping.
5) Provide the projection to the external agent.
6) Re-integrate results into the private surface:
   - Re-run the relevant gates (GT-030/050/060) as needed.
   - Re-pin baseline locators for any updated artifacts.

## Non-goals

- This document does not introduce new object types, statuses, or new gate IDs.
- This document does not prescribe a single authoritative directory structure for DIP/SPEC/ARCH in all repositories.
- This document does not add or require automated tests/validators.