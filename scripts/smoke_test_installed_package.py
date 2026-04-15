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
import io
import json
import subprocess
import tempfile
from pathlib import Path


def _run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        rendered = " ".join(command)
        raise SystemExit(f"Command failed: {rendered}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-package-version")
    args = parser.parse_args()

    import lantern
    from lantern._compat import GRAMMAR_COMPAT_RANGE, check_grammar_compatibility, get_package_resource_path
    from lantern.cli.main import run_cli

    if args.expected_package_version and lantern.__version__ != args.expected_package_version:
        raise SystemExit(f"Expected package version {args.expected_package_version!r}, got {lantern.__version__!r}")

    compat = check_grammar_compatibility()
    if compat["status"] != "ok":
        raise SystemExit(compat["message"])

    manifest_path = get_package_resource_path("skills/packaged_default/skill-manifest.json")
    if not manifest_path.exists():
        raise SystemExit(f"Packaged-default skill manifest not found at {manifest_path}")

    with tempfile.TemporaryDirectory(prefix="lantern_installed_smoke_") as temp_root:
        root = Path(temp_root)
        product_root = root / "product"
        governance_root = root / "governance"
        product_root.mkdir()
        governance_root.mkdir()

        _run_command(
            [
                "lantern",
                "bootstrap-product",
                "--governance-root",
                str(governance_root),
                "--product-root",
                str(product_root),
                "--apply",
            ]
        )
        doctor_result = _run_command(
            [
                "lantern",
                "doctor",
                "--governance-root",
                str(governance_root),
                "--product-root",
                str(product_root),
                "--json",
            ]
        )
        report = json.loads(doctor_result.stdout)
        blockers = [finding for finding in report["findings"] if finding["classification"] == "blocker"]
        if blockers:
            subjects = ", ".join(sorted({finding["subject"] for finding in blockers}))
            raise SystemExit(f"Installed package doctor reported blocker findings: {subjects}")

        serve_stdout = io.StringIO()
        serve_stderr = io.StringIO()
        serve_exit_code = run_cli(
            [
                "serve",
                "--governance-root",
                str(governance_root),
                "--product-root",
                str(product_root),
            ],
            stdout=serve_stdout,
            stderr=serve_stderr,
            run_server=False,
        )
        if serve_exit_code != 0:
            raise SystemExit(
                "Installed package serve preflight failed.\n"
                f"stdout:\n{serve_stdout.getvalue()}\n"
                f"stderr:\n{serve_stderr.getvalue()}"
            )

    for command in ["lantern", "lantern-runtime"]:
        result = subprocess.run([command, "--help"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise SystemExit(f"Console command {command!r} failed with exit code {result.returncode}")

    print("Installed package smoke test passed.")
    print(f"Package version: {lantern.__version__}")
    print(f"Grammar compat range: {GRAMMAR_COMPAT_RANGE}")
    print(f"Grammar status: {compat['status']}")
    print(f"Skill manifest: {manifest_path}")


if __name__ == "__main__":
    main()
