# Lantern

Lantern is a governed workflow runtime that provides a discovery-first MCP
execution surface for AI-assisted development on top of a machine-readable
workflow layer.

It combines:

- **Machine-readable workflow layer** — governed workbench declarations, transaction profiles, and response-surface bindings
- **Workflow resolver** — governance-state-driven resolution of active workbench set and next valid actions
- **Discovery spine** — `inspect` and `orient` MCP tools for runtime posture and resource discovery
- **MCP server interface** — five-tool public surface (`inspect`, `orient`, `draft`, `commit`, `validate`) for AI-assisted execution

## Repository contents

This is the **product repository**. It contains:

- `lantern/` — the Lantern Python package
- `tests/` — the test suite

The companion governance workspace lives in a separate sibling repository and remains authoritative for governed artifacts. Keep governed artifact maintenance in that repository.

## Getting started

Lantern requires `lantern_grammar` to be installed before startup. Install it as a managed package.

### Installed-package mode

```bash
cd /path/to/lantern
pip install lantern-grammar
pip install -e ".[dev]"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

### Source-checkout mode for an external product workspace

```bash
cd /path/to/lantern
pip install lantern-grammar
PYTHONPATH=/path/to/lantern python -m lantern.mcp.server  \
  --product-root /path/to/product-repo   --governance-root /path/to/product-governance
```

In both modes, Lantern resolves its workflow release surface from the executing `lantern` runtime environment. Governed product repositories must **not** vendor or copy a `lantern/` runtime tree as a startup prerequisite.

If `lantern_grammar` is not installed, Lantern fails descriptively at startup and tells the operator to complete the prerequisite step before loading the workflow layer.

## Operational CLI

Lantern also ships a bounded operator CLI for startup, diagnostics, bootstrap, and flat discovery over the governed workspace.

- `serve` starts the MCP server with explicit workspace roots.
- `doctor` reports runtime, workspace, bootstrap, and discovery posture.
- `bootstrap-product` previews or applies the managed bootstrap surface for a product/governance pair.
- `list` filters the flat discovery registry by bounded metadata fields.
- `show` resolves one exact record from that same registry.

From this repository checkout, use repository-relative paths instead of machine-specific absolute paths:

```bash
python -m lantern.cli doctor --governance-root ../governance-root --product-root . --json
python -m lantern.cli bootstrap-product \
  --product-root ../example-product \
  --governance-root ../example-product-governance
python -m lantern.cli serve --governance-root ../governance-root --product-root .
python -m lantern.cli list --governance-root ../governance-root --product-root . --family CH --status Ready --json
python -m lantern.cli show ch_and_td_readiness --entity-kind workbench --governance-root ../governance-root --product-root .
```

Operational rules:

- `serve` requires an explicit governance root and uses the governed configuration to resolve the product root after bootstrap.
- `bootstrap-product` previews changes by default and only writes files when `--apply` is present.
- `doctor`, `list`, and `show` can emit machine-readable JSON with `--json`.
- `list` and `show` stay inside exact-token lookup and bounded metadata filtering; they do not run free-form text search or graph traversal.

## Packaged skill surface

Lantern generates a committed package-default skill surface from the workflow layer. When you modify workflow declarations (workbenches, transaction profiles, or resource manifests), regenerate the skill surface:

```bash
python -c "from lantern.skills.generator import write_packaged_skill_surface; write_packaged_skill_surface()"
```

Or use the provided installation script to set up git hooks that enforce skill freshness on commit:

```bash
cd /path/to/lantern
bash scripts/install_git_hooks.sh
```

The pre-commit hook will:
- Run the full pytest suite
- Regenerate committed skill artifacts if any workflow declarations changed
- Reject commits that would leave skill artifacts stale

## Workflow layer

The machine-readable workflow layer lives under `lantern/workflow/`. See
[`lantern/workflow/README.md`](lantern/workflow/README.md) for a detailed explanation of:

- Which files are authored inputs vs. generated aids
- The layering of Lantern Grammar, workflow declarations, and runtime execution
- Workbench and transaction profile semantics
- How the layer is validated on every load

## MCP server startup

The Lantern MCP server exposes exactly five tools: `inspect`, `orient`, `draft`, `commit`, and `validate`.

The server does not assume a default product path or governance path. Start it with an explicit product root. Pass a governance root when you want companion-governance posture and resource discovery; omitting it keeps the product runnable and surfaces a `missing_governance` workspace posture instead of creating a hard dependency.

When Lantern governs an external product, `--product-root` must point at the governed product repository, not at the Lantern checkout. The executing Lantern package or source checkout provides the workflow release surface; the product repository should carry only product-local identity, local operator contract, bounded launcher scripts, and ignored local MCP wiring.

### Basic startup

```bash
python -m lantern.mcp.server \
  --product-root /path/to/product-repo/ \
  --governance-root /path/to/governance-root/
```

### Minimal tracked bootstrap surface for an external product repo

A fresh governed product repository may contain only the following Lantern-related tracked files:

- `README.md` for product identity and local operating notes
- managed `AGENTS.md`
- a bounded `tools/run-lantern-mcp.sh` launcher that points to an installed Lantern package or external Lantern checkout
- minimal `.gitignore` entries for Python/test/cache artifacts when needed

Repo-local editor or MCP wiring such as `.vscode/mcp.json` should stay ignored and must not be used to vendor Lantern into the product repository.

### Product-only startup

```bash
python -m lantern.mcp.server \
  --product-root /path/to/product-repo/
```

With product-only startup, `inspect(kind="workspace")` reports `missing_governance` posture. No sibling discovery or hidden fallback path is used.

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

Adapt the absolute paths to your local setup and ensure the Python environment can import the `lantern` package.

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

### Tool surface

`inspect` and `orient` provide read-only discovery and posture
resolution against the validated workflow layer:

- `inspect(kind="catalog")` — enumeration of five tools and contract references
- `inspect(kind="contract", contract_ref="...")` — scoped contract definition for a transaction kind
- `inspect(kind="workspace")` — read-only topology and startup-validation posture
- `orient(governance_state, intent, ch_id)` — active workbench set, blockers, and next valid actions

`draft`, `commit`, and `validate` cover governed mutation and verification over the same runtime contract.

### Packaged operator surface

Lantern ships one package-owned thin operator surface under `lantern/skills/packaged_default/`:

- `SKILL.md` — applicability, the first MCP move, the universal discovery sequence, and immutable safety rules only.
- `skill-manifest.json` — mode-first routing keyed by stable logical refs.

The packaged pair does not embed guide or template bodies. Live authoritative content is delivered dynamically through inline `resource_packets` on `orient(...)` and `inspect(kind="contract")`.

## Native MVP smoke path

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
