"""Regression cases for provenance boundaries and deterministic credit generation."""
import json
from pathlib import Path
import tempfile
import unittest

from attributions import build_attributions


class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.write("LICENSES/LICENSE-MIT", "MIT License\nCopyright (c) SolidCraft contributors\n")
        self.records = []

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")
        return path

    def asset(self, aid, definition=None, **kwargs):
        folder = "assets/appearances/" + aid
        self.write(folder + "/definition.json", definition or {"id": aid})
        self.write(folder + "/extra.json", {"id": aid, "source_id": aid})
        record = {"id": aid, "path": folder, "name": aid, **kwargs}
        self.records.append(record)
        return record

    def build(self, **kwargs):
        return build_attributions(self.root, self.records, **kwargs)

    def test_scanned_authors_are_not_original_authors(self):
        row = self.asset("scan.one", {"source_url": "https://example.org/scan", "provider": "Scan provider", "authors": ["Named photographer"], "license": "CC0-1.0"}, method="scanned")
        result = self.build()["records"]["scan.one"]
        self.assertEqual(result["display_authors"], [])
        self.assertEqual(result["authoring"]["license_expression"], "MIT OR Apache-2.0")
        payload = result["sources"][0]
        self.assertEqual(payload["role"], "payload")
        self.assertEqual(payload["authors"], ["Named photographer"])
        self.assertEqual(payload["license_expression"], "CC0-1.0")
        self.assertIn("imported sources: CC0-1.0", result["display_license"])
        self.assertEqual(payload["evidence"][0]["path"], row["path"] + "/definition.json")

    def test_cited_document_does_not_relicense_asset(self):
        self.asset("physics", {"url": "https://supplier.example/data", "authors": ["Paper author"], "source_license": "CC-BY-4.0", "redistributed_document": False})
        item = self.build()["records"]["physics"]
        self.assertEqual(item["sources"][0]["role"], "reference")
        self.assertEqual(item["sources"][0]["license_expression"], "CC-BY-4.0")
        self.assertNotIn("CC-BY", item["display_license"])
        self.assertEqual(item["display_authors"], [])

    def test_registry_is_scoped_and_keeps_missing_terms(self):
        self.write("archive/legacy/authoring/stage-a/data/sources.json", {"items": [{"id": "supplier", "url": "https://supplier.example/a", "source_license": None, "redistributed_document": False}]})
        self.write("archive/legacy/authoring/stage-b/data/sources.json", {"items": [{"id": "supplier", "url": "https://supplier.example/b", "source_license": "OTHER"}]})
        self.asset("grade", {"properties": [{"source_id": "supplier"}]}, origin={"collection": "stage-a"})
        item = self.build()["records"]["grade"]
        self.assertEqual(item["unresolved_source_ids"], [])
        self.assertEqual(len(item["sources"]), 1)
        self.assertEqual(item["sources"][0]["urls"], ["https://supplier.example/a"])
        self.assertEqual(item["sources"][0]["license_status"], "not-stated")

    def test_dependency_attribution_does_not_claim_payload_ownership(self):
        self.asset("physical", {"url": "https://example.org/ref", "authors": ["Source author"], "source_license": "CC-BY-4.0"}, depends_on=["appearance"])
        self.asset("appearance", depends_on=["physical"])
        item = self.build()["records"]["appearance"]
        self.assertEqual(item["sources"][0]["via_assets"], ["physical"])
        self.assertEqual(item["sources"][0]["role"], "reference")
        self.assertEqual(item["authoring"]["authors"], [])

    def test_credits_are_editable_inputs_not_generated_feedback(self):
        row = self.asset("one")
        self.write(row["path"] + "/credits.json", {"authoring": {"authors": ["Original creator"], "license_expression": "MIT"}, "sources": [{"role": "payload", "id": "texture", "title": "Imported texture", "urls": ["https://example.org/texture"], "authors": ["Source creator"], "license_expression": "CC0-1.0", "notice": "Original credit text"}]})
        item = self.build()["records"]["one"]
        self.assertEqual(item["display_authors"], ["Original creator"])
        self.assertEqual(item["authoring"]["license_expression"], "MIT")
        self.assertEqual(item["sources"][0]["notice"], "Original credit text")
        self.assertEqual(self.build(check=True)["changed_files"], [])
        self.assertEqual(self.build()["changed_files"], [])

    def test_check_is_read_only_and_detects_drift(self):
        row = self.asset("one")
        self.build()
        generated = self.root / row["path"] / "attribution.json"
        original = generated.read_bytes()
        self.write(row["path"] + "/definition.json", {"source_url": "https://example.org/new"})
        result = self.build(check=True)
        self.assertTrue(result["errors"])
        self.assertIn(row["path"] + "/attribution.json", result["changed_files"])
        self.assertEqual(generated.read_bytes(), original)
        self.build()
        self.assertEqual(self.build(check=True)["errors"], [])

    def test_unresolved_ids_are_explicit_and_identity_is_not_a_citation(self):
        self.asset("one", {"source_ids": ["unknown-reference"]})
        item = self.build()["records"]["one"]
        self.assertEqual(item["unresolved_source_ids"], ["unknown-reference"])
        self.assertEqual(item["sources"], [])

    def test_invalid_credit_role_is_rejected(self):
        row = self.asset("one")
        self.write(row["path"] + "/credits.json", {"sources": [{"role": "invented-role", "urls": ["https://example.org"]}]})
        with self.assertRaisesRegex(ValueError, "source role"):
            self.build()

    def test_repository_escape_is_rejected(self):
        self.records = [{"id": "escape", "path": "../outside"}]
        with self.assertRaisesRegex(ValueError, "escapes repository"):
            self.build()

    def test_conflicting_source_terms_are_not_synthesized(self):
        row = self.asset("one", {"source_url": "https://example.org/asset", "provider": "Provider", "license": "CC0-1.0"})
        self.write(row["path"] + "/provenance/source.json", {"source_url": "https://example.org/asset", "provider": "Provider", "license": "CC-BY-4.0"})
        source = self.build()["records"]["one"]["sources"][0]
        self.assertIsNone(source["license_expression"])
        self.assertEqual(source["license_status"], "multiple-statements")
        self.assertEqual(source["recorded_license_terms"], ["CC-BY-4.0", "CC0-1.0"])

    def test_source_registry_mapping_keys_are_identifiers(self):
        self.write("archive/legacy/authoring/earth/data/sources.json", {"cement-guide": {"url": "https://example.org/cement", "title": "Cement guide", "provider": "Institute"}})
        self.asset("cement", {"source_id": "cement-guide"})
        item = self.build()["records"]["cement"]
        self.assertEqual(item["unresolved_source_ids"], [])
        self.assertEqual(item["sources"][0]["id"], "cement-guide")
        self.assertEqual(item["sources"][0]["role"], "reference")

    def test_provider_alone_does_not_prove_imported_payload(self):
        self.asset("physical", {"url": "https://supplier.example/data", "provider": "Supplier", "authors": ["Technical writer"]})
        item = self.build()["records"]["physical"]
        self.assertEqual(item["sources"][0]["role"], "reference")

    def test_map_urls_are_components_of_explicit_scan_credit(self):
        self.asset("scan", {"kind": "photo_scanned_PBR", "source_url": "https://example.org/scan", "license": "CC0-1.0", "provider": "Provider", "roles": {"normal": {"file": "source/normal.png", "source_url": "https://example.org/normal.png", "sha256": "hash", "role": "Normal"}}})
        item = self.build()["records"]["scan"]
        self.assertEqual(len(item["sources"]), 1)
        self.assertEqual(item["sources"][0]["license_expression"], "CC0-1.0")
        self.assertEqual(item["sources"][0]["components"][0]["urls"], ["https://example.org/normal.png"])
        self.assertEqual(item["sources"][0]["components"][0]["sha256"], "hash")

    def test_current_relations_replace_frozen_legacy_links(self):
        self.asset("old", {"url": "https://example.org/old"})
        self.asset("new", {"url": "https://example.org/new"})
        self.asset("appearance", depends_on=["old"], relations=[{"role": "physical_reference", "id": "new"}], runtime_dependencies=[])
        item = self.build()["records"]["appearance"]
        self.assertEqual([source["urls"] for source in item["sources"]], [["https://example.org/new"]])

    def test_markdown_escapes_html_and_url_parentheses(self):
        row = self.asset("one", {"title": "<script>alert(1)</script>", "url": "https://example.org/ref(v1)"})
        self.build()
        markdown = (self.root / row["path"] / "ATTRIBUTIONS.md").read_text()
        self.assertNotIn("<script>", markdown)
        self.assertIn("&lt;script&gt;", markdown)
        self.assertIn("https://example.org/ref%28v1%29", markdown)
        self.assertIn("ref%28v1%29", (self.root / "ATTRIBUTIONS.md").read_text())

    def test_extracted_source_registry_verifies_unchanged_origin(self):
        import hashlib
        script = self.write("archive/legacy/prepare_data.py", "sources = {}\n")
        self.write("provenance/source-registries/recovered-sources.json", {"sources": [{"id": "handbook", "url": "https://example.org/book", "authors": ["Published author"], "rights": "Factual references only.", "extracted_from": {"path": "archive/legacy/prepare_data.py", "assignment": "sources", "sha256": hashlib.sha256(script.read_bytes()).hexdigest()}}]})
        self.asset("wood", {"source_id": "handbook"})
        source = self.build()["records"]["wood"]["sources"][0]
        self.assertEqual(source["authors"], ["Published author"])
        self.assertEqual(source["notice"], "Factual references only.")
        self.assertEqual(source["license_status"], "not-stated")
        script.write_text("sources = {'changed': True}\n")
        with self.assertRaisesRegex(ValueError, "source hash differs"):
            self.build()


if __name__ == "__main__":
    unittest.main()
