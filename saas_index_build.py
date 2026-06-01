#!/usr/bin/env python3
"""
Build BM25 index from SaaS API schema docs.
Sources (all .md files in saas-schema/):
  cs_ls_graphql_schema.md  — CS/LS/PREX GraphQL queries, args, response shapes
  grpc_schema.md           — CS gRPC methods, request/response fields
  prex_rest_schema.md      — PREX REST endpoints, request/response fields

Chunked by ## headings (one chunk per API section).
Output: saas_brain.pkl
"""

import pickle
import re
import sys
from pathlib import Path

BRAIN_DIR = Path(__file__).parent
INDEX_FILE = BRAIN_DIR / "saas_brain.pkl"
SAAS_DIR = BRAIN_DIR / "saas-schema"


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def chunk_by_h2(content: str, source: str) -> list[dict]:
    """Split on ## headings — one chunk per API section."""
    chunks = []
    parts = re.split(r"\n(?=## )", content)
    for part in parts[1:]:
        part = part.strip()
        if len(part) < 80:
            continue
        title = part.split("\n")[0].lstrip("# ").strip()
        chunks.append({
            "source": source,
            "title": title,
            "content": part,
            "tokens": tokenize(part),
        })
    return chunks


def collect_docs() -> list[dict]:
    docs = []
    md_files = sorted(SAAS_DIR.glob("*.md"))
    if not md_files:
        print(f"  ERROR: No .md files found in {SAAS_DIR}")
        return docs
    for path in md_files:
        content = path.read_text(errors="ignore")
        source = path.stem
        chunks = chunk_by_h2(content, source)
        print(f"  {path.name}: {len(chunks)} chunks")
        docs.extend(chunks)
    return docs


def main():
    print("Building SaaS Brain index...")
    docs = collect_docs()
    if not docs:
        print("ERROR: No documents found. Check saas-schema/ directory exists.")
        sys.exit(1)

    print(f"Total: {len(docs)} chunks — building BM25 index...")
    from rank_bm25 import BM25Okapi
    corpus = [d["tokens"] for d in docs]
    bm25 = BM25Okapi(corpus)

    store = {"bm25": bm25, "docs": docs}
    with open(INDEX_FILE, "wb") as fh:
        pickle.dump(store, fh)

    size_kb = INDEX_FILE.stat().st_size // 1024
    print(f"Saved: {INDEX_FILE} ({size_kb} KB)")
    print("Done — search_saas_schema tool is ready.")


if __name__ == "__main__":
    main()
