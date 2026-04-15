# Lantern Runtime

Lantern is a governed workflow runtime that provides a discovery-first MCP
execution surface for AI-assisted development on top of a machine-readable
workflow layer.

Lantern's first public release supports one public operating posture: install the
published `lantern-runtime` package and run it as a single-operator runtime against
an explicit product/governance pair. Concurrent team operation is unsupported in
this release. Source-checkout and maintainer notes below are not the public operator
install/start contract.

It combines:

- **Machine-readable workflow layer** — governed workbench declarations, transaction profiles, and response-surface bindings
- **Workflow resolver** — governance-state-driven resolution of active workbench set and next valid actions
- **Discovery spine** — `inspect` and `orient` MCP tools for runtime posture and resource discovery
- **MCP server interface** — five-tool public surface (`inspect`, `orient`, `draft`, `commit`, `validate`) for AI-assisted execution

This is the **product repository**. It contains the `lantern/` Python package and the product-local test suite. The companion governance workspace remains authoritative for governed artifacts.

## Operator guide

Install Lantern Runtime as the published package:

```bash
pip install lantern-runtime
```

The documented `pip install lantern-runtime` path supplies the supported
package-managed runtime prerequisites for the normal operator flow, including a
compatible `lantern-grammar` dependency.

The documented primary command is `lantern`. `lantern-runtime` is an explicit package-identity alias.

Lantern ships a bounded operator CLI for startup, diagnostics, bootstrap, and flat discovery over the governed workspace.

- `serve` starts the MCP server with explicit workspace roots.
- `doctor` reports runtime, workspace, bootstrap, and discovery posture.
- `bootstrap-product` previews or applies the managed bootstrap surface for a product/governance pair.
- `list` filters the flat discovery registry by bounded metadata fields.
- `show` resolves one exact record from that same registry.

Typical installed-package commands:

```bash
lantern doctor --governance-root /path/to/governance-root --product-root /path/to/product-repo --json
lantern bootstrap-product --governance-root /path/to/governance-root --product-root /path/to/product-repo
lantern serve --governance-root /path/to/governance-root --product-root /path/to/product-repo
lantern list --governance-root /path/to/governance-root --product-root /path/to/product-repo --family CH --status Ready --json
lantern show ch_and_td_readiness --entity-kind workbench --governance-root /path/to/governance-root --product-root /path/to/product-repo
```

Operational rules:

- `serve` requires an explicit governance root and uses the governed configuration to resolve the product root after bootstrap.
- `bootstrap-product` previews changes by default and only writes files when `--apply` is present.
- `doctor`, `list`, and `show` can emit machine-readable JSON with `--json`.
- `list` and `show` stay inside exact-token lookup and bounded metadata filtering; they do not run free-form text search or graph traversal.

If `lantern_grammar` is missing or unsupported, Lantern fails descriptively at startup and tells the operator to install a compatible published package before loading the workflow layer.

## Maintainer guide

> This section is for release and repository maintenance. It is not the public operator install/start contract.

Lantern Runtime reuses the `lantern-grammar` `linting -> test -> build -> publish` topology under one pinned local/CI posture.

Install the local release toolchain:

```bash
pip install -e ".[dev,release]"
```

Run the authoritative local release gate:

```bash
python scripts/check_version_alignment.py --require-grammar-first-release-equality
python scripts/check_repo_hygiene.py
pylint --fail-under=7.5 lantern/
ruff check lantern/ tests/ scripts/
mypy lantern/
black --check lantern/ tests/ scripts/
python scripts/check_license_headers.py
coverage run -m pytest --maxfail=1 -q
coverage report
python scripts/build_runtime_release.py
rm -rf .venv-smoke
python -m venv .venv-smoke
. .venv-smoke/bin/activate
python -m pip install --upgrade pip
python -m pip install dist/*.whl
python scripts/smoke_test_installed_package.py --expected-package-version "$(python scripts/check_version_alignment.py --print-package-version)"
deactivate
python -m twine check dist/*
python scripts/check_artifact_hygiene.py
```

The build job also performs a clean-environment install smoke, license report generation, and CycloneDX SBOM generation. The tag used for publication must match `[project].version` in `pyproject.toml`.

Lantern generates a committed package-default skill surface from the workflow layer. When workflow declarations change, regenerate the packaged surface:

```bash
python -c "from lantern.skills.generator import write_packaged_skill_surface; write_packaged_skill_surface()"
```

## Contributor guide

> This section is for source-checkout development. It is not the public operator install/start contract. Normal operators should use the installed-package workflow above.

Clone the repository and install the dev environment:

```bash
git clone https://github.com/lantern-authors/lantern.git
cd lantern
pip install -e ".[dev]"
pip install lantern-grammar
```

Use the workflow-layer README for the authored-vs-generated boundary and runtime surface details:

- `lantern/workflow/README.md`

Start the runtime directly from a source checkout when you are developing Lantern itself:

```bash
python -m lantern.mcp.server \
  --product-root /path/to/product-repo/ \
  --governance-root /path/to/governance-root/
```

When Lantern governs an external product, `--product-root` must point at the governed product repository, not at the Lantern checkout. The executing Lantern package or source checkout provides the workflow release surface; governed product repositories must **not** vendor or copy a `lantern/` runtime tree as a startup prerequisite.

### Minimal tracked bootstrap surface for an external product repo

A fresh governed product repository may contain only the following Lantern-related tracked files:

- `README.md` for product identity and local operating notes
- managed `AGENTS.md`
- a bounded `tools/run-lantern-mcp.sh` launcher that points to an installed Lantern package or external Lantern checkout
- minimal `.gitignore` entries for Python/test/cache artifacts when needed

Repo-local editor or MCP wiring such as `.vscode/mcp.json` should stay ignored and must not be used to vendor Lantern into the product repository.

### VS Code + GitHub Copilot

Edit your VS Code user settings at `~/.config/Code/User/mcp.json` (create if missing):

```json
{
  "servers": {
    "Lantern development": {
      "type": "stdio",
      "command": "python",
      "args": [
        "-m",
        "lantern.mcp.server",
        "--product-root",
        "/path/to/product-repo/",
        "--governance-root",
        "/path/to/governance-root/"
      ]
    }
  },
  "inputs": []
}
```

### CODEX

Use the following configuration in your CODEX settings:

```toml
[features]
multi_agent = true

[mcp_servers.governed_workspace]
command = "python"
args = [
  "-m",
  "lantern.mcp.server",
  "--product-root",
  "/path/to/product-repo/",
  "--governance-root",
  "/path/to/governance-root/"
]
enabled = true
```

### Native MVP smoke path

Use this bridge-free smoke path after the manual `lantern_grammar` install is complete:

```bash
python -m lantern.mcp.server \
  --product-root /path/to/lantern/ \
  --governance-root /path/to/governance-root/
```

In a second shell, run the bounded native regression path that exercises startup, mutation, selected-CI application hygiene, and validation without `lantern-ops-bridge`:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest \
  tests/test_workflow_loader.py \
  tests/test_mcp_server.py \
  tests/test_mcp_mutation.py \
  tests/test_transaction_journal.py -q
```

The native smoke path is only complete when startup succeeds with explicit product/governance roots, the selected-CI application flow records an application handoff that is `awaiting_gt130`, and `validate(scope="workspace")` plus `validate(scope="transaction")` both produce deterministic findings or a clean pass on the post-hardening baseline.
