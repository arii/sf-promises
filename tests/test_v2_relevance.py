import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.v2_relevance import record_relevance


class RelevanceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(Path("src/schema_v2.sql").read_text())
        self.db.execute("INSERT INTO candidates VALUES ('P1', 'library')")
        self.db.commit()
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close()

    def test_records_existing_gate_scores_once_per_assessment(self):
        kwargs = dict(
            assessment_id="run-1", promise_id="P1",
            promise_text="Build 10 new homes in San Francisco",
            evaluated_at=self.now,
            signals={"has_verbatim": True, "has_speaker": True, "has_date": True,
                     "has_number": True, "names_sf_or_sf_address_agency_ordinance": True},
        )
        for _ in range(2):
            scores = record_relevance(self.db, **kwargs)
        self.assertTrue(scores["publish"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM relevance_assessments").fetchone()[0], 1)

    def test_non_boolean_signal_or_reused_id_with_different_input_is_rejected(self):
        base = dict(assessment_id="run-1", promise_id="P1", promise_text="Build 10 homes",
                    evaluated_at=self.now)
        with self.assertRaises(ValueError):
            record_relevance(self.db, **base, signals={"has_verbatim": "true"})
        record_relevance(self.db, **base, signals={"has_verbatim": True})
        with self.assertRaises(ValueError):
            record_relevance(self.db, **base, signals={"has_verbatim": False})


if __name__ == "__main__":
    unittest.main()
