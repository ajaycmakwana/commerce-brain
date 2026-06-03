# Commerce Brain — Agent Instructions

## Rule 1 — Call the tool. Always. Before writing anything.

For ANY question involving Commerce tables, feed columns, indexer IDs, config paths, CLI commands, ES field names, or query structures:

**Call the tool first. Then answer.**

Do NOT write a table name, column name, field path, or query from training knowledge. Training knowledge is wrong for Commerce-specific details — it hallucinates column names, uses wrong join fields, guesses config paths.

- Need a table schema or column names? → `search_db_schema("{table_name}")` — exact lookup, returns columns, types, constraints
- Need an ES query? → `search_kibana_queries("{scenario}")`
- Need a SaaS API structure? → `search_saas_schema("{api or field name}")`
- Need a config path? → `search_commerce_knowledge("{module} config path")`

If the tool returns nothing useful, say "I couldn't find this in Commerce Brain" — do NOT fall back to training knowledge.

## Rule 2 — Never execute queries or API calls unless the user explicitly asks.

Investigation = providing queries and commands for the user to run. NOT running them yourself.

- **Knowledge tools** (`search_commerce_knowledge`, `search_kibana_queries`, `search_saas_schema`) — call these autonomously to look up schemas and patterns.
- **Everything else** — SQL queries, Bash commands, `adobe-saas-tools` (`grpc_*`, `ls_product_search`, `cs_products_by_sku`, etc.), Kibana queries — present them to the user. Do NOT execute them unless the user explicitly says "run this" or "execute this".

Default behavior: provide the query → user runs it → user shares results → you analyze.

## Rule 3 — Read-only. Always.

All SQL and API calls are read-only. Never run INSERT, UPDATE, DELETE, DROP, TRUNCATE. Never call any tool or API that modifies data. Provide write queries as text only when the user explicitly asks for them.

## Rule 3 — Report data, don't judge it.

Report what the query result shows. Do NOT compare against expectations from training data. Field counts, row shapes, and JSON structures vary by Commerce version and environment — you do not know what "normal" looks like.

## Rule 4 — Substitute values before presenting queries.

Never show a query with unfilled placeholders like `<entity_id>` or `{PRODUCT_ID}`. Substitute actual values from the conversation. If a value isn't known yet, say so.

---

## Investigation order — follow the data flow

```
Magento DB → indexer → cde_products_feed → SaaS export → Elasticsearch
```

1. Call `search_commerce_knowledge` FIRST — check Commerce source: indexer, feed table, data exporter
2. Call `search_kibana_queries` SECOND — verify whether data reached the ES index
3. Call `search_saas_schema` for SaaS API structure (CS GraphQL, gRPC, PREX REST)

Never start from Kibana. Always start from Commerce and follow the flow forward.

---

## search_commerce_knowledge — query patterns

| What you need | Query to use |
|---|---|
| Table columns | `"{table_name} feed schema fields"` — e.g. `"cde_products_feed feed schema fields"` |
| Indexer dependencies | `"{indexer_id} indexer dependencies"` |
| Changelog / mview subscriptions | `"{table_name} mview subscriptions"` |
| CLI command | `"{command_name} command saas resync"` |
| Feed field definitions | `"et_schema {feed_name} feed fields"` |
| Query model / SELECT pattern | `"{topic} query model select php"` |

Do NOT use `"db_schema columns"` — BM25 matches that against test files. Use `"feed schema fields"` instead.

## search_kibana_queries — what it covers

| Query type | Example |
|---|---|
| Product visibility / displayability | `"product not showing in search"` |
| Index existence and health | `"product missing from index"` |
| B2B price / customer group | `"B2B price for customer group"` |
| Category membership | `"product not in expected category"` |
| Staleness / reindex | `"when was product last indexed"` |
| Field schema and nesting rules | `"filterable nested query"` |
| Stock, product type, variants | `"configurable product missing children"` |

## search_saas_schema — what it covers

| Query type | Example |
|---|---|
| CS/LS GraphQL query structure | `"productSearch filter args"` |
| gRPC method and request fields | `"GetProductOverrides request"` |
| PREX REST endpoints | `"recommendations REST request body"` |
| Response field names | `"products skus response shape"` |
| Customer group SHA1 | `"customer group SHA1"` |
