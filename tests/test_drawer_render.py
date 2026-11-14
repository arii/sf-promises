"""Drawer render test: the inspect drawer shows exactly what the export carries.

The drawer's verdict-timeline and provenance HTML builders live in a marked
pure block of docs/app.js (SFPDRAWER_PURE_START .. SFPDRAWER_PURE_END). This
test executes that block with node over docs/data.json and asserts:

- a verdict timeline renders if and only if verdict_history has more than one
  entry (single-verdict records keep the static chip);
- P83 — the sole kept_then_reversed record — renders the two-step timeline
  with its exported dates;
- check provenance lines render model/reviewer/run/date only when the export
  records them.
"""
import json
import subprocess
import unittest
from pathlib import Path

APP_JS = Path("docs/app.js")
DATA_JSON = Path("docs/data.json")
REPO_ROOT = Path(__file__).resolve().parent.parent
PURE_START = "/* SFPDRAWER_PURE_START */"
PURE_END = "/* SFPDRAWER_PURE_END */"

NODE_HARNESS = """
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const start = src.indexOf('/* SFPDRAWER_PURE_START */');
const end = src.indexOf('/* SFPDRAWER_PURE_END */');
if (start < 0 || end < 0) {
  console.error('pure drawer block missing from docs/app.js');
  process.exit(2);
}
const window = {};
new Function('window', src.slice(start, end + '/* SFPDRAWER_PURE_END */'.length) + '\\nwindow.SFPDrawer = SFPDrawer;')(window);
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const SFPDrawer = window.SFPDrawer;
const p83 = data.promises.find(p => p.promise_id === 'P83');
const p02 = data.promises.find(p => p.promise_id === 'P02') || data.promises[0];
console.log(JSON.stringify({
  p83: SFPDrawer.verdictTimelineHtml(p83.verdict_history),
  p83_decided_at: p83.verdict_history[p83.verdict_history.length - 1].decided_at || null,
  p02: SFPDrawer.verdictTimelineHtml(p02.verdict_history),
  perRecord: data.promises.map(p => ({
    id: p.promise_id,
    n: (p.verdict_history || []).length,
    html: SFPDrawer.verdictTimelineHtml(p.verdict_history)
  })),
  provenanceFull: SFPDrawer.checkProvenanceHtml({
    check: 'authenticity_domain', passed: true,
    model_id: 'model-x', checked_by: 'durability_cron',
    run_id: 'RUN_abcd1234', checked_at: '2026-11-14T09:35:18Z'
  }),
  provenanceEmpty: SFPDrawer.checkProvenanceHtml({ check: 'accuracy_quote', passed: true }),
  provenanceMissing: SFPDrawer.checkProvenanceHtml(undefined)
}));
"""


def run_harness():
    proc = subprocess.run(
        ["node", "-e", NODE_HARNESS], capture_output=True, text=True, timeout=60, cwd=REPO_ROOT
    )
    if proc.returncode != 0:
        raise AssertionError(f"node drawer harness failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


class TestDrawerTimeline(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DATA_JSON.exists(), "docs/data.json must exist")
        self.out = run_harness()

    def test_p83_two_step_timeline_with_dates(self):
        html = self.out["p83"]
        self.assertTrue(html, "P83 (2 verdict rows) must render a timeline")
        self.assertIn("Kept", html)
        self.assertIn("Later closed / reversed", html)
        self.assertEqual(html.count("verdict-chip"), 2, "timeline has exactly two steps")
        self.assertIn("drawer-timeline-arrow", html)
        # The newest entry's exported decided_at renders as a month name.
        decided = self.out["p83_decided_at"]
        self.assertTrue(decided, "P83's newest verdict row carries decided_at")
        from datetime import date
        d = date.fromisoformat(decided[:10])
        self.assertIn(d.strftime("%B %Y"), html)

    def test_single_verdict_record_has_no_timeline(self):
        self.assertIsNone(self.out["p02"], "single-verdict record must not render a timeline")

    def test_timeline_iff_history_longer_than_one(self):
        for r in self.out["perRecord"]:
            self.assertEqual(
                bool(r["html"]), r["n"] > 1,
                f"{r['id']}: timeline truthiness must match history length {r['n']}",
            )
        # Exactly one corpus record (P83) carries the two-step timeline.
        with_timeline = [r["id"] for r in self.out["perRecord"] if r["html"]]
        self.assertEqual(with_timeline, ["P83"])

    def test_provenance_line_carries_exported_fields(self):
        html = self.out["provenanceFull"]
        self.assertIn("model model-x", html)
        self.assertIn("reviewer durability_cron", html)
        self.assertIn("run RUN_abcd1234", html)
        self.assertIn("2026-11-14", html)

    def test_provenance_empty_when_export_has_none(self):
        self.assertEqual(self.out["provenanceEmpty"], "")
        self.assertEqual(self.out["provenanceMissing"], "")


if __name__ == "__main__":
    unittest.main()
