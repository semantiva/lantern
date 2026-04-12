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

"""Generate a CycloneDX SBOM for lantern-runtime."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def generate_sbom(output: Path, python_interpreter: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cyclonedx = shutil.which("cyclonedx-py")
    if cyclonedx is None:
        raise SystemExit("cyclonedx-py not found. Install the release extras first.")

    cmd = [
        cyclonedx,
        "environment",
        "--pyproject",
        "pyproject.toml",
        "--mc-type",
        "library",
        "--output-reproducible",
        "--output-format",
        "JSON",
        "--outfile",
        str(output),
        str(python_interpreter),
    ]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(f"SBOM generation failed with exit code {result.returncode}")
    print(f"SBOM generated: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/sbom.cyclonedx.json", type=Path)
    parser.add_argument("--python", default=sys.executable, type=Path)
    args = parser.parse_args()
    generate_sbom(args.output, args.python)


if __name__ == "__main__":
    main()