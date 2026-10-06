# Commerce Brain

Commerce Brain provides BM25 search over bundled Adobe Commerce source references, Live Search Elasticsearch query examples, and Adobe Commerce SaaS API schemas. Clients connect to the MCP stdio server; search is performed by the configured Adobe I/O Runtime (App Builder) actions against JSON indexes bundled with those actions.

The tools return reference material. They do not query a merchant database, Elasticsearch cluster, or SaaS API, and they do not execute SQL or commands. The stage actions are configured with `require-adobe-auth: false` for the intended internal team use; that setting is not perimeter access control.

## Install an MCP client

Python 3 is required. Clone this repository, then select the client(s) to configure:

```bash
git clone https://github.com/ajaycmakwana/commerce-brain.git
cd commerce-brain
bash install.sh copilot
# Or select more than one: bash install.sh copilot,claude-code,vscode
```

The installer preserves unrelated JSON settings, replaces a stale `commerce-brain` entry, and writes atomically. It configures only the selected client:

| Client | Configuration file | MCP server section |
|---|---|---|
| Copilot app/CLI | `~/.copilot/mcp-config.json` | `mcpServers` |
| Claude Code | `~/.claude.json` | `mcpServers` |
| Claude Desktop | platform-specific Claude config | `mcpServers` |
| Cursor | `~/.cursor/mcp.json` | `mcpServers` |
| VS Code | platform-specific user `settings.json` | `mcp.servers` |

The Claude Code installer does not put `mcpServers` in `~/.claude/settings.json`. Restart the selected client after installation. The MCP server uses Python's standard library; no per-user index or Python search package is needed.

For local Commerce-index maintainer checks after a build, `python3 search_cli.py "cde_products_feed columns"` searches the local Commerce pickle. It is not an MCP runtime path.

## Available tools

- `search_commerce_knowledge` — BM25 search over Commerce source, feed, indexer, mview, CLI, and query references.
- `search_db_schema` — exact table-name lookup across every matching `db_schema.xml` table declaration, including source path and repository provenance. Results are not limited by BM25 ranking.
- `search_kibana_queries` — BM25 search over Live Search Elasticsearch query examples and catalog-index reference material.
- `search_saas_schema` — BM25 search over CS/Live Search GraphQL, CS gRPC, and PREX REST reference material.

Exact table lookup is for source declarations in the built index, not a live merchant schema. The index can be out of date; check the generated manifest's source commit/ref and timestamp before relying on it.

## Refresh and bundle all indexes

An index maintainer needs Git access to the source repositories and Python with `rank-bm25`. Setup clones sources to `./sources` by default. Set `COMMERCE_BRAIN_SOURCE_DIR` to use another local source directory. Existing clean checkouts are only fast-forwarded on their current configured branch when Git proves the update is a fast-forward; dirty, detached, divergent, or non-target checkouts are left unchanged and reported.

```bash
bash setup.sh
```

`setup.sh` runs the complete local pipeline: build Commerce, Kibana, and SaaS BM25 indexes; export all three; copy them to their respective App Builder action bundles; write `app-builder/index-manifest.json`; and verify bundle hashes and structure. It does **not** deploy.

To run individual stages, use `index_build.py`, `kibana_index_build.py`, or `saas_index_build.py`, followed by the corresponding `export_*_json.py`. For the supported all-index workflow, prefer `python3 build_indexes.py`; verify artifacts with `python3 verify_indexes.py`.

Commerce table schema chunks are exported in full. Other document content remains bounded for ordinary search. The shared action scorer uses term frequencies precomputed in the export while preserving the existing BM25 parameters and ranking behavior. Index metadata includes format/build version, build time, available source refs/commits, and source-checkout dirty state.

## Deployment

Deployment is a separate, explicitly approved operation. Follow [DEPLOYMENT.md](DEPLOYMENT.md) for preflight, stage rollout order, version checks, and rollback. No build script deploys or uploads an index.

## Repository map

| Path | Purpose |
|---|---|
| `mcp_server.py` | MCP JSON-RPC stdio server |
| `install.sh` | Explicit, client-specific MCP configuration installer |
| `setup.sh` / `build_indexes.py` | Safe source checkout refresh and all-index build/bundle pipeline |
| `index_build.py`, `kibana_index_build.py`, `saas_index_build.py` | Source document collection and BM25 pickle builds |
| `export_*_json.py`, `index_export.py` | Versioned JSON export with full schema declarations |
| `verify_indexes.py` | Bundle/manifest preflight checks |
| `app-builder/actions/` | Runtime search actions and bundled indexes (generated/ignored) |
| `CLAUDE.md` | Commerce Brain agent usage guidance |
| `WIKI.md` | Proposed replacement text for the internal wiki page |
