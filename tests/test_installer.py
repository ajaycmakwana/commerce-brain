import json
import os
import platform
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_copilot_and_vscode_install_preserves_settings_and_updates_stale_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            copilot = home / ".copilot/mcp-config.json"
            copilot.parent.mkdir()
            copilot.write_text(json.dumps({
                "otherSetting": {"keep": True},
                "mcpServers": {
                    "another-server": {"command": "other"},
                    "commerce-brain": {"command": "old-python", "args": ["old-server.py"]}
                }
            }), encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(home)
            result = subprocess.run(
                ["bash", str(ROOT / "install.sh"), "copilot,vscode"],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            config = json.loads(copilot.read_text(encoding="utf-8"))
            self.assertEqual(config["otherSetting"], {"keep": True})
            self.assertEqual(config["mcpServers"]["another-server"], {"command": "other"})
            self.assertEqual(config["mcpServers"]["commerce-brain"]["args"], [str(ROOT / "mcp_server.py")])
            self.assertIn("python", Path(config["mcpServers"]["commerce-brain"]["command"]).name.lower())

            vscode = (
                home / "Library/Application Support/Code/User/settings.json"
                if platform.system() == "Darwin"
                else home / ".config/Code/User/settings.json"
            )
            vscode_config = json.loads(vscode.read_text(encoding="utf-8"))
            entry = vscode_config["mcp"]["servers"]["commerce-brain"]
            self.assertEqual(entry["type"], "stdio")
            self.assertEqual(entry["args"], [str(ROOT / "mcp_server.py")])
            self.assertFalse((home / ".claude/settings.json").exists())

            second = subprocess.run(
                ["bash", str(ROOT / "install.sh"), "copilot"],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("Already current", second.stdout)

    def test_invalid_selection_does_not_create_client_configuration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["HOME"] = temp_dir
            result = subprocess.run(
                ["bash", str(ROOT / "install.sh"), "not-a-client"],
                cwd=ROOT, env=env, text=True, capture_output=True, check=False
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(temp_dir).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
