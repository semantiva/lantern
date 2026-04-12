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

"""Package-owned thin operator skill-surface generation for CH-0006.

This module owns the committed package-default `SKILL.md` and `skill-manifest.json`
under `lantern/skills/packaged_default/`. It does not manage governance-folder
freshness checks or generated template mirrors.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from lantern.mcp.catalog import filter_resources_for_workbench
from lantern.workflow.loader import WorkflowLayer, load_workflow_layer

PACKAGED_DEFAULT_ROOT = Path(__file__).resolve().parent / "packaged_default"
PACKAGED_SKILL_MD_PATH = PACKAGED_DEFAULT_ROOT / "SKILL.md"
PACKAGED_SKILL_MANIFEST_PATH = PACKAGED_DEFAULT_ROOT / "skill-manifest.json"


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_workflow_layer_hash(workflow_layer: WorkflowLayer) -> str:
    payload = {
        "grammar_version": workflow_layer.grammar_version,
        "grammar_package_version": workflow_layer.grammar_package_version,
        "workbench_ids": [workbench.workbench_id for workbench in workflow_layer.workbenches],
        "contract_refs": [entry.contract_ref for entry in workflow_layer.contract_catalog],
        "resource_ids": [entry.resource_id for entry in workflow_layer.resource_manifest],
    }
    return _sha256_text(_canonical_json(payload))


def _contract_catalog_hash(workflow_layer: WorkflowLayer) -> str:
    payload = [
        {
            "contract_ref": entry.contract_ref,
            "request_schema_ref": entry.request_schema_ref,
            "transaction_kind": entry.transaction_kind,
            "workbench_refs": list(entry.workbench_refs),
            "family_binding": list(entry.family_binding),
            "gate_binding": list(entry.gate_binding),
            "response_surface_bindings": [
                {
                    "transaction_kind": binding.transaction_kind,
                    "response_envelope": binding.response_envelope,
                    "allowed_resource_roles": list(binding.allowed_resource_roles),
                }
                for binding in entry.response_surface_bindings
            ],
        }
        for entry in workflow_layer.contract_catalog
    ]
    return _sha256_text(_canonical_json(payload))


def _resource_manifest_hash(workflow_layer: WorkflowLayer) -> str:
    payload = [
        {
            "resource_id": entry.resource_id,
            "kind": entry.kind,
            "workbench_id": entry.workbench_id,
            "content_hash": entry.content_hash,
            "roles": list(entry.roles),
        }
        for entry in workflow_layer.resource_manifest
    ]
    return _sha256_text(_canonical_json(payload))


def _mode_id_for_workbench(workbench: Any) -> str:
    if workbench.intent_classes:
        return workbench.intent_classes[0]
    return workbench.workbench_id


def _build_mode_entries(workflow_layer: WorkflowLayer) -> list[dict[str, Any]]:
    seen_mode_ids: set[str] = set()
    modes: list[dict[str, Any]] = []
    for workbench in workflow_layer.workbenches:
        mode_id = _mode_id_for_workbench(workbench)
        if mode_id in seen_mode_ids:
            raise AssertionError(
                f"Duplicate packaged mode_id {mode_id!r}; CH-0006 packaged routing must stay unambiguous"
            )
        seen_mode_ids.add(mode_id)
        inspect_roles = tuple(
            role
            for role in next(
                (
                    binding.allowed_resource_roles
                    for binding in workbench.response_surface_bindings
                    if binding.transaction_kind == "inspect"
                ),
                (),
            )
            if role
            in {
                "instruction_resource",
                "authoritative_guides",
                "administration_guides",
                "artifact_templates",
            }
        )
        resource_refs = [
            item["resource_id"]
            for item in filter_resources_for_workbench(
                workflow_layer=workflow_layer,
                workbench_id=workbench.workbench_id,
                allowed_roles=inspect_roles,
            )
        ]
        modes.append(
            {
                "mode_id": mode_id,
                "entry_workbench_id": workbench.workbench_id,
                "entry_contract_refs": list(workbench.contract_refs),
                "resource_refs": resource_refs,
            }
        )
    return modes


def _workflow_mode_ids(workflow_layer: WorkflowLayer) -> list[str]:
    return [entry["mode_id"] for entry in _build_mode_entries(workflow_layer)]


def build_packaged_skill_md(workflow_layer: WorkflowLayer) -> str:
    workflow_modes = "\n".join(f"- `{mode_id}`" for mode_id in _workflow_mode_ids(workflow_layer))
    return f"""---
name: lantern
description: Use this skill when the task involves Lantern-governed workflow work. This includes authoring or assessing change handlers (CH, TD, DB, CI), upstream baseline intake (DIP, SPEC, ARCH), design candidate or design selection steps, CI authoring or selection, applying a selected CI, verification or closure, issue intake, governance onboarding, or bootstrap. Triggers on any mention of Lantern gates (GT-030, GT-050, GT-060, GT-110, GT-115, GT-120, GT-130), Lantern MCP tools (inspect, orient, draft, commit, validate), Lantern artifact families, or requests to operate through Lantern workflow procedures rather than direct repository editing.
---

# Lantern Operator Skill

Lantern is a governed workflow runtime for work that is controlled by formal artifacts, lifecycle states, gates, and workbench procedures.

Use this skill to decide whether Lantern applies, and to route into the correct MCP discovery path. This skill is intentionally thin: it gives the operator the right mindset and the first moves, but live MCP resources remain authoritative.

## Use Lantern when

Use Lantern when the request is about any of the following:

- governed change work, such as CH, TD, DB, CI, verification, or closure
- baseline or upstream intake work, such as SPEC, ARCH, or DIP intake and baseline preparation
- issue intake or governed problem handling
- governance onboarding or bootstrap
- Lantern workflow gates, statuses, dependencies, required evidence, or required decisions
- choosing the correct workbench, contract, guide, or template for governed work
- operating through Lantern MCP procedures rather than direct repository spelunking

Typical examples:

- “Prepare or assess a CH/TD for readiness”
- “Work a design candidate or design selection step”
- “Author or select a CI”
- “Apply a selected CI and move toward verification/closure”
- “Handle an issue through the governed workflow”
- “Bootstrap or onboard a governed product into Lantern”
- “Explain which Lantern workflow mode or workbench applies”

## Do not use Lantern as

Do not treat Lantern as:

- a raw repository search tool
- a general file browser
- a substitute for live MCP discovery packets
- a place to invent workflow meaning from filenames or repository paths
- an authority over mutable guides, templates, or workbench details

If the task is ordinary repo editing with no Lantern governance context, Lantern may not be the right first tool.

## What Lantern gives you

Lantern gives you a governed routing layer over workflow truth.

It helps you:

- determine whether a governed workflow applies
- identify the right workflow mode and entry workbench
- inspect the authoritative contract for that workbench
- consume live guides, instructions, and templates through MCP before any write
- stay on the fixed public tool surface

## First MCP move

Call:

`inspect(kind="catalog")`

Then call:

`inspect(kind="workspace")`

These two calls establish the governed vocabulary and the active runtime/workspace posture before you choose a mode.

## Universal discovery sequence

1. `inspect(kind="catalog")`
2. `inspect(kind="workspace")`
3. read `skill-manifest.json`
4. choose the most relevant workflow mode and entry workbench
5. `orient(...)`
6. `inspect(kind="contract", contract_ref="...")`
7. consume the returned live `resource_packets`
8. only then consider `draft`, `commit`, or `validate`

## Workflow modes currently exposed

Use the manifest to choose among these mode families:

{workflow_modes}

When unsure, do not guess from names alone. Use the manifest entry workbench and contract refs, then confirm through `orient(...)` and `inspect(kind="contract", ...)`.

## Minimal routing hints

- If the user is preparing or assessing governed change work, start by checking `change_readiness`.
- If the user is working from upstream baseline artifacts, check `baseline_intake`.
- If the user is handling a reported problem or issue, check `issue_intake`.
- If the user is onboarding or setting up governance, check `bootstrap`.
- If the user is in the middle of design, CI, application, or closure work, use the corresponding mode from the manifest rather than inferring from repository layout.

## Immutable safety rules

- Treat this skill and manifest as routing only; live MCP resources remain authoritative.
- Stay on the fixed public tool surface: `inspect`, `orient`, `draft`, `commit`, `validate`.
- Do not rely on raw repository paths as the operator contract.
- Do not require local skill regeneration or generated guide/template folders before source-tree discovery.
- Do not skip `inspect(kind="contract", ...)` before acting on a workbench.
- Do not invent gate semantics, status meaning, or workflow transitions from memory when MCP can resolve them.

## Operating posture

This skill is meant to create the right initial mindset:

- first identify whether the request is governed by Lantern
- then route to the correct mode/workbench
- then read authoritative live packets
- then act

Lantern is strongest when used as governed routing and inspection, not as opportunistic repo search.
"""


def build_packaged_skill_manifest(workflow_layer: WorkflowLayer) -> dict[str, Any]:
    return {
        "skill_schema_version": "1",
        "workflow_release": {
            "grammar_version": workflow_layer.grammar_version,
            "grammar_package_version": workflow_layer.grammar_package_version,
            "workflow_layer_hash": compute_workflow_layer_hash(workflow_layer),
            "contract_catalog_hash": _contract_catalog_hash(workflow_layer),
            "resource_manifest_hash": _resource_manifest_hash(workflow_layer),
        },
        "workflow_modes": _build_mode_entries(workflow_layer),
    }


class SkillGenerator:
    """Generate and verify the package-owned thin CH-0006 skill surface."""

    def render(self, workflow_layer: WorkflowLayer | None = None) -> tuple[str, dict[str, Any]]:
        layer = workflow_layer or load_workflow_layer()
        return build_packaged_skill_md(layer), build_packaged_skill_manifest(layer)

    def write_packaged_surface(self, workflow_layer: WorkflowLayer | None = None) -> None:
        skill_md, manifest = self.render(workflow_layer)
        PACKAGED_DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
        PACKAGED_SKILL_MD_PATH.write_text(skill_md, encoding="utf-8")
        PACKAGED_SKILL_MANIFEST_PATH.write_text(_canonical_json(manifest), encoding="utf-8")

    def assert_current(self, workflow_layer: WorkflowLayer | None = None) -> None:
        skill_md, manifest = self.render(workflow_layer)
        assert PACKAGED_SKILL_MD_PATH.exists(), f"missing packaged skill file: {PACKAGED_SKILL_MD_PATH}"
        assert PACKAGED_SKILL_MANIFEST_PATH.exists(), f"missing packaged manifest file: {PACKAGED_SKILL_MANIFEST_PATH}"
        assert PACKAGED_SKILL_MD_PATH.read_text(encoding="utf-8") == skill_md
        assert json.loads(PACKAGED_SKILL_MANIFEST_PATH.read_text(encoding="utf-8")) == manifest


def write_packaged_skill_surface(workflow_layer: WorkflowLayer | None = None) -> None:
    SkillGenerator().write_packaged_surface(workflow_layer)


def assert_packaged_skill_surface_current(workflow_layer: WorkflowLayer | None = None) -> None:
    SkillGenerator().assert_current(workflow_layer)
