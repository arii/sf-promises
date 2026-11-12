import sqlite3
import unittest
from pathlib import Path

from src.v2_quarantine import quarantine_candidate


class QuarantineTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(Path("src/schema_v2.sql").read_text())

    def tearDown(self):
        self.db.close()

    def test_quarantine_is_atomic_and_does_not_publish(self):
        quarantine_candidate(self.db, "P01", "library", "origin",
                             ["missing_source"], {"id": "P01"})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 1)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_duplicate_slug_does_not_partially_write(self):
        quarantine_candidate(self.db, "P01", "library", "origin", ["missing"], {})
        with self.assertRaises(sqlite3.IntegrityError):
            quarantine_candidate(self.db, "P02", "library", "origin", ["missing"], {})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 1)

    def test_existing_candidate_can_be_quarantined_and_retried(self):
        self.db.execute("INSERT INTO candidates VALUES ('P01', 'library')")
        self.db.commit()
        for _ in range(2):
            quarantine_candidate(self.db, "P01", "library", "origin", ["missing"], {})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 1)

    def test_failed_checks_are_recorded_once_with_quarantine(self):
        for _ in range(2):
            quarantine_candidate(self.db, "P01", "library", "origin",
                                 ["source_hash_mismatch", "origin_date_missing"], {})
        checks = self.db.execute(
            "SELECT check_type, passed, reason FROM verifications ORDER BY check_type"
        ).fetchall()
        self.assertEqual(checks, [
            ("origin_date_missing", 0, "origin_date_missing"),
            ("source_hash_mismatch", 0, "source_hash_mismatch"),
        ])

    def test_published_candidate_cannot_be_quarantined(self):
        self.db.execute("INSERT INTO candidates VALUES ('P01', 'library')")
        self.db.execute(
            "INSERT INTO promises VALUES ('P01', 'entity', 'type', 'sector', "
            "'neighborhood', 'text', '2020-01-01', '2021-01-01', '2020-01-01')"
        )
        self.db.commit()
        with self.assertRaises(ValueError):
            quarantine_candidate(self.db, "P01", "library", "origin", ["missing"], {})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 0)

    def test_autocommit_rolls_back_after_candidate_insert(self):
        self.db.isolation_level = None
        with self.assertRaises(TypeError):
            quarantine_candidate(self.db, "P01", "library", "origin", ["missing"], object())
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 0)

    def test_verification_failure_rolls_back_quarantine(self):
        self.db.executescript(
            "CREATE TRIGGER reject_verification BEFORE INSERT ON verifications "
            "BEGIN SELECT RAISE(ABORT, 'rejected'); END;"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            quarantine_candidate(self.db, "P01", "library", "origin", ["missing"], {})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
