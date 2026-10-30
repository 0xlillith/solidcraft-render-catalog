"""Regression tests for complete listings, evidence freshness and availability."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

# A parallel authoring checkout may not yet contain the attribution generator.
# The temporary import fallback is removed immediately and never shadows a real
# module. These tests exercise catalog mechanics, not attribution extraction.
fallback = None
try:
    import attributions  # noqa: F401
except ModuleNotFoundError as error:
    if error.name != "attributions":
        raise
    fallback = types.ModuleType("attributions")
    fallback.build_attributions = lambda *args, **kwargs: {"status": "fixture"}
    sys.modules["attributions"] = fallback

try:
    spec = importlib.util.spec_from_file_location("library_catalog_regression", TOOLS / "catalog.py")
    catalog = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(catalog)
finally:
    if fallback is not None and sys.modules.get("attributions") is fallback:
        del sys.modules["attributions"]

import browser
from common import digest


def put(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class CatalogRegressions(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def asset(self, identity="test-resource", family="Wood"):
        relative = "assets/appearances/fixture/" + identity
        folder = self.root / relative
        row = {
            "id": identity,
            "name": identity,
            "path": relative,
            "type": "appearance",
            "category": "appearances",
            "family": family,
            "method": "authored",
            "definition": "definition.json",
            "origin": {"collection": "fixture"},
        }
        put(folder / "asset.json", row)
        put(folder / "definition.json", {"id": identity, "name": identity})
        put(folder / "FILES.json", {"files": []})
        return row, folder

    def test_distinct_families_with_the_same_slug_keep_every_resource(self):
        self.asset("test-slash", "A/B")
        self.asset("test-space", "A B")
        self.assertEqual(catalog.slug("A/B"), catalog.slug("A B"))
        with patch.object(catalog, "build_attributions", return_value={"status": "fixture"}):
            result = catalog.build(self.root)
        pages = sorted((self.root / "catalog/pages").glob("*.md"))
        self.assertEqual(result["assets"], 2)
        self.assertEqual(len(pages), 2)
        listed_ids = [identity for page in pages for identity in re.findall(r"`(test-[^`]+)`", page.read_text(encoding="utf-8"))]
        self.assertCountEqual(listed_ids, ["test-slash", "test-space"])
        index = (self.root / "INDEX.md").read_text(encoding="utf-8")
        for page in pages:
            self.assertIn(page.relative_to(self.root).as_posix(), index)

    def test_editing_a_referenced_map_invalidates_native_evidence(self):
        row, folder = self.asset()
        texture = folder / "authored/native/map.png"
        texture.parent.mkdir(parents=True)
        texture.write_bytes(b"Original map bytes")
        profile = folder / "authored/native/material.json"
        put(profile, {"maps": {"base_color": {"path": "map.png", "sha256": digest(texture)}}})
        put(folder / "validation/fresh-native-20261027.json", {
            "version": "solidcraft-cli 0.24.0",
            "passed": ["GPU coupon render"],
        })
        definition_hash = digest(folder / "definition.json")
        row.update({
            "active_appearance": "authored/native/material.json",
            "evidence_baseline": {
                "definition_sha256": definition_hash,
                "active_appearance_sha256": digest(profile),
            },
        })
        label, evidence = catalog.evidence(self.root, row, definition_hash)
        self.assertEqual(label, "Current native sample")
        self.assertTrue(evidence["baseline_matches"])
        texture.write_bytes(b"Edited map bytes without updating the profile")
        label, evidence = catalog.evidence(self.root, row, definition_hash)
        self.assertEqual(label, "Needs revalidation")
        self.assertFalse(evidence["baseline_matches"])

    def test_restorable_originals_remain_distinct_from_published_payloads(self):
        row, folder = self.asset()
        original = folder / "files/model.glb"
        original.parent.mkdir(parents=True)
        original.write_bytes(b"Restored local copy, intentionally not tracked")
        put(folder / "FILES.json", {"files": [{
            "path": "files/model.glb",
            "archive": "historical-original.zip",
            "member": "original/model.glb",
            "bytes": original.stat().st_size,
            "sha256": digest(original),
        }]})
        row["entrypoints"] = ["files/model.glb"]
        representations, _ = catalog.representation_records(self.root, row, {})
        self.assertEqual(len(representations), 1)
        self.assertFalse(representations[0]["available"])
        self.assertEqual(representations[0]["availability"], "restore_required")
        display = browser._representations(representations)[0]
        self.assertEqual(display["availability"], "Historical files need restoration")
        self.assertIsNone(display["path"])
        self.assertEqual(representations[0]["restoration"]["archive"], "historical-original.zip")

    def test_new_asset_without_historical_receipt_has_no_broken_receipt_link(self):
        row, folder = self.asset("new-authored-resource")
        (folder / "FILES.json").unlink()
        record = catalog.make_record(self.root, row)
        page = catalog.resource_page(record, {record['id']: record})
        self.assertNotIn('](FILES.json)', page)
        self.assertIn('No historical archive members', page)
        self.assertEqual(record['representations'][0]['availability'], 'tracked')


if __name__ == "__main__":
    unittest.main()
