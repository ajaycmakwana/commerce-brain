#!/usr/bin/env python3
"""
Commerce Brain MCP Server
Calls the App Builder search endpoint and exposes search_commerce_knowledge()
as an MCP tool for Claude / Cursor agents.

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
import pickle
import re
import sys
import urllib.request
import urllib.parse
from pathlib import Path

SEARCH_URL = (
    "https://development-200136-commercebrain-stage.dev.runtime.adobe.io"
    "/api/v1/web/app-builder/search"
)

KIBANA_INDEX_FILE = Path(__file__).parent / "kibana_brain.pkl"
_kibana_store = None

SAAS_INDEX_FILE = Path(__file__).parent / "saas_brain.pkl"
_saas_store = None


def _get_saas_store():
    global _saas_store
    if _saas_store is None and SAAS_INDEX_FILE.exists():
        with open(SAAS_INDEX_FILE, "rb") as fh:
            _saas_store = pickle.load(fh)
    return _saas_store


def search_saas_schema(query: str, top_k: int = 5) -> str:
    store = _get_saas_store()
    if not store:
        return "SaaS Brain index not found. Run: python3 saas_index_build.py"
    bm25 = store["bm25"]
    docs = store["docs"]
    tokens = _tokenize(query)
    scores = bm25.get_scores(tokens)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for idx, score in ranked[:top_k]:
        if score <= 0:
            break
        results.append((round(score, 2), docs[idx]))
    if not results:
        return f"No results found for: {query!r}"
    lines = [f"Top {len(results)} results for: {query!r}\n"]
    for score, d in results:
        lines.append(f"**[{d['source']}] {d['title']}** (score: {score})")
        lines.append(d["content"].strip())
        lines.append("\n---\n")
    return "\n".join(lines)


def _get_kibana_store():
    global _kibana_store
    if _kibana_store is None and KIBANA_INDEX_FILE.exists():
        with open(KIBANA_INDEX_FILE, "rb") as fh:
            _kibana_store = pickle.load(fh)
    return _kibana_store


def _tokenize(text: str) -> list:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def search_kibana(query: str, top_k: int = 5) -> str:
    store = _get_kibana_store()
    if not store:
        return (
            "Kibana Brain index not found. "
            "Run: python3 kibana_index_build.py"
        )
    bm25 = store["bm25"]
    docs = store["docs"]
    tokens = _tokenize(query)
    scores = bm25.get_scores(tokens)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for idx, score in ranked[:top_k]:
        if score <= 0:
            break
        results.append((round(score, 2), docs[idx]))
    if not results:
        return f"No results found for: {query!r}"
    lines = [f"Top {len(results)} results for: {query!r}\n"]
    for score, d in results:
        lines.append(f"### [{d['source']}] {d['title']}")
        lines.append(f"Score: {score}\n")
        lines.append(d["content"].strip())
        lines.append("\n---\n")
    return "\n".join(lines)

TOOLS = [
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
                    "description": "API name, field name, query name, or scenario — e.g. 'products skus response shape', 'recommendations field names', 'GetProductOverrides request', 'productSearch filter args', 'customer group SHA1'",
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
            "Use the returned content as domain knowledge to construct the right ES query for the investigation — "
            "do not return results verbatim, adapt them to the specific scenario. "
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
                    "description": "Investigation scenario or question — e.g. 'product not showing in search', 'check if product is displayable', 'B2B price for customer group'",
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
            "Do NOT ask clarifying questions before calling this tool — call it first, get ground truth, then answer. "
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
    }
]


def call_search(query: str, top_k: int = 5) -> str:
    params = urllib.parse.urlencode({"query": query, "top_k": top_k})
    url = f"{SEARCH_URL}?{params}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read())

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


def send(obj: dict):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def handle(msg: dict):
    method = msg.get("method")
    msg_id = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "commerce-brain", "version": "2.0.0"},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = msg.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "search_saas_schema":
            query = args.get("query", "")
            top_k = min(int(args.get("top_k", 5)), 10)
            try:
                result = search_saas_schema(query, top_k)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": result}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True,
                    },
                }

        if tool_name == "search_kibana_queries":
            query = args.get("query", "")
            top_k = min(int(args.get("top_k", 5)), 10)
            try:
                result = search_kibana(query, top_k)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": result}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True,
                    },
                }

        if tool_name == "search_commerce_knowledge":
            query = args.get("query", "")
            top_k = min(int(args.get("top_k", 5)), 10)
            try:
                result = call_search(query, top_k)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": result}]},
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True,
                    },
                }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
        }

    if method == "notifications/initialized":
        return None

    return None


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
