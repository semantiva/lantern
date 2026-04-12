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

"""Package-owned thin operator skill surface helpers for Lantern (CH-0006)."""

from .generator import (
    PACKAGED_SKILL_MANIFEST_PATH,
    PACKAGED_SKILL_MD_PATH,
    SkillGenerator,
    assert_packaged_skill_surface_current,
    compute_workflow_layer_hash,
    write_packaged_skill_surface,
)

__all__ = [
    "PACKAGED_SKILL_MANIFEST_PATH",
    "PACKAGED_SKILL_MD_PATH",
    "SkillGenerator",
    "assert_packaged_skill_surface_current",
    "compute_workflow_layer_hash",
    "write_packaged_skill_surface",
]
