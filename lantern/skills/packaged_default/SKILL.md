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

- “Prepare or assess a CH/TD for readiness”
- “Work a design candidate or design selection step”
- “Author or select a CI”
- “Apply a selected CI and move toward verification/closure”
- “Handle an issue through the governed workflow”
- “Bootstrap or onboard a governed product into Lantern”
- “Explain which Lantern workflow mode or workbench applies”

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
- consume live guides, instructions, and templates through MCP before any write
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
3. read `skill-manifest.json`
4. choose the most relevant workflow mode and entry workbench
5. `orient(...)`
6. `inspect(kind="contract", contract_ref="...")`
7. consume the returned live `resource_packets`
8. only then consider `draft`, `commit`, or `validate`

## Workflow modes currently exposed

Use the manifest to choose among these mode families:

- `baseline_intake`
- `change_readiness`
- `design_candidate_authoring`
- `design_selection`
- `ci_authoring`
- `ci_selection`
- `selected_ci_application`
- `verification_and_closure`
- `issue_intake`
- `bootstrap`

When unsure, do not guess from names alone. Use the manifest entry workbench and contract refs, then confirm through `orient(...)` and `inspect(kind="contract", ...)`.

## Minimal routing hints

- If the user is preparing or assessing governed change work, start by checking `change_readiness`.
- If the user is working from upstream baseline artifacts, check `baseline_intake`.
- If the user is handling a reported problem or issue, check `issue_intake`.
- If the user is onboarding or setting up governance, check `bootstrap`.
- If the user is in the middle of design, CI, application, or closure work, use the corresponding mode from the manifest rather than inferring from repository layout.

## Immutable safety rules

- Treat this skill and manifest as routing only; live MCP resources remain authoritative.
- Stay on the fixed public tool surface: `inspect`, `orient`, `draft`, `commit`, `validate`.
- Do not rely on raw repository paths as the operator contract.
- Do not require local skill regeneration or generated guide/template folders before source-tree discovery.
- Do not skip `inspect(kind="contract", ...)` before acting on a workbench.
- Do not invent gate semantics, status meaning, or workflow transitions from memory when MCP can resolve them.

## Operating posture

This skill is meant to create the right initial mindset:

- first identify whether the request is governed by Lantern
- then route to the correct mode/workbench
- then read authoritative live packets
- then act

Lantern is strongest when used as governed routing and inspection, not as opportunistic repo search.
