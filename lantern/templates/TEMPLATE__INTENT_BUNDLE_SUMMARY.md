# Intent Bundle Summary — <short request title>

Use this summary to replace section-by-section design interviews.
One approval should cover the bundle unless a blocking ambiguity remains.

## 1. Workspace posture

- `workspace_bootstrapped`: `<true|false>`
- `recommended_posture`: `<bootstrap-intake|downstream-change>`
- `related_governed_context`: `<none | CH/DB/CI references>`
- `authoring_mode_proposal`: `<fresh|differential>`

## 2. Request in plain language

- User goal:
- Requested product behavior:
- Key capabilities:
- Constraints:
- Non-goals:

## 3. Proposed governed slice

- Proposed CH title:
- Proposed origin statement:
- Proposed reuse of existing approved artifacts:
  - DIP:
  - SPEC:
  - ARCH:
  - TD:
  - DB:
- Proposed new or updated governed artifacts:
- Why this is `fresh` or `differential`:

## 4. Acceptance and verification intent

- Expected user-visible outcomes:
- Expected verification signals:
- Product-side constraints:
- SSOT-side constraints:

## 5. Blocking questions only

- Question 1:
- Question 2:

If there are no blocking questions, write `None`.

## 6. Approval checkpoint

- Operator decision: `Pending | Approved | Revise`
- Approval notes:
- If revised, what changed:

**Next steps by decision:**
- `Approved` → proceed immediately to MCP intake realization using the composite intake operation; do not wait for additional user commands.
- `Revise` → update sections 2–4 to reflect the changes noted above, then re-present the bundle for a single approval.
- `Pending` → ask only the remaining blocking question(s) listed in section 5.
