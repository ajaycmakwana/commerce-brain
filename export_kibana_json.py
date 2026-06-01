#!/usr/bin/env python3
"""
Export Kibana BM25 index to JSON for the App Builder Node.js action.
Output: kibana_brain_index.json
"""

import json
import math
import pickle
from pathlib import Path

INDEX_FILE = Path(__file__).parent / "kibana_brain.pkl"
OUTPUT_FILE = Path(__file__).parent / "kibana_brain_index.json"


def main():
    with open(INDEX_FILE, "rb") as fh:
        store = pickle.load(fh)

    docs = store["docs"]
    N = len(docs)
    print(f"Exporting {N} documents...")

    df = {}
    for d in docs:
        for term in set(d["tokens"]):
            df[term] = df.get(term, 0) + 1

    idf = {}
    for term, freq in df.items():
        idf[term] = math.log((N - freq + 0.5) / (freq + 0.5) + 1)

    avgdl = sum(len(d["tokens"]) for d in docs) / N

    export_docs = []
    for d in docs:
        export_docs.append({
            "source":  d["source"],
            "title":   d["title"],
            "tokens":  d["tokens"],
            "content": d["content"][:3000],
        })

    output = {
        "n":     N,
        "avgdl": round(avgdl, 2),
        "idf":   idf,
        "docs":  export_docs,
    }

    with open(OUTPUT_FILE, "w") as fh:
        json.dump(output, fh, separators=(",", ":"))

    size_kb = OUTPUT_FILE.stat().st_size // 1024
    print(f"Exported: {OUTPUT_FILE} ({size_kb} KB)")
    print(f"  {len(idf):,} unique terms, avgdl={avgdl:.1f} tokens")


if __name__ == "__main__":
    main()
