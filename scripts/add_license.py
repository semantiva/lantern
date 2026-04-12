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

"""Add Apache 2.0 license headers to Python files that do not already have them."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import EXTENSIONS, HEADER, HEADER_PATTERN, INCLUDE_DIRS, INCLUDE_FILES


def add_header(filepath: Path) -> bool:
    """Add the Lantern Apache header when the target file does not already have it."""
    content = filepath.read_text(encoding="utf-8")
    if HEADER_PATTERN.search(content):
        return False

    shebang = ""
    remainder = content
    if remainder.startswith("#!"):
        first_line, separator, tail = remainder.partition("\n")
        shebang = f"{first_line}\n"
        remainder = tail if separator else ""
        if remainder.startswith("\n"):
            remainder = remainder[1:]

    new_content = f"{shebang}{HEADER}\n{remainder}" if remainder else f"{shebang}{HEADER}\n"
    filepath.write_text(new_content, encoding="utf-8")
    return True


def main() -> None:
    """Batch add headers to all configured Python files."""
    added_count = 0

    for dirpath in INCLUDE_DIRS:
        if not os.path.exists(dirpath):
            continue
        for root, _dirs, files in os.walk(dirpath):
            for filename in files:
                file_path = Path(root) / filename
                if file_path.suffix not in EXTENSIONS:
                    continue
                if add_header(file_path):
                    print(f"Added header: {file_path}")
                    added_count += 1

    for include_file in INCLUDE_FILES:
        file_path = Path(include_file)
        if file_path.exists() and file_path.suffix in EXTENSIONS and add_header(file_path):
            print(f"Added header: {file_path}")
            added_count += 1

    print(f"License header addition complete. Updated files: {added_count}")


if __name__ == "__main__":
    main()