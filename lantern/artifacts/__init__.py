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

"""Artifact helpers for Lantern governed mutations."""

from lantern.artifacts.allocator import allocate_artifact_id, artifact_path
from lantern.artifacts.renderers import canonical_render_markdown, parse_header_block

__all__ = [
    "allocate_artifact_id",
    "artifact_path",
    "canonical_render_markdown",
    "parse_header_block",
]
