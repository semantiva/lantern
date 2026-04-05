# Lantern Workflow Layer — Maintainer Reference

This document is the repo-local entry point for operators and maintainers working
with the Lantern workflow layer. It explains the architecture, where declarations live,
which files are authored versus generated, and how the layer is validated.

> **This document is a navigational guide, not a competing SSOT.**
> The authoritative workflow authority surface is the authored input files
> described below. Do not hand-edit the generated files listed under
> "Generated aid files" — regenerate them by re-running `load_workflow_layer()`
> or the generation command shown below.

---

## Architecture: Grammar, Workflow, and Execution

Lantern's design separates concerns across three layers:

### 1. **Lantern Grammar** (Semantic Layer)
The Grammar layer defines the **universe of valid governance concepts**: change intents (CH), test definitions (TD), design baselines (DB), evidence (EV), decisions (DEC), etc. It is the semantic authority maintained separately and referenced by all other layers.

**Defined in**: `lantern-grammar` repository
**Usage here**: The workflow layer references Grammar concepts and validates that workbench declarations conform to valid intent classes, artifact families, and transaction kinds.

### 2. **Workflow Layer** (Declaration Layer — This Repository)
The Workflow layer translates Grammar concepts into **machine-readable workbench and transaction declarations** that govern runtime behavior. It is **authored input** and **generated supporting artifacts** that bind governance state to execution surfaces.

**Defined in**: `lantern/workflow/definitions/` (authored files) and `lantern/workflow/definitions/` (generated files)
**Usage**: Consumed by the MCP runtime to compute active workbench eligibility, enforce response-surface bindings, and expose discovery surfaces.

### 3. **Execution Layer** (Runtime)
The Execution layer **consumes workflow declarations** and translates them into active runtime behavior. It includes:

- **Resolver** (`lantern/workflow/resolver.py`) — derives active workbench set from governance state + workflow declarations
- **Discovery spine** (`lantern/mcp/`) — exposes `inspect` and `orient` tools bounded by response-surface bindings
- **MCP server** (`lantern/mcp/server.py`) — five-tool public surface for AI-assisted development

**Defined in**: `lantern/mcp/` modules
**Usage**: Driven by operators and AI agents through MCP tool calls

---

## Workbench Semantics

A **workbench** is a named, scoped runtime context within which certain governed artifact types can be authored, reviewed, or validated. Each workbench declares:

### Core Fields

- **`workbench_id`** — stable identifier used by resolver, MCP tools, and all governance artifacts (e.g., `ch_and_td_readiness`, `design_candidate_authoring`)

- **`lifecycle_placement`** — governs **when** the workbench is eligible for use based on workflow stage:
  - `lifecycle-independent` — always eligible regardless of gate state
  - `covered_gates: [GT-110, GT-115]` — eligible when any listed gate is active
  - `lifecycle_span: {start_gate: GT-110, end_gate: GT-115}` — eligible after start gate passed, before end gate passed

- **`intent_classes`** — list of natural-language intent patterns (e.g., `["change readiness", "readiness review"]`) that the `orient` tool uses to **prefer** this workbench when multiple are active and an intent string is supplied

- **`allowed_transaction_kinds`** — transaction kinds permitted in this workbench (e.g., `["realize_intent_bundle", "start_design_selection"]`), exposed as next valid actions

### Authority and Enforcement

- **`workflow_surface.response_surface_bindings`** — **CH-0002-authored authority** that governs which resource roles (`instruction_resource`, `authoritative_guides`, `administration_guides`) each transaction kind may surface
  - `inspect` and `orient` readers enforce these bindings; disallowed roles never appear in responses
  - This is the **contract between workflow authoring and runtime discovery enforcement**

- **`instruction_resource`, `authoritative_guides`, `administration_guides`** — repo-local resource paths (guides, templates, contract references) available to operators and maintainers working in this workbench; projected into the resource manifest

---

## Transaction Profile Semantics

A **transaction profile** describes the contract for one transaction kind (e.g., `realize_intent_bundle`, `complete_gt120`). Each profile declares:

- **`transaction_kind`** — stable identifier
- **`allowed_contract_refs`** — which artifact family refs (e.g., `CI-*`, `EV-*`) are permitted as inputs
- **`bounded_artifact_families`** — artifact families affected by this transaction (e.g., creating a CH also creates a TD)
- **`side_effect_class`** — `read_only`, `staged_write`, `durable_write`, or `validation_only`
- **`response_envelopes_when_declared`** — envelope shape for responses; gates when this transaction is permitted

This **separates the shape contract (what fields a response must have) from enforcement (which roles are allowed to appear in them)**.

---

## Authored input files

The following files are the authoritative workflow inputs. Edit them to change
workbench definitions, transaction profiles, or response-surface bindings.

| File | Purpose |
|---|---|
| `definitions/workbench_registry.yaml` | Workbench declarations: lifecycle placement, intent classes, transaction kinds, response-surface bindings, resource references |
| `definitions/workbench_schema.yaml` | JSON/YAML schema that validates `workbench_registry.yaml` on every load |
| `definitions/transaction_profiles.yaml` | Transaction kind profiles: allowed refs, affected families, side-effect class, response envelopes |

---

## Generated aid files

The following files are **generated** from the authored inputs by
`lantern.workflow.loader.load_workflow_layer()`. They are committed to the repo
for offline inspection but must not be hand-edited. Run the command below to
regenerate them after changing any authored input file.

| File | Generated from |
|---|---|
| `definitions/workflow_map.md` | `workbench_registry.yaml` + `transaction_profiles.yaml` — human-readable summary of all workbenches and transaction boundaries |
| `definitions/workbench_resource_bindings.md` | `workbench_registry.yaml` + resource manifest — navigation guide linking workbenches to available resources |
| `definitions/contract_catalog.json` | `workbench_registry.yaml` + `transaction_profiles.yaml` + Grammar API — machine-readable contract atlas for MCP discovery |
| `definitions/resource_manifest.json` | `workbench_registry.yaml` + `lantern/preservation/relocation_manifest.yaml` — all resources addressable by workbench and role |

To regenerate (from the product repo root):

```bash
python - <<'PY'
from lantern.workflow.loader import load_workflow_layer
# load_workflow_layer() asserts that committed generated files match
# freshly-derived output; if this call succeeds without error, the
# committed files are current.
load_workflow_layer()
print("Workflow layer valid; all committed generated files are current.")
PY
```

If the committed files are stale, `WorkflowLayerError` is raised with the name of
the mismatched file. Regenerate the committed files by running
`render_generated_artifacts()` from `lantern.workflow.loader` and committing the
result.

---

## How the workflow layer is validated

`load_workflow_layer()` validates the full layer on every call:

1. **Grammar integrity**: `Grammar.validate_integrity()` must return `ok=True`.
2. **Schema validation**: `workbench_registry.yaml` is checked against `workbench_schema.yaml` (required fields, allowed resource roles, binding shape, workbench inventory order).
3. **Binding coverage**: every transaction kind that declares response envelopes must have a `response_surface_bindings` entry for each workbench that permits the transaction; disallowed resource roles are rejected.
4. **Resource manifest completeness**: every path declared as `instruction_resource`, `authoritative_guides`, or `administration_guides` must exist on disk.
5. **Committed index concordance**: the four generated files are re-derived from authored inputs and asserted byte-for-byte identical to the committed versions.

A descriptive `WorkflowLayerError` is raised on any failure, naming the offending workbench ID, field, or path.

---

## Common Tasks

### Add a new workbench

1. Edit `definitions/workbench_registry.yaml`: add entry under `workbenches:` with `workbench_id`, `lifecycle_placement`, `response_surface_bindings`, etc.
2. Ensure `workbench_schema.yaml` validates the new entry (or update schema if extending allowed fields).
3. Run `load_workflow_layer()` to validate and regenerate `contract_catalog.json` and `workbench_resource_bindings.md`.
4. Commit the updated authored files and regenerated aid files.

### Update response-surface bindings

Response-surface bindings control which resource roles can appear in `inspect` and `orient` responses for a given workbench/transaction pair.
This is the governance control point for runtime discovery enforcement.

1. Edit the `workflow_surface.response_surface_bindings` table in the target workbench within `workbench_registry.yaml`.
2. Run `load_workflow_layer()` to validate.
3. Regenerated `contract_catalog.json` will reflect the updated bindings.
4. MCP `inspect` and `orient` handlers will automatically enforce the new restrictions on next run.

### Check what resources are available in a workbench

Open `definitions/workbench_resource_bindings.md` for a human-readable navigation guide, or query `definitions/resource_manifest.json` programmatically for machine-readable lookups by workbench and role.

---

## Authored vs generated — decision rule

A file is **authored** if it contains normative declarations that governance
directly references (workbench IDs, lifecycle placement, response-surface
bindings, transaction profiles). A file is **generated** if it is derived
deterministically from authored inputs by a single mechanical rule inside
`lantern.workflow.loader`. When in doubt, check whether the file name appears in
`load_workflow_layer()`'s assertion calls: files asserted there are generated.
