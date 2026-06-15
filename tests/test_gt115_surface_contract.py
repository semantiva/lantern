# Copyright 2025 Lantern Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parents[1]


def test_gt115_templates_use_live_conventions() -> None:
    ev_template = (PRODUCT_ROOT / "lantern/templates/EV_TEMPLATE__GT115_SELECTION_REPORT.md").read_text(
        encoding="utf-8"
    )
    dec_template = (PRODUCT_ROOT / "lantern/templates/DEC_TEMPLATE__GT115_SELECTION.md").read_text(encoding="utf-8")

    assert "applies_to_initiative" in ev_template
    assert 'gate_id: "GT-115"' in ev_template
    assert 'title: "GT-115 selection report for CH-####"' in ev_template
    assert 'artifacts: ["DB-####", "DEC-####"]' in ev_template
    assert 'artifacts: ["DEC-####"]' not in ev_template
    assert 'path: "ch/CH-####.md"' in ev_template
    assert 'path: "spec/SPEC-####.md"' in ev_template
    assert 'path: "arch/ARCH-####.md"' in ev_template
    assert "governance repo root" in ev_template
    assert (
        "references:" in ev_template
        and "  ch:" in ev_template
        and "  td:" in ev_template
        and "  spec:" in ev_template
        and "  arch:" in ev_template
    )
    assert "applies_to_initiative" in dec_template
    assert 'outcome: "PASS"' in dec_template
    assert "## Decision" in dec_template
    assert "## Decision rationale" in dec_template


def test_allocator_wrapper_allocates_sequential_and_ch_anchored_ids(tmp_path: Path) -> None:
    governance_root = tmp_path / "governance_root"
    (governance_root / "ev").mkdir(parents=True)
    (governance_root / "db").mkdir(parents=True)
    (governance_root / "ev/EV-0007.md").write_text("# fixture\n", encoding="utf-8")
    (governance_root / "db/DB-0002.md").write_text("# fixture\n", encoding="utf-8")

    wrapper = PRODUCT_ROOT / "tools/allocate_lantern_id.py"

    ev = subprocess.run(
        [sys.executable, str(wrapper), "--artifact", "EV", "--repo", str(governance_root)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert ev.returncode == 0
    assert ev.stdout.strip() == "EV-0008"

    dc = subprocess.run(
        [sys.executable, str(wrapper), "--artifact", "DC", "--repo", str(governance_root), "--ch", "CH-0019"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert dc.returncode == 0
    assert re.fullmatch(r"DC-0019-[0-9a-f-]{36}", dc.stdout.strip())
