---
name: lantern
description: Use this skill when the task involves Lantern-governed workflow work. This includes authoring or assessing change handlers (CH, TD, DB, CI), upstream baseline intake (DIP, SPEC, ARCH), design candidate or design selection steps, CI authoring or selection, applying a selected CI, verification or closure, issue intake, governance onboarding, or bootstrap. Triggers on any mention of Lantern gates (GT-030, GT-050, GT-060, GT-110, GT-115, GT-120, GT-130), Lantern MCP tools (inspect, orient, draft, commit, validate), Lantern artifact families, or requests to operate through Lantern workflow procedures rather than direct repository editing.
---

# Lantern Operator Skill

Lantern is a governed workflow runtime for work that is controlled by formal artifacts, lifecycle states, gates, and workbench procedures.

Use this skill to decide whether Lantern applies, and to route into the correct MCP discovery path. This skill is intentionally thin: it gives the operator the right mindset and the first moves, but live MCP resources remain authoritative.

## Use Lantern when

Use Lantern when the request is about any of the following:

- governed change work, such as CH, TD, DB, CI, verification, or closure
- baseline or upstream intake work, such as SPEC, ARCH, or DIP intake and baseline preparation
- issue intake or governed problem handling
- governance onboarding or bootstrap
- Lantern workflow gates, statuses, dependencies, required evidence, or required decisions
- choosing the correct workbench, contract, guide, or template for governed work
- operating through Lantern MCP procedures rather than direct repository spelunking

Typical examples:

- "Prepare or assess a CH/TD for readiness"
- "Work a design candidate or design selection step"
- "Author or select a CI"
- "Apply a selected CI and move toward verification/closure"
- "Handle an issue through the governed workflow"
- "Bootstrap or onboard a governed product into Lantern"
- "Explain which Lantern workflow mode or workbench applies"

## Do not use Lantern as

Do not treat Lantern as:

- a raw repository search tool
- a general file browser
- a substitute for live MCP discovery packets
- a place to invent workflow meaning from filenames or repository paths
- an authority over mutable guides, templates, or workbench details

If the task is ordinary repo editing with no Lantern governance context, Lantern may not be the right first tool.

## What Lantern gives you

Lantern gives you a governed routing layer over workflow truth.

It helps you:

- determine whether a governed workflow applies
- identify the right workflow mode and entry workbench
- inspect the authoritative contract for that workbench
- consume live Charter task cards, layer bodies, and templates through MCP before any write
- stay on the fixed public tool surface

## First MCP move

Call:

`inspect(kind="catalog")`

Then call:

`inspect(kind="workspace")`

These two calls establish the governed vocabulary and the active runtime/workspace posture before you choose a mode.

## Universal discovery sequence

1. `inspect(kind="catalog")`
2. `inspect(kind="workspace")`
3. `orient(...)` — use the active workbench from catalog to get the task card and charter routing
4. `inspect(kind="contract", contract_ref="...")`
5. consume the returned live `resource_packets` and `charter_layer_bodies`
6. only then consider `draft`, `commit`, or `validate`

## Routing

Workflow mode and workbench selection is driven by live MCP discovery. Call `inspect(kind="catalog")` to enumerate available workbenches and their contract refs, then use `orient(...)` to confirm the active workbench for the current lifecycle position.

Do not enumerate modes from filenames or repository paths. Use `inspect(kind="catalog")` as the authoritative source.

## Operator invocation requirements (default full governed workflow only)

**Scope note:** The guidance in this section applies to the default `full_governed_surface` workflow. If the MCP server is loaded with a custom workflow or custom workbenches, the task boundaries, authorization postures, and required inputs for those workbenches are defined by their own workflow surface — not by this document. Consult the live MCP resources for that workflow's task-specific guidance.

Before calling `orient(...)`, confirm that the operator has provided all of the following for the intended task. If any item is missing, ask before proceeding.

**Required for every governed task invocation:**
- Target artifact ID(s) and scope anchor (`INI`, `DIP`, `SPEC`, `ARCH`, `CH`, `TD`, `DC`, `DB`, `CI` as applicable)
- Target gate ID, if the task executes a gate (e.g., `GT-110`, `GT-115`, `GT-120`, `GT-130`)
- Scope boundary: what is in scope and what is explicitly out of scope for this invocation
- Authorization posture: one of:
  - **Analysis only** — `inspect` and `draft` transactions are permitted; `commit` is NOT authorized
  - **Administration authorized** — `inspect`, `draft`, and `commit` are permitted for the named scope
- Stop condition: when the task ends (do not proceed past it without re-authorization)
- Expected deliverables: which artifact files must exist at completion

**Recommended (state when available):**
- `governance_root`: path to the SSOT container repository root
- Binding posture: committed product SHA or release ID, when the task involves product verification
- Governing authoring contract: when the task creates `DC` or `CI` artifacts, state the locked contract ref explicitly

**Authorization posture matters most at selection gates.** When working GT-115 (design baseline selection) or GT-120 (CI selection): if the operator has not explicitly stated "administration authorized," treat the task as analysis-only and do not execute `commit` transactions. The workbench allows both postures; the operator's stated scope determines which applies.

## Immutable safety rules

- Treat this skill as routing only; live MCP resources remain authoritative.
- Stay on the fixed public tool surface: `inspect`, `orient`, `draft`, `commit`, `validate`.
- Do not rely on raw repository paths as the operator contract.
- Do not require local skill regeneration or generated guide/template folders before source-tree discovery.
- Do not skip `inspect(kind="contract", ...)` before acting on a workbench.
- Do not invent gate semantics, status meaning, or workflow transitions from memory when MCP can resolve them.

## Operating posture

This skill is meant to create the right initial mindset:

- first identify whether the request is governed by Lantern
- then route to the correct mode/workbench via `inspect(kind="catalog")` and `orient(...)`
- then read authoritative live packets and Charter layer bodies
- then act

Lantern is strongest when used as governed routing and inspection, not as opportunistic repo search.
