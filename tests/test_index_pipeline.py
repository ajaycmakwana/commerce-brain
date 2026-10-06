import json
import pickle
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_indexes
import index_build
import index_export
import index_metadata
import verify_indexes


class IndexPipelineTests(unittest.TestCase):
    def test_collection_excludes_worktree_container_from_source_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for repo in ("source-module", "copilot-worktrees"):
                source = root / repo / "etc" / "db_schema.xml"
                source.parent.mkdir(parents=True)
                source.write_text(
                    '<schema><table name="fixture_table"><column name="id"/></table></schema>',
                    encoding="utf-8",
                )
            with patch.object(index_build, "REPOS_DIR", root), \
                    patch.object(index_build, "COMMERCE_QUERIES_DIR", root / "missing-queries"):
                docs = index_build.collect_docs()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["repo"], "source-module")

    def test_schema_chunking_keeps_complete_declarations_and_names(self):
        xml = (
            '<schema xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<table name="sample_table"><column name="entity_id" '
            'xsi:type="int" nullable="false"/><constraint xsi:type="primary">'
            '<column name="entity_id"/></constraint></table></schema>'
        )
        chunks = index_build.chunk_db_schema(xml, "module/etc/db_schema.xml", "module")
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0]["path"].endswith(" :: sample_table"))
        self.assertIn("</table>", chunks[0]["content"])
        self.assertIn("entity_id", chunks[0]["content"])

    def test_schema_chunking_recovers_namespace_and_malformed_table_blocks(self):
        namespaced = (
            '<schema xmlns="urn:commerce"><table name="first_table">'
            '<column name="id"/></table></schema>'
        )
        self.assertEqual(
            index_build.chunk_db_schema(namespaced, "schema.xml", "module")[0]["path"],
            "schema.xml :: first_table",
        )
        malformed = (
            '<schema><table name="first_table"><column name="id"></table>'
            '<table name="second_table"><column name="sku"></table></schema>'
        )
        chunks = index_build.chunk_db_schema(malformed, "schema.xml", "module")
        self.assertEqual([chunk["path"] for chunk in chunks], [
            "schema.xml :: first_table", "schema.xml :: second_table"
        ])

    def test_export_preserves_full_schema_and_bounds_regular_search_snippets(self):
        long_schema = "schema-source-" + ("x" * 2500) + "</table>"
        regular_content = "ordinary-source-" + ("y" * 2500)
        docs = [
            {"repo": "module-a", "file_type": "db_schema", "path": "a.xml :: sample_table",
             "content": long_schema, "tokens": ["sample_table", "column"]},
            {"source": "queries", "title": "example", "content": regular_content,
             "tokens": ["example", "query"]},
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            pickle_path = Path(temp_dir) / "index.pkl"
            output_path = Path(temp_dir) / "index.json"
            with pickle_path.open("wb") as output:
                pickle.dump({"docs": docs}, output)
            exported = index_export.export_index(pickle_path, output_path, snippet_limit=2000)

        self.assertEqual(exported["docs"][0]["content"], long_schema)
        self.assertEqual(len(exported["docs"][1]["content"]), 2000)
        self.assertEqual(exported["docs"][0]["term_freqs"]["sample_table"], 1)
        self.assertEqual(exported["metadata"]["source_provenance"], "unavailable")
        self.assertIsNone(exported["metadata"]["built_at"])

    def test_missing_git_provenance_is_marked_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata = index_metadata.build_metadata([Path(temp_dir)])
        self.assertEqual(metadata["source_provenance"], "unavailable")
        self.assertIsNone(metadata["source_repositories"][0]["commit"])
        self.assertIsNone(metadata["source_repositories"][0]["ref"])
        self.assertIsNone(metadata["source_repositories"][0]["dirty"])

    def test_git_provenance_marks_dirty_source_checkouts_as_partial(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            checkout = Path(temp_dir)
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            source = checkout / "source.md"
            source.write_text("fixture", encoding="utf-8")
            subprocess.run(["git", "-C", str(checkout), "add", "source.md"], check=True)
            subprocess.run([
                "git", "-C", str(checkout), "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"
            ], check=True)
            clean = index_metadata.build_metadata([checkout])
            source.write_text("modified fixture", encoding="utf-8")
            dirty = index_metadata.build_metadata([checkout])

        self.assertEqual(clean["source_provenance"], "complete")
        self.assertFalse(clean["source_repositories"][0]["dirty"])
        self.assertEqual(dirty["source_provenance"], "partial")
        self.assertTrue(dirty["source_repositories"][0]["dirty"])

    def test_pipeline_bundles_and_verifies_all_three_indexes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_builder = root / "app-builder"
            indexes = (
                ("commerce", "commerce.pkl", "commerce.json", "search", "", ""),
                ("kibana", "kibana.pkl", "kibana.json", "search-kibana", "", ""),
                ("saas", "saas.pkl", "saas.json", "search-saas", "", ""),
            )
            for name, _pickle, export_name, _action, *_ in indexes:
                docs = (
                    [{"file_type": "db_schema", "path": "module/etc/db_schema.xml :: sample_table",
                      "content": "<table></table>", "tokens": ["sample_table"], "term_freqs": {"sample_table": 1}}]
                    if name == "commerce"
                    else [{"source": name, "title": "fixture", "content": "fixture", "tokens": ["fixture"],
                           "term_freqs": {"fixture": 1}}]
                )
                data = {
                    "metadata": {
                        "index_format_version": 2, "build_version": 1, "built_at": "fixture",
                        "source_provenance": "unavailable", "source_repositories": []
                    },
                    "content_policy": {"db_schema": "full", "other": "bounded"},
                    "n": len(docs), "avgdl": 1, "idf": {}, "docs": docs
                }
                (root / export_name).write_text(json.dumps(data), encoding="utf-8")

            with patch.object(build_indexes, "ROOT", root), \
                    patch.object(build_indexes, "APP_BUILDER", app_builder), \
                    patch.object(build_indexes, "INDEXES", indexes), \
                    patch.object(verify_indexes, "APP_BUILDER", app_builder):
                manifest_path = build_indexes.bundle_exports()
                self.assertEqual(verify_indexes.verify(), [])
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(set(manifest["indexes"]), {"commerce", "kibana", "saas"})
                (app_builder / "actions/search-kibana/index.json").write_text("{}", encoding="utf-8")
                self.assertTrue(any("SHA-256" in error for error in verify_indexes.verify()))


if __name__ == "__main__":
    unittest.main()
