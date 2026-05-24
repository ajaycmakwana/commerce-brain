#!/usr/bin/env python3
"""
Build BM25 index from cloned Commerce repos.
Scans for high-signal files: mview.xml, et_schema.xml, db_schema.xml,
indexer.xml, Model/Query/*.php, Console/Command/*.php

Output: commerce_brain.pkl  (BM25 index + document store)
"""

import pickle
import re
import sys
from pathlib import Path

from rank_bm25 import BM25Okapi

REPOS_DIR = Path(__file__).parent
INDEX_FILE = REPOS_DIR / "commerce_brain.pkl"

MATCHERS = [
    ("mview",    lambda p: p.name == "mview.xml"    and p.parent.name == "etc"),
    ("et_schema",lambda p: p.name == "et_schema.xml" and p.parent.name == "etc"),
    ("db_schema",lambda p: p.name == "db_schema.xml" and p.parent.name == "etc"),
    ("indexer",  lambda p: p.name == "indexer.xml"   and p.parent.name == "etc"),
    ("query",    lambda p: p.suffix == ".php" and p.parent.name == "Query"   and p.parent.parent.name == "Model"),
    ("command",  lambda p: p.suffix == ".php" and p.parent.name == "Command" and p.parent.parent.name == "Console"),
]

SKIP_DIRS = {"app-builder", ".git"}
COMMERCE_QUERIES_DIR = REPOS_DIR / "commerce_queries"


def tokenize(text: str) -> list[str]:
    """Split on non-alphanumeric chars, lowercase, drop short tokens."""
    return [t for t in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if len(t) > 2]


def collect_sql_queries():
    """Chunk commerce_queries/*.md by ### heading — one chunk per SQL query."""
    docs = []
    if not COMMERCE_QUERIES_DIR.exists():
        return docs
    for md_file in sorted(COMMERCE_QUERIES_DIR.glob("*.md")):
        content = md_file.read_text(errors="ignore")
        parts = re.split(r"\n(?=### )", content)
        for part in parts[1:]:
            part = part.strip()
            if not part:
                continue
            title = part.split("\n")[0].lstrip("# ").strip()
            docs.append({
                "repo": "commerce_queries",
                "file_type": "sql",
                "path": str(md_file.relative_to(REPOS_DIR)),
                "content": part,
                "tokens": tokenize(part),
            })
    if docs:
        print(f"  sql          {len(docs)} queries (from commerce_queries/)")
    return docs


def collect_docs():
    docs = []  # list of dicts: {repo, file_type, path, content, tokens}
    repos = sorted(d for d in REPOS_DIR.iterdir() if d.is_dir() and d.name not in SKIP_DIRS)

    print(f"Scanning {len(repos)} repos...")
    for repo in repos:
        for file_type, matcher in MATCHERS:
            for f in repo.rglob("*"):
                if f.is_file() and matcher(f):
                    try:
                        content = f.read_text(errors="ignore")
                        rel_path = str(f.relative_to(REPOS_DIR))
                        tokens = tokenize(content)
                        docs.append({
                            "repo": repo.name,
                            "file_type": file_type,
                            "path": rel_path,
                            "content": content,
                            "tokens": tokens,
                        })
                    except Exception as e:
                        print(f"  Error reading {f}: {e}")

    docs.extend(collect_sql_queries())
    return docs


def build_index(docs):
    corpus = [d["tokens"] for d in docs]
    bm25 = BM25Okapi(corpus)
    return bm25


def main():
    docs = collect_docs()
    if not docs:
        print("ERROR: No documents found. Run clone_commerce_repos.sh first.")
        sys.exit(1)

    print(f"Indexed {len(docs)} files")
    by_type = {}
    for d in docs:
        by_type[d["file_type"]] = by_type.get(d["file_type"], 0) + 1
    for ft, count in sorted(by_type.items()):
        print(f"  {ft:12s} {count} files")

    print("Building BM25 index...")
    bm25 = build_index(docs)

    store = {"bm25": bm25, "docs": docs}
    with open(INDEX_FILE, "wb") as fh:
        pickle.dump(store, fh)

    size_kb = INDEX_FILE.stat().st_size // 1024
    print(f"\nSaved index: {INDEX_FILE} ({size_kb} KB)")
    print("Run: python3 mcp_server.py  (or  python3 search_cli.py <query>)")


if __name__ == "__main__":
    main()
