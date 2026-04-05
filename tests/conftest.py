from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)

_CANDIDATE_GRAMMAR_PATHS = [
    ROOT.parent / "lantern-grammar" / "src",
    ROOT.parent / "lantern-project" / "lantern-grammar" / "src",
    ROOT.parent / "lantern_v29" / "lantern-project" / "lantern-grammar" / "src",
    ROOT.parents[1] / "lantern_v29" / "lantern-project" / "lantern-grammar" / "src",
]

for grammar_src in _CANDIDATE_GRAMMAR_PATHS:
    grammar_src_str = str(grammar_src)
    if grammar_src.is_dir() and grammar_src_str not in sys.path:
        sys.path.insert(0, grammar_src_str)
        break
