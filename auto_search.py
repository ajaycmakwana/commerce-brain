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
import time
from pathlib import Path

BRAIN_DIR = Path(__file__).parent
FLAG_FILE = Path("/tmp/commerce_brain_active")
FLAG_TTL = 300  # 5 minutes — expires after session context clears
COMMERCE_INDEX = BRAIN_DIR / "commerce_brain.pkl"
KIBANA_INDEX = BRAIN_DIR / "kibana_brain.pkl"
SAAS_INDEX = BRAIN_DIR / "saas_brain.pkl"

MIN_SCORE_COMMERCE = 8.0   # higher — command files are noise at low scores
MIN_SCORE_KIBANA = 7.0
MIN_SCORE_SAAS = 5.0
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

    # Only fire when user explicitly invokes with @commercebrain
    if "@commercebrain" not in prompt.lower():
        sys.exit(0)

    # Write flag file so MCP tools know Commerce Brain is active for this session
    FLAG_FILE.write_text(str(time.time()))

    # Strip the trigger word before BM25 search
    clean_prompt = prompt.lower().replace("@commercebrain", "").strip()

    commerce_store = _load(COMMERCE_INDEX)
    kibana_store = _load(KIBANA_INDEX)
    saas_store = _load(SAAS_INDEX)

    commerce_results = _search(commerce_store, clean_prompt, MIN_SCORE_COMMERCE, EXCLUDE_FILE_TYPES)
    kibana_results = _search(kibana_store, clean_prompt, MIN_SCORE_KIBANA)
    saas_results = _search(saas_store, clean_prompt, MIN_SCORE_SAAS)

    if not commerce_results and not kibana_results and not saas_results:
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

    if commerce_results:
        sections.append(format_commerce(commerce_results))
        sections.append("")

    if kibana_results:
        sections.append(format_kibana(kibana_results))
        sections.append("")

    if saas_results:
        sections.append(format_saas(saas_results))
        sections.append("")

    sections.append("END OF COMMERCE BRAIN AUTO-CONTEXT — answer using only the above.")

    print("\n".join(sections))


if __name__ == "__main__":
    main()
