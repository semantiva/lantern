# Initiative authoring and readying — v0.1.0


Status: AUTHORITATIVE — Guidance
Date (UTC): 2026-03-07

Purpose:
- Provide the canonical Lantern workflow entry point for creating an Initiative and making it operationally ready for execution planning.
- Define a deterministic path from Initiative `Draft` to Initiative `Ready` using self-contained upstream artifacts and the active upstream gate set.

Normative anchors (must not contradict):
- `lantern/preservation/EPISTEMIC_FRAME.md`
- `lantern/preservation/GATES.md`
- `lantern/preservation/ARTIFACT_ID_ALLOCATION.md`
- `lantern/preservation/LANTERN_MODEL_BINDING.md`
- `lantern/preservation/UPSTREAM_INPUT_ARTIFACTS.md`
- `guides/SSOT_BLOB_INGESTION_v0.2.0.md`
- `guides/INITIATIVE__DECOMPOSITION_AND_CH_SIZING_v0.1.0.md`
- `change_intention_refinement_guide_v0.2.1.md`

## Scope

In scope:
- allocate and author Initiative records,
- create Initiative-owned DIP/SPEC/ARCH artifacts,
- execute GT-030, then GT-050 and GT-060 with the required derivation/coherence evidence for Initiative-owned upstream baselines,
- declare an Initiative operationally `Ready` when upstream baselines are approved and at least one bounded CH slice can proceed to GT-110 refinement.

Out of scope:
- GT-110, GT-120, and GT-130 execution,
- implementation work in product repositories,
- redefining CH/CI lifecycle semantics,
- introducing new gate ids.

## Canonical storage and identifiers

- Initiative records MUST live in `ini/`.
- Initiative identifiers MUST use the form `INI-####`.
- Initiative identifiers MUST be allocated using:

`python tools/allocate_lantern_id.py --artifact INI --repo <path-to-ssot-repo>`

Hard rule:
- do not invent Initiative identifiers,
- do not use slug-only filenames in place of `INI-####.md` records.

## Initiative readiness posture

Lantern workflow does not define a separate Initiative gate family.

Operationally, an Initiative is `Ready` when ALL are true:
1. the Initiative record is complete and bounded,
2. the Initiative-owned DIP is locked (`GT-030` PASS),
3. the Initiative-owned SPEC and ARCH carry documented derivation and coherence evidence suitable for baseline approval review,
4. the Initiative-owned SPEC and ARCH are approved baselines (`GT-050`, `GT-060` PASS),
5. at least one bounded CH slice is identified with sufficient pinned inputs to begin GT-110 refinement.

Important:
- Initiative execution planning MAY begin as soon as one derived CH can be refined to `Ready`.
- You do NOT need the full future CH inventory before execution starts.

## Self-contained upstream artifact rule

Initiative-owned upstream artifacts MUST be self-contained authoritative records.

This means:
- relevant source material from a blob, legacy SSOT bundle, or planning archive MUST be copied, translated, normalized, or summarized into the DIP/SPEC/ARCH artifacts,
- external references MAY remain as provenance pointers,
- external references MUST NOT remain required semantic dependencies for understanding the authoritative baseline.

Preferred posture:
- translate and adapt source material when that produces clearer authoritative artifacts,
- avoid blind content migration when it preserves ambiguity or obsolete structure.

## Procedure

### Step 0 — Allocate and author Initiative in `Draft`

1. Allocate `INI-####`.
2. Create `ini/INI-####.md` from `lantern/templates/TEMPLATE__INITIATIVE.md`.
3. Record:
   - objective,
   - scope in/out,
   - source/evidence pointers,
   - decomposition notes,
   - initial candidate CH slices (these may be provisional).

### Step 1 — Create the Initiative-owned DIP

Follow `guides/SSOT_BLOB_INGESTION_v0.2.0.md`.

Minimum expectation:
- the DIP becomes the authority map for the Initiative,
- the DIP captures source inventory, constraints, non-goals, and planning intent,
- the DIP is understandable without requiring the operator to re-open the original blob for core semantics.

### Step 2 — Lock the DIP with GT-030

Execute GT-030 and produce required EV/DEC records.

Outcome on PASS:
- DIP transitions to `Approved`.

### Step 3 — Derive SPEC/ARCH and assemble readiness evidence

1. Create Initiative-owned SPEC and ARCH drafts from the locked DIP.
2. Assemble derivation linkage evidence showing how both drafts trace back to the locked DIP.
3. Assemble coherence evidence showing the DIP, SPEC, and ARCH remain mutually consistent.

Outcome when complete:
- the Initiative has coherent draft upstream baselines and the supporting evidence packet required for GT-050 / GT-060.

### Step 4 — Approve SPEC/ARCH baselines

1. Execute GT-050 for ARCH.
2. Execute GT-060 for SPEC.

Outcome on PASS:
- Initiative upstream baselines are approved and pinned.

### Step 5 — Establish first executable CH slice

Use `guides/INITIATIVE__DECOMPOSITION_AND_CH_SIZING_v0.1.0.md` to identify at least one bounded CH slice.

Required posture:
- the first CH slice MUST be small enough for safe single-session delivery,
- the first CH slice MUST be large enough that the gate overhead is justified.

### Step 6 — Move Initiative to `Ready`

Set Initiative status to `Ready` only when:
- Steps 0–5 are satisfied,
- upstream references in the Initiative are updated to the approved DIP/SPEC/ARCH,
- the Initiative clearly identifies at least one CH candidate that can proceed to GT-110.

## CH sizing compromise

CH sizing is a compromise between two failure modes.

Too small:
- administrative overhead dominates,
- GT-110 / GT-120 / GT-130 processing cost becomes excessive,
- planning fragments into bookkeeping instead of progress.

Too large:
- the CH exceeds what a capable LLM can safely and reliably implement in a single coding session with one prompt,
- validation becomes ambiguous,
- drift and hidden scope growth increase.

Preferred posture:
- each CH should represent one coherent, independently refinable execution slice,
- tests/docs posture should fit within the same slice whenever practical.

## Relationship to CH execution

- Initiative is the planning object above CH.
- CH remains the execution-grade requirement anchor.
- CI remains the candidate implementation unit.
- Initiative status MUST NOT be used as a substitute for GT-110 / GT-120 / GT-130 outcomes.
