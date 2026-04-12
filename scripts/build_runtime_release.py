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

"""Create staged release artifacts for lantern-runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGED_DEFAULT_ROOT = REPO_ROOT / "lantern" / "skills" / "packaged_default"
FIXTURE_SKILL_MD = PACKAGED_DEFAULT_ROOT / "SKILL.md"
FIXTURE_MANIFEST = PACKAGED_DEFAULT_ROOT / "skill-manifest.json"
EXCLUDE_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv-smoke",
    "__pycache__",
    "build",
    "dist",
    "venv",
}
EXCLUDE_SUFFIXES = {".egg-info", ".pyc", ".pyd", ".pyo", ".tmp", ".temp"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _should_skip(path: Path) -> bool:
    if path.name in EXCLUDE_DIRS:
        return True
    return any(path.name.endswith(suffix) for suffix in EXCLUDE_SUFFIXES)


def _copy_repo(staging_root: Path) -> None:
    for item in REPO_ROOT.iterdir():
        if _should_skip(item):
            continue
        if item.name.startswith(".") and item.name not in {".github", ".pre-commit-config.yaml"}:
            continue
        destination = staging_root / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                destination,
                ignore=shutil.ignore_patterns(*sorted(EXCLUDE_DIRS), *(f"*{suffix}" for suffix in EXCLUDE_SUFFIXES)),
            )
        else:
            shutil.copy2(item, destination)


def _regenerate_packaged_surface(staging_root: Path) -> tuple[Path, Path]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(staging_root) if not existing_pythonpath else f"{staging_root}{os.pathsep}{existing_pythonpath}"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from lantern.skills.generator import write_packaged_skill_surface; write_packaged_skill_surface()",
        ],
        cwd=staging_root,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"Failed to regenerate the packaged skill surface in staging (exit {result.returncode})")

    staged_root = staging_root / "lantern" / "skills" / "packaged_default"
    return staged_root / "SKILL.md", staged_root / "skill-manifest.json"


def _verify_staged_assets(staged_skill_md: Path, staged_manifest: Path) -> None:
    if not FIXTURE_SKILL_MD.exists():
        raise SystemExit(f"Missing packaged skill fixture: {FIXTURE_SKILL_MD}")
    if not FIXTURE_MANIFEST.exists():
        raise SystemExit(f"Missing packaged manifest fixture: {FIXTURE_MANIFEST}")

    if _sha256(staged_skill_md) != _sha256(FIXTURE_SKILL_MD):
        raise SystemExit("Staged SKILL.md diverges from the governed source-tree fixture")

    if json.loads(staged_manifest.read_text(encoding="utf-8")) != json.loads(
        FIXTURE_MANIFEST.read_text(encoding="utf-8")
    ):
        raise SystemExit("Staged skill-manifest.json diverges from the governed source-tree fixture")

    print("Staged operator assets verified against source-tree fixture.")


def _build_distributions(staging_root: Path) -> None:
    result = subprocess.run([sys.executable, "-m", "build"], cwd=staging_root, check=False)
    if result.returncode != 0:
        raise SystemExit(f"python -m build failed with exit code {result.returncode}")

    dist_root = REPO_ROOT / "dist"
    dist_root.mkdir(exist_ok=True)
    for artifact in (staging_root / "dist").iterdir():
        shutil.copy2(artifact, dist_root / artifact.name)
        print(f"Copied build artifact: {dist_root / artifact.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    staging_root = Path(tempfile.mkdtemp(prefix="lantern_runtime_release_"))
    print(f"Staging directory: {staging_root}")
    try:
        _copy_repo(staging_root)
        staged_skill_md, staged_manifest = _regenerate_packaged_surface(staging_root)
        _verify_staged_assets(staged_skill_md, staged_manifest)
        if args.verify_only:
            print("--verify-only selected; skipping build step.")
            return
        _build_distributions(staging_root)
        print("Staged build complete.")
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


if __name__ == "__main__":
    main()
