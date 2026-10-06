#!/usr/bin/env python3
"""Build, export, and bundle all three indexes without deploying them."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
APP_BUILDER = ROOT / "app-builder"
INDEXES = (
    ("commerce", "commerce_brain.pkl", "commerce_brain_index.json", "search", "index_build.py", "export_index_json.py"),
    ("kibana", "kibana_brain.pkl", "kibana_brain_index.json", "search-kibana", "kibana_index_build.py", "export_kibana_json.py"),
    ("saas", "saas_brain.pkl", "saas_brain_index.json", "search-saas", "saas_index_build.py", "export_saas_json.py"),
)


def run_script(script: str, env: dict) -> None:
    print(f"\n==> {script}", flush=True)
    subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, env=env, check=True)


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as target, source.open("rb") as original:
            shutil.copyfileobj(original, target)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, destination)
    except Exception:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_exports() -> Path:
    manifest = {
        "manifest_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "indexes": {},
    }
    for name, _pickle, export_name, action, *_ in INDEXES:
        exported = ROOT / export_name
        if not exported.is_file():
            raise FileNotFoundError(f"Expected export is missing: {exported}")
        bundle = APP_BUILDER / "actions" / action / "index.json"
        atomic_copy(exported, bundle)
        with exported.open(encoding="utf-8") as source:
            data = json.load(source)
        metadata = data.get("metadata", {})
        manifest["indexes"][name] = {
            "bundle_path": str(bundle.relative_to(APP_BUILDER)),
            "sha256": sha256(bundle),
            "document_count": data.get("n"),
            "index_format_version": metadata.get("index_format_version"),
            "build_version": metadata.get("build_version"),
            "built_at": metadata.get("built_at"),
            "source_provenance": metadata.get("source_provenance", "unavailable"),
            "source_repositories": metadata.get("source_repositories", []),
        }
        print(f"Bundled {name}: {bundle.relative_to(ROOT)}")

    manifest_path = APP_BUILDER / "index-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_path = tempfile.mkstemp(prefix=".index-manifest.", dir=manifest_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as destination:
            json.dump(manifest, destination, indent=2, allow_nan=False)
            destination.write("\n")
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary_path, manifest_path)
    except Exception:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise
    return manifest_path


def main() -> int:
    env = os.environ.copy()
    env.setdefault("COMMERCE_BRAIN_SOURCE_DIR", str(ROOT / "sources"))
    try:
        for *_, build_script, export_script in INDEXES:
            run_script(build_script, env)
            run_script(export_script, env)
        manifest_path = bundle_exports()
        print(f"\nPreflight manifest: {manifest_path}")
        subprocess.run(
            [sys.executable, str(ROOT / "verify_indexes.py")],
            cwd=ROOT,
            env=env,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: Index build pipeline failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
