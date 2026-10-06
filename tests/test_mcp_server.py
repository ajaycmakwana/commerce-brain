import io
import json
import unittest
import urllib.parse
from unittest.mock import patch

import mcp_server


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class McpServerTests(unittest.TestCase):
    def test_initialize_ping_and_notifications_follow_jsonrpc(self):
        initialized = mcp_server.handle({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"}
        })
        self.assertEqual(initialized["result"]["protocolVersion"], "2024-11-05")
        self.assertEqual(initialized["result"]["serverInfo"]["version"], "4.1.0")
        self.assertEqual(mcp_server.handle({"jsonrpc": "2.0", "id": 2, "method": "ping"})["result"], {})
        self.assertIsNone(mcp_server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_invalid_and_unknown_requests_have_protocol_errors(self):
        self.assertEqual(mcp_server.handle({"jsonrpc": "1.0", "id": 1, "method": "ping"})["error"]["code"], -32600)
        self.assertEqual(mcp_server.handle({"id": 1})["error"]["code"], -32600)
        self.assertEqual(mcp_server.handle({"jsonrpc": "2.0", "id": 1, "method": "not/a/method"})["error"]["code"], -32601)
        self.assertIsNone(mcp_server.handle({"jsonrpc": "2.0", "method": "unknown-notification"}))

    def test_tools_call_validates_arguments_without_network_calls(self):
        with patch.object(mcp_server.urllib.request, "urlopen") as urlopen:
            response = mcp_server.handle({
                "jsonrpc": "2.0", "id": 7, "method": "tools/call",
                "params": {"name": "search_commerce_knowledge", "arguments": {"query": "  ", "top_k": 2}}
            })
        self.assertTrue(response["result"]["isError"])
        self.assertIn("non-empty", response["result"]["content"][0]["text"])
        urlopen.assert_not_called()

    def test_tools_call_rejects_unexpected_arguments(self):
        response = mcp_server.handle({
            "jsonrpc": "2.0", "id": 8, "method": "tools/call",
            "params": {"name": "search_commerce_knowledge", "arguments": {"query": "feed", "surprise": True}}
        })
        self.assertTrue(response["result"]["isError"])
        self.assertIn("Unsupported argument", response["result"]["content"][0]["text"])

    def test_exact_schema_lookup_uses_unranked_request_and_returns_every_declaration(self):
        declarations = [
            {"file_type": "db_schema", "path": "repo-a/etc/db_schema.xml :: sample_table",
             "content": "<table name='sample_table'>a</table>"},
            {"file_type": "db_schema", "path": "repo-b/etc/db_schema.xml :: sample_table",
             "content": "<table name='sample_table'>b</table>"},
        ]
        with patch.object(mcp_server.urllib.request, "urlopen", return_value=FakeResponse({"results": declarations})) as urlopen:
            output = mcp_server.search_db_schema("sample_table")
        request_url = urlopen.call_args.args[0]
        params = urllib.parse.parse_qs(urllib.parse.urlparse(request_url).query)
        self.assertEqual(params, {"table_name": ["sample_table"]})
        self.assertIn("2 source declaration(s)", output)
        self.assertIn("repo-a", output)
        self.assertIn("repo-b", output)

    def test_missing_table_and_invalid_name(self):
        with patch.object(mcp_server, "_call", return_value={"results": []}):
            self.assertIn("not found", mcp_server.search_db_schema("missing_table"))
        with self.assertRaises(ValueError):
            mcp_server.search_db_schema("sample;DROP")

    def test_bad_top_k_is_rejected_and_not_silently_clamped(self):
        for value in (0, -1, 11, 1.2, True, "5"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                mcp_server._validated_top_k(value)

    def test_main_returns_parse_error_and_keeps_stdout_protocol_only(self):
        input_stream = io.StringIO("not-json\n" + json.dumps({"jsonrpc": "2.0", "id": 3, "method": "ping"}) + "\n")
        output_stream = io.StringIO()
        with patch("sys.stdin", input_stream), patch("sys.stdout", output_stream):
            mcp_server.main()
        responses = [json.loads(line) for line in output_stream.getvalue().splitlines()]
        self.assertEqual([response["error"]["code"] for response in responses[:1]], [-32700])
        self.assertEqual(responses[1]["result"], {})


if __name__ == "__main__":
    unittest.main()
