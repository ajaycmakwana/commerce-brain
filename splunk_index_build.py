#!/usr/bin/env python3
"""Build a local, curated Splunk reference index; never connect to Splunk."""

import json
import pickle
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from index_metadata import build_metadata

ROOT = Path(__file__).parent
SOURCE = ROOT / "splunk-reference" / "references.json"
SERVICES = {"live-search", "product-recommendations", "payment-services"}
PLATFORMS = {"paas", "cell", "any"}
STATUSES = {"source-reviewed-not-live-tested", "source-conflict-not-live-tested"}
SENSITIVE_PATTERN = re.compile(
    r"eyJ[A-Za-z0-9_-]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    r"|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)
MAX_CONTENT = 12000


def collect_docs(path=SOURCE):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or type(data.get("format_version")) is not int or data["format_version"] != 1:
        raise ValueError("Unsupported Splunk reference format")
    sources, records = data.get("sources"), data.get("records")
    if not isinstance(sources, dict) or not isinstance(records, list) or not records:
        raise ValueError("Splunk references require sources and nonempty records")
    docs, ids = [], set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Splunk reference record must be an object")
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("Splunk reference IDs must be nonempty and unique")
        ids.add(identifier)
        source_key = record.get("source")
        source = sources.get(source_key) if isinstance(source_key, str) else None
        if not isinstance(source, dict):
            raise ValueError(f"{identifier}: missing source")
        url = source.get("url")
        if not isinstance(url, str):
            raise ValueError(f"{identifier}: invalid source URL")
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https" or parsed_url.hostname != "wiki.corp.adobe.com" or parsed_url.username is not None:
            raise ValueError(f"{identifier}: invalid source URL")
        revision = source.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise ValueError(f"{identifier}: source revision is required")
        if not isinstance(source.get("reviewed_at"), str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["reviewed_at"]):
            raise ValueError(f"{identifier}: review date is required")
        try:
            date.fromisoformat(source["reviewed_at"])
        except ValueError:
            raise ValueError(f"{identifier}: invalid review date") from None
        if not isinstance(source.get("title"), str) or not source["title"].strip():
            raise ValueError(f"{identifier}: source title is required")
        services = record.get("services")
        if not isinstance(services, list) or not services or any(not isinstance(service, str) or service not in SERVICES for service in services):
            raise ValueError(f"{identifier}: invalid service labels")
        if record.get("platform") not in tuple(PLATFORMS) or record.get("environment") not in ("prod", "nonprod", "any"):
            raise ValueError(f"{identifier}: invalid applicability")
        if record.get("validation_status") not in tuple(STATUSES):
            raise ValueError(f"{identifier}: missing honest validation status")
        title, content = record.get("title"), record.get("content")
        if not isinstance(title, str) or not title.strip() or not isinstance(content, str) or not content.strip():
            raise ValueError(f"{identifier}: title and content required")
        if len(content) > MAX_CONTENT or content.count("```") % 2:
            raise ValueError(f"{identifier}: oversized content or incomplete code fence")
        if SENSITIVE_PATTERN.search(title + "\n" + content):
            raise ValueError(f"{identifier}: example identifier or sensitive-looking value requires review")
        doc = dict(record)
        doc.update({
            "file_type": "splunk_reference",
            "source_url": url,
            "source_title": source["title"],
            "source_revision": revision,
            "reviewed_at": source["reviewed_at"],
            "tokens": [term for term in re.split(r"[^a-zA-Z0-9_]+", title.lower() + " " + content.lower()) if len(term) > 2],
        })
        docs.append(doc)
    return docs


def main():
    docs = collect_docs()
    store = {"docs": docs, "metadata": build_metadata([ROOT])}
    with (ROOT / "splunk_brain.pkl").open("wb") as destination:
        pickle.dump(store, destination)
    print(f"Built {len(docs)} curated Splunk reference documents; no Splunk access performed.")


if __name__ == "__main__":
    main()
