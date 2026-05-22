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
import sys
import urllib.request
import urllib.parse

SEARCH_URL = (
    "https://development-200136-commercebrain-stage.dev.runtime.adobe.io"
    "/api/v1/web/app-builder/search"
)

TOOLS = [
    {
        "name": "search_commerce_knowledge",
        "description": (
            "Search Adobe Commerce source code knowledge base. "
            "Returns relevant schema definitions (db_schema.xml), feed structures (et_schema.xml), "
            "mview subscriptions, indexer definitions, Query models (PHP), and CLI commands. "
            "Use this during merchant issue investigations to find table columns, feed fields, "
            "indexer IDs, and query patterns without browsing source code manually."
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
