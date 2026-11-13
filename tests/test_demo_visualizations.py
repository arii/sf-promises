"""Reconcile the demo's visualization charts against the exported snapshot.

The chart derivations live in a marked pure block of docs/app.js
(SFPVIZ_PURE_START .. SFPVIZ_PURE_END). This test executes that block with
node and asserts that every count it produces equals an independent tally
computed from docs/data.json — so charts can only ever show exported data.
"""
import json
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path

APP_JS = Path("docs/app.js")
DATA_JSON = Path("docs/data.json")
INDEX_HTML = Path("docs/index.html")
REPO_ROOT = Path(__file__).resolve().parent.parent
PURE_START = "/* SFPVIZ_PURE_START */"
PURE_END = "/* SFPVIZ_PURE_END */"

NODE_HARNESS = """
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const start = src.indexOf('{pure_start}');
const end = src.indexOf('{pure_end}');
if (start < 0 || end < 0) {{
  console.error('pure viz block missing from docs/app.js');
  process.exit(2);
}}
const window = {{}};
new Function('window', src.slice(start, end + '{pure_end}'.length) + '\\nwindow.SFPViz = SFPViz;')(window);
const promises = JSON.parse(fs.readFileSync('docs/data.json', 'utf8')).promises;
const databaseStatus = JSON.parse(fs.readFileSync('docs/data.json', 'utf8')).database_status || {{}};
const result = window.SFPViz.{fn}({args});
console.log(JSON.stringify(result));
"""


def run_pure_fn(fn, args="promises"):
    script = NODE_HARNESS.format(pure_start=PURE_START, pure_end=PURE_END, fn=fn, args=args)
    proc = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, timeout=60, cwd=REPO_ROOT
    )
    if proc.returncode != 0:
        raise AssertionError(f"node harness failed for {fn}: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def read_script_srcs(html):
    return re.findall(r'<script[^>]+src="([^"]+)"', html)


class TestDemoVisualizations(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DATA_JSON.exists(), "docs/data.json must exist")
        full = json.loads(DATA_JSON.read_text(encoding="utf-8"))
        self.promises = full["promises"]
        self.database_status = full.get("database_status", {})
        self.quarantined = full.get("quarantined", [])
        self.app_js = APP_JS.read_text(encoding="utf-8")
        self.index_html = INDEX_HTML.read_text(encoding="utf-8")

    # ---- independent tallies from the export ----

    def py_verdicts(self):
        return Counter((p.get("verdict") or "undecided").lower() for p in self.promises)

    def py_categories(self):
        return Counter((p.get("category") or "Other").strip() for p in self.promises)

    def py_source_types(self):
        return Counter((p.get("source_type") or "unknown").strip() for p in self.promises)

    def py_year_verdicts(self):
        # Zero-fill every year between the earliest and latest promise date so
        # gap years compare equal to the chart's coverage-gap view.
        years = sorted(str(p["promised_date"])[:4] for p in self.promises)
        buckets = {str(y): Counter() for y in range(int(years[0]), int(years[-1]) + 1)}
        for p in self.promises:
            buckets[str(p["promised_date"])[:4]][(p.get("verdict") or "undecided").lower()] += 1
        return buckets

    # ---- chart logic matches the export ----

    def test_verdict_chart_matches_export(self):
        js = run_pure_fn("countByVerdict")
        self.assertEqual(js, dict(self.py_verdicts()))

    def test_category_chart_matches_export(self):
        js = run_pure_fn("countByCategory")
        self.assertEqual(js, dict(self.py_categories()))

    def test_source_type_chart_matches_export(self):
        js = run_pure_fn("countBySourceType")
        self.assertEqual(js, dict(self.py_source_types()))

    def test_timeline_matches_export(self):
        js = {b["year"]: b["verdicts"] for b in run_pure_fn("countByYearAndVerdict")}
        expected = {y: dict(c) for y, c in self.py_year_verdicts().items()}
        self.assertEqual(js, expected)

    # ---- counts reconcile with dataset totals ----

    def test_verdict_counts_reconcile_with_totals(self):
        counts = self.py_verdicts()
        self.assertEqual(sum(counts.values()), len(self.promises))
        # README's last-known benchmark numbers
        self.assertEqual(counts.get("kept"), 25)
        self.assertEqual(counts.get("in_progress"), 10)
        self.assertEqual(counts.get("broken"), 17)
        self.assertEqual(counts.get("undecided"), 2)

    def test_timeline_covers_every_promise_once(self):
        buckets = run_pure_fn("countByYearAndVerdict")
        self.assertEqual(
            sum(sum(b["verdicts"].values()) for b in buckets), len(self.promises)
        )
        # zero-filled years between min and max so gaps stay visible
        years = [int(b["year"]) for b in buckets]
        self.assertEqual(years, list(range(years[0], years[-1] + 1)))

    # ---- audit-view panels (D3) derive from the export ----

    def py_funnel_stage_counts(self):
        stages = (self.database_status.get("funnel") or {}).get("stages") or []
        return {
            s["stage"]: s["count"] for s in stages
            if isinstance(s.get("count"), (int, float))
        }

    def py_quarantine_reason_tally(self):
        # Independent tally over the exported registry's reason_codes fields.
        tally = Counter()
        for item in self.quarantined:
            codes = item.get("reason_codes") or [item.get("failing_check_code")
                                                 or item.get("check_type") or "unknown"]
            for code in codes:
                tally[str(code)] += 1
        return tally

    def test_funnel_panel_matches_export(self):
        js = {s["stage"]: s["count"] for s in run_pure_fn("funnelStages", "databaseStatus")}
        self.assertEqual(js, self.py_funnel_stage_counts())
        # the funnel's published stage is exactly the exported promise count
        published = (self.database_status.get("funnel") or {}).get("stage_counts", {}).get("published")
        if published is not None:
            self.assertEqual(published, len(self.promises))

    def test_reason_code_panel_sums_to_quarantine_registry(self):
        js = run_pure_fn("quarantineReasons", "databaseStatus")
        expected = self.py_quarantine_reason_tally()
        self.assertEqual(js["byReason"], dict(expected))
        self.assertEqual(sum(js["byReason"].values()), len(self.quarantined))
        self.assertEqual(js["totalQuarantined"], len(self.quarantined))

    def test_denial_histogram_matches_export(self):
        js = run_pure_fn("denialDomains", "databaseStatus")
        by_domain = (self.database_status.get("denials") or {}).get("by_domain") or {}
        self.assertEqual(
            {d["domain"]: d["count"] for d in js},
            {domain: entry.get("count", 0) for domain, entry in by_domain.items()},
        )
        total = (self.database_status.get("denials") or {}).get("total_denials")
        if total is not None:
            self.assertEqual(sum(d["count"] for d in js), total)

    def test_audit_panel_hooks_present(self):
        for hook in ("audit-funnel-bars", "audit-reason-bars", "audit-denial-bars"):
            self.assertIn(hook, self.index_html)
            self.assertIn(hook, self.app_js)

    # ---- section wiring ----

    def test_visualization_section_present(self):
        self.assertIn('id="visualizations"', self.index_html)
        for hook in ("viz-verdict-bars", "viz-domain-bars", "viz-timeline",
                     "viz-timeline-legend", "viz-source-bars", "viz-total"):
            self.assertIn(hook, self.index_html)
            self.assertIn(hook, self.app_js)

    def test_no_new_runtime_cdn_dependencies(self):
        for src in read_script_srcs(self.index_html):
            self.assertFalse(
                src.startswith("http://") or src.startswith("https://"),
                f"runtime script must be local, got {src}",
            )


if __name__ == "__main__":
    unittest.main()
