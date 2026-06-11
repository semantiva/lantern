#!/usr/bin/env python3

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

"""Developer entrypoint: regenerate all committed projections.

For Lantern maintainers only. Run after any authored workflow-input change
(workbench YAML, workflow YAML, resource files) to bring committed projections
back into committed-equals-derived agreement before committing.

Usage (from the lantern/ product directory root):
    python -m scripts.regenerate_committed_projections

The user-facing `lantern` CLI is not modified by this script.
"""

from __future__ import annotations

import sys

from lantern.workflow.regenerate import write_committed_projections

if __name__ == "__main__":
    write_committed_projections()
    print("Committed projections regenerated.", file=sys.stderr)
