import json
import re
from pathlib import Path
import unittest


class TestUICounts(unittest.TestCase):
    def setUp(self):
        self.data_path = Path("docs/data.json")
        self.html_path = Path("docs/index.html")
        self.assertTrue(self.data_path.exists(), "docs/data.json must exist")
        self.assertTrue(self.html_path.exists(), "docs/index.html must exist")

        with open(self.data_path, encoding="utf-8") as f:
            self.data = json.load(f)
        with open(self.html_path, encoding="utf-8") as f:
            self.html = f.read()

        self.promises = self.data.get("promises", [])
        self.quarantined = self.data.get("quarantined", [])
        self.total_promises = len(self.promises)
        self.total_quarantined = len(self.quarantined)

        self.verdict_counts = {}
        for p in self.promises:
            v = (p.get("verdict") or "undecided").lower().replace(" ", "_")
            self.verdict_counts[v] = self.verdict_counts.get(v, 0) + 1

    def test_data_length_matches_contract(self):
        """Contract: exactly 54 verified commitments and 13 quarantined items."""
        self.assertEqual(self.total_promises, 54, f"Expected 54 promises, got {self.total_promises}")
        self.assertEqual(self.total_quarantined, 13, f"Expected 13 quarantined items, got {self.total_quarantined}")
        self.assertEqual(
            sum(self.verdict_counts.values()),
            54,
            "Sum of verdict counts must equal total promises"
        )

    def test_html_tally_numbers_match_data(self):
        """All static tally numbers in docs/index.html must match loaded data exactly."""
        m_total = re.search(r'id="tally-total"[^>]*>(\d+)<', self.html)
        self.assertIsNotNone(m_total, "Missing #tally-total in HTML")
        self.assertEqual(int(m_total.group(1)), self.total_promises)

        m_kept = re.search(r'id="tally-kept"[^>]*>(\d+)<', self.html)
        self.assertIsNotNone(m_kept, "Missing #tally-kept in HTML")
        self.assertEqual(int(m_kept.group(1)), self.verdict_counts.get("kept", 0))

        m_prog = re.search(r'id="tally-progress"[^>]*>(\d+)<', self.html)
        self.assertIsNotNone(m_prog, "Missing #tally-progress in HTML")
        self.assertEqual(int(m_prog.group(1)), self.verdict_counts.get("in_progress", 0))

        m_broken = re.search(r'id="tally-broken"[^>]*>(\d+)<', self.html)
        self.assertIsNotNone(m_broken, "Missing #tally-broken in HTML")
        self.assertEqual(int(m_broken.group(1)), self.verdict_counts.get("broken", 0))

        m_undecided = re.search(r'id="tally-undecided"[^>]*>(\d+)<', self.html)
        self.assertIsNotNone(m_undecided, "Missing #tally-undecided in HTML")
        self.assertEqual(int(m_undecided.group(1)), self.verdict_counts.get("undecided", 0))

    def test_tab_counts_match_data(self):
        """Tab badges must match promises and quarantine lengths."""
        m_tab_promises = re.search(r'id="tab-count-promises"[^>]*>(\d+)<', self.html)
        self.assertIsNotNone(m_tab_promises, "Missing #tab-count-promises")
        self.assertEqual(int(m_tab_promises.group(1)), self.total_promises)

        m_tab_q = re.search(r'id="tab-count-quarantine"[^>]*>(\d+)<', self.html)
        self.assertIsNotNone(m_tab_q, "Missing #tab-count-quarantine")
        self.assertEqual(int(m_tab_q.group(1)), self.total_quarantined)

    def test_no_zero_category_chips(self):
        """No chip or pill in the page should read (0)."""
        zero_chips = re.findall(r'>[^<]*\(\s*0\s*\)[^<]*<', self.html)
        self.assertEqual(zero_chips, [], f"Found category chip with (0) count: {zero_chips}")

    def test_no_out_of_bounds_ranks(self):
        """No promise row in the HTML should display a rank higher than the total promises count."""
        rank_matches = re.findall(r'class="rank-num"[^>]*>#(\d+)<', self.html)
        for r_str in rank_matches:
            r = int(r_str)
            self.assertLessEqual(
                r, self.total_promises,
                f"Rank #{r} exceeds total promises count {self.total_promises}"
            )

    def test_version_query_strings_present(self):
        """Asset links must include ?v= cache-busting query strings."""
        css_match = re.search(r'<link[^>]+href="styles\.css\?v=[a-zA-Z0-9_-]+"', self.html)
        self.assertIsNotNone(css_match, "styles.css missing ?v= query string")

        app_match = re.search(r'<script[^>]+src="app\.js\?v=[a-zA-Z0-9_-]+"', self.html)
        self.assertIsNotNone(app_match, "app.js missing ?v= query string")

        data_match = re.search(r'<script[^>]+src="data\.js\?v=[a-zA-Z0-9_-]+"', self.html)
        self.assertIsNotNone(data_match, "data.js missing ?v= query string")


if __name__ == "__main__":
    unittest.main()
