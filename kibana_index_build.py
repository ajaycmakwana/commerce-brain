#!/usr/bin/env python3
"""
Build BM25 index from Kibana query docs.
Sources:
  kibana/queries/query_templates.md  — chunked by ### heading (one chunk per query)
  kibana/schema/catalog_index_schema.md — chunked by ## heading (one chunk per field section)

coverage_matrix.md is intentionally excluded — it only contains template number pointers,
no actual query content.

Output: kibana_brain.pkl
"""

import pickle
import re
import sys
from pathlib import Path

BRAIN_DIR = Path(__file__).parent
INDEX_FILE = BRAIN_DIR / "kibana_brain.pkl"

KIBANA_DIR = BRAIN_DIR / "kibana"
SOURCES = [
    KIBANA_DIR / "queries" / "query_templates.md",
    KIBANA_DIR / "schema" / "catalog_index_schema.md",
]


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def chunk_by_h3(content: str, source: str) -> list[dict]:
    """Split on ### headings — one chunk per query template. No intro chunk."""
    chunks = []
    parts = re.split(r"\n(?=### )", content)
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        title = part.split("\n")[0].lstrip("# ").strip()
        chunks.append({
            "source": source,
            "title": title,
            "content": part,
            "tokens": tokenize(part),
        })
    return chunks


def chunk_by_h2(content: str, source: str) -> list[dict]:
    """Split on ## headings — one chunk per schema section."""
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
    for path in SOURCES:
        if not path.exists():
            print(f"  WARNING: {path} not found — skipping")
            continue
        content = path.read_text(errors="ignore")
        source = path.stem
        if path.name == "query_templates.md":
            chunks = chunk_by_h3(content, source)
        else:
            chunks = chunk_by_h2(content, source)
        print(f"  {path.name}: {len(chunks)} chunks")
        docs.extend(chunks)
    return docs


def main():
    print(f"Building Kibana Brain index...")
    docs = collect_docs()
    if not docs:
        print("ERROR: No documents found. Check kibana/ directory exists.")
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
    print("Done — search_kibana_queries tool is ready.")


if __name__ == "__main__":
    main()
