#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lantern.artifacts.allocator import allocate_artifact_id


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Allocate the next Lantern governance artifact id.")
    parser.add_argument("--artifact", required=True, help="Artifact family, e.g. EV, DEC, DB, CI, DC")
    parser.add_argument("--repo", required=True, type=Path, help="Path to the governance repository root")
    parser.add_argument("--ch", help="Parent CH id required for CI/DC allocation")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    governance_root = args.repo.resolve()
    artifact = args.artifact.upper()
    try:
        artifact_id = allocate_artifact_id(artifact, governance_root, ch_id=args.ch)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(artifact_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
