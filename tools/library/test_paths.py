"""ID resolution and restoration regressions for the reorganized library."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY / "tools/library"))
sys.path.insert(0, str(REPOSITORY / "tools/extras"))
import common
import improve
import manage


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class IdentityPathTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.root = self.workspace / "library"
        self.root.mkdir()
        self.mapping = {}

    def asset(self, identity="wood.example", relative=None, source_id=None):
        relative = relative or "assets/appearances/woods/" + identity
        folder = self.root / relative
        meta = {
            "id": identity,
            "source_id": source_id or identity,
            "entrypoints": [],
            "previews": [],
            "depends_on": [],
            "packaging_decision": None,
            "editable_recipes": [],
            "historical_evidence": [],
        }
        write_json(folder / "asset.json", meta)
        write_json(folder / "extra.json", meta)
        write_json(folder / "definition.json", {"id": source_id or identity})
        write_json(folder / "FILES.json", {"files": []})
        self.mapping[identity] = relative
        self.save_paths()
        return folder

    def save_paths(self):
        write_json(self.root / "catalog/paths.json", {"assets": self.mapping})

    def test_relocation_keeps_identity_and_sibling_independent(self):
        original = self.asset()
        sibling = self.asset("wood.other")
        relocated = self.root / "assets/appearances/timber/wood.example"
        relocated.parent.mkdir(parents=True)
        original.rename(relocated)
        self.mapping["wood.example"] = relocated.relative_to(self.root).as_posix()
        self.save_paths()

        self.assertEqual(common.asset_directory("wood.example", self.root), relocated)
        self.assertEqual(improve.asset_folder("wood.example", self.root), relocated)
        self.assertEqual(common.asset_directory("wood.other", self.root), sibling)
        self.assertEqual(
            manage.entries(["wood.example"], self.root),
            [{"id": "wood.example", "folder": self.mapping["wood.example"]}],
        )

    def test_missing_identity_does_not_guess_a_folder(self):
        self.asset()
        for operation in (
            lambda: common.asset_directory("missing", self.root),
            lambda: improve.asset_folder("missing", self.root),
            lambda: manage.entries(["missing"], self.root),
        ):
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(ValueError, "Unknown"):
                    operation()

    def test_unsafe_catalog_paths_are_rejected(self):
        self.asset()
        for relative in (
            "../outside",
            str(self.workspace / "outside"),
            "C:/outside",
            "assets\\outside",
            "assets/appearances/../outside",
        ):
            with self.subTest(path=relative):
                self.mapping["wood.example"] = relative
                self.save_paths()
                for operation in (
                    lambda: common.asset_directory("wood.example", self.root),
                    lambda: improve.asset_folder("wood.example", self.root),
                    lambda: manage.entries(["wood.example"], self.root),
                ):
                    with self.assertRaisesRegex(ValueError, "Unsafe"):
                        operation()

    def test_symlink_escape_is_rejected(self):
        self.asset()
        outside = self.workspace / "outside"
        outside.mkdir()
        write_json(outside / "definition.json", {"id": "wood.example"})
        link = self.root / "assets/linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest("Directory symlinks unavailable: " + str(error))
        self.mapping["wood.example"] = "assets/linked"
        self.save_paths()
        with self.assertRaisesRegex(ValueError, "escapes"):
            common.asset_directory("wood.example", self.root)

    def test_catalog_cannot_point_one_id_at_another_asset(self):
        self.asset()
        other = self.asset("wood.other")
        self.mapping["wood.example"] = other.relative_to(self.root).as_posix()
        self.save_paths()
        for operation in (
            lambda: common.asset_directory("wood.example", self.root),
            lambda: improve.asset_folder("wood.example", self.root),
            lambda: manage.entries(["wood.example"], self.root),
        ):
            with self.assertRaisesRegex(ValueError, "identity does not match"):
                operation()

    def test_definition_source_id_can_differ_from_stable_id(self):
        folder = self.asset("alloy.c93200.reference", source_id="c93200")
        self.assertEqual(common.asset_directory("alloy.c93200.reference", self.root), folder)
        write_json(common.archive_sources(self.root), {"archives": []})
        self.assertEqual(manage.validate(self.root)["extras"], 1)

    def test_descriptors_resolve_before_first_catalog_generation(self):
        folder = self.asset()
        (self.root / "catalog/paths.json").unlink()
        write_json(folder / "extra.json", {"id": "preserved-old-source"})
        self.assertEqual(common.asset_directory("wood.example", self.root), folder)
        self.assertEqual(manage.entries(root=self.root)[0]["id"], "wood.example")
        self.assertEqual(improve.asset_folder("wood.example", self.root), folder)

    def test_legacy_index_paths_work_for_both_fixture_roots(self):
        legacy = self.root / "extras"
        folder = legacy / "custom-folder-name"
        identity = "MAT-001"
        meta = {
            "id": identity, "source_id": identity, "depends_on": [],
            "packaging_decision": None, "entrypoints": [], "previews": [],
        }
        write_json(folder / "extra.json", meta)
        write_json(folder / "definition.json", {"id": identity})
        write_json(folder / "FILES.json", {"files": []})
        write_json(legacy / "INDEX.json", {
            "count": 1, "items": [{"id": identity, "folder": "custom-folder-name"}],
        })
        write_json(legacy / "ARCHIVE-SOURCES.json", {"archives": []})
        for root in (self.root, legacy):
            with self.subTest(root=root):
                row = manage.entries([identity], root)[0]
                self.assertEqual(root / row["folder"], folder)
                self.assertEqual(improve.asset_folder(identity, root), folder)
                self.assertEqual(manage.validate(root)["extras"], 1)

    def test_legacy_index_count_must_match(self):
        write_json(self.root / "INDEX.json", {"count": 1, "items": []})
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            manage.entries(root=self.root)
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            improve.asset_folder("missing", self.root)

    def test_archived_receipts_restore_at_new_path_without_resetting_edits(self):
        folder = self.asset("MAT-001", "assets/appearances/metals/renamed-location")
        cache = self.workspace / "cache"
        cache.mkdir()
        archive = cache / "original-fixture.zip"
        payload = b"An original resource, preserved exactly.\n"
        member = "original/resource.bin"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr(member, payload)
        write_json(folder / "FILES.json", {"files": [{
            "path": "files/resource.bin", "archive": archive.name, "member": member,
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
        }]})
        write_json(common.archive_sources(self.root), {"archives": [{
            "archive": archive.name,
            "bytes": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "url": "https://github.com/0xlillith/solidcraft-render-catalog/releases/download/fixture/" + archive.name,
        }]})
        self.assertEqual(manage.validate(self.root)["status"], "PASS")
        restored = manage.restore(["MAT-001"], [cache], False, self.root)
        self.assertEqual(restored["copied"], 1)
        self.assertEqual((folder / "files/resource.bin").read_bytes(), payload)
        self.assertEqual(manage.verify(["MAT-001"], self.root)["status"], "PASS")
        repeated = manage.restore(["MAT-001"], [cache], False, self.root)
        self.assertEqual(repeated["already_identical"], 1)

        edited = b"A deliberate user edit.\n"
        (folder / "files/resource.bin").write_bytes(edited)
        with self.assertRaisesRegex(FileExistsError, "edited working file"):
            manage.restore(["MAT-001"], [cache], False, self.root)
        self.assertEqual((folder / "files/resource.bin").read_bytes(), edited)
        self.assertEqual(manage.verify(["MAT-001"], self.root)["status"], "DIFFERENCES")


if __name__ == "__main__":
    unittest.main()
