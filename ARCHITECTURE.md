# Commerce Brain — Architecture

## Runtime

```text
MCP client (Copilot / Claude / Cursor / VS Code)
        │ JSON-RPC over stdio
        ▼
mcp_server.py
        │ HTTPS request to the configured App Builder stage endpoint
        ├── /search          ── Commerce BM25 index bundled in search action
        ├── /search-kibana   ── Kibana BM25 index bundled in action
        └── /search-saas     ── SaaS BM25 index bundled in action
```

The MCP server uses only Python's standard library. It validates JSON-RPC requests and tool arguments, and returns protocol errors or safe tool errors rather than terminating on malformed input. `search_db_schema` uses the Commerce action's exact table-name path: it scans all bundled `db_schema` documents for exact suffix matches, without BM25 ranking or a result limit, and retains each declaration's source path.

The actions use BM25 scoring with the existing `k1=1.5` and `b=0.75` values. Export builds per-document term-frequency maps once; the action's shared scoring helper consumes those maps and falls back to token counting for older indexes. Regular search continues to return bounded content excerpts; `db_schema` declarations are exported in full.

These APIs return reference documents only. They do not run SQL/CLI commands, query merchant data, or connect to a merchant's Elasticsearch or SaaS services. The stage action configuration retains `require-adobe-auth: false` as requested for internal team use; this is not an access-control perimeter.

`auto_search.py` is an optional Claude Code prompt hook. It is not required to activate or authorize the MCP server, and the MCP tools work without an `@commercebrain` flag.

## Index build and provenance

```text
COMMERCE_BRAIN_SOURCE_DIR (default: ./sources)
  ├─ Commerce source checkouts ── index_build.py ── commerce_brain.pkl
  │                                               └─ export_index_json.py
  ├─ kibana/ references ───────── kibana_index_build.py ─ export_kibana_json.py
  └─ saas-schema/ references ──── saas_index_build.py ─── export_saas_json.py
                                                        │
                          build_indexes.py ──────────────┘
                               ├─ app-builder/actions/search/index.json
                               ├─ app-builder/actions/search-kibana/index.json
                               ├─ app-builder/actions/search-saas/index.json
                               └─ app-builder/index-manifest.json
```

`index_metadata.py` records index format/build versions, build time, locally observable Git refs and commit IDs, and source-checkout dirty state. Missing source version data is represented as `null` and marked unavailable/partial; no source version is inferred. The manifest records each bundled artifact's SHA-256 and document count. Generated indexes, sources, and manifests are ignored by Git.

The complete local build is `python3 build_indexes.py` (or `bash setup.sh`, which also prepares source checkouts). `python3 verify_indexes.py` verifies the generated bundle and manifest. Neither command deploys. App Builder actions import their JSON index at build time; an Adobe I/O Files upload does not update these bundles and is not part of the supported pipeline.

## Configuration and rollout

`install.sh` configures only explicitly selected client files and atomically merges the MCP server entry into the correct JSON schema. It preserves all unrelated settings and updates stale Commerce Brain entries.

Deployment is separate from index generation. Verify generated provenance and SHA-256 values, obtain the required deployment approval, then deploy the App Builder project using its stage workflow. Confirm action health and all three search paths before promoting any release. To roll back, redeploy the prior known-good App Builder source and matching bundled action indexes together; use the prior manifest to verify the restored artifact hashes. Keep a copy of the prior bundle and manifest through rollout.
