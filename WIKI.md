# Commerce Brain — Wiki

> **Maintainer:** Ajay Makwana (@makwana)
> **Created:** May 2026

---

## What is Commerce Brain?

Commerce Brain is a BM25 search engine over Adobe Commerce source code, exposed as:
- An **MCP tool** (`search_commerce_knowledge`) for Claude / Cursor AI agents
- A **Web UI** for anyone to search in the browser
- A **CLI tool** for local terminal search

It indexes high-signal files from magento-sparta repos related to magento modules and returns real source-of-truth results in under 1 second — no hallucination, no API key, fully within Adobe infrastructure.

---

## Why does this exist?

During merchant issue investigations, engineers waste hours manually tracing source code:
- "What columns does `cde_products_feed` have?"
- "Which indexers need to run before product sync?"
- "How does the SaaS resync command work?"

Without Commerce Brain, Claude guesses from training data → **wrong answers**.

**Example of hallucination (before):**
> Claude: `cde_products_feed` has a `sku` column and a `store_view_code` column.
> Reality: Neither column exists.

**With Commerce Brain:**
> Claude calls `search_commerce_knowledge("cde_products_feed db_schema columns")` → returns the actual `db_schema.xml` → gives the correct 10 columns.

---

## Architecture

```
Claude / Cursor Agent
        │
        │  search_commerce_knowledge("query")
        ▼
mcp_server.py  (local, ~110 lines, zero dependencies)
        │
        │  HTTP GET
        ▼
App Builder Action  (Adobe I/O Runtime - staging)
https://development-200136-commercebrain-stage.dev.runtime.adobe.io
/api/v1/web/app-builder/search
        │
        │  BM25 scoring over bundled index
        ▼
Returns top-5 source file snippets
```

### Index build pipeline (run by maintainer)

```
24 magento-sparta repos  →  index_build.py  →  commerce_brain.pkl
                         →  export_index_json.py  →  commerce_brain_index.json
                         →  aio app deploy  →  App Builder (bundled)
```

---

## What's Indexed

| File Type | Count | What it tells you |
|-----------|-------|-------------------|
| `Console/Command/*.php` | 229 | All CLI commands and their options/logic |
| `etc/db_schema.xml` | 159 | Table columns, types, indexes, foreign keys |
| `Model/Query/*.php` | 64 | DB query builders — exact SELECT patterns |
| `etc/indexer.xml` | 25 | Indexer IDs, classes, dependencies |
| `etc/mview.xml` | 25 | Which DB tables trigger which indexer |
| `etc/et_schema.xml` | 17 | Feed field definitions (what goes to SaaS) |

### Repos covered (24 total)

| Category | Repos |
|----------|-------|
| Core Commerce | magento2ce, magento2ee, magento2b2b, inventory |
| SaaS / Data Export | commerce-data-export, commerce-data-export-ee, saas-export, data-services, data-services-graphql |
| Live Search / PREX | magento-live-search, magento-product-recommendations, magento-product-recommendations-admin, magento-catalog-sync-admin |
| Services | services-connector, services-id |
| Extensions | adobe-stock-integration, adobe-ims, magento2-page-builder, magento2-page-builder-ee, magento2-payments, ext-braintree |
| Security | security-package, security-package-b2b, security-package-ee |

---

## Setup

### Option A — MCP only (recommended for teammates)

You only need one file and one config entry. No repos, no Python packages.

**1. Get `mcp_server.py`**
```bash
# Copy from makwana or clone the repo
cp /path/from/makwana/mcp_server.py ~/commerce-brain/mcp_server.py
```

**2. Add to Claude Code (`~/.claude.json`)**
```json
"mcpServers": {
  "commerce-brain": {
    "type": "stdio",
    "command": "python3",
    "args": ["/path/to/mcp_server.py"]
  }
}
```

**3. Add to Cursor (`~/.cursor/mcp.json`)**
```json
"mcpServers": {
  "commerce-brain": {
    "command": "python3",
    "args": ["/path/to/mcp_server.py"]
  }
}
```

Restart Claude Code / Cursor. Done.

---

### Option B — Full local setup (for index refresh / development)

**Requirements:** Python 3.9+, GitHub PAT with magento-sparta SSO

```bash
git clone <repo> commerce-brain
cd commerce-brain
bash setup.sh   # prompts for GitHub PAT
# restart Cursor / Claude Code
```

`setup.sh` does:
1. Installs `rank-bm25` (pip)
2. Clones all 24 repos (shallow, `--depth 1`)
3. Builds BM25 index (`commerce_brain.pkl`)
4. Configures MCP in Cursor + Claude Desktop

---

## Usage

### In Claude / Cursor (MCP)

The tool is available automatically once configured. Claude calls it when you ask Commerce source code questions.

**Ask naturally:**
- *"What columns does `cde_products_feed` have?"*
- *"Which tables trigger the product feed indexer?"*
- *"Show me how the SaaS resync CLI command works"*
- *"What are the dependencies of `catalog_data_exporter_products`?"*

**Or explicitly:**
> Use `search_commerce_knowledge` to find the `cde_products_feed` table structure.

### Web UI (browser)

Open in browser — no login required:
```
https://development-200136-commercebrain-stage.dev.runtime.adobe.io/index.html
```

- Type a query and press Enter
- Click example chips for common queries
- Click any result card to expand the full source

### REST API

```bash
curl "https://development-200136-commercebrain-stage.dev.runtime.adobe.io\
/api/v1/web/app-builder/search?query=cde_products_feed+columns&top_k=5"
```

Response:
```json
{
  "query": "cde_products_feed columns",
  "count": 5,
  "results": [
    {
      "score": 20.23,
      "repo": "commerce-data-export",
      "file_type": "db_schema",
      "path": "commerce-data-export/CatalogDataExporter/etc/db_schema.xml",
      "content": "..."
    }
  ]
}
```

### CLI (local only)

```bash
python3 search_cli.py "cde_products_feed columns"
python3 search_cli.py "saas resync command"
python3 search_cli.py "live search indexer class"
```

---

## Query Tips

| Goal | Query example |
|------|--------------|
| Table columns | `cde_products_feed feed schema fields product` |
| Indexer dependencies | `catalog_data_exporter_products indexer dependencies` |
| mview subscriptions | `cde_products_feed mview subscriptions tables` |
| CLI command | `saas resync command sync feed` |
| Feed fields | `et_schema product attributes feed` |
| Query model | `product price query select` |

**Tip:** Adding the file type to the query (`db_schema`, `mview`, `indexer`, `command`) improves BM25 precision.

---

## Refresh Index (after repos updated)

Run by maintainer (@makwana):

```bash
cd /Users/makwana/Claude/Ideas/commerce-brain

# 1. Update all repos
bash setup.sh

# 2. Rebuild BM25 index
python3 index_build.py

# 3. Export to JSON for App Builder
python3 export_index_json.py

# 4. Redeploy to App Builder
cp commerce_brain_index.json app-builder/actions/search/index.json
cd app-builder
AIO_CLI_ENV=stage aio app deploy
```

---

## Files

| File | Purpose |
|------|---------|
| `mcp_server.py` | MCP stdio server — the only file teammates need |
| `setup.sh` | One-command full local setup |
| `index_build.py` | Builds `commerce_brain.pkl` from cloned repos |
| `export_index_json.py` | Exports pickle → JSON for App Builder |
| `search_cli.py` | Terminal search for local testing |
| `commerce_brain.pkl` | Local BM25 index (Python, not committed) |
| `commerce_brain_index.json` | JSON index for App Builder (not committed) |
| `app-builder/` | Adobe I/O App Builder project |
| `app-builder/actions/search/index.js` | Search web action (Node.js, inline BM25) |
| `app-builder/web-src/` | React web UI |
| `CLAUDE.md` | Instructions for Claude agents in this workspace |

---

## Troubleshooting

**MCP tool not appearing in Claude:**
- Restart Claude Code fully (quit + reopen), not just a new tab
- Check `~/.claude.json` has the `commerce-brain` entry under `mcpServers`
- Verify: `python3 mcp_server.py` starts without errors

**Wrong results / missing columns:**
- Add file type to query: `"cde_products_feed db_schema feed schema fields"`
- The more specific the query, the better BM25 precision

**App Builder endpoint down:**
- Contact @makwana to redeploy: `AIO_CLI_ENV=stage aio app deploy`
- Fallback: use local `search_cli.py` if repos are cloned

**Index outdated:**
- Repos are shallow clones — ask @makwana to refresh and redeploy

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Search algorithm | BM25 (rank-bm25) | No ML model, no API key, great for code/XML |
| Hosting | Adobe I/O Runtime (App Builder) | Adobe-internal, no external services |
| Index format | JSON (bundled in action) | No storage service needed |
| MCP protocol | JSON-RPC over stdio | Standard Claude/Cursor tool interface |
| Web UI | React (App Builder web-src) | Served from Adobe CDN |

---

*Questions or issues → ping @makwana on Slack*
