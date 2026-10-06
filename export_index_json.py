#!/usr/bin/env python3
"""Export the Commerce BM25 index for the App Builder search action."""

from pathlib import Path

from index_export import export_index

BRAIN_DIR = Path(__file__).parent


def main():
    export_index(
        BRAIN_DIR / "commerce_brain.pkl",
        BRAIN_DIR / "commerce_brain_index.json",
        snippet_limit=2000,
    )


if __name__ == "__main__":
    main()
