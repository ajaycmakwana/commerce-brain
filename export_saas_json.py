#!/usr/bin/env python3
"""Export the SaaS BM25 index for its App Builder action."""
from pathlib import Path

from index_export import export_index


def main():
    root = Path(__file__).parent
    export_index(root / "saas_brain.pkl", root / "saas_brain_index.json", 3000)


if __name__ == "__main__":
    main()
