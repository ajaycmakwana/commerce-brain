#!/usr/bin/env bash
# Install/update Commerce Brain's stdio MCP entry for explicitly selected clients.
set -euo pipefail

BRAIN_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_SERVER="$BRAIN_DIR/mcp_server.py"
if ! command -v python3 >/dev/null 2>&1 || [ ! -r "$MCP_SERVER" ]; then
    echo "ERROR: Python 3 and the readable mcp_server.py are required." >&2
    exit 1
fi

if [ "$#" -gt 0 ]; then
    CLIENT_SELECTION="$*"
else
    echo "Choose one or more MCP clients (comma-separated):"
    echo "  claude-code, claude-desktop, cursor, copilot, vscode"
    read -r -p "> " CLIENT_SELECTION
fi
CLIENT_SELECTION="${CLIENT_SELECTION// /}"
IFS=',' read -r -a CLIENTS <<< "$CLIENT_SELECTION"
if [ "${#CLIENTS[@]}" -eq 0 ] || [ -z "${CLIENTS[0]}" ]; then
    echo "ERROR: Select at least one client." >&2
    exit 1
fi
for client in "${CLIENTS[@]}"; do
    case "$client" in
        claude-code|claude-desktop|cursor|copilot|vscode) ;;
        *) echo "ERROR: Unsupported client '$client'." >&2; exit 1 ;;
    esac
done

python3 - "$MCP_SERVER" "${CLIENTS[@]}" <<'PY'
import json
import os
import platform
import stat
import sys
import tempfile
from pathlib import Path

server_path = str(Path(sys.argv[1]).resolve())
clients = sys.argv[2:]
home = Path.home()
python_path = sys.executable
entry = {"type": "stdio", "command": python_path, "args": [server_path]}

def config_path(client):
    system = platform.system()
    if client == "claude-code":
        return home / ".claude.json", ("mcpServers",)
    if client == "claude-desktop":
        if system == "Darwin":
            return home / "Library/Application Support/Claude/claude_desktop_config.json", ("mcpServers",)
        return home / ".config/Claude/claude_desktop_config.json", ("mcpServers",)
    if client == "cursor":
        return home / ".cursor/mcp.json", ("mcpServers",)
    if client == "copilot":
        return home / ".copilot/mcp-config.json", ("mcpServers",)
    if client == "vscode":
        if system == "Darwin":
            path = home / "Library/Application Support/Code/User/settings.json"
        elif system == "Windows":
            path = Path(os.environ.get("APPDATA", home)) / "Code/User/settings.json"
        else:
            path = home / ".config/Code/User/settings.json"
        return path, ("mcp", "servers")
    raise ValueError(f"Unsupported client: {client}")

def atomic_write(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(data, output, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

for client in clients:
    path, nesting = config_path(client)
    if path.exists():
        try:
            with path.open(encoding="utf-8") as source:
                config = json.load(source)
        except (OSError, json.JSONDecodeError) as error:
            raise SystemExit(f"ERROR: Cannot safely update {path}: {error}")
        if not isinstance(config, dict):
            raise SystemExit(f"ERROR: Cannot safely update {path}: top-level JSON value must be an object")
        mode = stat.S_IMODE(path.stat().st_mode)
    else:
        config = {}
        mode = 0o600

    target = config
    for key in nesting[:-1]:
        current = target.get(key)
        if current is None:
            current = {}
            target[key] = current
        if not isinstance(current, dict):
            raise SystemExit(f"ERROR: Cannot safely update {path}: '{key}' must be an object")
        target = current
    servers_key = nesting[-1]
    servers = target.get(servers_key)
    if servers is None:
        servers = {}
        target[servers_key] = servers
    if not isinstance(servers, dict):
        raise SystemExit(f"ERROR: Cannot safely update {path}: '{servers_key}' must be an object")
    if servers.get("commerce-brain") == entry:
        print(f"Already current: {client} ({path})")
        continue
    servers["commerce-brain"] = entry
    atomic_write(path, config, mode)
    print(f"Configured: {client} ({path})")
PY
