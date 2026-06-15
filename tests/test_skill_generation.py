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

"""TD-0006 static operator skill surface tests (CH-0034: skill generator retired).

SKILL.md is a hand-maintained static file. The generator.py and skill-manifest.json
were removed in CH-0034 because SKILL.md contains no dynamic content.
"""

from __future__ import annotations

from pathlib import Path

from lantern.workflow.loader import load_workflow_layer

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
SKILL_MD_PATH = PRODUCT_ROOT / "lantern" / "skills" / "packaged_default" / "SKILL.md"


def test_td0006_c01_packaged_skill_has_mandatory_header_and_routing_content() -> None:
    skill = SKILL_MD_PATH.read_text(encoding="utf-8")

    assert skill.startswith(
        "---\nname: lantern\ndescription: Use this skill when the task involves Lantern-governed workflow work."
    )
    assert "---\n\n# Lantern Operator Skill\n" in skill
    assert "## Use Lantern when" in skill
    assert "## Do not use Lantern as" in skill
    assert "## What Lantern gives you" in skill
    assert "## First MCP move" in skill
    assert '`inspect(kind="catalog")`' in skill
    assert '`inspect(kind="workspace")`' in skill
    assert "## Universal discovery sequence" in skill
    assert "## Immutable safety rules" in skill
    assert "## Operating posture" in skill

    for forbidden in (
        "Operator instruction resource for workbench",
        "GT-120__CI_SELECTION_ADMINISTRATION",
        "TEMPLATE__CI",
        "lantern/resources/",
        "lantern/templates/",
    ):
        assert forbidden not in skill


def test_td0006_c02_skill_md_has_no_mode_or_workbench_projection() -> None:
    """CH-0034: SKILL.md is static — no workbench/mode enumeration."""
    layer = load_workflow_layer()
    skill = SKILL_MD_PATH.read_text(encoding="utf-8")

    for wb in layer.workbenches:
        assert (
            wb.workbench_id not in skill
        ), f"SKILL.md enumerates workbench_id {wb.workbench_id!r}: must be static and workflow-agnostic"


def test_td0006_c03_packaged_first_touch_route_is_mechanically_derivable() -> None:
    skill = SKILL_MD_PATH.read_text(encoding="utf-8")
    assert 'inspect(kind="catalog")' in skill
    assert 'inspect(kind="workspace")' in skill
