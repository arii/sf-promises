import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("demo_export_counts", ROOT / "docs/export_data.py")
EXPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORT)

PAGE = """<html><head>
<meta name="description" content="A sourced record of 54 San Francisco public commitments, each checked.">
</head><body>
<span class="bar-header-count" id="outcome-dist-verified">54 VERIFIED</span>
<p>This site tracks 54 such commitments.</p>
<option value="all">All Commitments (54)</option>
<button id="btn-show-all">
  Show all 54</button>
</body></html>
"""


def promise(pid, verdict="kept"):
    return {"promise_id": pid, "entity": "SFO", "role": "", "verdict": verdict,
            "promise_text": "A promise.", "promised_date": "2024-01-01",
            "promise_date_precision": "day", "document_title": f"Title {pid}"}


class TestExportCountsAndFeatured(unittest.TestCase):
    def test_hard_coded_counts_follow_the_dataset(self):
        promises = [promise(f"X{i}") for i in range(7)]
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text(PAGE, encoding="utf-8")
            old = EXPORT.OUTPUT_DIR
            EXPORT.OUTPUT_DIR = Path(tmp)
            try:
                EXPORT.pre_render_index_html(promises, [], {"kept": 7}, "abc12345")
            finally:
                EXPORT.OUTPUT_DIR = old
            html = page.read_text(encoding="utf-8")
        self.assertIn("A sourced record of 7 San Francisco", html)
        self.assertIn("This site tracks 7 such", html)
        self.assertIn("All Commitments (7)", html)
        self.assertIn("Show all 7", html)
        self.assertNotIn("54", html)

    def test_header_label_says_published_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "index.html"
            page.write_text(PAGE, encoding="utf-8")
            old = EXPORT.OUTPUT_DIR
            EXPORT.OUTPUT_DIR = Path(tmp)
            try:
                EXPORT.pre_render_index_html([promise("A")], [], {"kept": 1}, "abc12345")
            finally:
                EXPORT.OUTPUT_DIR = old
            html = page.read_text(encoding="utf-8")
        self.assertIn(">1 PUBLISHED<", html)
        self.assertNotIn("VERIFIED", html)

    def test_featured_stories_exclude_quarantined_and_test_records(self):
        promises = [promise(pid) for pid in EXPORT.FEATURED_IDS]
        quarantined = [{"quarantine_id": "Q-N01", "planted_claim": "x"},
                       {"quarantine_id": "Q-9", "promise_id": EXPORT.FEATURED_IDS[0]}]
        html = EXPORT.generate_featured_stories_html(promises, quarantined)
        self.assertNotIn("QUARANTINED", html)
        self.assertNotIn("Quote Mutation Detection", html)
        self.assertNotIn(f'data-story-pid="{EXPORT.FEATURED_IDS[0]}"', html)
        for pid in EXPORT.FEATURED_IDS[1:]:
            self.assertIn(f'data-story-pid="{pid}"', html)

    def test_featured_ids_are_all_published_in_the_exported_dataset(self):
        import json
        text = (ROOT / "docs/data.js").read_text(encoding="utf-8")
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
        published = {p["promise_id"] for p in data["promises"]}
        self.assertEqual([pid for pid in EXPORT.FEATURED_IDS if pid not in published], [])


if __name__ == "__main__":
    unittest.main()
