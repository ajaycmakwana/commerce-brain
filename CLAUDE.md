# Commerce Brain — Agent Instructions

## Investigation order — always follow the data flow

```
Magento DB → indexer → cde_products_feed → SaaS export → Elasticsearch
```

1. Call `search_commerce_knowledge` FIRST — check Commerce source: indexer, feed table, data exporter
2. Call `search_kibana_queries` SECOND — verify whether data reached the ES index
- Never start from Kibana. Always start from Commerce and follow the flow forward.
- For pure index-state questions where Commerce side is already confirmed healthy — `search_kibana_queries` alone is acceptable.

## How to use tool results

The tools return domain knowledge: table schemas, query structures, field types, indexer configs, SQL/ES examples.
Use this to UNDERSTAND the domain, then construct the right answer for the specific question.
Do NOT dump raw tool output. Do NOT hardcode answers. Reason from what the tool returns.

- Tool returns `db_schema.xml` with column `source_entity_id` → construct `SELECT ... FROM cde_products_feed WHERE source_entity_id = {PRODUCT_ID}`
- Tool returns ES query showing `nested` path for `filterable` → construct the right nested ES query for the user's specific attribute
- Do NOT ask the user clarifying questions before calling the tool — call the tool first, get the ground truth, then answer with placeholders

## search_commerce_knowledge — query patterns

| What you need | Query to use |
|---|---|
| Table columns | `"{table_name} feed schema fields"` — e.g. `"cde_products_feed feed schema fields"` |
| Indexer dependencies | `"{indexer_id} indexer dependencies"` — e.g. `"catalog_data_exporter_products indexer dependencies"` |
| Changelog / mview subscriptions | `"{table_name} mview subscriptions"` — e.g. `"cde_products_feed mview subscriptions"` |
| CLI command | `"{command_name} command saas resync"` |
| Feed field definitions | `"et_schema {feed_name} feed fields"` |
| Query model / SELECT pattern | `"{topic} query model select php"` |

Do NOT use `"db_schema columns"` as a suffix — BM25 matches that against test files. Use `"feed schema fields"` instead.

## search_commerce_knowledge — what it covers

| Query type | Example |
|---|---|
| Table columns | `"cde_products_feed feed schema fields"` |
| Feed structure | `"et_schema product feed fields"` |
| Indexer class / dependencies | `"catalog_data_exporter_products indexer"` |
| Which tables trigger an indexer | `"cde_products_feed mview subscriptions"` |
| CLI command source | `"saas resync command"` |
| DB query builders | `"product price query model"` |

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
