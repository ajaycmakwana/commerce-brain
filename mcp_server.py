#!/usr/bin/env python3
"""
Commerce Brain MCP Server
All 4 tools call the App Builder endpoints — no local pkl at runtime.

Usage: python3 mcp_server.py
MCP config entry:
  {
    "commerce-brain": {
      "command": "python3",
      "args": ["/path/to/commerce-brain/mcp_server.py"]
    }
  }
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

FLAG_FILE = Path("/tmp/commerce_brain_active")
FLAG_TTL = 300  # 5 minutes

BASE_URL = (
    "https://development-200136-commercebrain-stage.dev.runtime.adobe.io"
    "/api/v1/web/app-builder"
)


def _is_active() -> bool:
    """Return True if Commerce Brain was explicitly invoked (@commercebrain) recently."""
    try:
        if not FLAG_FILE.exists():
            return False
        age = time.time() - float(FLAG_FILE.read_text().strip())
        return age < FLAG_TTL
    except Exception:
        return False


NOT_ACTIVE_MSG = (
    "Commerce Brain is not active for this query.\n"
    "To invoke it, start your message with @commercebrain — e.g.:\n"
    "  @commercebrain bundle products disappearing from Live Search after resync"
)


def _call(endpoint: str, query: str, top_k: int = 5) -> dict:
    """Call an App Builder search endpoint and return parsed JSON."""
    params = urllib.parse.urlencode({"query": query, "top_k": top_k})
    url = f"{BASE_URL}/{endpoint}?{params}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read())


def search_commerce_knowledge(query: str, top_k: int = 5) -> str:
    data = _call("search", query, top_k)
    results = data.get("results", [])
    if not results:
        return f"No results found for: {query!r}"
    lines = [f"Top {len(results)} results for: {query!r}\n"]
    for r in results:
        lines.append(f"### [{r['file_type']}] {r['repo']} — {r['path']}")
        lines.append(f"Score: {r['score']}\n")
        lines.append(f"```\n{r['content'].strip()}\n```\n")
        lines.append("---\n")
    return "\n".join(lines)


def search_kibana_queries(query: str, top_k: int = 5) -> str:
    data = _call("search-kibana", query, top_k)
    results = data.get("results", [])
    if not results:
        return f"No results found for: {query!r}"
    lines = [f"Top {len(results)} results for: {query!r}\n"]
    for r in results:
        lines.append(f"### [{r['source']}] {r['title']}")
        lines.append(f"Score: {r['score']}\n")
        lines.append(r["content"].strip())
        lines.append("\n---\n")
    return "\n".join(lines)


def search_saas_schema(query: str, top_k: int = 5) -> str:
    data = _call("search-saas", query, top_k)
    results = data.get("results", [])
    if not results:
        return f"No results found for: {query!r}"
    lines = [f"Top {len(results)} results for: {query!r}\n"]
    for r in results:
        lines.append(f"**[{r['source']}] {r['title']}** (score: {r['score']})")
        lines.append(r["content"].strip())
        lines.append("\n---\n")
    return "\n".join(lines)


def search_db_schema(table_name: str) -> str:
    """Exact column lookup — queries Commerce search filtered to db_schema file_type."""
    table_name = table_name.strip()
    params = urllib.parse.urlencode({"query": table_name, "file_type": "db_schema", "top_k": 20})
    url = f"{BASE_URL}/search?{params}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read())
    results = data.get("results", [])

    suffix = f":: {table_name}"
    matches = [r for r in results
               if r.get("file_type") == "db_schema" and r.get("path", "").endswith(suffix)]

    if not matches:
        return (
            f"Table `{table_name}` not found in Commerce Brain index.\n"
            f"Verify the table name — run DESCRIBE {table_name}; in MySQL to confirm it exists."
        )

    lines = [f"Schema for `{table_name}` — {len(matches)} source(s):\n"]
    for r in matches:
        repo_path = r["path"].split(" :: ")[0]
        lines.append(f"**{repo_path}**")
        lines.append(r["content"].strip())
        lines.append("\n---\n")
    return "\n".join(lines)


TOOLS = [
    {
        "name": "search_db_schema",
        "description": (
            "Exact column lookup for any Adobe Commerce database table. "
            "Returns the full column list, types, indexes, and constraints from db_schema.xml. "
            "MUST be called before writing any SQL query — do not write a column name without calling this first. "
            "If the table is not found, returns a DESCRIBE fallback instruction. "
            "Covers all tables across magento2ce, magento2ee, commerce-data-export, and related repos."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Exact table name — e.g. 'cde_products_feed', 'catalog_product_entity', 'cataloginventory_stock_item'",
                },
            },
            "required": ["table_name"],
        },
    },
    {
        "name": "search_saas_schema",
        "description": (
            "Search Adobe Commerce SaaS API schema reference: CS GraphQL, Live Search GraphQL, CS gRPC, PREX REST. "
            "Returns query structures, field names, response shapes, arg types, and gotchas for all SaaS APIs. "
            "Use when you need: exact field names in a response, required vs optional args, "
            "response shape for a specific query, known gotchas (e.g. 'attribute' not 'code' in attributeMetadata, "
            "'results' not 'units' in recommendations, max 86400s in GetUpdatedProductSkus, "
            "parent_sku required in GetProductVariants, count NON-NULL in categories). "
            "Schema is Adobe-defined and stable across all merchant environments — only values differ. "
            "Also covers: SHA1 customer group codes, auth headers, PREX REST request body fields, "
            "gRPC service names and method signatures."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "API name, field name, query name, or scenario — e.g. 'products skus response shape', 'GetProductOverrides request', 'productSearch filter args', 'customer group SHA1'",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (default 5, max 10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_kibana_queries",
        "description": (
            "Search Kibana ES query patterns and field schema for Live Search catalog index investigation. "
            "Returns ES query structures, field types, nesting rules, and schema gotchas for catalog_1_* indexes. "
            "ALWAYS call search_commerce_knowledge first for Live Search issues — Commerce is the data source. "
            "Call this second to verify whether data reached the ES index. "
            "Covers: product visibility/displayability, index existence, B2B price, category membership, "
            "staleness/reindex, filterable nested queries, stock, product type, variants."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Investigation scenario — e.g. 'product not showing in search', 'B2B price for customer group'",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (default 5, max 10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_commerce_knowledge",
        "description": (
            "Search Adobe Commerce source code: table schemas, feed structures, indexer definitions, mview subscriptions, "
            "CLI commands, SQL query patterns. Use the returned content as domain knowledge — read the schema, "
            "understand the table structure, then construct the appropriate SQL or investigation steps. "
            "For Live Search investigations, call this FIRST (Commerce is the data source), then call search_kibana_queries. "
            "Query tips: use 'feed schema fields' not 'db_schema columns' for table columns. "
            "Example queries: 'cde_products_feed feed schema fields', "
            "'catalog_data_exporter_products indexer dependencies', "
            "'cde_products_feed mview subscriptions', 'saas resync command'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — table names, field names, module names, or natural language",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (default 5, max 10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
]


def _dispatch(tool_name: str, args: dict, msg_id) -> dict:
    top_k = min(int(args.get("top_k", 5)), 10)
    try:
        if tool_name == "search_db_schema":
            result = search_db_schema(args.get("table_name", ""))
        elif tool_name == "search_kibana_queries":
            result = search_kibana_queries(args.get("query", ""), top_k)
        elif tool_name == "search_saas_schema":
            result = search_saas_schema(args.get("query", ""), top_k)
        elif tool_name == "search_commerce_knowledge":
            result = search_commerce_knowledge(args.get("query", ""), top_k)
        else:
            return {
                "jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        return {
            "jsonrpc": "2.0", "id": msg_id,
            "result": {"content": [{"type": "text", "text": result}]},
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0", "id": msg_id,
            "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True},
        }


def handle(msg: dict):
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "commerce-brain", "version": "3.0.0"},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = msg.get("params", {})
        if not _is_active():
            return {
                "jsonrpc": "2.0", "id": msg_id,
                "result": {"content": [{"type": "text", "text": NOT_ACTIVE_MSG}]},
            }
        return _dispatch(params.get("name"), params.get("arguments", {}), msg_id)

    return None


def send(obj: dict):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(msg)
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()
