#!/usr/bin/env python3
"""MCP stdio client for the Commerce Brain App Builder reference indexes."""

import json
import re
import sys
from typing import Optional
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = (
    "https://development-200136-commercebrain-stage.dev.runtime.adobe.io"
    "/api/v1/web/app-builder"
)
MAX_TOP_K = 10
TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,255}$")
SUPPORTED_PROTOCOL_VERSION = "2024-11-05"


class SearchServiceError(Exception):
    """A safe-to-display failure while querying the reference search service."""


def _validated_query(value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("query must be a non-empty string")
    return value.strip()


def _validated_top_k(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_TOP_K:
        raise ValueError(f"top_k must be an integer between 1 and {MAX_TOP_K}")
    return value


def _call(endpoint: str, query: Optional[str] = None, top_k: int = 5, table_name: Optional[str] = None) -> dict:
    params = {}
    if table_name is not None:
        params["table_name"] = table_name
    else:
        params.update({"query": query, "top_k": top_k})
    url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise SearchServiceError(f"Search service returned HTTP status {error.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise SearchServiceError("Could not reach the Commerce Brain search service.") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise SearchServiceError("Search service returned an invalid response.") from None
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise SearchServiceError("Search service returned an invalid response.")
    if any(not isinstance(item, dict) for item in data["results"]):
        raise SearchServiceError("Search service returned an invalid response.")
    return data


def _render_results(query: str, results: list[dict], fields: tuple[str, ...]) -> str:
    if not results:
        return f"No results found for: {query!r}"
    lines = [f"Top {len(results)} results for: {query!r}\n"]
    for result in results:
        if fields == ("file_type", "repo", "path"):
            lines.extend([
                f"### [{result.get('file_type', '')}] {result.get('repo', '')} — {result.get('path', '')}",
                f"Score: {result.get('score', 0)}\n",
                f"```\n{result.get('content', '').strip()}\n```\n",
                "---\n",
            ])
        elif fields == ("source", "title", "score"):
            lines.extend([
                f"**[{result.get('source', '')}] {result.get('title', '')}** (score: {result.get('score', 0)})",
                result.get("content", "").strip(),
                "\n---\n",
            ])
        else:
            lines.extend([
                f"### [{result.get('source', '')}] {result.get('title', '')}",
                f"Score: {result.get('score', 0)}\n",
                result.get("content", "").strip(),
                "\n---\n",
            ])
    return "\n".join(lines)


def search_commerce_knowledge(query: str, top_k: int = 5) -> str:
    query = _validated_query(query)
    top_k = _validated_top_k(top_k)
    data = _call("search", query, top_k)
    return _render_results(query, data["results"], ("file_type", "repo", "path"))


def search_kibana_queries(query: str, top_k: int = 5) -> str:
    query = _validated_query(query)
    top_k = _validated_top_k(top_k)
    data = _call("search-kibana", query, top_k)
    return _render_results(query, data["results"], ("source", "title"))


def search_saas_schema(query: str, top_k: int = 5) -> str:
    query = _validated_query(query)
    top_k = _validated_top_k(top_k)
    data = _call("search-saas", query, top_k)
    return _render_results(query, data["results"], ("source", "title", "score"))


def search_db_schema(table_name: str) -> str:
    if not isinstance(table_name, str) or not TABLE_NAME_PATTERN.fullmatch(table_name.strip()):
        raise ValueError("table_name must contain only letters, numbers, and underscores")
    table_name = table_name.strip()
    data = _call("search", table_name=table_name)
    results = [
        result for result in data["results"]
        if result.get("file_type") == "db_schema"
        and isinstance(result.get("path"), str)
        and result["path"].endswith(f" :: {table_name}")
    ]
    if not results:
        return (
            f"Table `{table_name}` not found in the bundled Commerce schema index. "
            "Confirm the table name and schema version in the target database."
        )

    lines = [f"Schema for `{table_name}` — {len(results)} source declaration(s):\n"]
    for result in results:
        repo_path = result["path"].rsplit(" :: ", 1)[0]
        lines.extend([f"**{repo_path}**", result.get("content", "").strip(), "\n---\n"])
    return "\n".join(lines)


TOOLS = [
    {
        "name": "search_db_schema",
        "description": (
            "Exact table-name lookup across all db_schema declarations in the bundled Commerce index. "
            "Returns every matching source declaration with its repository/path provenance, independent of BM25 ranking. "
            "This is source-code reference data, not a live query against a merchant database."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Exact table identifier containing letters, numbers, or underscores.",
                    "minLength": 1,
                    "maxLength": 255,
                    "pattern": "^[A-Za-z0-9_]+$",
                },
            },
            "required": ["table_name"],
        },
    },
    {
        "name": "search_saas_schema",
        "description": (
            "Search the bundled Adobe Commerce SaaS API reference: CS GraphQL, Live Search GraphQL, CS gRPC, and PREX REST. "
            "Returns API query structures, field names, response shapes, argument types, and documented gotchas. "
            "This retrieves reference documents; it does not call SaaS APIs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "API, field, query name, or scenario."},
                "top_k": {
                    "type": "integer", "description": "Number of results (1-10; default 5).",
                    "minimum": 1, "maximum": 10, "default": 5
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_kibana_queries",
        "description": (
            "Search bundled Live Search Elasticsearch query patterns and catalog-index reference docs. "
            "It does not query a merchant's Elasticsearch cluster."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Investigation scenario or field/query concept."},
                "top_k": {
                    "type": "integer", "description": "Number of results (1-10; default 5).",
                    "minimum": 1, "maximum": 10, "default": 5
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_commerce_knowledge",
        "description": (
            "Search the bundled Adobe Commerce source reference for schemas, feed structures, indexers, mview subscriptions, "
            "CLI commands, and SQL patterns. This retrieves source-code reference material; it does not run SQL or commands. "
            "For a complete table declaration, call search_db_schema."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Table, field, module, or natural-language search."},
                "top_k": {
                    "type": "integer", "description": "Number of results (1-10; default 5).",
                    "minimum": 1, "maximum": 10, "default": 5
                },
            },
            "required": ["query"],
        },
    },
]


def _jsonrpc_error(msg_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _dispatch(tool_name, args, msg_id) -> dict:
    if not isinstance(tool_name, str) or not isinstance(args, dict):
        return _jsonrpc_error(msg_id, -32602, "tools/call requires a tool name and object arguments")
    if tool_name not in {tool["name"] for tool in TOOLS}:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            },
        }
    try:
        allowed_arguments = {
            "search_db_schema": {"table_name"},
            "search_kibana_queries": {"query", "top_k"},
            "search_saas_schema": {"query", "top_k"},
            "search_commerce_knowledge": {"query", "top_k"},
        }[tool_name]
        unexpected = set(args) - allowed_arguments
        if unexpected:
            raise ValueError(f"Unsupported argument(s): {', '.join(sorted(unexpected))}")
        if tool_name == "search_db_schema":
            result = search_db_schema(args.get("table_name"))
        elif tool_name == "search_kibana_queries":
            result = search_kibana_queries(args.get("query"), args.get("top_k", 5))
        elif tool_name == "search_saas_schema":
            result = search_saas_schema(args.get("query"), args.get("top_k", 5))
        elif tool_name == "search_commerce_knowledge":
            result = search_commerce_knowledge(args.get("query"), args.get("top_k", 5))
    except ValueError as error:
        result = str(error)
        is_error = True
    except SearchServiceError as error:
        result = str(error)
        is_error = True
    except Exception:
        result = "Search failed due to an internal error."
        is_error = True
    else:
        is_error = False
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {"content": [{"type": "text", "text": result}], **({"isError": True} if is_error else {})},
    }


def handle(message):
    if not isinstance(message, dict):
        return _jsonrpc_error(None, -32600, "Invalid Request")
    msg_id = message.get("id")
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return _jsonrpc_error(msg_id, -32600, "Invalid Request")
    if "id" in message and (isinstance(msg_id, bool) or not isinstance(msg_id, (str, int, float, type(None)))):
        return _jsonrpc_error(None, -32600, "Invalid Request")
    method = message["method"]
    params = message.get("params", {})
    if not isinstance(params, dict):
        return None if "id" not in message else _jsonrpc_error(msg_id, -32602, "Invalid params")

    if method == "initialize":
        if not isinstance(params.get("protocolVersion"), str):
            return None if "id" not in message else _jsonrpc_error(msg_id, -32602, "Invalid initialize parameters")
        response = {
            "protocolVersion": SUPPORTED_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "commerce-brain", "version": "4.1.0"},
        }
        return None if "id" not in message else {"jsonrpc": "2.0", "id": msg_id, "result": response}
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return None if "id" not in message else {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method == "tools/list":
        return None if "id" not in message else {
            "jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}
        }
    if method == "tools/call":
        if not isinstance(params.get("name"), str) or not isinstance(params.get("arguments", {}), dict):
            return None if "id" not in message else _jsonrpc_error(msg_id, -32602, "Invalid tools/call parameters")
        response = _dispatch(params["name"], params.get("arguments", {}), msg_id)
        return None if "id" not in message else response
    if "id" not in message:
        return None
    return _jsonrpc_error(msg_id, -32601, f"Method not found: {method}")


def send(response: dict) -> None:
    sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            send(_jsonrpc_error(None, -32700, "Parse error"))
            continue
        response = handle(message)
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()
