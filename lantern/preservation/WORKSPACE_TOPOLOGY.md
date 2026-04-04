# WORKSPACE_TOPOLOGY — Lantern workflow operation across separated repositories

## Scope

This specification defines how Lantern workflow MUST operate in a workspace where:
- product repositories and SSOT container repositories are separated (hard boundary), and
- operators and agents may need to reason across multiple repositories.

This spec is normative for Lantern workflow execution and documentation.

## Definitions

- **Workspace**: any working directory containing multiple repositories required for an operation.
- **Product repository**: a repository containing product code and/or tooling (no SSOT scaffolding).
- **SSOT container repository**: a repository containing governance artifacts and decision records for a governed product.

## Boundary rules (hard)

1) Product repositories MUST NOT contain:
   - SSOT entrypoints (e.g., `README__SSOT.md`),
   - ADR/decision record scaffolding (e.g., `decisions/` folders as SSOT posture),
   - workflow run artifacts (CH/CI/EV/DEC).

2) SSOT container repositories MUST contain:
   - decision records and open questions for that product,
   - governance artifacts (CH/CI/EV/DEC) for that product.

3) **Product repository identity MUST be repo-local and authoritative:**
   - Each product repo's `README.md` is the authoritative identity and scope entrypoint for that product.
   - Product repositories MUST NOT reference their companion SSOT containers by name or URL.

4) **All product↔SSOT binding is one-way (SSOT→product only):**
   - SSOT container `README.md` MUST name and link to the governed product repo and state that the product repo `README.md` is authoritative for product identity.
   - SSOT containers record binding information (commit SHAs, governance records) - products do not replicate or reference this.
   - Product repositories MUST NOT be required to reference Lantern workflow, Lantern model, or their companion SSOT containers (no mandatory config files, no mandatory pointers back to SSOT).

## Canonical path conventions

When recording pointers to files, paths MUST be one of:

- **SSOT-repo relative**: paths relative to the SSOT container repo root (recommended inside `lantern/` artifacts).
- **Product-repo relative**: paths relative to the governed product repo root (recommended when pointing to code within that repo).
- **Cross-repo reference**: repository name + immutable commit SHA + repo-relative path (recommended when a record needs to reference another repository).

A record MUST NOT assume co-location of SSOT and product material inside a single Git repository.

## Binding record posture

Each SSOT container repository MUST contain a `binding_record.md` (or equivalent) that records immutable identifiers for the relevant repos:

Minimum required bindings:
- governed product repo identifier (commit SHA)
- Lantern model identifier (commit SHA) and `model_id`+`model_version` when available
- Lantern workflow tooling identifier (commit SHA)
- ECT identifier (commit SHA) when ECT tooling is used as part of validation

A binding record MUST be updated by the operator (human or authorized assistant) when the governed product moves.

## Operating modes

### Mode L — Local agent (full workspace access)

This is the preferred mode.

Requirements:
- The operator and AI assistant have filesystem access to the full workspace root.
- Gate execution MAY inspect both SSOT and product repos as needed.
- All written artifacts MUST be written only to SSOT container repos.

### Mode R — Remote agent with single-repo visibility (e.g., CODEX snapshot)

A remote agent that only receives one repository snapshot cannot reliably operate across separated repos without an execution bridge.

Two supported bridge options:

#### Option R1 — Execution bundle repository (recommended)

Create a temporary “bundle” repository that contains the required repos as submodules.

Bundle repo structure (example):
- `bundle/`
   - `product/semantiva/` (submodule)
   - `governance/semantiva/` (submodule)
   - `product/lantern-workflow/` (submodule)  ← tooling
   - `governance/lantern-workflow/` (submodule)     ← guides/specs
   - `product/lantern-model/` (submodule)     ← semantics
  - `WORKSPACE_MANIFEST.md` (records SHAs/tags for all submodules)

Rules:
- The bundle repository MUST NOT become the SSOT container. It is an execution convenience only.
- The bundle repository MUST record the exact SHAs/tags used (the agent’s snapshot MUST include `WORKSPACE_MANIFEST.md`).
- Outputs MUST still be committed to the real SSOT container repos, not to the bundle repo.

Example: create a bundle repo (git submodules)

```bash
# from a clean working directory
mkdir lantern_bundle
cd lantern_bundle
git init

# Add the required repos as submodules at fixed paths
git submodule add <URL> product/semantiva
git submodule add <URL> governance/semantiva
git submodule add <URL> product/lantern-workflow
git submodule add <URL> governance/lantern-workflow
git submodule add <URL> product/lantern-model
git submodule add <URL> product/ect

# Pin submodules to explicit SHAs (example; repeat for each)
cd product/semantiva
git checkout <SHA>

# Return to bundle root and repeat for each submodule.

# Record SHAs/tags in a manifest for snapshot consumers
cat > WORKSPACE_MANIFEST.md <<'EOF'
# Workspace manifest — lantern_bundle

Record the exact SHAs/tags for each submodule so a snapshot-only agent can reason precisely.

- product/semantiva: <SHA or tag>
- governance/semantiva: <SHA or tag>
- product/lantern-workflow: <SHA or tag>
- governance/lantern-workflow: <SHA or tag>
- product/lantern-model: <SHA or tag>
- product/ect: <SHA or tag>
EOF

git add .gitmodules WORKSPACE_MANIFEST.md
git commit -m "Bundle: pin submodules for remote execution"
```


#### Option R2 — SSOT projection pack (restricted use)

Provide a curated pack containing:
- only the SSOT artifacts required for the task,
- only the minimal product code excerpts required (if any),
- and a manifest of the source commit(s).

This option is appropriate when code access must be minimized or when the task is purely SSOT administration (e.g., GT-120 selection within already-authored CI candidates).

This option MUST include a manifest containing:
- source repo URL(s),
- source commit SHA(s) or tags,
- included file list.

## Non-goals

- This spec does not mandate any change to product repositories to “integrate” Lantern workflow.
- This spec does not define cryptographic signing or attestation (may be added later).
