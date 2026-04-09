# Artifact ID allocation

This document is normative for Lantern workflow artifact identifier allocation.

## Sequential families

The following families use sequential ids of width 4:
- `INI-####`
- `CH-####`
- `EV-####`
- `DEC-####`
- `IS-####`
- `DIP-####`
- `SPEC-####`
- `ARCH-####`
- `TD-####`
- `DB-####`

## CH-anchored families

The following families use `CH_NUM + UUID`:
- `CI-<CH_NUM>-<UUID>`
- `DC-<CH_NUM>-<UUID>`

Where `CH_NUM` is the numeric suffix of the governing `CH-####` identifier.

## Allocator rule

Allocation MUST be performed using `python tools/allocate_lantern_id.py --artifact <FAMILY> --repo <path-to-governance-root>` from the Lantern workflow product repository.

For CH-anchored families (`CI`, `DC`), the allocator invocation MUST also include `--ch CH-####`. The wrapper delegates to `lantern.artifacts.allocator.allocate_artifact_id` so sequential and CH-anchored families use the same runtime authority.
