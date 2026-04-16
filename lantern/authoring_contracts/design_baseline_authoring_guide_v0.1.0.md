# Design Baseline authoring guide — v0.1.0


Status: AUTHORITATIVE — Normative
Date (UTC): 2026-03-15

Applies to:
- Lantern workflow SSOT container repositories in a multi-repository workspace
- AI-assisted execution following GT-115 selection of a Design Candidate

Normative anchors:
- `lantern/preservation/EPISTEMIC_FRAME.md`
- `lantern/preservation/GATES.md`
- `lantern/preservation/WORKSPACE_TOPOLOGY.md`
- `lantern/preservation/LANTERN_MODEL_BINDING.md`
- `lantern/preservation/ARTIFACT_ID_ALLOCATION.md`
- `lantern/authoring_contracts/design_candidate_authoring_guide_v0.1.0.md`

---

## 1. Definitions (normative)

### 1.1 Change Intent (CH)
A CH is the stable problem definition and assessment anchor for downstream work.

CH id format (required): `CH-####`

### 1.2 Design Candidate (DC)
A DC is a candidate design compared at GT-115.
A DC becomes the source of an Approved DB when it is selected.

DC id format (required): `DC-<CH_NUM>-<UUID>`

### 1.3 Design Baseline (DB)
A DB is the authoritative selected design artifact approved at GT-115.
It is extracted from the Selected DC and formalized as a locked, governing baseline for downstream CI authoring.

A DB is not a fresh design document. It makes the selected design commitments explicit, separates what is fixed from what is open to implementation, and governs its declared scope until it is superseded or the CH is Addressed.

DB id format (required): `DB-####`
DB statuses (required): `Draft`, `Approved`, `Superseded`

Allocation rule (normative): DB ids MUST be generated using the Lantern allocator tool:
- `python tools/allocate_lantern_id.py --artifact DB --repo <path-to-ssot-root>`

### 1.4 Test Definition (TD)
A TD is the approved test-definition baseline.

TD id format (required): `TD-####`

---

## 2. DB lifecycle semantics (normative)

- `Approved` is the required status for a DB to unlock GT-120 and CI authoring.
- `Draft` is exceptional and is allowed only when the DB cannot yet be completed from the Selected DC (e.g., the Selected DC contains ambiguities that block fixed-vs-latitude extraction).
- `Superseded` applies when a DB has been replaced by a newer Approved DB following a new GT-115 run.

Authoring workflow (normative):
1. GT-115 must have produced exactly one Selected DC before DB authoring begins.
2. Extract the design commitments from the Selected DC into the DB record.
3. Explicitly separate fixed design commitments from downstream implementation latitude.
4. State reopen GT-115 conditions clearly.
5. Set `status: "Approved"` when all required fields are complete and the DB accurately represents the Selected DC.
6. If completion is blocked (e.g., the Selected DC is ambiguous on a required commitment), set `status: "Draft"` and include `## Blocking Items` referencing the specific DC section that needs clarification.
7. Ensure the DB is listed in `INDEX.md` at the governance repo root.

Eligibility rules:
- A DB MUST be `Approved` before GT-120 and CI authoring may begin.
- A DB MUST NOT be authored before a DC has been formally selected at GT-115.
- A DB in `Draft` status blocks GT-120 until it is promoted to `Approved`.

---

## 3. Non-negotiable boundaries

### 3.1 DB is extracted from the Selected DC, not authored independently
A DB is a formalization and consolidation of the commitments made in the Selected DC.

Hard rule:
- If the DB introduces design decisions not present in the Selected DC, it MUST block and the Selected DC must be updated (triggering a GT-115 re-check) rather than silently expanding DB scope.
- If the DB omits non-trivial design decisions from the Selected DC, it is incomplete.

### 3.2 Fixed-vs-latitude extraction discipline
Every DB MUST explicitly separate:
- **Fixed design commitments** — what the approved design mandates; CI authoring MUST NOT deviate from these.
- **Downstream implementation latitude** — what CI candidates may vary without reopening GT-115.
- **Reopen GT-115 conditions** — changes that would require a new GT-115 run.

Hard rule:
- If this separation is missing or ambiguous, the DB is incomplete even if the design narrative is otherwise strong.
- "Ambiguous latitude" — where it is unclear whether a choice is fixed or free — MUST be resolved in the DB, not deferred to CI authoring.

### 3.3 Supersession protocol
A DB governs its declared governed scope until it is Superseded or the CH is Addressed.

Hard rule:
- A DB MUST NOT be superseded by direct edit. Supersession requires a new GT-115 run that produces a new Approved DB.
- The new DB MUST list the superseded DB id(s) in `supersedes`.
- The superseded DB MUST have its `status` updated to `Superseded` and `superseded_by` updated to the new DB id as part of GT-115 administration.

### 3.4 Governed scope boundary
Every DB MUST declare a `governed_scope` that matches or is bounded by the Selected DC's `governed_scope`.

Hard rule:
- The DB `governed_scope` MUST NOT exceed the Selected DC's `governed_scope`.
- If the CH addresses multiple scopes, they MUST be governed by a single DB unless an explicit partial-scope waiver is recorded in the GT-115 DEC.

### 3.5 Boundary between DB and CI
A DB defines authoritative design truth for a governed scope. A CI implements that design.

Hard rule:
- A DB MUST NOT contain implementation instructions, patch payloads, commit messages, or drop-in packs.
- A DB MUST NOT prescribe test function names, file names, or code-level patterns.
- A DB that reads like a CI is invalid.

---

## 4. SSOT storage locations and registry (normative)

Canonical locations:
- `db/DB-####.md`
- `INDEX.md` (governance repo root)

Registry rules:
- Every DB MUST appear exactly once under `## Design Baselines` in `INDEX.md` at the governance repo root.
- The DB header status and registry status MUST match.
- When a DB is superseded, both the old DB (updated to `Superseded`) and the new DB (`Approved`) MUST be reflected in the registry.

---

## 5. Required DB header (normative)

File: `db/DB-####.md`

Every DB MUST include a machine-readable header block with at least:

```yaml
db_id: "DB-####"
status: "Draft|Approved|Superseded"
title: "<concise title>"
applies_to_ch: "CH-####"
source_dc_id: "DC-<CH_NUM>-<UUID>"
test_definition_refs:
  - "TD-####"
governed_scope:
  - "<module-or-surface>"
supersedes: []  # list of superseded DB ids, or empty
superseded_by: ""  # id of the superseding DB, or empty
```

Header rules:
- `applies_to_ch` MUST reference exactly one CH id.
- `source_dc_id` MUST reference the exact Selected DC id that is the source of this DB.
- `test_definition_refs` MUST be non-empty and match the Approved TD set used at GT-115.
- `governed_scope` MUST be explicit and non-empty.
- `supersedes` MUST be an explicit list (may be empty; MUST be non-empty if this DB replaces a prior DB for the same scope).
- `superseded_by` MUST be empty until this DB is itself superseded.
- `status: "Approved"` MUST NOT be set while any required field is a placeholder or while `## Blocking Items` is non-empty.

---

## 6. Required DB body sections (normative)

Every DB MUST contain these top-level sections:

1. `# DB-#### — <short title>`
2. `## Selected Design`
3. `## Selection Rationale`
4. `## Governed Scope`
5. `## Supersession Posture`
6. `## Implementation Latitude`

Required only when blocked:
- `## Blocking Items`

Recommended additional sections:
- `## Key Technical Commitments`
- `## Interface / Public Surface Freeze`
- `## Risks and Deferred Design Questions`

---

## 7. DB authoring contract (design-baseline-grade)

### 7.1 Extraction posture (do not invent)
The DB content MUST be extractable from the Selected DC.

Rules:
- `## Selected Design` MUST reflect the design as described in the Selected DC, not a paraphrase or simplification that loses design precision.
- `## Selection Rationale` MUST reference the GT-115 decision (EV and DEC ids) and state why this DC was selected over the alternatives.
- `## Governed Scope` MUST match the `governed_scope` declared in the Selected DC.
- If the DB author cannot trace a design commitment to the Selected DC, it MUST block rather than invent.
- Every fixed commitment, downstream latitude item, and reopen condition MUST include an explicit `Source:` traceback to the selected DC clause or section that authorizes it.
- Missing traceback is non-admissible extraction: if the author cannot point to the selected DC source, the item MUST NOT appear as DB truth.

### 7.2 Fixed commitments vs downstream latitude
The `## Implementation Latitude` section MUST contain all three sub-lists:

1. **Fixed commitments** — a list of specific design decisions that CI candidates MUST implement exactly as stated.
   - Examples: "The public API must expose `canonicalize(record: dict) -> str`; signature is frozen.", "The processing pipeline must be deterministic."
   - Every fixed commitment MUST include `Source: <selected DC section or clause>`.

2. **Downstream latitude** — a list of implementation choices that CI candidates may make freely.
   - Examples: "CI candidates may choose any internal data structure for intermediate computation.", "Logging level and format are at CI author discretion."
   - Every downstream latitude item MUST include `Source: <selected DC section or clause>`.

3. **Reopen GT-115 conditions** — a list of changes that would require a new GT-115 run.
   - Examples: "Changing the public API signature would require reopening GT-115.", "Adding governed scope beyond what this DB declares requires a new GT-115 run."
   - Every reopen condition MUST include `Source: <selected DC section or clause>`.

Hard rule:
- All three sub-lists MUST be present and non-empty. If a sub-list is genuinely empty (e.g., no latitude exists), this MUST be stated explicitly with a brief rationale, not simply omitted.
- A DB line item without `Source:` traceback is non-admissible extraction and MUST block approval until the selected DC authorization is explicit.

### 7.3 Supersession authoring rules
When authoring a DB that supersedes a prior DB:
1. Include the superseded DB id(s) in the header `supersedes` list.
2. In `## Supersession Posture`, explicitly state:
   - which prior DB is superseded and why,
   - whether the supersession is total (full replacement) or partial (scoped replacement),
   - if partial: what scope remains governed by the prior DB.
3. The prior DB's `superseded_by` field and `status` MUST be updated as part of GT-115 administration (do not leave the prior DB in `Approved` state).

### 7.4 DB is design truth, not implementation instructions
The DB communicates what design is authoritative, not how to code it.

Hard rules:
- The DB MUST NOT prescribe file layout, test function names, or implementation step sequences.
- The DB SHOULD NOT reference specific product repo commit hashes as design anchors (design truth is not tied to a specific commit).
- When the DB mentions product repo artifacts, it MUST reference them by stable interface name (e.g., class name, API method, schema field) not by internal file path or line number.

---

## 8. Supersession protocol (normative)

A DB may be superseded only via a new GT-115 gate run. Informal edits to an Approved DB are prohibited.

Steps required for valid supersession:
1. Author new DC candidates for the same or revised CH scope.
2. Run GT-115 selection using the DC selection guide to select a new DC.
3. Author the new DB, setting `supersedes: ["DB-####"]` for each prior DB that is being replaced.
4. During GT-115 administration, update the old DB header: set `status: "Superseded"` and `superseded_by: "DB-####"` (the new DB id).
5. Update `INDEX.md` at the governance repo root to reflect the new DB and the updated status of the superseded DB.
6. Record the supersession rationale in the GT-115 DEC.

Hard rule:
- Setting `status: "Superseded"` on a DB without a corresponding new Approved DB is invalid.
- The CH `status` MUST NOT change during supersession (it remains `Ready` until GT-130 passes).
- Any CIs that referenced the superseded DB are automatically invalidated; they MUST be re-evaluated against the new DB before GT-120 proceeds.

---

## 9. Gate-driven lifecycle implications

### GT-115
- The DB is authored as the final step of GT-115 administration, immediately after the DEC is recorded.
- The DB MUST accurately represent the Selected DC; it MUST NOT expand, contract, or reinterpret the selected design.
- After the DB is `Approved`, the Selected DC becomes historical; the DB is the only design-truth artifact that CI authoring may consume.

### GT-120
- A DB in `Approved` status is required before GT-120 and CI authoring may begin.
- CI candidates MUST reference the Approved DB id in their `design_baseline_ref` header field.
- CI candidates MUST NOT contradict fixed commitments declared in the Approved DB.
- If CI authoring reveals the DB is incorrect or incomplete, GT-115 MUST be reopened; CI authoring MUST NOT silently patch DB truth.

### GT-130
- The selected CI is verified against the approved `CH + DB + TD` envelope.
- The DB fixed commitments are the reference for what the integrated implementation must preserve.
- If verification reveals a DB gap, GT-115 MUST be reopened rather than working around the gap in the verification record.

---

## 10. Common failure modes (avoid)

- DB introduces design commitments not present in the Selected DC.
- DB is a paraphrase of the Selected DC that loses precision in the fixed commitments.
- `## Implementation Latitude` mixes fixed commitments with downstream latitude (ambiguous posture for CI authoring).
- Reopen GT-115 conditions are omitted, leading to unexpected reopening pressure during CI evaluation.
- `## Supersession Posture` is left as `none` when a prior DB governs the same scope.
- DB is authored before a DC is formally selected at GT-115 (pre-emptive DB).
- DB references specific product repo commit hashes or file paths instead of stable interface names.
- DB is treated as a living document and edited post-approval (any substantive change requires GT-115 reopen).
- `governed_scope` in DB exceeds the `governed_scope` declared in the Selected DC.
- `test_definition_refs` in DB diverges from the TD set used at GT-115.
- Prior superseded DBs left in `Approved` status alongside the new DB.
- CI candidates invalidated by a supersession event are not identified and re-evaluated.
