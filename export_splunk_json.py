#!/usr/bin/env python3
"""Export complete curated references, including complete SPL code blocks."""

from pathlib import Path

from index_export import export_index
from splunk_index_build import MAX_CONTENT

ROOT = Path(__file__).parent

if __name__ == "__main__":
    export_index(ROOT / "splunk_brain.pkl", ROOT / "splunk_brain_index.json", MAX_CONTENT)
