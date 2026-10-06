# Commerce Brain — Agent Instructions

## How to invoke

The `@commercebrain` prefix is an optional conversational cue:

```
@commercebrain bundle products disappearing from Live Search after resync
```

MCP tools are available whenever configured; the prefix is not an activation or access-control mechanism.

## Use reference tools first

For questions involving Commerce tables, feed columns, indexer IDs, config paths, CLI commands, Elasticsearch fields, or SaaS API structures, call the relevant Commerce Brain reference tool before writing those names or structures.

- Table declarations: `search_db_schema("table_name")` — exact table-name lookup across all bundled `db_schema.xml` declarations. This is source-index data, not a live merchant schema.
- Commerce source/config/CLI: `search_commerce_knowledge("topic")`
- Elasticsearch query patterns: `search_kibana_queries("scenario")`
- SaaS API shapes: `search_saas_schema("API or field")`

If results are missing or stale, say that the bundled reference did not provide the needed information. Do not fabricate source details from memory.

## Investigation boundaries

- For Live Search investigations, start with Commerce source (`search_commerce_knowledge`), then consult Elasticsearch query references (`search_kibana_queries`), and use `search_saas_schema` for SaaS API structures.
- These tools retrieve bundled references. They do not query a merchant database, Elasticsearch cluster, or SaaS API.
- Provide SQL, commands, Kibana queries, and API calls as text for the user to run. Do not execute them unless explicitly asked.
- Keep investigation queries read-only unless the user explicitly asks for a state-changing operation; clearly label any state-changing command.
- Report what supplied query results show. Substitute known values instead of presenting unfilled placeholders.

## Reference search patterns

| Goal | Example |
|---|---|
| Table columns | `search_db_schema("cde_products_feed")` |
| Feed field definitions | `search_commerce_knowledge("cde_products_feed feed schema fields")` |
| Indexer dependencies | `search_commerce_knowledge("catalog_data_exporter_products indexer dependencies")` |
| mview subscriptions | `search_commerce_knowledge("cde_products_feed mview subscriptions")` |
| CLI command | `search_commerce_knowledge("saas resync command")` |
| Elasticsearch query pattern | `search_kibana_queries("product not showing in search")` |
| SaaS API schema | `search_saas_schema("GetProductOverrides request")` |
