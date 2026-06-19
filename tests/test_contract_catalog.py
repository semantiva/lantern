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

from lantern.workflow.loader import load_workflow_layer


def test_contract_catalog_and_resource_manifest_cover_selected_workflow() -> None:
    layer = load_workflow_layer()

    workbench_ids = {workbench.workbench_id for workbench in layer.workbenches}
    contract_refs = {workbench.contract_refs[0] for workbench in layer.workbenches}

    assert {entry.contract_ref for entry in layer.contract_catalog} == contract_refs
    assert {entry.workbench_refs[0] for entry in layer.contract_catalog} == workbench_ids
    for entry in layer.contract_catalog:
        assert entry.request_schema_ref == f"schema.request.{entry.workbench_refs[0]}.v1"
        assert entry.response_surface_bindings
        assert entry.compatibility["runtime_surface_classification"] == layer.runtime_surface_classification
        assert entry.compatibility["selected_workflow_id"] == layer.selected_workflow_id


def test_operating_references_slot_is_unpopulated_until_ch0035() -> None:
    layer = load_workflow_layer()
    assert (
        layer.resource_manifest == ()
    ), "CH-0034 must leave no legacy guide-resource entries and must not populate operating_references; CH-0035 owns operating-reference document binding."
