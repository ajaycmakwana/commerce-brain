#!/usr/bin/env bash
# Build the local reference indexes and bundle all three App Builder indexes.
set -euo pipefail

BRAIN_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="${COMMERCE_BRAIN_SOURCE_DIR:-$BRAIN_DIR/sources}"
SOURCE_DIR="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$SOURCE_DIR")"
export COMMERCE_BRAIN_SOURCE_DIR="$SOURCE_DIR"
ORG="https://github.com/magento-sparta"

echo "Commerce Brain source directory: $SOURCE_DIR"

if ! python3 -c "import rank_bm25" >/dev/null 2>&1; then
    echo "Installing the required rank-bm25 Python package..."
    python3 -m pip install rank-bm25
fi

mkdir -p "$SOURCE_DIR"
if [ -z "${GITHUB_TOKEN:-}" ]; then
    read -r -s -p "GitHub PAT with magento-sparta SSO access (or press Enter to use configured Git credentials): " GITHUB_TOKEN
    echo
fi

ASKPASS=""
if [ -n "${GITHUB_TOKEN:-}" ]; then
    ASKPASS="$(mktemp "${TMPDIR:-/tmp}/commerce-brain-askpass.XXXXXX")"
    cat > "$ASKPASS" <<'ASKPASS_SCRIPT'
#!/bin/sh
case "$1" in
  *sername*) printf '%s\n' x-access-token ;;
  *) printf '%s\n' "$GITHUB_TOKEN" ;;
esac
ASKPASS_SCRIPT
    chmod 700 "$ASKPASS"
    export GIT_ASKPASS="$ASKPASS"
    export GIT_TERMINAL_PROMPT=0
    export GITHUB_TOKEN
fi
cleanup() {
    if [ -n "$ASKPASS" ]; then
        rm -f "$ASKPASS"
    fi
}
trap cleanup EXIT

clone_or_update() {
    local repo="$1" branch="$2" target="$SOURCE_DIR/$1"
    if [ ! -e "$target" ]; then
        echo "Cloning $repo ($branch)..."
        git clone --depth 1 --branch "$branch" "$ORG/$repo.git" "$target"
        return
    fi
    if [ ! -d "$target/.git" ] && [ ! -f "$target/.git" ]; then
        echo "ERROR: $target exists but is not a Git checkout; leaving it unchanged." >&2
        return 1
    fi
    if [ -n "$(git -C "$target" status --porcelain --untracked-files=all)" ]; then
        echo "Preserving modified $repo checkout; not updating it."
        return
    fi
    local current_branch
    current_branch="$(git -C "$target" symbolic-ref --short -q HEAD || true)"
    if [ "$current_branch" != "$branch" ]; then
        echo "Preserving $repo on branch '${current_branch:-detached}'; expected $branch, not updating it."
        return
    fi
    echo "Fast-forwarding clean $repo checkout..."
    git -C "$target" fetch --depth 50 origin "$branch"
    if git -C "$target" merge-base --is-ancestor HEAD FETCH_HEAD; then
        git -C "$target" merge --ff-only FETCH_HEAD
    else
        echo "Cannot prove a fast-forward for $repo; preserving it unchanged. Update it manually if needed."
    fi
}

echo "Preparing source repositories (dirty/non-target checkouts are never reset)..."
clone_or_update magento2ce 2.4-develop
clone_or_update magento2ee 2.4-develop
clone_or_update magento2b2b develop
clone_or_update inventory develop
clone_or_update commerce-data-export main
clone_or_update commerce-data-export-ee main
clone_or_update magento-live-search main
clone_or_update magento-product-recommendations main
clone_or_update magento-product-recommendations-admin main
clone_or_update magento-catalog-sync-admin main
clone_or_update saas-export main
clone_or_update data-services main
clone_or_update data-services-graphql master
clone_or_update services-connector main
clone_or_update services-id main
clone_or_update adobe-stock-integration develop
clone_or_update adobe-ims develop
clone_or_update magento2-page-builder develop
clone_or_update magento2-page-builder-ee develop
clone_or_update magento2-payments main
clone_or_update ext-braintree master
clone_or_update security-package develop
clone_or_update security-package-b2b develop
clone_or_update security-package-ee 1.0-develop

unset GITHUB_TOKEN GIT_ASKPASS GIT_TERMINAL_PROMPT

echo "Building, exporting, and bundling Commerce, Kibana, and SaaS indexes..."
python3 "$BRAIN_DIR/build_indexes.py"

cat <<EOF

All local indexes were built and bundled. No deployment was performed.
Select clients explicitly to install the stdio MCP configuration, for example:
  bash "$BRAIN_DIR/install.sh" copilot
  bash "$BRAIN_DIR/install.sh" claude-code
Supported clients: claude-code, claude-desktop, cursor, copilot, vscode
EOF
