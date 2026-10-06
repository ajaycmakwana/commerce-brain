#!/usr/bin/env python3
"""Verify all bundled indexes against the generated deployment manifest."""

import hashlib
import json
import math
import sys
from pathlib import Path

APP_BUILDER = Path(__file__).parent / "app-builder"
EXPECTED = {
    "commerce": ("actions/search/index.json", "full"),
    "kibana": ("actions/search-kibana/index.json", None),
    "saas": ("actions/search-saas/index.json", None),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> list[str]:
    manifest_path = APP_BUILDER / "index-manifest.json"
    if not manifest_path.is_file():
        return [f"Missing generated manifest: {manifest_path}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"Invalid manifest: {error}"]
    if not isinstance(manifest, dict):
        return ["Manifest root must be a JSON object."]
    if manifest.get("manifest_version") != 1:
        return ["Unsupported or missing manifest version."]
    if not isinstance(manifest.get("created_at"), str) or not manifest["created_at"]:
        return ["Manifest has no creation timestamp."]

    errors = []
    indexes = manifest.get("indexes")
    if not isinstance(indexes, dict):
        return ["Manifest has no indexes map."]
    for name, (relative_path, required_schema_policy) in EXPECTED.items():
        entry = indexes.get(name)
        bundle = APP_BUILDER / relative_path
        if not isinstance(entry, dict):
            errors.append(f"Manifest entry missing for {name}.")
            continue
        if not bundle.is_file():
            errors.append(f"Bundled index missing: {relative_path}.")
            continue
        if entry.get("bundle_path") != relative_path:
            errors.append(f"{name}: manifest bundle path does not match.")
        if entry.get("sha256") != sha256(bundle):
            errors.append(f"{name}: bundled index SHA-256 does not match manifest.")
        try:
            data = json.loads(bundle.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{name}: invalid JSON: {error}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{name}: index root must be a JSON object.")
            continue
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{name}: missing index metadata.")
            metadata = {}
        docs = data.get("docs")
        if not isinstance(docs, list) or not docs:
            errors.append(f"{name}: index contains no documents.")
            continue
        if data.get("n") != len(docs) or entry.get("document_count") != len(docs):
            errors.append(f"{name}: document count does not match manifest.")
        if metadata.get("index_format_version") != 2:
            errors.append(f"{name}: unsupported or missing index format version.")
        if metadata.get("index_format_version") != entry.get("index_format_version"):
            errors.append(f"{name}: index format version does not match manifest.")
        if metadata.get("build_version") != 1 or metadata.get("build_version") != entry.get("build_version"):
            errors.append(f"{name}: build version does not match manifest.")
        if metadata.get("built_at") != entry.get("built_at"):
            errors.append(f"{name}: build timestamp does not match manifest.")
        provenance = metadata.get("source_provenance")
        sources = metadata.get("source_repositories")
        if not isinstance(provenance, str) or provenance not in {"complete", "partial", "unavailable"} or not isinstance(sources, list):
            errors.append(f"{name}: invalid source provenance metadata.")
        else:
            malformed_source = any(
                not isinstance(source, dict)
                or not isinstance(source.get("repository"), str)
                or (source.get("ref") is not None and not isinstance(source.get("ref"), str))
                or (source.get("commit") is not None and not isinstance(source.get("commit"), str))
                or (source.get("dirty") is not None and not isinstance(source.get("dirty"), bool))
                for source in sources
            )
            if malformed_source:
                errors.append(f"{name}: invalid source repository metadata.")
            elif provenance == "complete" and (
                not sources or any(not source.get("commit") or source.get("dirty") is not False for source in sources)
            ):
                errors.append(f"{name}: provenance marked complete but a source is unversioned or dirty.")
            elif provenance == "partial" and (
                not any(source.get("commit") for source in sources)
                or all(source.get("commit") and source.get("dirty") is False for source in sources)
            ):
                errors.append(f"{name}: provenance marked partial without dirty or unversioned sources.")
            elif provenance == "unavailable" and any(source.get("commit") for source in sources):
                errors.append(f"{name}: provenance marked unavailable but a source commit is present.")
        if metadata.get("source_provenance") != entry.get("source_provenance"):
            errors.append(f"{name}: source provenance status does not match manifest.")
        if metadata.get("source_repositories") != entry.get("source_repositories"):
            errors.append(f"{name}: source repositories do not match manifest.")
        idf = data.get("idf")
        avgdl = data.get("avgdl")
        if not isinstance(idf, dict) or not isinstance(avgdl, (int, float)) or not math.isfinite(avgdl) or avgdl <= 0:
            errors.append(f"{name}: invalid BM25 scoring metadata.")
        for index, doc in enumerate(docs):
            if not isinstance(doc, dict) or not isinstance(doc.get("tokens"), list):
                errors.append(f"{name}: invalid document at position {index}.")
                continue
            if not isinstance(doc.get("term_freqs"), dict):
                errors.append(f"{name}: missing term frequencies at document position {index}.")
            if not isinstance(doc.get("content"), str):
                errors.append(f"{name}: invalid content at document position {index}.")
        content_policy = data.get("content_policy")
        if not isinstance(content_policy, dict):
            errors.append(f"{name}: missing content policy.")
            content_policy = {}
        if required_schema_policy and content_policy.get("db_schema") != required_schema_policy:
            errors.append(f"{name}: db_schema content is not marked complete.")
        if name == "commerce" and not any(
            isinstance(doc, dict) and doc.get("file_type") == "db_schema" for doc in docs
        ):
            errors.append("commerce: index has no db_schema documents.")
    extra = set(indexes) - set(EXPECTED)
    if extra:
        errors.append(f"Unexpected manifest index entries: {', '.join(sorted(extra))}.")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("All three bundled indexes match the manifest and passed structural checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
