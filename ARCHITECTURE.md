# Commerce Brain — Architecture Decisions

## Non-negotiable principles

**Before declaring any change "done", verify these hold across the entire system.**

### 1. All runtime access goes through App Builder
Every tool, hook, and search operation calls the App Builder endpoints at runtime.
Local pkl files are build artifacts only — they exist to export JSON for App Builder deployment.
They are NEVER loaded at runtime by any user-facing component.

- `mcp_server.py` → App Builder (all 4 tools)
- `auto_search.py` → App Builder (hook injection)
- `search_cli.py` → local pkl (maintainer tool only, not user-facing)

### 2. App Builder endpoints
```
BASE: https://development-200136-commercebrain-stage.dev.runtime.adobe.io/api/v1/web/app-builder

/search          — Commerce Brain (source code, db_schema, indexers, CLI)
/search-kibana   — Kibana Brain (ES query templates, catalog index schema)
/search-saas     — SaaS Brain (CS GraphQL, gRPC, PREX REST schema)
```

### 3. @commercebrain is the activation trigger
- Hook fires ONLY when `@commercebrain` is in the prompt
- Hook writes `/tmp/commerce_brain_active` flag (TTL: 30 min)
- MCP tools check flag before responding — inactive without it

### 4. No local build needed for users
Users only run `setup.sh` to configure files. They do NOT build indexes.
Index building is a maintainer-only operation when source code changes.

### 5. setup.sh responsibilities (user setup)
1. Install rank-bm25 (needed for maintainer index builds, harmless for users)
2. Clone repos → `~/Claude/commerce-brain-resources/` (maintainer only, skippable)
3. Configure MCP in `~/.claude.json`
4. Configure hook in `~/.claude/settings.json`
5. Configure `~/.claude/CLAUDE.md`
6. Install `/commercebrain` slash command

### 6. When any change is made
Check: does this change need to be applied to BOTH `mcp_server.py` AND `auto_search.py`?
They are the two runtime entry points. They must stay in sync.
