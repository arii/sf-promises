import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from src.discovery import fetch_and_archive
from src.database import initialize_database
from src.evidence import record_preliminary_evidence
from src.extract import parse_extraction
from src.load import load_extraction
from src.quarantine import quarantine_candidate
from src.screening import screen_origin, screen_pending_origin
from src.sources import archive_source


class ExtractionLoadTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(Path("src/schema.sql").read_text())

        class Client:
            async def fetch(self, url):
                return SimpleNamespace(
                    url=url, content="We will build a library.", published_at="2024-01-02",
                    raw={"truncated": False},
                )

        self.source = await fetch_and_archive(Client(), "https://sf.gov/example", self.root, "P1")
        self.response = json.dumps({"candidates": [{
            "promise_id": "P1", "promise_text": "We will build a library.", "speaker": None,
            "promised_date": "2024-01-01", "deadline": "2025-01-01",
        }]})

    def load(self, **overrides):
        values = {
            "conn": self.db, "root": self.root, "promise_id": "P1",
            "canonical_slug": "library", "source": self.source, "response": self.response,
        }
        values.update(overrides)
        return load_extraction(**values)

    async def test_extraction_is_read_only_then_load_is_retry_safe(self):
        parse_extraction(root=self.root, promise_id="P1", path=self.source["path"],
                         digest=self.source["sha256"], response=self.response)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 0)
        ids = self.load()
        self.assertEqual(ids, self.load())
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises_pending").fetchone()[0], 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    async def test_tampered_metadata_never_loads(self):
        Path(self.source["metadata_path"]).write_text("{}")
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises_pending").fetchone()[0], 0)

    async def test_invented_quote_never_loads(self):
        response = json.loads(self.response)
        response["candidates"][0]["promise_text"] = "Invented quote"
        with self.assertRaises(ValueError):
            self.load(response=json.dumps(response))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 0)

    async def test_duplicate_proposals_return_one_pending_id(self):
        response = json.loads(self.response)
        response["candidates"].append(response["candidates"][0])
        ids = self.load(response=json.dumps(response))
        self.assertEqual(len(ids), 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises_pending").fetchone()[0], 1)

    async def test_corrupted_existing_pending_record_is_not_silently_reused(self):
        self.load()
        self.db.execute("UPDATE promises_pending SET proposal_json = '{}'")
        self.db.commit()
        with self.assertRaises(ValueError):
            self.load()

    async def test_retry_rechecks_original_fetch_metadata(self):
        self.load()
        metadata = {key: self.source[key] for key in
                    ("path", "sha256", "url", "requested_url", "published_at", "fetched_at")}
        metadata["fetched_at"] = "2025-01-01T00:00:00+00:00"
        archived = archive_source(
            self.root, "P1", json.dumps(metadata).encode(), ".json"
        )
        new_source = {**metadata, "metadata_path": archived["path"],
                      "metadata_sha256": archived["sha256"]}
        Path(self.source["metadata_path"]).write_text("{}")
        with self.assertRaises(ValueError):
            self.load(source=new_source)

    async def test_existing_identity_conflict_rolls_back(self):
        self.db.execute("INSERT INTO candidates VALUES ('P1', 'different')")
        self.db.commit()
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises_pending").fetchone()[0], 0)

    async def test_empty_bundle_does_not_create_candidate(self):
        self.assertEqual(self.load(response='{"candidates":[]}'), [])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0], 0)

    async def test_cli_loads_saved_extraction_into_existing_database(self):
        database = self.root / "candidate.sqlite"
        initialize_database(database)
        response = self.root / "extraction.json"
        response.write_text(self.response, encoding="utf-8")
        command = [
            sys.executable, "-m", "src.load", "--database", str(database),
            "--sources", str(self.root), "--promise-id", "P1", "--slug", "library",
            "--metadata", self.source["metadata_path"],
            "--metadata-sha256", self.source["metadata_sha256"],
            "--response", str(response),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        subprocess.run(command, check=True, capture_output=True, text=True)
        with sqlite3.connect(database) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM promises_pending").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    async def test_cli_never_creates_a_missing_database(self):
        database = self.root / "missing.sqlite"
        response = self.root / "extraction.json"
        response.write_text(self.response, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "src.load", "--database", str(database),
             "--sources", str(self.root), "--promise-id", "P1", "--slug", "library",
             "--metadata", self.source["metadata_path"],
             "--metadata-sha256", self.source["metadata_sha256"],
             "--response", str(response)], capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(database.exists())

    async def test_cli_rejects_an_unidentified_database_without_writing(self):
        database = self.root / "other.sqlite"
        initialize_database(database)
        with sqlite3.connect(database) as target:
            target.execute("PRAGMA application_id = 0")
        before = database.read_bytes()
        response = self.root / "extraction.json"
        response.write_text(self.response, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "src.load", "--database", str(database),
             "--sources", str(self.root), "--promise-id", "P1", "--slug", "library",
             "--metadata", self.source["metadata_path"],
             "--metadata-sha256", self.source["metadata_sha256"],
             "--response", str(response)], capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(database.read_bytes(), before)

    async def test_quarantine_atomically_marks_pending_and_blocks_reloading(self):
        self.load()
        quarantine_candidate(self.db, "P1", "library", "origin", ["unsupported"], {})
        self.assertEqual(
            self.db.execute("SELECT status FROM promises_pending").fetchone()[0], "quarantined"
        )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)
        with self.assertRaises(ValueError):
            self.load()

    async def test_failed_screen_quarantines_loaded_proposal_without_publishing(self):
        self.load()
        Path(self.source["path"]).write_text("tampered", encoding="utf-8")
        result = screen_origin(
            conn=self.db, root=self.root, promise_id="P1", canonical_slug="library",
            source={"path": self.source["path"], "digest": self.source["sha256"],
                    "quote": "We will build a library.", "url": self.source["url"],
                    "source_tier": "TIER1_GOV"},
            promised=date(2024, 1, 1), published=date(2024, 1, 2),
            deadline=date(2025, 1, 1), search_exhausted=True,
        )
        self.assertEqual(result["status"], "quarantined")
        self.assertIn("source_hash_mismatch", result["failures"])
        self.assertEqual(self.db.execute("SELECT status FROM promises_pending").fetchone()[0], "quarantined")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)
        self.assertEqual(
            self.db.execute("SELECT reason FROM verifications").fetchone()[0], "source_hash_mismatch"
        )

    async def test_loaded_proposal_can_be_screened_but_not_published(self):
        pending_id = self.load()[0]
        result = screen_pending_origin(
            self.db, root=self.root, pending_id=pending_id,
            source_tier="TIER1_GOV", search_exhausted=False
        )
        self.assertEqual(result, {"status": "review_required", "failures": []})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    async def test_pending_screen_retries_then_quarantines_changed_metadata(self):
        pending_id = self.load()[0]
        Path(self.source["metadata_path"]).write_text("{}")
        result = screen_pending_origin(
            self.db, root=self.root, pending_id=pending_id,
            source_tier="TIER1_GOV", search_exhausted=False
        )
        self.assertEqual(result["status"], "retry_discovery")
        self.assertIn("source_metadata_invalid", result["failures"])
        result = screen_pending_origin(
            self.db, root=self.root, pending_id=pending_id,
            source_tier="TIER1_GOV", search_exhausted=True
        )
        self.assertEqual(result["status"], "quarantined")
        self.assertEqual(self.db.execute("SELECT status FROM promises_pending").fetchone()[0], "quarantined")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    async def test_pending_screen_does_not_trust_a_changed_proposal(self):
        pending_id = self.load()[0]
        self.db.execute("UPDATE promises_pending SET proposal_json = '{}'")
        self.db.commit()
        result = screen_pending_origin(
            self.db, root=self.root, pending_id=pending_id,
            source_tier="TIER1_GOV", search_exhausted=True
        )
        self.assertEqual(result["status"], "quarantined")
        self.assertIn("pending_proposal_invalid", result["failures"])

    async def test_pending_screen_blocks_missing_source_publication_date(self):
        metadata = {key: self.source[key] for key in
                    ("path", "sha256", "url", "requested_url", "published_at", "fetched_at")}
        metadata["published_at"] = None
        archived = archive_source(self.root, "P1", json.dumps(metadata).encode(), ".json")
        source = {**metadata, "metadata_path": archived["path"],
                  "metadata_sha256": archived["sha256"]}
        pending_id = self.load(source=source)[0]
        result = screen_pending_origin(
            self.db, root=self.root, pending_id=pending_id,
            source_tier="TIER1_GOV", search_exhausted=False,
        )
        self.assertEqual(result["status"], "retry_discovery")
        self.assertIn("origin_date_missing", result["failures"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    async def test_evidence_ingestion_is_retry_safe_and_not_semantic_proof(self):
        self.load()
        kwargs = dict(
            conn=self.db, root=self.root, promise_id="P1", source=self.source,
            phase="ORIGIN", source_tier="TIER1_GOV", quote="We will build a library.",
        )
        result = record_preliminary_evidence(**kwargs)
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(record_preliminary_evidence(**kwargs), result)
        row = self.db.execute(
            "SELECT quote_verified, verification_record_json, ingested_at FROM evidence_ledger"
        ).fetchone()
        self.assertEqual(row[0], 1)
        self.assertFalse(json.loads(row[1])["semantics_verified"])
        self.assertTrue(row[2].endswith("+00:00"))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM evidence_ledger").fetchone()[0], 1)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 0)

    async def test_rejected_evidence_records_failure_without_promoting_it(self):
        self.load()
        result = record_preliminary_evidence(
            self.db, root=self.root, promise_id="P1", source=self.source,
            phase="ORIGIN", source_tier="TIER1_GOV", quote="Invented quote",
        )
        self.assertEqual(result["status"], "rejected")
        self.assertIn("quote_not_found", result["failures"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM evidence_ledger").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT passed FROM verifications").fetchone()[0], 0)

    async def test_refetch_of_same_evidence_does_not_create_new_corroboration(self):
        self.load()
        kwargs = dict(
            conn=self.db, root=self.root, promise_id="P1", source=self.source,
            phase="ORIGIN", source_tier="TIER1_GOV", quote="We will build a library.",
        )
        original = record_preliminary_evidence(**kwargs)
        metadata = {key: self.source[key] for key in
                    ("path", "sha256", "url", "requested_url", "published_at", "fetched_at")}
        metadata["fetched_at"] = "2025-01-01T00:00:00+00:00"
        archived = archive_source(self.root, "P1", json.dumps(metadata).encode(), ".json")
        second = {**metadata, "metadata_path": archived["path"],
                  "metadata_sha256": archived["sha256"]}
        self.assertEqual(record_preliminary_evidence(**(kwargs | {"source": second})), original)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM evidence_ledger").fetchone()[0], 1)
        metadata["published_at"] = "2024-01-03"
        changed = archive_source(self.root, "P1", json.dumps(metadata).encode(), ".json")
        conflicting = {**metadata, "metadata_path": changed["path"],
                       "metadata_sha256": changed["sha256"]}
        with self.assertRaises(ValueError):
            record_preliminary_evidence(**(kwargs | {"source": conflicting}))

    async def test_evidence_and_verification_roll_back_together(self):
        self.load()
        self.db.executescript(
            "CREATE TRIGGER reject_evidence_verification BEFORE INSERT ON verifications "
            "BEGIN SELECT RAISE(ABORT, 'rejected'); END;"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            record_preliminary_evidence(
                self.db, root=self.root, promise_id="P1", source=self.source,
                phase="ORIGIN", source_tier="TIER1_GOV", quote="We will build a library.",
            )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM evidence_ledger").fetchone()[0], 0)

    async def test_failed_quarantine_keeps_proposal_pending(self):
        self.load()
        self.db.executescript(
            "CREATE TRIGGER reject_verification BEFORE INSERT ON verifications "
            "BEGIN SELECT RAISE(ABORT, 'rejected'); END;"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            quarantine_candidate(self.db, "P1", "library", "origin", ["unsupported"], {})
        self.assertEqual(
            self.db.execute("SELECT status FROM promises_pending").fetchone()[0], "pending"
        )
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 0)

    async def test_pending_cannot_reference_another_candidates_quarantine(self):
        self.load()
        quarantine_candidate(self.db, "P2", "other", "origin", ["unsupported"], {})
        quarantine_id = self.db.execute("SELECT quarantine_id FROM quarantined").fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "UPDATE promises_pending SET status = 'quarantined', quarantine_id = ?",
                (quarantine_id,),
            )

    async def test_pending_update_failure_rolls_back_quarantine_and_verifications(self):
        self.load()
        self.db.executescript(
            "CREATE TRIGGER reject_pending_update AFTER UPDATE ON promises_pending "
            "BEGIN SELECT RAISE(ABORT, 'rejected'); END;"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            quarantine_candidate(self.db, "P1", "library", "origin", ["unsupported"], {})
        self.assertEqual(self.db.execute("SELECT status FROM promises_pending").fetchone()[0], "pending")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM quarantined").fetchone()[0], 0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM verifications").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
