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

    def test_disclosure_iff_counts_exceed_listed_claims(self):
        for pid, o in self.out.items():
            if o["view"] is None:
                continue
            recorded = o["view"]["supporting"] + o["view"]["contradicting"]
            if sum(o["listed"]) >= recorded:
                self.assertIsNone(o["note"], pid)
            else:
                self.assertIn(f"lists {sum(o['listed'])} individual claim", o["note"], pid)
                self.assertIn(f"for {recorded} counted", o["note"], pid)

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

    def test_recorded_counts_are_not_altered(self):
        self.assertEqual(self.out["P11"]["view"], {"supporting": 4, "contradicting": 4})
        self.assertIn("kept 0, broken 4", self.out["P11"]["note"])
        self.assertIsNone(self.out["P26"]["note"])


if __name__ == "__main__":
    unittest.main()
