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

The companion governance workspace (`lantern-governance/`) lives in a separate sibling repository and is the authoritative SSOT for all governed artifacts. Do not create or edit governed records or `binding_record.md` in this repository.

## Getting started

```bash
pip install -e ".[dev]"
pytest
```

All tests should pass without requiring external configuration.

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

### Basic startup

```bash
python -m lantern.mcp.server \
  --product-root /path/to/lantern/ \
  --governance-root /path/to/lantern-governance/
```

### Product-only startup

```bash
python -m lantern.mcp.server \
  --product-root /path/to/lantern/
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
        "/path/to/lantern/",
        "--governance-root",
        "/path/to/lantern-governance/"
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

[mcp_servers.lantern_governance]
command = "python"
args = [
  "-m",
  "lantern.mcp.server",
  "--product-root",
  "/path/to/lantern/",
  "--governance-root",
  "/path/to/lantern-governance/"
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

`draft`, `commit`, and `validate` mutation behavior is delivered in CH-0004.
