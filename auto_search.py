#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit hook.
Fires when user types @commercebrain — calls App Builder endpoints,
injects relevant results as context before the agent responds.

All search goes through App Builder (same as MCP tools).
No local pkl files needed at runtime.
"""

import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

FLAG_FILE = Path("/tmp/commerce_brain_active")
FLAG_TTL = 1800  # 30 minutes — covers full investigation sessions

BASE_URL = (
    "https://development-200136-commercebrain-stage.dev.runtime.adobe.io"
    "/api/v1/web/app-builder"
)

MIN_SCORE_COMMERCE = 8.0
MIN_SCORE_KIBANA = 7.0
MIN_SCORE_SAAS = 5.0
TOP_K = 4


def _call(endpoint: str, query: str, top_k: int = TOP_K) -> list:
    try:
        params = urllib.parse.urlencode({"query": query, "top_k": top_k})
        url = f"{BASE_URL}/{endpoint}?{params}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get("results", [])
    except Exception:
        return []


def format_commerce(results):
    lines = ["### Commerce Knowledge (schemas · indexers · CLI · SQL)"]
    for r in results:
        if r.get("score", 0) < MIN_SCORE_COMMERCE:
            continue
        lines.append(f"**[{r.get('file_type', '')}] {r.get('repo', '')} — {r.get('path', '')}** (score: {r.get('score', 0)})")
        lines.append(f"```\n{r.get('content', '').strip()[:2000]}\n```")
    return "\n".join(lines) if len(lines) > 1 else ""


def format_kibana(results):
    lines = ["### Kibana Knowledge (ES query templates · catalog index schema)"]
    for r in results:
        if r.get("score", 0) < MIN_SCORE_KIBANA:
            continue
        lines.append(f"**[{r.get('source', '')}] {r.get('title', '')}** (score: {r.get('score', 0)})")
        lines.append(r.get("content", "").strip()[:2000])
    return "\n".join(lines) if len(lines) > 1 else ""


def format_saas(results):
    lines = ["### SaaS API Schema (CS GraphQL · gRPC · PREX REST)"]
    for r in results:
        if r.get("score", 0) < MIN_SCORE_SAAS:
            continue
        lines.append(f"**[{r.get('source', '')}] {r.get('title', '')}** (score: {r.get('score', 0)})")
        lines.append(r.get("content", "").strip()[:2000])
    return "\n".join(lines) if len(lines) > 1 else ""


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = (
        data.get("message")
        or data.get("prompt")
        or ""
    )
    if not prompt and data.get("transcript"):
        last = data["transcript"][-1]
        if isinstance(last, dict):
            prompt = last.get("content") or last.get("message") or ""

    prompt = str(prompt).strip()
    if len(prompt) < 8:
        sys.exit(0)

    if "@commercebrain" not in prompt.lower():
        sys.exit(0)

    # Write flag — MCP tools check this before responding
    FLAG_FILE.write_text(str(time.time()))

    clean_prompt = prompt.lower().replace("@commercebrain", "").strip()
    if not clean_prompt:
        sys.exit(0)

    # Call App Builder endpoints (same source as MCP tools)
    commerce_results = _call("search", clean_prompt, TOP_K)
    kibana_results = _call("search-kibana", clean_prompt, TOP_K)
    saas_results = _call("search-saas", clean_prompt, TOP_K)

    commerce_block = format_commerce(commerce_results)
    kibana_block = format_kibana(kibana_results)
    saas_block = format_saas(saas_results)

    if not any([commerce_block, kibana_block, saas_block]):
        sys.exit(0)

    sections = [
        "## COMMERCE BRAIN AUTO-CONTEXT",
        "INSTRUCTIONS:",
        "1. Answer using only the injected results below — no training knowledge for table names, columns, field paths, or CLI commands.",
        "2. Call `search_db_schema(table_name)` before writing any column name in SQL. No exceptions.",
        "3. Provide queries and commands as text only — never execute them. User runs them and shares results.",
        "",
        "### ARCHITECTURE FACTS (not in the index — these override training knowledge):",
        "- Live Search ES index: `catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}`. Never `magento2_product_*` or `localhost:9200`.",
        "- Adobe Commerce EE/Cloud: EAV join field is `row_id`, not `entity_id` (CE uses entity_id).",
        "",
        f"Query: {clean_prompt[:300]!r}",
        "",
    ]

    if commerce_block:
        sections.append(commerce_block)
        sections.append("")

    if kibana_block:
        sections.append(kibana_block)
        sections.append("")

    if saas_block:
        sections.append(saas_block)
        sections.append("")

    sections.append("END OF COMMERCE BRAIN AUTO-CONTEXT — answer using only the above.")

    print("\n".join(sections))


if __name__ == "__main__":
    main()
