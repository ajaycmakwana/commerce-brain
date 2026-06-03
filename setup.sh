#!/bin/bash
# Commerce Brain — One-time setup
# Clones 24 Commerce repos, builds BM25 index, configures MCP
# Run once: bash setup.sh

set -e

BRAIN_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Commerce Brain setup: $BRAIN_DIR"
echo ""

# ── 1. Python dependency ──────────────────────────────────────────────────────
echo "[1/4] Checking Python dependencies..."
python3 -c "import rank_bm25" 2>/dev/null || {
    echo "  Installing rank-bm25..."
    pip3 install rank-bm25 --quiet
}
echo "  OK"

# ── 2. Clone repos ───────────────────────────────────────────────────────────
echo ""
echo "[2/4] Cloning Commerce repos (shallow, ~25 repos)..."
echo "      Requires GitHub PAT with magento-sparta SSO access."
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo -n "  Enter your GitHub PAT (or set GITHUB_TOKEN env var): "
    read -r GITHUB_TOKEN
fi

ORG="https://$GITHUB_TOKEN@github.com/magento-sparta"

clone_or_update() {
    local repo=$1 branch=$2
    if [ -d "$BRAIN_DIR/$repo" ]; then
        echo "  ↑ Updating $repo..."
        git -C "$BRAIN_DIR/$repo" fetch --depth 1 origin "$branch" -q
        git -C "$BRAIN_DIR/$repo" reset --hard "origin/$branch" -q
    else
        echo "  ↓ Cloning $repo ($branch)..."
        git clone "$ORG/$repo" "$BRAIN_DIR/$repo" --branch "$branch" --depth 1 -q
    fi
}

clone_or_update magento2ce                        2.4-develop
clone_or_update magento2ee                        2.4-develop
clone_or_update magento2b2b                       develop
clone_or_update inventory                         develop
clone_or_update commerce-data-export              main
clone_or_update commerce-data-export-ee           main
clone_or_update magento-live-search               main
clone_or_update magento-product-recommendations   main
clone_or_update magento-product-recommendations-admin main
clone_or_update magento-catalog-sync-admin        main
clone_or_update saas-export                       main
clone_or_update data-services                     main
clone_or_update data-services-graphql             master
clone_or_update services-connector                main
clone_or_update services-id                       main
clone_or_update adobe-stock-integration           develop
clone_or_update adobe-ims                         develop
clone_or_update magento2-page-builder             develop
clone_or_update magento2-page-builder-ee          develop
clone_or_update magento2-payments                 main
clone_or_update ext-braintree                     master
clone_or_update security-package                  develop
clone_or_update security-package-b2b              develop
clone_or_update security-package-ee               1.0-develop

# ── 3. Build BM25 indexes ────────────────────────────────────────────────────
echo ""
echo "[3/4] Building BM25 indexes..."
python3 "$BRAIN_DIR/index_build.py"
python3 "$BRAIN_DIR/kibana_index_build.py"

# ── 4. Configure MCP ─────────────────────────────────────────────────────────
echo ""
echo "[4/4] Configuring MCP..."

MCP_SERVER="$BRAIN_DIR/mcp_server.py"


CURSOR_MCP="$HOME/.cursor/mcp.json"
CLAUDE_MCP="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

add_to_mcp() {
    local cfg=$1
    if [ ! -f "$cfg" ]; then
        mkdir -p "$(dirname "$cfg")"
        echo '{"mcpServers":{}}' > "$cfg"
    fi
    if grep -q "commerce-brain" "$cfg" 2>/dev/null; then
        echo "  Already configured: $cfg"
    else
        python3 - "$cfg" "$MCP_SERVER" <<'EOF'
import json, sys
cfg_path, server_path = sys.argv[1], sys.argv[2]
with open(cfg_path) as f:
    cfg = json.load(f)
cfg.setdefault("mcpServers", {})["commerce-brain"] = {
    "command": "python3",
    "args": [server_path]
}
with open(cfg_path, "w") as f:
    json.dump(cfg, f, indent=2)
print(f"  Added commerce-brain to: {cfg_path}")
EOF
    fi
}

[ -d "$HOME/.cursor" ] && add_to_mcp "$CURSOR_MCP"
[ -d "$HOME/Library/Application Support/Claude" ] && add_to_mcp "$CLAUDE_MCP"

# ── 5. Configure Claude Code hook ────────────────────────────────────────────
echo ""
echo "[5/6] Configuring Claude Code auto-search hook..."

CLAUDE_CODE_SETTINGS="$HOME/.claude/settings.json"
AUTO_SEARCH="$BRAIN_DIR/auto_search.py"

if [ ! -f "$CLAUDE_CODE_SETTINGS" ]; then
    mkdir -p "$HOME/.claude"
    echo '{}' > "$CLAUDE_CODE_SETTINGS"
fi

if grep -q "auto_search.py" "$CLAUDE_CODE_SETTINGS" 2>/dev/null; then
    echo "  Hook already configured: $CLAUDE_CODE_SETTINGS"
else
    python3 - "$CLAUDE_CODE_SETTINGS" "$AUTO_SEARCH" <<'EOF'
import json, sys
cfg_path, hook_script = sys.argv[1], sys.argv[2]
with open(cfg_path) as f:
    cfg = json.load(f)
cfg.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
hook_entry = {
    "matcher": "",
    "hooks": [{"type": "command", "command": f"python3 {hook_script}"}]
}
if not any(
    any(h.get("command", "").endswith("auto_search.py") for h in e.get("hooks", []))
    for e in cfg["hooks"]["UserPromptSubmit"]
):
    cfg["hooks"]["UserPromptSubmit"].append(hook_entry)
    with open(cfg_path, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"  Added auto-search hook to: {cfg_path}")
else:
    print(f"  Hook already present: {cfg_path}")
EOF
fi

# ── 6. Configure global Claude Code CLAUDE.md ────────────────────────────────
echo ""
echo "[6/6] Configuring global Claude Code rules (~/.claude/CLAUDE.md)..."

GLOBAL_CLAUDE_MD="$HOME/.claude/CLAUDE.md"
mkdir -p "$HOME/.claude"

if grep -q "Commerce Brain — Investigation Rules" "$GLOBAL_CLAUDE_MD" 2>/dev/null; then
    echo "  Commerce Brain rules already present: $GLOBAL_CLAUDE_MD"
else
    cat >> "$GLOBAL_CLAUDE_MD" <<'RULES'

## Commerce Brain — Investigation Rules

These rules apply ONLY when the user starts their message with `@commercebrain`, or when COMMERCE BRAIN AUTO-CONTEXT is present in context.

1. **Call knowledge tools first** — before writing any table name, column, field, or query, call `search_commerce_knowledge`, `search_kibana_queries`, or `search_saas_schema`. Never answer Commerce-specific questions from training knowledge.
1a. **`search_db_schema` is mandatory before any SQL** — Call `search_db_schema(table_name)` for EVERY table in the query. Do NOT write a column name without a confirmed schema. On EE, join fields differ from CE — only `search_db_schema` gives the correct column names.
2. **Never execute autonomously** — provide SQL, CLI commands, Kibana queries, and API calls as text for the user to run. Never call `grpc_*`, `ls_product_search`, `cs_products_by_sku`, Bash, or live tools unless explicitly asked.
3. **Read-only** — never run INSERT, UPDATE, DELETE, DROP, TRUNCATE. CLI commands that modify state (`saas:resync`, `indexer:reindex`, `cache:flush`, etc.) are write operations — provide as text only when explicitly asked, clearly labeled as data-modifying.
4. **Report data, don't judge** — report what results show; do not compare against training expectations.
5. **Substitute values** — never present queries with unfilled placeholders like `<entity_id>`.
RULES
    echo "  Added Commerce Brain rules to: $GLOBAL_CLAUDE_MD"
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "  Commerce Brain is ready!"
echo ""
echo "  Restart Claude Code to activate the hook + MCP."
echo ""
echo "  Test in terminal:"
echo "    python3 $BRAIN_DIR/search_cli.py \"cde_products_feed columns\""
echo "══════════════════════════════════════════════════════"
