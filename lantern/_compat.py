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

"""Runtime package-resource resolution and Lantern Grammar compatibility checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lantern import GRAMMAR_COMPAT_RANGE

_GRAMMAR_MIN = (0, 3, 0)
_GRAMMAR_MAX_EXCLUSIVE = (0, 4, 0)
_PACKAGE_ROOT = Path(__file__).resolve().parent


class GrammarCompatibilityError(RuntimeError):
    """Raised when the installed lantern-grammar package is not supported."""


def get_package_resource_path(relative: str) -> Path:
    """Return an absolute path to a package-owned resource."""
    return _PACKAGE_ROOT / Path(relative)


def _parse_version(version_str: str | None) -> tuple[int, ...]:
    if not version_str:
        return ()
    numbers = [int(value) for value in re.findall(r"\d+", version_str)]
    if not numbers:
        return ()
    return tuple(numbers[:3])


def _supported_result(
    *,
    package_version: str | None,
    model_version: str | None,
    message: str = "",
) -> dict[str, Any]:
    return {
        "status": "ok",
        "supported_range": GRAMMAR_COMPAT_RANGE,
        "installed_package_version": package_version,
        "installed_model_version": model_version,
        "message": message,
    }


def _unsupported_result(
    *,
    package_version: str | None,
    model_version: str | None,
    message: str,
) -> dict[str, Any]:
    return {
        "status": "unsupported",
        "supported_range": GRAMMAR_COMPAT_RANGE,
        "installed_package_version": package_version,
        "installed_model_version": model_version,
        "message": message,
    }


def _evaluate_versions(package_version: str | None, model_version: str | None) -> dict[str, Any]:
    parsed_package_version = _parse_version(package_version)
    if not parsed_package_version:
        return _unsupported_result(
            package_version=package_version,
            model_version=model_version,
            message=(
                "Lantern Runtime could not determine the installed lantern-grammar package version. "
                f"Install a compatible version in the supported range {GRAMMAR_COMPAT_RANGE}."
            ),
        )

    if not (_GRAMMAR_MIN <= parsed_package_version < _GRAMMAR_MAX_EXCLUSIVE):
        return _unsupported_result(
            package_version=package_version,
            model_version=model_version,
            message=(
                f"Installed lantern-grammar package version {package_version!r} is outside the supported "
                f"range {GRAMMAR_COMPAT_RANGE}."
            ),
        )

    if package_version and model_version and package_version != model_version:
        return _unsupported_result(
            package_version=package_version,
            model_version=model_version,
            message=(
                "Lantern Runtime requires the first lantern-grammar release to keep package and model "
                f"versions equal; installed package version is {package_version!r} and model version is "
                f"{model_version!r}."
            ),
        )

    return _supported_result(package_version=package_version, model_version=model_version)


def require_supported_grammar(grammar: Any | None = None) -> dict[str, Any]:
    """Return the compatibility result or raise if the loaded Grammar is unsupported."""
    if grammar is None:
        try:
            from lantern_grammar import Grammar
        except Exception as exc:
            raise GrammarCompatibilityError(
                "lantern-grammar is not importable. Install a compatible published package with "
                f"pip install 'lantern-grammar{GRAMMAR_COMPAT_RANGE}'."
            ) from exc
        grammar = Grammar.load()

    package_version = str(grammar.package_version())
    model_version = str(dict(grammar.manifest()).get("model_version", ""))
    result = _evaluate_versions(package_version, model_version)
    if result["status"] != "ok":
        raise GrammarCompatibilityError(result["message"])
    return result


def check_grammar_compatibility() -> dict[str, Any]:
    """Return a structured Lantern Runtime to Lantern Grammar compatibility report."""
    try:
        import lantern_grammar
        from lantern_grammar import Grammar
    except Exception as exc:
        return {
            "status": "missing",
            "supported_range": GRAMMAR_COMPAT_RANGE,
            "installed_package_version": None,
            "installed_model_version": None,
            "message": (
                f"lantern-grammar is not importable: {exc}. Install a compatible published package with "
                f"pip install 'lantern-grammar{GRAMMAR_COMPAT_RANGE}'."
            ),
        }

    package_version = getattr(lantern_grammar, "__version__", None)
    try:
        grammar = Grammar.load()
    except Exception as exc:
        return _unsupported_result(
            package_version=package_version,
            model_version=None,
            message=(
                f"lantern-grammar is installed but its model bundle could not be loaded: {exc}. "
                f"Install a compatible published package in the supported range {GRAMMAR_COMPAT_RANGE}."
            ),
        )

    loaded_package_version = package_version or str(grammar.package_version())
    model_version = str(dict(grammar.manifest()).get("model_version", ""))
    return _evaluate_versions(loaded_package_version, model_version)
