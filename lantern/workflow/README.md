# Lantern Workflow Layer

This document explains which workflow files are authored authority, which files are generated compatibility projections, and how the Lantern runtime resolves the active workflow.

The short version:

- authored authority lives in per-file workbench and workflow catalogs;
- `load_workflow_layer()` always loads built-in catalogs and optionally adds repo-local catalogs;
- the active workflow is selected by `workflow_id`, not by raw file path;
- `workbench_registry.yaml`, `contract_catalog.json`, `resource_manifest.json`, `workflow_map.md`, and `workbench_resource_bindings.md` remain packaged for inspection and compatibility, but they are no longer runtime authority.

## Authored Authority

These files are the runtime source of truth:

| File | Purpose |
|---|---|
| `definitions/workbenches/*.yaml` | One file per workbench. Declares lifecycle placement, contracts, inspect views, response-surface bindings, and resource refs. |
| `definitions/workflows/default_full_governed_surface.yaml` | The shipped built-in default workflow. Declares `workflow_id`, `display_name`, `runtime_surface_classification`, and ordered `active_workbench_ids`. |
| `definitions/workbench_schema.yaml` | Schema metadata for workbench definition validation, built-in workbench inventory order, and retired field rejection. |
| `definitions/workflow_schema.yaml` | Schema metadata for workflow definition validation. |
| `definitions/transaction_profiles.yaml` | Transaction-kind profiles used while deriving contract and response surfaces. |

Built-in workbenches are always available. They are never implicitly active merely because the file exists. A workflow becomes active only when its `workflow_id` is selected.

## Generated Compatibility Projections

These files are still useful and still shipped, but they are generated from the selected built-in workflow instead of being loaded as runtime truth:

| File | Role |
|---|---|
| `definitions/workbench_registry.yaml` | Generated compatibility projection retained for unchanged preservation and topology consumers. |
| `definitions/contract_catalog.json` | Generated machine-readable contract atlas for the selected workflow. |
| `definitions/resource_manifest.json` | Generated resource manifest for the selected workflow. |
| `definitions/workflow_map.md` | Generated human-readable summary for the selected workflow. |
| `definitions/workbench_resource_bindings.md` | Generated guide linking selected workbenches to their surfaced resources. |
| `generated/workflow_maps/default_full_governed_surface.md` | Shipped read-only built-in workflow map keyed by `workflow_id`. |

Do not treat these generated files as authoritative workflow inputs.

## Runtime Selection Model

`load_workflow_layer()` resolves the active workflow like this:

1. Load built-in workbench catalogs from `definitions/workbenches/`.
2. Load built-in workflow catalogs from `definitions/workflows/`.
3. Optionally load repo-local workbench catalogs from `<governance-root>/workflow/definitions/workbenches/` or `--workbench-folder`.
4. Optionally load repo-local workflow catalogs from `<governance-root>/workflow/definitions/workflows/` or `--workflow-folder`.
5. Select the workflow by `--workflow-id`.
6. Resolve the active workbench tuple from that workflow's `active_workbench_ids` in declared order.

The no-flag default is `default_full_governed_surface`.

Repo-local catalogs are additive only. They may not reuse built-in workbench ids, built-in workbench display names, or built-in workflow ids.

## Validation Rules

The loader enforces these invariants:

- workbench files must satisfy `workbench_schema.yaml`;
- workflow files must satisfy `workflow_schema.yaml`;
- `source`, `enabled`, and `governance_mode` are rejected in authored workbench files;
- repo-local workbench id and display-name collisions fail closed;
- workflow id collisions fail closed;
- missing `active_workbench_ids` fail closed;
- built-in full-governed selection still covers the required governed families and gates;
- generated projections can be checked explicitly, but they do not block ordinary runtime loading.

## Maintainer Workflow

### Add or edit a built-in workbench

1. Edit the specific file in `definitions/workbenches/`.
2. Keep the `built_in_workbench_ids` order in `definitions/workbench_schema.yaml` aligned with the shipped inventory.
3. Rebuild the generated compatibility projections.

### Add or edit a workflow

1. Edit or add a file in `definitions/workflows/`.
2. Set `workflow_id`, `display_name`, `runtime_surface_classification`, and ordered `active_workbench_ids`.
3. Rebuild the generated compatibility projections for any shipped built-in workflow.

### Refresh generated projections

`load_workflow_layer(enforce_generated_artifacts=True)` verifies the generated projections for the shipped default workflow.

When you intentionally change authored workflow inputs, regenerate:

- `workbench_registry.yaml`
- `contract_catalog.json`
- `resource_manifest.json`
- `workflow_map.md`
- `workbench_resource_bindings.md`
- `generated/workflow_maps/default_full_governed_surface.md`

## Authored vs Generated Decision Rule

A file is authored if runtime startup must read it directly to resolve the active workflow or active workbench set.

A file is generated if it is a deterministic projection of authored catalogs and transaction profiles. Generated files may still be committed for inspection, packaging, or compatibility, but the runtime must not depend on them as the activation source.