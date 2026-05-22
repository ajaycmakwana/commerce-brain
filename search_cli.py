#!/usr/bin/env python3
"""
CLI search tool for Commerce Brain BM25 index.
Usage: python3 search_cli.py "cde_products_feed schema"
"""

import pickle
import re
import sys
from pathlib import Path

INDEX_FILE = Path(__file__).parent / "commerce_brain.pkl"
TOP_K = 5


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def search(query: str, top_k: int = TOP_K) -> list[dict]:
    with open(INDEX_FILE, "rb") as fh:
        store = pickle.load(fh)

    bm25 = store["bm25"]
    docs = store["docs"]

    tokens = tokenize(query)
    scores = bm25.get_scores(tokens)

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    results = []
    for idx, score in ranked[:top_k]:
        if score <= 0:
            break
        d = docs[idx]
        snippet = d["content"][:800].strip()
        results.append({
            "score": round(score, 2),
            "repo": d["repo"],
            "file_type": d["file_type"],
            "path": d["path"],
            "snippet": snippet,
        })
    return results


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "cde_products_feed columns schema"
    print(f"Query: {query!r}\n")

    results = search(query)
    if not results:
        print("No results found.")
        return

    for i, r in enumerate(results, 1):
        print(f"{'='*70}")
        print(f"[{i}] score={r['score']}  type={r['file_type']}  repo={r['repo']}")
        print(f"    {r['path']}")
        print(f"{'─'*70}")
        print(r["snippet"])
        if len(r["snippet"]) == 800:
            print("... (truncated)")
        print()


if __name__ == "__main__":
    main()
