# Commerce Brain

> Search Adobe Commerce source code from inside Claude / Cursor in < 0.1s.

BM25 index over high-signal files from 24 magento-sparta repos:
`db_schema.xml`, `et_schema.xml`, `mview.xml`, `indexer.xml`, `Model/Query/*.php`, `Console/Command/*.php`

---

## Setup (one time, ~10 min)

```bash
git clone <this-repo> commerce-brain
cd commerce-brain
bash setup.sh
```

You'll be prompted for a GitHub PAT that has **magento-sparta SAML SSO** access.
Then restart Cursor / Claude Desktop.

---

## Usage — in Claude / Cursor

The tool `search_commerce_knowledge` is available automatically once MCP is active.

**Example prompts:**

- *"What columns does cde_products_feed have?"*
- *"Which tables does the product feed indexer subscribe to?"*
- *"Show me how SaaS resync command works"*
- *"What CLI commands does Live Search expose?"*

Claude will call `search_commerce_knowledge(query)` and get real source-of-truth results.

---

## Usage — CLI

```bash
python3 search_cli.py "cde_products_feed columns"
python3 search_cli.py "saas resync command"
python3 search_cli.py "live search indexer"
```

---

## Refresh index (after repos updated)

```bash
bash setup.sh   # re-runs clone + index steps
```

---

## What's indexed

| File type | Count | What it tells you |
|-----------|-------|-------------------|
| `db_schema.xml` | 159 | Actual table columns, types, indexes |
| `Console/Command/*.php` | 229 | All CLI commands and their logic |
| `Model/Query/*.php` | 64 | DB query builders — exact SELECT patterns |
| `indexer.xml` | 25 | Indexer IDs, classes, dependencies |
| `mview.xml` | 25 | Which tables trigger which indexer |
| `et_schema.xml` | 17 | Feed field definitions |

---

## Files

| File | Purpose |
|------|---------|
| `setup.sh` | One-command setup |
| `index_build.py` | Builds `commerce_brain.pkl` from cloned repos |
| `mcp_server.py` | MCP stdio server — exposes `search_commerce_knowledge` |
| `search_cli.py` | Terminal search tool for testing |
| `commerce_brain.pkl` | BM25 index (generated, not committed) |
