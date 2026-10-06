"""Version and provenance metadata shared by all generated search indexes."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

INDEX_FORMAT_VERSION = 2
BUILD_VERSION = 1


def _git_value(path: Path, *args: str) -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _is_checkout_root(path: Path) -> bool:
    try:
        root = subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        ).strip()
        return Path(root).resolve() == path.resolve()
    except (OSError, subprocess.SubprocessError):
        return False


def _git_dirty(path: Path) -> Optional[bool]:
    try:
        status = subprocess.check_output(
            ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return bool(status.strip())
    except (OSError, subprocess.SubprocessError):
        return None


def build_metadata(paths: list[Path]) -> dict:
    """Capture only locally available source provenance; never invent a version."""
    project_root = Path(__file__).parent.resolve()
    sources = []
    for path in paths:
        checkout = _is_checkout_root(path)
        sources.append({
            "repository": "commerce-brain" if path.resolve() == project_root else path.name,
            "ref": _git_value(path, "symbolic-ref", "--short", "-q", "HEAD") if checkout else None,
            "commit": _git_value(path, "rev-parse", "HEAD") if checkout else None,
            "dirty": _git_dirty(path) if checkout else None,
        })
    clean_versioned = sum(bool(source["commit"]) and source["dirty"] is False for source in sources)
    versioned = sum(bool(source["commit"]) for source in sources)
    status = (
        "complete" if sources and clean_versioned == len(sources)
        else "partial" if versioned
        else "unavailable"
    )
    return {
        "index_format_version": INDEX_FORMAT_VERSION,
        "build_version": BUILD_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source_provenance": status,
        "source_repositories": sources,
    }
