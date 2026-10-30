"""Focused tests for the portable catalog's data boundary and search behavior."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


MODULE_PATH = Path(__file__).with_name("browser.py")
SPEC = importlib.util.spec_from_file_location("library_browser", MODULE_PATH)
BROWSER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BROWSER)


def snapshot(html: str) -> dict:
    return json.loads(re.search(r'<script type="application/json" id="catalog-data">(.*?)</script>', html, re.S).group(1))


def example(**changes):
    record = {
        "id": "wood.white-oak.raw",
        "name": "White oak / raw",
        "type": "appearance",
        "family": "Wood",
        "path": "assets/appearances/wood/wood.white-oak.raw",
        "method": "Scanned",
        "license": "CC0-1.0",
        "authors": ["Example author"],
        "availability": "mixed",
        "validation": "Current native sample",
        "representations": [{"label": "Native profile", "path": "assets/appearances/wood/wood.white-oak.raw/authored/native-1024-r1/material.json", "available": True}],
    }
    record.update(changes)
    return record


class BrowserTests(unittest.TestCase):
    def test_script_termination_and_html_are_data(self):
        attack = '</script><script>alert("bad")</script><img onerror="bad()">'
        html = BROWSER.render_browser([example(name=attack, description=attack)])
        self.assertNotIn(attack, html)
        self.assertNotIn('<img onerror=', html)
        self.assertEqual(snapshot(html)["records"][0]["name"], attack)
        self.assertIn("\\u003c/script\\u003e", html)

    def test_repository_paths_are_confined_and_punctuation_is_encoded(self):
        self.assertEqual(BROWSER._relative_url("assets/wood/white oak#1/ATTRIBUTIONS.md"), "assets/wood/white%20oak%231/ATTRIBUTIONS.md")
        for invalid in ("../secret", "/etc/passwd", "C:\\private", "javascript:alert(1)", "https://host/file", "assets/../other", "assets//other"):
            self.assertIsNone(BROWSER._relative_url(invalid), invalid)
        record = snapshot(BROWSER.render_browser([example(path="/etc")]))["records"][0]
        self.assertIsNone(record["links"]["readme"])

    def test_payload_link_requires_declared_availability(self):
        records = snapshot(BROWSER.render_browser([example(representations=[
            {"label": "Unrecorded", "path": "assets/test/file.glb"},
            {"label": "Restorable", "path": "assets/test/file.glb", "availability": "restore_required"},
            {"label": "Present", "path": "assets/test/file.glb", "available": True},
            {"label": "Rejected URL", "path": "https://untrusted.invalid/file.glb", "available": True},
            {"label": "Explicitly absent", "path": "assets/test/file.glb", "availability": "tracked", "available": False},
        ])]))["records"][0]
        reps = records["representations"]
        self.assertIsNone(reps[0]["path"])
        self.assertIsNone(reps[1]["path"])
        self.assertEqual(reps[2]["path"], "assets/test/file.glb")
        self.assertIsNone(reps[3]["path"])
        self.assertIsNone(reps[4]["path"])

    def test_source_links_reject_executable_and_credential_urls(self):
        sources = BROWSER._sources([
            "https://example.org/reference",
            "javascript:alert(1)",
            "file:///private/path",
            "https://secret@example.org/reference",
            {"title": "Duplicate", "url": "https://example.org/reference"},
        ])
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["url"], "https://example.org/reference")

    def test_categories_use_actual_counts_and_keep_future_placeholders(self):
        data = snapshot(BROWSER.render_browser([example()], {"categories": [
            {"id": "appearances", "count": 100000, "planned": True},
            {"id": "drawings", "path": "assets/drawings"},
        ]}))
        categories = {item["id"]: item for item in data["categories"]}
        self.assertEqual(categories["appearances"]["count"], 1)
        self.assertFalse(categories["appearances"]["planned"])
        self.assertTrue(categories["drawings"]["planned"])
        self.assertEqual(categories["drawings"]["url"], "assets/drawings/README.md")

    def test_evidence_and_availability_remain_independent(self):
        data = snapshot(BROWSER.render_browser([example(
            availability="restore_required", validation="Current native sample",
            quality={"status": "not_run", "scope": "Only the declared native revision was sampled"},
        )]))["records"][0]
        self.assertEqual(data["availability"], "restore_required")
        self.assertEqual(data["validation"], "Current native sample")
        self.assertIn("declared native revision", data["quality_note"])

    def test_deterministic_without_modifying_input(self):
        records = [example(id="b", name="Beta"), example(id="a", name="Alpha")]
        original = json.dumps(records, sort_keys=True)
        self.assertEqual(BROWSER.render_browser(records), BROWSER.render_browser(list(reversed(records))))
        self.assertEqual(original, json.dumps(records, sort_keys=True))

    @unittest.skipUnless(shutil.which("node"), "Node is optional; required only to execute the browser's JavaScript core")
    def test_javascript_search_filter_sort_and_pagination(self):
        html = BROWSER.render_browser([])
        core = re.search(r'<script id="catalog-core">(.*?)</script>', html, re.S).group(1)
        checks = r'''
const assert=require("node:assert/strict");
const records=[
 {id:"wood.2",name:"White oak",search:"White oak José CC0 raw",type:"appearance",origin_collection:"scans",category:"appearances",family:"Wood",method:"Scanned",license:"CC0",availability:"mixed",validation:"Current native sample"},
 {id:"wood.10",name:"Red oak",search:"Red oak Jose CC0 polished",type:"appearance",origin_collection:"scans",category:"appearances",family:"Wood",method:"Scanned",license:"CC0",availability:"restore_required",validation:"Historical evidence"},
 {id:"metal.1",name:"White steel",search:"White steel CC0 raw",type:"appearance",origin_collection:"original",category:"appearances",family:"Metal",method:"Procedural",license:"CC0",availability:"tracked",validation:"Not recorded"}
];
assert.deepEqual(CatalogCore.filter(records,{search:"oak jose"}).map(x=>x.id),["wood.2","wood.10"]);
assert.deepEqual(CatalogCore.filter(records,{search:'"white oak"'}).map(x=>x.id),["wood.2"]);
assert.deepEqual(CatalogCore.filter(records,{search:"oak",availability:"restore_required"}).map(x=>x.id),["wood.10"]);
assert.equal(CatalogCore.filter(records,{search:"oak",family:"Metal"}).length,0);
assert.deepEqual(CatalogCore.sort(records,"id").map(x=>x.id),["metal.1","wood.2","wood.10"]);
const many=Array.from({length:2991},(_,i)=>i);
const page=CatalogCore.paginate(many,120,25);
assert.equal(page.page,120);assert.equal(page.pages,120);assert.equal(page.items.length,16);assert.equal(page.start,2976);assert.equal(page.end,2991);
assert.equal(CatalogCore.paginate(many,1000,25).page,120);
assert.equal(CatalogCore.paginate([],1,25).start,0);
assert.equal(CatalogCore.paginate([],1,25).pages,1);
console.log("search, phrase matching, facets, natural sorting and 2,991-item pagination passed");
'''
        result = subprocess.run([shutil.which("node"), "-e", core + "\n" + checks], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
