"""A merged v2 record with a null deadline renders in docs/app.js without errors.

Builds an open-ended `undecided` record with the real merge, then runs, with
node, every docs/app.js code path that reads due_date/deadline_date: the pure
drawer block (including outcomeBasisText), outcomePhases, timelineStripHtml
and the drawer's due-date formatting.
"""

import copy
import json
import re
import subprocess
from pathlib import Path

from src.site_merge import merge_v2
from tests.test_export_v2_merge import OPEN_ENDED_BASIS, ROOT, make_v2

APP_JS = ROOT / "docs" / "app.js"


def _function_source(src, name):
    start = src.index(f"  function {name}(")
    end = src.index("\n  }\n", start) + len("\n  }\n")
    return src[start:end]


def _merged_record(tmp_path, **spec):
    db, sources = make_v2(tmp_path / "v2", [{"pid": "P901", **spec}])
    payload = copy.deepcopy(json.loads((ROOT / "docs" / "data.json").read_text()))
    report = merge_v2(payload, [(db, sources)])
    assert report["added"], report
    return payload["promises"][-1]


def _render(record):
    src = APP_JS.read_text()
    pure = src[src.index("/* SFPDRAWER_PURE_START */"):src.index("/* SFPDRAWER_PURE_END */")]
    helpers = "\n".join(_function_source(src, name) for name in (
        "formatPrecisionDate", "normalizeVerdict", "dateKey", "escapeHtml",
        "earliestBundleEvidenceDate", "reversalDate", "outcomePhases", "timelineStripHtml"))
    due = src[src.index("    const dueStatusLabels = {"):src.index("    if (dueVal) dueVal.textContent")]
    phase_order = re.search(r"  const PHASE_ORDER = .*?;\n", src).group(0)
    script = f"""
const window = {{}};
{pure}
{phase_order}
{helpers}
const p = {json.dumps(record)};
const due = (() => {{ {due} return dueDateFormatted; }})();
console.log(JSON.stringify({{
  due,
  basis: window.SFPDrawer.outcomeBasisText(p),
  phases: outcomePhases(p),
  strip: timelineStripHtml(p),
  checks: window.SFPDrawer.drawerChecksSummary(window.SFPDrawer.drawerCheckOutcomes(p), p),
  timeline: window.SFPDrawer.verdictTimelineHtml(p.verdict_history),
}}));
"""
    proc = subprocess.run(["node", "-e", script], capture_output=True, text=True,
                          timeout=60, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_open_ended_record_renders_no_deadline(tmp_path):
    record = _merged_record(tmp_path, deadline=None, verdict="UNDECIDED",
                            outcome_basis=OPEN_ENDED_BASIS)
    assert record["due_date"] is None and record["outcome_basis"]["open_ended"] is True
    out = _render(record)
    assert out["due"] == "No deadline (not applicable)"
    assert [p["phase"] for p in out["phases"]] == ["made"]
    assert "Due</span> \u2014" in out["strip"]
    assert out["basis"] == "Open-ended commitment \u00b7 no outcome evidence found"
    assert out["timeline"] is None


def test_status_not_checked_and_plain_records(tmp_path):
    basis = {**OPEN_ENDED_BASIS, "rules": ["R1", "R4"], "outcome_rule": "R4",
             "reason": "current status not checked", "relied_on": ["DELIVERY"], "verdict": "KEPT"}
    record = _merged_record(
        tmp_path / "a", deadline=None, verdict="KEPT", outcome_basis=basis,
        extra=[("DELIVERY", "The Mission Street library opened on June 3, 2024.", "2024-06-03")],
        verifier={"delivery": True})
    assert _render(record)["basis"] == "Open-ended commitment \u00b7 current status not checked"
    plain = _merged_record(tmp_path / "b")
    out = _render(plain)
    assert out["basis"] == "" and out["due"] == "2025-01-01"
