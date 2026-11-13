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

    def test_no_unsanitized_local_paths_in_html(self):
        """Zero /home/ or /mnt/ local paths allowed in docs/index.html."""
        home_matches = re.findall(r'/home/[^\s"\'<>]+', self.html)
        mnt_matches = re.findall(r'/mnt/[^\s"\'<>]+', self.html)
        self.assertEqual(home_matches, [], f"Found /home/ paths in docs/index.html: {home_matches}")
        self.assertEqual(mnt_matches, [], f"Found /mnt/ paths in docs/index.html: {mnt_matches}")

    def test_no_stale_contradictory_hardcoded_claims(self):
        """Ensure no stale or contradicting hardcoded claim text in docs/index.html."""
        stale_phrases = [
            "place 300 individuals",
            "35 fatalities",
        ]
        for phrase in stale_phrases:
            self.assertNotIn(phrase, self.html, f"Found stale hardcoded phrase '{phrase}' in docs/index.html")

    def test_featured_stories_contract(self):
        """Featured stories must contain exactly 6 stories matching expected IDs."""
        story_cards = re.findall(r'class="story-card"[^>]*data-story-pid="([^"]+)"', self.html)
        expected_ids = ["P02", "SFO-01", "P05", "P06", "P37", "Q-N01"]
        self.assertEqual(len(story_cards), 6, f"Expected 6 story cards, found {len(story_cards)}")
        self.assertEqual(story_cards, expected_ids, f"Story cards IDs mismatch: {story_cards}")

    def test_master_dataset_schema_and_types(self):
        """sf_promises_master.csv must strictly conform to the 16-column Adaption schema."""
        import csv
        csv_path = Path("data/sf_promises_master.csv")
        self.assertTrue(csv_path.exists(), "data/sf_promises_master.csv must exist")

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        expected_columns = [
            "promise_id", "promise_text", "entity", "entity_role", "entity_type",
            "category", "promise_made_date", "deadline_date", "verdict", "confidence",
            "evidence_count", "primary_source_url", "primary_source_type",
            "neighborhood", "impact_score", "notes"
        ]
        self.assertEqual(reader.fieldnames, expected_columns, "Master CSV columns mismatch")
        self.assertEqual(len(rows), 54, f"Expected 54 rows in master CSV, got {len(rows)}")

        for r in rows:
            self.assertTrue(r["promise_id"])
            self.assertTrue(r["promise_text"])
            self.assertTrue(r["entity"])
            self.assertIn(r["verdict"], ("kept", "broken", "in_progress", "undecided"))
            conf = float(r["confidence"])
            self.assertGreaterEqual(conf, 0.0)
            self.assertLessEqual(conf, 1.0)
            self.assertGreaterEqual(int(r["evidence_count"]), 1)
            self.assertGreaterEqual(int(r["impact_score"]), 0)


if __name__ == "__main__":
    unittest.main()
