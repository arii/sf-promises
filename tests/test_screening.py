import sqlite3
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.screening import screen_origin
from src.extract import parse_extraction
from src.sources import archive_source


class OriginScreenTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        saved = archive_source(self.root, "P1", b"We will build a library.", ".txt")
        self.source = {
            "path": saved["path"],
            "digest": saved["sha256"],
            "quote": "We will build a library.",
            "url": "https://sf.gov/news/example",
            "source_tier": "TIER1_GOV",
        }
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(Path("src/schema.sql").read_text())

    def tearDown(self):
        self.db.close()
        self.directory.cleanup()

    def screen(self, **overrides):
        args = {
            "conn": self.db, "root": self.root, "promise_id": "P1",
            "canonical_slug": "library", "source": self.source,
            "promised": date(2024, 1, 1), "published": date(2024, 1, 2),
            "deadline": date(2024, 3, 1), "search_exhausted": False,
        }
        args.update(overrides)
        return screen_origin(**args)

    def test_passing_screen_requires_further_review_and_never_publishes(self):
        self.assertEqual(self.screen()["status"], "review_required")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    def test_failed_screen_retries_before_atomic_quarantine(self):
        self.source["quote"] = "made up"
        result = self.screen()
        self.assertEqual(result["status"], "retry_discovery")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 0)
        result = self.screen(search_exhausted=True)
        self.assertEqual(result["status"], "quarantined")
        self.assertIn("quote_not_found", result["failures"])
        self.assertEqual(
            self.db.execute("SELECT check_type, passed FROM verifications").fetchall(),
            [("quote_not_found", 0)],
        )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    def test_late_official_origin_requires_review_not_automatic_quarantine(self):
        result = self.screen(published=date(2025, 1, 1), search_exhausted=True)
        self.assertEqual(result["status"], "review_required")
        self.assertIn("historical_origin_requires_review", result["failures"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 0)

    def test_corporate_primary_is_not_historical_government_exception(self):
        self.source["url"] = "https://zoox.com/news/example"
        result = self.screen(published=date(2025, 1, 1))
        self.assertEqual(result["status"], "retry_discovery")
        self.assertIn("origin_publication_late", result["failures"])

    def test_extracted_candidate_is_screened_without_publishing(self):
        response = json.dumps({"candidates": [{
            "promise_id": "P1", "promise_text": self.source["quote"],
            "speaker": None, "promised_date": "2024-01-01",
            "deadline": "2024-03-01",
        }]})
        candidate = parse_extraction(
            root=self.root, promise_id="P1", path=self.source["path"],
            digest=self.source["digest"], response=response,
        )[0]
        result = self.screen(promised=candidate.promised_date, deadline=candidate.deadline)
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
