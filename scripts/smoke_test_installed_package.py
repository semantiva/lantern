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

"""Exercise the installed lantern-runtime package from a clean environment."""

from __future__ import annotations

import argparse
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-package-version")
    args = parser.parse_args()

    import lantern
    from lantern._compat import GRAMMAR_COMPAT_RANGE, check_grammar_compatibility, get_package_resource_path
    from lantern.cli.main import main as cli_main  # noqa: F401

    if args.expected_package_version and lantern.__version__ != args.expected_package_version:
        raise SystemExit(f"Expected package version {args.expected_package_version!r}, got {lantern.__version__!r}")

    compat = check_grammar_compatibility()
    if compat["status"] not in {"ok", "missing", "unsupported"}:
        raise SystemExit(f"Unexpected compatibility status: {compat['status']!r}")

    manifest_path = get_package_resource_path("skills/packaged_default/skill-manifest.json")
    if not manifest_path.exists():
        raise SystemExit(f"Packaged-default skill manifest not found at {manifest_path}")

    for command in ["lantern", "lantern-runtime"]:
        result = subprocess.run([command, "--help"], capture_output=True, check=False)
        if result.returncode != 0:
            raise SystemExit(f"Console command {command!r} failed with exit code {result.returncode}")

    print("Installed package smoke test passed.")
    print(f"Package version: {lantern.__version__}")
    print(f"Grammar compat range: {GRAMMAR_COMPAT_RANGE}")
    print(f"Grammar status: {compat['status']}")
    print(f"Skill manifest: {manifest_path}")


if __name__ == "__main__":
    main()
