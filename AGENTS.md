<!-- LANTERN-MANAGED:BEGIN -->
<!-- Lantern workflow release: to be filled at install time (e.g. 0.5.0-phase1) -->
# AGENTS.md — Lantern governed product workspace

This managed block was generated from the Lantern workflow release surface.
Keep the managed markers intact so a future Lantern refresh can update this file safely.
You may add repo-specific notes below the managed block.

## Workspace boundary

- This repository is the **product workspace**.
- Governed records live in the companion Lantern governance workspace and are authoritative there.
- Never create or edit governed records or `binding_record.md` in this repository.
- Reach governed SSOT only through the configured Lantern MCP server and the shipped Lantern skills.

## Default operating posture

- Start from the user's plain-language request.
- First inspect runtime posture, then load the active stage packet for the current stage.
- Use **governance autopilot** by default:
  - synthesize one intent bundle,
  - ask only blocking questions,
  - then administer the governed path through MCP.
- Do not ask the user to choose gates, artifact IDs, or skills by name unless the runtime genuinely lacks the required skill.
- Prefer the stage packet's recommended Lantern runtime tool over manual low-level gate choreography when the workflow release surface provides it.

## Bootstrap and intake

- If `bootstrap_required` is true, use the Lantern bootstrap/intake posture before any other governed write.
- If this `AGENTS.md` file is missing, create it from the Lantern-managed template before continuing.
- After bootstrap, continue governed intake from the same user request rather than making the user restart the conversation.

## Differential change posture

- For additive changes, inspect existing approved governed inputs first.
- Reuse existing approved DIP, SPEC, ARCH, TD, and DB references when they still govern the requested slice.
- Create new governed artifacts only when the requested slice materially changes governed scope, constraints, architecture, or verification expectations.
- State the reuse-vs-new-authoring decision explicitly in the intent bundle summary before writing governed artifacts.

## Closure integrity

- After GT-130, treat the result as **quarantined** until post-close checks are clean.
- If tests fail, the worktree changes, or the bound commit no longer matches the working tree, do not claim clean closure.
- Reopen or create a follow-on governed change through Lantern before additional code edits continue.

## Non-negotiables

- Do not invent artifact IDs, statuses, schema fields, or lifecycle shortcuts.
- Do not bypass MCP to edit governed SSOT files directly.
- Do not tell the user to drive the workflow by gate number.
- Do not leave the repo dirty while claiming the governed closure is complete.
- If a blocking ambiguity remains, ask the smallest possible question.
<!-- LANTERN-MANAGED:END -->

## Project-specific notes

Add repository-specific build, test, and contribution notes below this line.
Do not edit the managed block above unless you are updating the Lantern workflow release surface itself.
