import copy
import json
import pickle
import shutil
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import index_export
import mcp_server
import splunk_index_build


class SplunkReferenceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for curated action retrieval tests")
    def test_actual_export_and_action_retrieve_curated_golden_queries(self):
        docs = splunk_index_build.collect_docs()
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            actions = Path(directory) / "actions"
            action = actions / "search-splunk"
            action.mkdir(parents=True)
            for helper in ("bm25.js", "request-validation.js"):
                shutil.copyfile(root / "app-builder" / "actions" / helper, actions / helper)
            shutil.copyfile(root / "app-builder/actions/search-splunk/index.js", action / "index.js")
            source = Path(directory) / "source.pkl"
            source.write_bytes(pickle.dumps({"docs": docs}))
            index_export.export_index(source, action / "index.json", 12000)
            subprocess.run(["node", "-e", """
const assert = require('assert');
const { main } = require(process.argv[1]);
(async () => {
  const cases = [
    ['SKU sync timeline', 'live-search', 'paas', 'ls-sku-timeline'],
    ['Sensei Cell upstream errors', 'product-recommendations', 'cell', 'prex-sensei-cell'],
    ['HTTP 400 without PayPalOrderID', 'payment-services', 'paas', 'pay-no-order-id'],
    ['non-success response conflict', 'payment-services', 'cell', 'pay-http-status-caveat']
  ];
  for (const [query, service, platform, expected] of cases) {
    const response = await main({ query, service, platform, top_k: 1 });
    assert.strictEqual(response.statusCode, 200);
    const data = JSON.parse(response.body);
    assert.strictEqual(data.reference_only, true);
    assert.strictEqual(data.results[0].id, expected);
    assert.ok(data.results[0].source_url.startsWith('https://wiki.corp.adobe.com/'));
    assert.ok(data.results[0].content.includes('```spl'));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
""", str(action)], check=True, capture_output=True, text=True)

    def test_curated_collection_has_sources_and_all_services(self):
        docs = splunk_index_build.collect_docs()
        self.assertEqual(len(docs), 17)
        self.assertEqual({s for doc in docs for s in doc["services"]}, splunk_index_build.SERVICES)
        for doc in docs:
            self.assertIn("pageId=", doc["source_url"])
            self.assertGreater(doc["source_revision"], 0)
            self.assertIn("not-live-tested", doc["validation_status"])
            self.assertEqual(doc["content"].count("```") % 2, 0)
        conflict = next(doc for doc in docs if doc["id"] == "pay-http-status-caveat")
        self.assertEqual(conflict["validation_status"], "source-conflict-not-live-tested")

    def test_collection_rejects_bad_provenance_sensitive_values_and_truncated_queries(self):
        original = json.loads(splunk_index_build.SOURCE.read_text())
        changes = [
            lambda data: data["sources"]["ls-sync"].update(revision=None),
            lambda data: data["sources"]["ls-sync"].update(url="http://wiki.corp.adobe.com/test"),
            lambda data: data["sources"]["ls-sync"].update(reviewed_at="2026-02-30"),
            lambda data: data["records"][0].update(source=[]),
            lambda data: data["records"][0].update(services=[{}]),
            lambda data: data.update(format_version=True),
            lambda data: data["records"][0].update(content="email=user@example.com"),
            lambda data: data["records"][0].update(content="```spl\nindex=test"),
            lambda data: data["records"][0].update(content="x" * 12001),
            lambda data: data["records"][0].update(platform="unknown"),
            lambda data: data["records"][1].update(id=data["records"][0]["id"]),
        ]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = copy.deepcopy(original)
                change(data)
                path = Path(directory) / "references.json"
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    splunk_index_build.collect_docs(path)

    def test_export_preserves_complete_content_and_reference_metadata(self):
        docs = splunk_index_build.collect_docs()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pkl"
            source.write_bytes(pickle.dumps({"docs": docs}))
            exported = index_export.export_index(source, Path(directory) / "export.json", 100)
        self.assertEqual(exported["content_policy"]["splunk_reference"], "full")
        for original, doc in zip(docs, exported["docs"]):
            self.assertEqual(doc["content"], original["content"])
            for field in ("services", "platform", "environment", "source_url", "source_revision",
                          "reviewed_at", "validation_status", "source_title"):
                self.assertEqual(doc[field], original[field])

    def test_mcp_routes_filters_and_renders_provenance(self):
        doc = splunk_index_build.collect_docs()[0]
        with patch.object(mcp_server, "_call", return_value={"results": [doc]}) as call:
            response = mcp_server.handle({
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": "search_splunk_log_reference", "arguments": {
                    "query": "SKU sync", "service": "live-search", "platform": "paas", "top_k": 2
                }}
            })
        call.assert_called_once_with("search-splunk", "SKU sync", 2, service="live-search", platform="paas")
        text = response["result"]["content"][0]["text"]
        self.assertIn(doc["source_url"], text)
        self.assertIn("revision 2", text)
        self.assertIn("not-live-tested", text)
        self.assertIn("no searches executed", text)

    def test_mcp_validation_and_missing_reference_are_explicit(self):
        with patch.object(mcp_server, "_call") as call:
            for args in ({"query": ""}, {"query": "test", "service": "unknown"},
                         {"query": "test", "platform": "unknown"}, {"query": "test", "top_k": 0}):
                result = mcp_server._dispatch("search_splunk_log_reference", args, 1)
                self.assertTrue(result["result"]["isError"])
            call.assert_not_called()
        with patch.object(mcp_server, "_call", return_value={"results": []}):
            self.assertIn("does not mean no logs", mcp_server.search_splunk_log_reference("not documented"))
        tool_names = {tool["name"] for tool in mcp_server.TOOLS}
        self.assertIn("search_splunk_log_reference", tool_names)

    def test_mcp_handles_malformed_splunk_response_safely(self):
        with patch.object(mcp_server, "_call", return_value={"results": [{"services": [None]}]}):
            response = mcp_server._dispatch("search_splunk_log_reference", {"query": "test"}, 1)
        self.assertTrue(response["result"]["isError"])
        self.assertIn("invalid Splunk reference", response["result"]["content"][0]["text"])

    def test_unreleased_route_failure_is_a_safe_tool_error(self):
        error = urllib.error.HTTPError("https://example.invalid/private", 404, "private detail", {}, None)
        with patch.object(mcp_server.urllib.request, "urlopen", side_effect=error):
            response = mcp_server._dispatch("search_splunk_log_reference", {"query": "HTTP 400"}, 1)
        self.assertTrue(response["result"]["isError"])
        text = response["result"]["content"][0]["text"]
        self.assertIn("HTTP status 404", text)
        self.assertNotIn("private", text)


if __name__ == "__main__":
    unittest.main()
