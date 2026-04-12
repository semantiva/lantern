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

"""Verify that project Python files contain the required Apache 2.0 header."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import EXTENSIONS, HEADER_PATTERN, INCLUDE_DIRS, INCLUDE_FILES

REPO_ROOT = Path(__file__).resolve().parents[1]


def has_header(filepath: Path) -> bool:
    return bool(HEADER_PATTERN.search(filepath.read_text(encoding="utf-8")))


def main() -> None:
    missing_files: list[str] = []

    for include_dir in INCLUDE_DIRS:
        dir_path = REPO_ROOT / include_dir
        if not dir_path.exists():
            continue
        for root, _dirs, files in os.walk(dir_path):
            for filename in files:
                file_path = Path(root) / filename
                if file_path.suffix in EXTENSIONS and not has_header(file_path):
                    missing_files.append(str(file_path.relative_to(REPO_ROOT)))

    for include_file in INCLUDE_FILES:
        file_path = REPO_ROOT / include_file
        if file_path.exists() and file_path.suffix in EXTENSIONS and not has_header(file_path):
            missing_files.append(str(file_path.relative_to(REPO_ROOT)))

    if missing_files:
        print("Missing license headers:")
        for missing in sorted(missing_files):
            print(f"  {missing}")
        raise SystemExit(1)

    print("License header check passed.")


if __name__ == "__main__":
    main()