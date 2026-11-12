import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class V2SchemaTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(Path("src/schema.sql").read_text())

    def tearDown(self):
        self.db.close()

    def test_quarantine_does_not_require_a_published_promise(self):
        self.db.execute(
            "INSERT INTO candidates (promise_id, canonical_slug) VALUES (?, ?)",
            ("P1", "example"),
        )
        self.db.execute(
            "INSERT INTO quarantined (promise_id, stage, reason_codes_json, "
            "candidate_payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            ("P1", "origin", '["missing"]', "{}", "2026-01-01"),
        )
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    def test_evidence_requires_a_real_candidate(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO evidence_ledger (promise_id, phase, source_tier, "
                "url, local_source_path, content_sha256, verbatim_quote, "
                "quote_verified, verification_record_json, ingested_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("missing", "ORIGIN", "TIER1_GOV", "https://sf.gov", "a", "x", "q", 0, "{}",
                 "2026-01-01T00:00:00+00:00"),
            )

    def test_canonical_slug_is_unique(self):
        self.db.execute("INSERT INTO candidates VALUES (?, ?)", ("P1", "same"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO candidates VALUES (?, ?)", ("P2", "same"))

    def test_cli_initializes_a_separate_database_without_overwriting_existing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "candidate.sqlite"
            command = [sys.executable, "-m", "src.database", str(target)]
            subprocess.run(command, check=True, capture_output=True, text=True)
            with sqlite3.connect(target) as db:
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                tables = {row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )}
                self.assertIn("promises_pending", tables)
                self.assertIn("quarantined", tables)
                db.execute("INSERT INTO candidates VALUES ('P1', 'library')")
            before = target.read_bytes()
            retry = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(target.read_bytes(), before)

    def test_cli_refuses_existing_v1_database(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "v1.sqlite"
            with sqlite3.connect(target) as db:
                db.execute("CREATE TABLE legacy_sample (id INT);")
            before = target.read_bytes()
            result = subprocess.run(
                [sys.executable, "-m", "src.database", str(target)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
