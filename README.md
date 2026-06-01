# Commerce Brain

> Search Adobe Commerce source code and Live Search ES queries from inside Claude / Cursor in < 0.1s.

Two MCP tools — no API key, no external services, fully within Adobe infrastructure:

| Tool | What it does |
|------|-------------|
| `search_commerce_knowledge` | BM25 over 529 Commerce source files — table schemas, indexers, feed structures, CLI commands, SQL patterns |
| `search_kibana_queries` | BM25 over Live Search ES query templates and catalog index schema — ready to adapt for Kibana investigation |

---

## Setup (one time, ~10 min)

```bash
git clone https://github.com/ajaycmakwana/commerce-brain ~/commerce-brain
cd ~/commerce-brain
bash setup.sh
```

You'll be prompted for a GitHub PAT with **magento-sparta SAML SSO** access.  
Then restart Claude Code / Cursor.

> **Note:** Cloning the repo also installs `CLAUDE.md` — the agent rules that tell Claude the correct investigation order and query patterns. Do not skip the clone step.

---

## Agent Rules (CLAUDE.md)

The `CLAUDE.md` in the repo root loads automatically when Claude Code's working directory is inside the cloned repo. It tells the agent:

- **Always follow the data flow:** `Magento DB → indexer → cde_products_feed → SaaS → Elasticsearch`  
  Call `search_commerce_knowledge` first, `search_kibana_queries` second.
- **Reason from tool results** — tools return domain knowledge (schemas, query structures). Agent derives SQL/ES queries from them. Does not dump raw XML.
- **Use the right query pattern:** `"cde_products_feed feed schema fields"` not `"cde_products_feed db_schema columns"` — the latter matches test files in BM25.
- **Call the tool first** — do not ask clarifying questions before calling. Get ground truth, then answer with placeholders.

---

## Usage — Live Search Investigation

Ask naturally — agent calls both tools, follows the data flow, constructs the investigation:

- *"Product is missing from Live Search — how to investigate?"*
- *"How to check product in Commerce and ES if it is missing on the frontend?"*
- *"No index was found for this request — what to check?"*
- *"Product has wrong B2B price in Live Search"*

Agent calls `search_commerce_knowledge` → gets feed table schema, indexer dependencies → derives SQL.  
Then calls `search_kibana_queries` → gets ES query patterns → constructs Kibana queries.  
Returns a complete investigation guide grounded in source truth.

---

## Usage — Commerce Source Code

- *"What columns does cde_products_feed have?"*
- *"Which tables does the product feed indexer subscribe to?"*
- *"Show me how SaaS resync command works"*
- *"What CLI commands does Live Search expose?"*

---

## Usage — CLI

```bash
python3 search_cli.py "cde_products_feed feed schema fields"
python3 search_cli.py "saas resync command"
python3 search_cli.py "catalog_data_exporter_products indexer dependencies"
```

---

## What's indexed

### search_commerce_knowledge (529 files from 24 magento-sparta repos)

| File type | Count | What it tells you |
|-----------|-------|-------------------|
| `Console/Command/*.php` | 229 | All CLI commands and their logic |
| `etc/db_schema.xml` | 159 | Table columns, types, foreign keys |
| `Model/Query/*.php` | 64 | DB query builders — exact SELECT patterns |
| `etc/indexer.xml` | 25 | Indexer IDs, classes, dependencies |
| `etc/mview.xml` | 25 | Which tables trigger which indexer |
| `etc/et_schema.xml` | 17 | Feed field definitions sent to SaaS |
| `commerce_queries/*.md` | 10 | SQL investigation patterns for feed tables |

### search_kibana_queries (92 chunks)

| Source | Chunks | What it provides |
|--------|--------|-----------------|
| `kibana/queries/query_templates.md` | 78 | ES query structures for catalog_1_* indexes |
| `kibana/schema/catalog_index_schema.md` | 14 | Field types, nesting rules, schema gotchas |

---

## Refresh index (after repos updated)

```bash
bash setup.sh   # re-runs clone + index build for both Commerce Brain and Kibana Brain
```

---

## Files

| File | Purpose |
|------|---------|
| `mcp_server.py` | MCP stdio server — exposes both tools |
| `setup.sh` | One-command setup |
| `index_build.py` | Builds `commerce_brain.pkl` from cloned repos |
| `kibana_index_build.py` | Builds `kibana_brain.pkl` from kibana/ docs |
| `search_cli.py` | Terminal search tool for local testing |
| `CLAUDE.md` | Agent rules — investigation order, query patterns, reasoning guidance |
| `commerce_queries/` | SQL investigation query patterns |
| `kibana/` | ES query templates and catalog index schema |
| `commerce_brain.pkl` | Commerce BM25 index (generated, not committed) |
| `kibana_brain.pkl` | Kibana BM25 index (generated, not committed) |
