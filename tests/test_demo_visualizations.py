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
        # README's last-known benchmark numbers; P83 moved to
        # kept_then_reversed in the E1b reopen.
        self.assertEqual(counts.get("kept"), 24)
        self.assertEqual(counts.get("in_progress"), 10)
        self.assertEqual(counts.get("broken"), 17)
        self.assertEqual(counts.get("undecided"), 2)
        self.assertEqual(counts.get("kept_then_reversed"), 1)

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

    def py_window_funnel_counts(self):
        # Independent tally: per-window stage_counts from the exported funnel.
        windows = (self.database_status.get("funnel") or {}).get("windows") or []
        return {
            w["window"]: dict(w.get("stage_counts") or {})
            for w in windows if isinstance(w, dict) and w.get("window")
        }

    def test_funnel_panel_matches_export(self):
        js = {s["stage"]: s["count"] for s in run_pure_fn("funnelStages", "databaseStatus")}
        self.assertEqual(js, self.py_funnel_stage_counts())
        # the funnel's published stage is exactly the exported promise count
        published = (self.database_status.get("funnel") or {}).get("stage_counts", {}).get("published")
        if published is not None:
            self.assertEqual(published, len(self.promises))

    def test_window_funnel_panel_matches_export(self):
        js_windows = run_pure_fn("windowFunnelStages", "databaseStatus")
        self.assertEqual(
            {w["window"]: {s["stage"]: s["count"] for s in w["stages"]} for w in js_windows},
            self.py_window_funnel_counts(),
        )
        # round counts match the exported round_ids length
        exported = {w["window"]: w for w in (self.database_status.get("funnel") or {}).get("windows") or []}
        for w in js_windows:
            self.assertEqual(w["roundCount"], len(exported[w["window"]].get("round_ids") or []))

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

    # ---- outcome-phase timelines (E5) ----

    @staticmethod
    def _date_key(value):
        # Mirrors the pure block's dateKey: 'YYYY-MM-DD…' -> 'YYYY-MM-DD'.
        import re
        s = str(value or "").strip()
        m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
        return m.group(1) if m else None

    def py_outcome_phases(self, p):
        # Independent re-derivation of the phase rules from the export:
        # made <- promise_made_date/promised_date; due <- deadline_date/
        # due_date; delivered <- completion_date, else for kept outcomes the
        # earliest kept-advocate evidence date; reversed <- the kept_then_
        # reversed verdict-history date (kept_then_reversed records only).
        phases = []
        made = self._date_key(p.get("promise_made_date")) or self._date_key(p.get("promised_date"))
        if made:
            phases.append(("made", made))
        due = self._date_key(p.get("deadline_date")) or self._date_key(p.get("due_date"))
        if due:
            phases.append(("due", due))
        verdict = (p.get("verdict") or "undecided").lower().replace(" ", "_").replace("-", "_")
        delivered = self._date_key(p.get("completion_date"))
        if not delivered and verdict in ("kept", "kept_then_reversed"):
            kept_claims = ((p.get("advocate_bundles") or {}).get("kept") or {}).get("claims") or []
            dates = sorted(d for d in (self._date_key(c.get("evidence_date")) for c in kept_claims) if d)
            delivered = dates[0] if dates else None
        if delivered:
            phases.append(("delivered", delivered))
        if verdict == "kept_then_reversed":
            history = p.get("verdict_history") or []
            for entry in reversed(history):
                if (entry.get("verdict") or "").lower() == "kept_then_reversed":
                    rev = self._date_key(entry.get("decided_at"))
                    if rev:
                        phases.append(("reversed", rev))
                    break
        return phases

    def py_phase_timelines(self):
        rows = []
        for p in self.promises:
            phases = self.py_outcome_phases(p)
            if len(phases) < 2:
                continue
            history = p.get("verdict_history") or []
            rows.append({
                "promiseId": str(p.get("promise_id") or ""),
                "displayNo": p.get("display_no") if isinstance(p.get("display_no"), (int, float)) else None,
                "historyChanged": len(history) > 1,
                "reversed": any(ph[0] == "reversed" for ph in phases),
                "phases": phases,
            })
        return sorted(rows, key=lambda r: (
            not r["reversed"],
            not r["historyChanged"],
            r["displayNo"] if r["displayNo"] is not None else float("inf"),
            r["promiseId"],
        ))

    def test_phase_timelines_match_export(self):
        js = run_pure_fn("phaseTimelines")
        expected = self.py_phase_timelines()
        self.assertEqual([r["promiseId"] for r in js], [r["promiseId"] for r in expected])
        for got, exp in zip(js, expected):
            self.assertEqual(
                [(ph["phase"], ph["date"]) for ph in got["phases"]], exp["phases"],
                f"{got['promiseId']} phase dates differ from the export",
            )

    def test_phase_timeline_renders_iff_two_dated_events(self):
        # The rendered row count equals the number of records carrying >= 2
        # dated phases, and every record with < 2 is excluded.
        js = run_pure_fn("phaseTimelines")
        expected_ids = [r["promiseId"] for r in self.py_phase_timelines()]
        self.assertEqual([r["promiseId"] for r in js], expected_ids)
        self.assertLess(len(expected_ids), len(self.promises))  # gate actually filters

    def test_p83_outcome_phases_fixture(self):
        # Unit check of the derivation function against the corpus fixture:
        # P83 is made -> due -> delivered -> reversed, its reversal date being
        # the kept_then_reversed verdict-history entry the drawer also shows.
        js = run_pure_fn("outcomePhases", "promises.find(x => x.promise_id === 'P83')")
        p83 = next(p for p in self.promises if p["promise_id"] == "P83")
        reversal = next(
            self._date_key(e.get("decided_at")) for e in reversed(p83["verdict_history"])
            if (e.get("verdict") or "").lower() == "kept_then_reversed"
        )
        self.assertEqual(js, [
            {"phase": "made", "date": "2022-02-17"},
            {"phase": "due", "date": "2022-03-10"},
            {"phase": "delivered", "date": "2022-03-10"},
            {"phase": "reversed", "date": reversal},
        ])
        self.assertEqual(reversal, "2026-11-14")

    def test_p83_leads_timeline_with_reversed_phase(self):
        js = run_pure_fn("phaseTimelines")
        self.assertEqual(js[0]["promiseId"], "P83")
        phase_names = [ph["phase"] for ph in js[0]["phases"]]
        self.assertIn("made", phase_names)
        self.assertIn("reversed", phase_names)

    def test_audit_panel_hooks_present(self):
        for hook in ("audit-funnel-bars", "audit-window-funnel-bars", "audit-reason-bars", "audit-denial-bars"):
            self.assertIn(hook, self.index_html)
            self.assertIn(hook, self.app_js)

    # ---- section wiring ----

    def test_visualization_section_present(self):
        self.assertIn('id="visualizations"', self.index_html)
        for hook in ("viz-verdict-bars", "viz-domain-bars", "viz-timeline",
                     "viz-timeline-legend", "viz-source-bars", "viz-total",
                     "viz-phase-timelines"):
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
