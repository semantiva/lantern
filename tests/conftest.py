from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)

# The lantern_grammar package must be installed before running tests.
# Do not probe sibling filesystem directories for the grammar source tree.
