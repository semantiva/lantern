# POC_VALUE_EXTRACTION_MAP — Mapping PoC `Lantern` workspace to Clean Restart Lantern workflow (WP3)

## Purpose

This document records how the mature `Lantern` proof-of-concept (PoC) workflow artifacts were mapped into the Clean Restart topology:

- Lantern model: Lantern model product repository (semantics only)
- Lantern workflow tooling: Lantern workflow product repository (tooling only)
- Lantern workflow SSOT: Lantern workflow SSOT container repository (definitions + governance artifacts)

This mapping is intended to be precise enough for an AI assistant to operate deterministically without “inventing” new process.

## High-level mapping decisions

1) The `lantern/` on-disk contract is preserved (indexes, change registry, templates, guides).
2) Gate semantics are bound to Lantern model ids (see `lantern/preservation/LANTERN_MODEL_BINDING.md`).
3) Operational gate procedures that previously lived in PoC `model/lantern/preservation/GATES.md` are placed under:
   - `lantern/preservation/GATES.md` (workflow SSOT; operational)

4) Upstream input authoring templates previously under PoC `workflow/templates/` are now under:
   - `lantern/templates/` (workflow SSOT)

5) Structural validation tooling previously under PoC `lantern/tools/validate_lantern.py` is now under:
   - `tools/validate_lantern_workspace.py` (Lantern workflow product repository)

## File-by-file map

### Guides

| PoC artifact | Clean Restart location | Notes |
|---|---|---|
| `lantern/change_increment_authoring_guide_v0.1.4.md` | `lantern/change_increment_authoring_guide_v0.2.0.md` | Updated for multi-repo topology + GT-110 guidance split |
| `lantern/change_intention_refinement_guide_v0.1.1.md` | `lantern/change_intention_refinement_guide_v0.2.0.md` | Rewritten to use DIP/SPEC/ARCH intake and GT-110 evidence classes |
| `lantern/change_increment_selection_guide_v0.1.0.md` | `lantern/change_increment_selection_guide_v0.2.0.md` | Version + anchor updates |
| `lantern/guides/GT-120__CI_SELECTION_ADMINISTRATION_v0.1.0.md` | `lantern/guides/GT-120__CI_SELECTION_ADMINISTRATION_v0.2.0.md` | Version + anchor updates |
| `workflow/process/SSOT_BLOB_INGESTION.md` | `lantern/guides/SSOT_BLOB_INGESTION_v0.2.0.md` | Updated to new template paths + output locations |

### Specifications

| PoC artifact | Clean Restart location | Notes |
|---|---|---|
| `lantern/preservation/EPISTEMIC_FRAME.md` | `lantern/preservation/EPISTEMIC_FRAME.md` | Preamble added; references adjusted |
| `model/lantern/preservation/UPSTREAM_INPUT_ARTIFACTS.md` | `lantern/preservation/UPSTREAM_INPUT_ARTIFACTS.md` | Preamble added |
| `model/lantern/preservation/GATES.md` | `lantern/preservation/GATES.md` | Preamble added; references adjusted |
| (new) | `lantern/preservation/WORKSPACE_TOPOLOGY.md` | Clean Restart multi-repo posture |
| (new) | `lantern/preservation/LANTERN_MODEL_BINDING.md` | Mapping to Lantern model ids |

### Templates

| PoC artifact | Clean Restart location | Notes |
|---|---|---|
| `lantern/templates/*.md` | `lantern/templates/*.md` | Updated CH template; GT-120 templates preserved |
| `workflow/lantern/templates/TEMPLATE__DIP.md` | `lantern/templates/TEMPLATE__DIP.md` | Moved for consistency |
| `workflow/lantern/templates/TEMPLATE__SPEC.md` | `lantern/templates/TEMPLATE__SPEC.md` | Moved for consistency |
| `workflow/lantern/templates/TEMPLATE__ARCH.md` | `lantern/templates/TEMPLATE__ARCH.md` | Moved for consistency |

### Tooling

| PoC artifact | Clean Restart location | Notes |
|---|---|---|
| `lantern/tools/validate_lantern.py` | `tools/validate_lantern_workspace.py` (Lantern workflow product repository) | Argument renamed to `--ssot-root` |

## Non-goals of this mapping

- Translating PoC CH/CI artifacts into new SSOT containers (explicitly out of scope).
- Adding new automation runners beyond structural validation (may be addressed later).
