#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit hook.
On every prompt: searches Commerce Brain + Kibana Brain + SaaS Brain locally,
injects relevant results as additionalContext before the agent sees the question.

Agent gets ground truth in context — no tool call decision, no training knowledge fallback.
"""

import json
import pickle
import re
import sys
from pathlib import Path

BRAIN_DIR = Path(__file__).parent
COMMERCE_INDEX = BRAIN_DIR / "commerce_brain.pkl"
KIBANA_INDEX = BRAIN_DIR / "kibana_brain.pkl"
SAAS_INDEX = BRAIN_DIR / "saas_brain.pkl"

MIN_SCORE_COMMERCE = 8.0   # higher — command files are noise at low scores
MIN_SCORE_KIBANA = 4.0
MIN_SCORE_SAAS = 2.0
TOP_K = 4

# Command PHP files (229 of 529) match on generic words — exclude from hook injection.
# Agents can still call search_commerce_knowledge directly for CLI command queries.
EXCLUDE_FILE_TYPES = {"command"}


def _load(path):
    try:
        if path.exists():
            with open(path, "rb") as f:
                return pickle.load(f)
    except Exception:
        pass
    return None


def _tokenize(text):
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def _search(store, query, min_score, exclude_types=None):
    if not store:
        return []
    tokens = _tokenize(query)
    scores = store["bm25"].get_scores(tokens)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for idx, score in ranked:
        if len(results) >= TOP_K:
            break
        if score < min_score:
            break
        doc = store["docs"][idx]
        if exclude_types and doc.get("file_type") in exclude_types:
            continue
        results.append((round(score, 2), doc))
    return results


def format_commerce(results):
    lines = ["### Commerce Knowledge (schemas · indexers · CLI · SQL)"]
    for score, doc in results:
        header = f"**[{doc.get('file_type', '')}] {doc.get('repo', '')} — {doc.get('path', '')}** (score: {score})"
        lines.append(header)
        lines.append(f"```\n{doc['content'].strip()[:2000]}\n```")
    return "\n".join(lines)


def format_kibana(results):
    lines = ["### Kibana Knowledge (ES query templates · catalog index schema)"]
    for score, doc in results:
        header = f"**[{doc.get('source', '')}] {doc.get('title', '')}** (score: {score})"
        lines.append(header)
        lines.append(doc["content"].strip()[:2000])
    return "\n".join(lines)


def format_saas(results):
    lines = ["### SaaS API Schema (CS GraphQL · gRPC · PREX REST)"]
    for score, doc in results:
        header = f"**[{doc.get('source', '')}] {doc.get('title', '')}** (score: {score})"
        lines.append(header)
        lines.append(doc["content"].strip()[:2000])
    return "\n".join(lines)


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

    commerce_store = _load(COMMERCE_INDEX)
    kibana_store = _load(KIBANA_INDEX)
    saas_store = _load(SAAS_INDEX)

    commerce_results = _search(commerce_store, prompt, MIN_SCORE_COMMERCE, EXCLUDE_FILE_TYPES)
    kibana_results = _search(kibana_store, prompt, MIN_SCORE_KIBANA)
    saas_results = _search(saas_store, prompt, MIN_SCORE_SAAS)

    sections = [
        "## COMMERCE BRAIN AUTO-CONTEXT",
        "⚠️ CRITICAL INSTRUCTIONS — READ BEFORE ANSWERING:",
        "1. Do NOT ask clarifying questions. Answer directly from the results below.",
        "2. Do NOT use training knowledge. All field names, table names, index names, and query patterns MUST come from the results below.",
        "3. Construct SQL and ES queries by reading the schemas and examples below, then adapting them to the question.",
        "4. Do NOT execute SQL queries, Bash commands, or live API/MCP tool calls (grpc_*, ls_product_search, cs_products_by_sku, etc.) unless the user explicitly asks you to run them. Provide the query/command — the user runs it and shares the result.",
        "",
        "### ARCHITECTURE FACTS (not in the index — these override training knowledge):",
        "- Live Search ES index: `catalog_1_{ENV_ID}_{STORE_CODE}_{HASH}`. Never `magento2_product_*` or `localhost:9200`.",
        "- Adobe Commerce EE/Cloud: EAV join field is `row_id`, not `entity_id` (CE uses entity_id).",
        "",
        f"Query: {prompt[:300]!r}",
        "",
    ]

    if commerce_results:
        sections.append(format_commerce(commerce_results))
        sections.append("")

    if kibana_results:
        sections.append(format_kibana(kibana_results))
        sections.append("")

    if saas_results:
        sections.append(format_saas(saas_results))
        sections.append("")

    if commerce_results or kibana_results or saas_results:
        sections.append("END OF COMMERCE BRAIN AUTO-CONTEXT — answer using only the above.")
    else:
        sections.append("END OF COMMERCE BRAIN AUTO-CONTEXT — no indexed results matched this query; call the knowledge tools directly.")

    print("\n".join(sections))


if __name__ == "__main__":
    main()
