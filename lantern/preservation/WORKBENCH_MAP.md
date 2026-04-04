# WORKBENCH_MAP — Lantern workflow all-gates workbench decomposition

This document is the human-readable authoritative workbench decomposition for the Lantern workflow.
The canonical machine-readable registry is `runtime/mcp/workbench_registry.yaml`.

> Gates are always explicit. Grouped workbench families cover multiple gates operationally,
> but gate identity is never omitted from runtime contracts or this document.

## Workbench families

### 1. Upstream Intake and Baselines

**Covered gates:** GT-030, GT-050, GT-060

**Purpose:**
Establish the upstream artifacts (DIP, SPEC, ARCH) as approved baselines suitable
for downstream change work. These gates progress from DIP lock through SPEC/ARCH drafting
and carried derivation/coherence evidence to ARCH and SPEC readiness approval.

**In-scope artifact families:** DIP, SPEC, ARCH, INI

**MCP authority expectations:**
MCP governs gate progression. `workbench_posture` from `lantern_runtime_health` names the
active workbench. `workbench_context` from `lantern_load_stage_context` returns authoritative
guide paths for the active gate.

**Authoritative guides (`lantern/authoring_contracts/`):**
- `dip_authoring_guide_v0.1.0.md`

**Administration procedures (`lantern/administration_procedures/`):**
- `GT-030__DIP_LOCK_ADMINISTRATION_v0.1.0.md`
- `GT-050_GT-060__BASELINE_READINESS_ADMINISTRATION_v0.1.0.md`
- `AI_OPERATOR_INVOCATION_TEMPLATES_v0.2.1.md`
- `INITIATIVE__AUTHORING_AND_READYING_v0.1.0.md`
- `INITIATIVE__DECOMPOSITION_AND_CH_SIZING_v0.1.0.md`

**Allowed next actions:** review DIP/SPEC/ARCH draft, begin write session, execute gate

**Blocked conditions:** upstream artifacts not yet approved or missing

**Product execution permitted:** no

---

### 2. CH and TD Readiness

**Covered gates:** GT-110

**Purpose:**
Establish that the proposed Change Intent (CH) has sufficient approved upstream inputs
and approved test-definition coverage to proceed to design selection.

**In-scope artifact families:** CH, TD, EV, DEC

**MCP authority expectations:**
`workbench_context` from `lantern_load_stage_context("intake")` names the authoritative
CH/TD authoring contracts.

**Authoritative guides (`lantern/authoring_contracts/`):**
- `change_intention_refinement_guide_v0.2.1.md` (primary for CH authoring)
- `test_definition_authoring_guide_v0.1.0.md` (primary for TD authoring)

**Blocked conditions:** upstream baselines not approved; CH not in ready state

**Product execution permitted:** no

---

### 3. Design Selection

**Covered gates:** GT-115

**Purpose:**
Select one Design Candidate and approve one Design Baseline as the authoritative design
commitment for the change.

**In-scope artifact families:** DC, DB, EV, DEC

**MCP authority expectations:**
`workbench_context` from `lantern_load_stage_context("gt115")` names the DC/DB authoring
contracts. MCP validates `selection_limits` and gates the composite on gate-limit compliance.

**Authoritative guides (`lantern/authoring_contracts/`):**
- `design_candidate_authoring_guide_v0.1.0.md`
- `design_candidate_selection_guide_v0.1.0.md`
- `design_baseline_authoring_guide_v0.1.0.md`

**Administration procedures (`lantern/administration_procedures/`):**
- `GT-115__DESIGN_BASELINE_SELECTION_v0.1.0.md`

**Blocked conditions:** GT-110 not passed; no DC candidates available

**Product execution permitted:** no

---

### 4. CI Authoring

**Covered gates:** (none — pre-gate authoring phase)

**Purpose:**
Author candidate Change Increments against the locked DB and TD baselines.
Not a gate phase, but a mandatory precondition for CI selection.

**In-scope artifact families:** CI

**Authoritative guides (`lantern/authoring_contracts/`):**
- `change_increment_authoring_guide_v0.2.1.md`

**Blocked conditions:** GT-115 not passed; DB not approved

**Product execution permitted:** no

---

### 5. CI Selection

**Covered gates:** GT-120

**Purpose:**
Select the governing Change Increment for implementation. One CI is marked Selected;
all others are marked Rejected.

**In-scope artifact families:** CI, EV, DEC

**Authoritative guides (`lantern/authoring_contracts/`):**
- `change_increment_selection_guide_v0.2.1.md`

**Administration procedures (`lantern/administration_procedures/`):**
- `GT-120__CI_SELECTION_ADMINISTRATION_v0.2.1.md`

**Blocked conditions:** No structurally complete CI candidates; GT-115 not passed

**Product execution permitted:** no

---

### 6. Selected CI Application

**Covered gates:** (none — inter-gate execution phase)

**Purpose:**
Apply the product changes prescribed by the selected CI against the locked DB,
TD, and ARCH baselines and gather execution evidence. Product code changes happen only in this phase.

**In-scope artifact families:** CI, EV

**Authoritative guides (`lantern/authoring_contracts/`):**
- `change_increment_authoring_guide_v0.2.1.md`

**Blocked conditions:** CI not selected; GT-120 not passed

**Product execution permitted:** yes — this is the only workbench where product writes are allowed

---

### 7. Verification and Closure

**Covered gates:** GT-130

**Purpose:**
Verify integration evidence, produce a Verification Decision, address the Change Intent,
and open closure quarantine. Product commits must be tied to governance decisions before
this gate closes.

**In-scope artifact families:** EV, DEC, CH, CI

**Authoritative guides (`lantern/authoring_contracts/`):**
- `change_increment_selection_guide_v0.2.1.md`

**Administration procedures (`lantern/administration_procedures/`):**
- `GT-130__INTEGRATION_VERIFICATION_ADMINISTRATION_v0.1.0.md`

**Blocked conditions:** selected CI not applied; implementation evidence not gathered

**Product execution permitted:** no

---

### 8. Issue Operations

**Covered gates:** (none — asynchronous issue lifecycle)

**Purpose:**
Track observed bugs, defects, and regressions through the governed issue lifecycle
(IS artifact family). Issues may be opened at any stage.

**In-scope artifact families:** IS

**Administration procedures (`lantern/administration_procedures/`):**
- `ISSUE__INTAKE_TRIAGE_RESOLUTION_v0.2.0.md`

**Blocked conditions:** none — issues may be created or updated at any workflow stage

**Product execution permitted:** no

---

## All-gates quick reference

| Gate | Workbench family | Purpose |
|---|---|---|
| GT-030 | Upstream Intake and Baselines | DIP baseline lock |
| GT-050 | Upstream Intake and Baselines | Architecture definition readiness |
| GT-060 | Upstream Intake and Baselines | Requirements specification readiness |
| GT-110 | CH and TD Readiness | Input kit readiness — CH + TD → CH Ready |
| GT-115 | Design Selection | Design baseline selection → DB Approved |
| GT-120 | CI Selection | Change increment selection → CI Selected |
| GT-130 | Verification and Closure | Integration verification → CI Verified, CH Addressed |
