"""A contradicting-evidence summary is shown to readers as evidence, so it must come from a listed claim."""
import copy
import json
import pathlib
import unittest

from scripts.enrich_dataset import enrich_promise

DATA = json.loads((pathlib.Path(__file__).resolve().parent.parent / "docs" / "data.json").read_text())
RECORDS = {p["promise_id"]: p for p in DATA.get("promises", DATA)}


class TestContradictionSummaryProvenance(unittest.TestCase):
    def test_no_claim_means_no_contradicting_summary(self):
        # P11 is broken, flagged contradictory, and lists no kept claim to quote.
        p = copy.deepcopy(RECORDS["P11"])
        p["contradicting_evidence_summary"] = "stale"
        out = enrich_promise(p)
        self.assertTrue(out["has_contradictory_evidence"])
        self.assertEqual(out["contradicting_evidence_summary"], "")

    def test_summary_quotes_the_listed_claim(self):
        p = copy.deepcopy(RECORDS["P11"])
        p["advocate_bundles"]["kept"] = {"claims": [{"claim": "Launch announced with first riders", "quote": "q"}]}
        out = enrich_promise(p)
        self.assertIn("Launch announced with first riders", out["contradicting_evidence_summary"])


if __name__ == "__main__":
    unittest.main()
