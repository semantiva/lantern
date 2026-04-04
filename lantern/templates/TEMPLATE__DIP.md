# DIP-[[TEMPLATE:DIP_ID]] — [[TEMPLATE:TITLE]]

Status: [[TEMPLATE:STATUS]]  <!-- Draft | Approved | Superseded -->
Supersedes: [[TEMPLATE:SUPERSEDES]]  <!-- DIP-#### | None -->
Timestamp: [[TEMPLATE:TIMESTAMP]]  <!-- ISO 8601 recommended -->

## Summary

[[TEMPLATE:SUMMARY]]

## Source inventory (required)

Rules
- Prefer repo-relative paths (no absolute paths).
- If the source is private/sensitive, use an opaque token (e.g., `PRIVATE_SOURCE_001`) and keep the real locator in a private mapping file outside any public projection.
- Keep the inventory structured; downstream derivations (SPEC/ARCH) should be traceable to one or more source items.

| Source ID | Type | Locator (repo-relative or token) | Privacy | Notes |
|---|---|---|---|---|
| SRC-001 | file/url/etc | [[TEMPLATE:LOCATOR_OR_TOKEN]] | private/public | [[TEMPLATE:NOTES]] |

## Constraints and non-goals (required)

[[TEMPLATE:CONSTRAINTS_AND_NON_GOALS]]

## Questions referenced (required; may be empty)

- (If none) `[]`
- Q-[[TEMPLATE:Q_ID]] (Blocking: [[TEMPLATE:YES_NO]]; Status: [[TEMPLATE:OPEN_RESOLVED]]) — [[TEMPLATE:QUESTION_TEXT]]

## Pinning pointers (optional; informative)

This section is optional. Baseline locator evidence is normally captured at GT-030 as an Evidence/Decision record.

- Candidate baseline locator: `[[TEMPLATE:DIP_PATH]]@[[TEMPLATE:COMMIT_HASH]]` (or equivalent immutable reference)

## Notes

[[TEMPLATE:NOTES]]
