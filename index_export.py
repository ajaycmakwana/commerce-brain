"""Export a BM25 pickle to the JSON format consumed by App Builder actions."""

import json
import math
import os
import pickle
import tempfile
from collections import Counter
from pathlib import Path


def export_index(index_file: Path, output_file: Path, snippet_limit: int) -> dict:
    with index_file.open("rb") as source:
        store = pickle.load(source)

    docs = store.get("docs")
    if not isinstance(docs, list) or not docs:
        raise ValueError(f"No documents available in {index_file}")

    count = len(docs)
    document_frequency = Counter(
        term for doc in docs for term in set(doc.get("tokens", []))
    )
    idf = {
        term: math.log((count - frequency + 0.5) / (frequency + 0.5) + 1)
        for term, frequency in document_frequency.items()
    }
    average_length = sum(len(doc.get("tokens", [])) for doc in docs) / count
    export_docs = []
    for doc in docs:
        content = doc.get("content", "")
        is_schema = doc.get("file_type") == "db_schema"
        exported = {
            key: doc[key]
            for key in ("repo", "file_type", "path", "source", "title")
            if key in doc
        }
        exported.update({
            "tokens": doc.get("tokens", []),
            "term_freqs": dict(Counter(doc.get("tokens", []))),
            "content": content if is_schema else content[:snippet_limit],
        })
        export_docs.append(exported)

    metadata = store.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {
            "index_format_version": 2,
            "build_version": 1,
            "built_at": None,
            "source_provenance": "unavailable",
            "source_repositories": [],
        }
    output = {
        "metadata": metadata,
        "content_policy": {
            "db_schema": "full",
            "other": f"bounded to {snippet_limit} characters",
        },
        "n": count,
        "avgdl": round(average_length, 2),
        "idf": idf,
        "docs": export_docs,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix=f".{output_file.name}.", dir=output_file.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as destination:
            json.dump(output, destination, separators=(",", ":"), allow_nan=False)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary_path, output_file)
    except Exception:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise

    print(f"Exported {count} documents: {output_file} ({output_file.stat().st_size // 1024} KB)")
    return output
