"""The contradiction banner discloses when recorded counts exceed the listed claims."""
import json
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

HARNESS = """
const fs = require('fs');
const src = fs.readFileSync('docs/app.js', 'utf8');
const s = src.indexOf('/* SFPDRAWER_PURE_START */');
const e = src.indexOf('/* SFPDRAWER_PURE_END */');
const window = {};
new Function('window', src.slice(s, e + 25) + '\\nwindow.SFPDrawer = SFPDrawer;')(window);
const data = JSON.parse(fs.readFileSync('docs/data.json', 'utf8'));
const out = {};
for (const p of data.promises) out[p.promise_id] = {
  note: window.SFPDrawer.drawerCountDisclosure(p),
  view: window.SFPDrawer.drawerContradictionView(p),
  listed: ['kept', 'broken'].map(k => (((p.advocate_bundles || {})[k] || {}).claims || []).length),
};
console.log(JSON.stringify(out));
"""


class CountDisclosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run(["node", "-e", HARNESS], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
        cls.out = json.loads(r.stdout)

    def test_no_banner_means_no_disclosure(self):
        for pid, o in self.out.items():
            if o["view"] is None:
                self.assertIsNone(o["note"], pid)

    def test_disclosure_is_per_verdict_side(self):
        data = json.loads((REPO_ROOT / "docs/data.json").read_text())
        verd = {p["promise_id"]: p["verdict"] for p in data["promises"]}
        for pid, o in self.out.items():
            if o["view"] is None:
                continue
            kept, broken = o["listed"]
            v = verd[pid]
            if v == "broken":
                sup, con = broken, kept
            elif v in ("kept", "in_progress"):
                sup, con = kept, broken
            else:
                total_gap = kept + broken < o["view"]["supporting"] + o["view"]["contradicting"]
                self.assertEqual(o["note"] is not None, total_gap, pid)
                continue
            gap = sup < o["view"]["supporting"] or con < o["view"]["contradicting"]
            self.assertEqual(o["note"] is not None, gap, pid)

    def test_p11_counts_now_trace_to_listed_sides(self):
        # broken: supporting 4 = 4 broken claims listed, contradicting 0 = 0 kept listed.
        self.assertIsNone(self.out["P11"]["note"])
        self.assertEqual(self.out["P11"]["listed"], [0, 4])

    def test_banner_labels_are_verdict_relative(self):
        src = (REPO_ROOT / "docs/app.js").read_text()
        self.assertIn("Supports the verdict:", src)
        self.assertIn("Contradicts the verdict:", src)
        self.assertNotIn("<strong>Supporting case:</strong>", src)
        self.assertNotIn("<strong>Contradicting case:</strong>", src)

    def test_p26_broken_verdict_summaries_come_from_the_broken_side(self):
        data = json.loads((REPO_ROOT / "docs/data.json").read_text())
        p = next(x for x in data["promises"] if x["promise_id"] == "P26")
        self.assertEqual(p["verdict"], "broken")
        self.assertIn("prohibiting the City", p["supporting_evidence_summary"])
        self.assertIn("voters approved", p["contradicting_evidence_summary"])

    def test_contradicting_is_verdict_contradicting_never_refuting(self):
        data = json.loads((REPO_ROOT / "docs/data.json").read_text())
        for p in data["promises"]:
            o = self.out[p["promise_id"]]
            if o["view"] is not None:
                self.assertEqual(o["view"]["contradicting"], p["verdict_contradicting_evidence_count"] or 0, p["promise_id"])

    def test_explicit_conflict_flags_and_p64_keep_their_banner(self):
        data = json.loads((REPO_ROOT / "docs/data.json").read_text())
        for p in data["promises"]:
            if p["has_contradictory_evidence"] or (p["verdict_contradicting_evidence_count"] or 0) > 0:
                self.assertIsNotNone(self.out[p["promise_id"]]["view"], p["promise_id"])
            else:
                self.assertIsNone(self.out[p["promise_id"]]["view"], p["promise_id"])
        self.assertEqual(self.out["P64"]["view"], {"supporting": 2, "contradicting": 2})
        self.assertEqual(sum(1 for o in self.out.values() if o["view"] is not None), 23)

    def test_recorded_counts_are_not_altered(self):
        self.assertEqual(self.out["P11"]["view"], {"supporting": 4, "contradicting": 0})
        self.assertIsNone(self.out["P26"]["note"])


if __name__ == "__main__":
    unittest.main()
