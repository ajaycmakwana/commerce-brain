#!/usr/bin/env python3
"""
Export BM25 index to JSON for the App Builder Node.js action.
Precomputes IDF so the JS action only needs to do TF scoring at query time.

Output: commerce_brain_index.json  (~3-5 MB)
"""

import json
import math
import pickle
from pathlib import Path

INDEX_FILE = Path(__file__).parent / "commerce_brain.pkl"
OUTPUT_FILE = Path(__file__).parent / "commerce_brain_index.json"


def main():
    with open(INDEX_FILE, "rb") as fh:
        store = pickle.load(fh)

    docs = store["docs"]
    N = len(docs)
    print(f"Exporting {N} documents...")

    # Compute document frequency for each term
    df = {}
    for d in docs:
        for term in set(d["tokens"]):
            df[term] = df.get(term, 0) + 1

    # Compute IDF (BM25 Okapi)
    idf = {}
    for term, freq in df.items():
        idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1)

    # Average doc length
    avgdl = sum(len(d["tokens"]) for d in docs) / N

    # Build export docs (keep tokens + content snippet)
    export_docs = []
    for d in docs:
        export_docs.append({
            "repo":      d["repo"],
            "file_type": d["file_type"],
            "path":      d["path"],
            "tokens":    d["tokens"],
            "content":   d["content"][:2000],
        })

    output = {
        "n":    N,
        "avgdl": round(avgdl, 2),
        "idf":  idf,
        "docs": export_docs,
    }

    with open(OUTPUT_FILE, "w") as fh:
        json.dump(output, fh, separators=(",", ":"))

    size_kb = OUTPUT_FILE.stat().st_size // 1024
    unique_terms = len(idf)
    print(f"Exported: {OUTPUT_FILE} ({size_kb} KB)")
    print(f"  {unique_terms:,} unique terms, avgdl={avgdl:.1f} tokens")


if __name__ == "__main__":
    main()
