"""Journal persistence for transaction correlation and post-application handoff."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def runtime_state_root(*, product_root: Path, governance_root: Path | None) -> Path:
    if governance_root is not None:
        return governance_root / ".lantern_runtime"
    return product_root / ".lantern_runtime"



def ensure_runtime_dirs(*, product_root: Path, governance_root: Path | None) -> Path:
    root = runtime_state_root(product_root=product_root, governance_root=governance_root)
    for relative in ("drafts", "journal", "validation"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    return root



def write_journal_record(
    *,
    runtime_root: Path,
    transaction_id: str,
    record: dict[str, Any],
) -> Path:
    journal_dir = runtime_root / "journal" / transaction_id
    journal_dir.mkdir(parents=True, exist_ok=True)
    journal_path = journal_dir / "journal.json"
    journal_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return journal_path



def write_validation_snapshot(
    *,
    runtime_root: Path,
    transaction_id: str,
    snapshot: dict[str, Any],
) -> Path:
    validation_dir = runtime_root / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    path = validation_dir / f"{transaction_id}.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path



def write_application_handoff(
    *,
    runtime_root: Path,
    transaction_id: str,
    handoff: dict[str, Any],
) -> Path:
    journal_dir = runtime_root / "journal" / transaction_id
    journal_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = journal_dir / "application_handoff.json"
    handoff_path.write_text(json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return handoff_path



def load_journal_record(*, runtime_root: Path, transaction_id: str) -> dict[str, Any]:
    path = runtime_root / "journal" / transaction_id / "journal.json"
    return json.loads(path.read_text(encoding="utf-8"))



def load_validation_snapshot(*, runtime_root: Path, transaction_id: str) -> dict[str, Any]:
    path = runtime_root / "validation" / f"{transaction_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))



def load_application_handoff(*, runtime_root: Path, transaction_id: str) -> dict[str, Any] | None:
    path = runtime_root / "journal" / transaction_id / "application_handoff.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
