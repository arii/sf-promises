import sqlite3
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import json

from src.export import build_snapshot, write_candidate_snapshot
from src.relevance import record_relevance
from src.sources import archive_source


def _load_exporter_module():
    """Load docs/export_data.py by path (docs is not a package)."""
    path = Path(__file__).resolve().parents[1] / "docs" / "export_data.py"
    spec = importlib.util.spec_from_file_location("docs_export_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_history_fixture_db(db_path):
    """Minimal schema _load_from_db reads: a P83-shaped promise reopened from
    kept to kept_then_reversed (append-only, two verdict rows), a
    single-verdict promise, verifications rows carrying model provenance, and
    the relevance/quarantine tables the loader walks unconditionally."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE entities (
            entity_id TEXT PRIMARY KEY, name TEXT, role TEXT, entity_type TEXT);
        CREATE TABLE promises (
            promise_id TEXT PRIMARY KEY, entity_id TEXT, promise_text TEXT,
            promised_date TEXT, due_date TEXT, source_url TEXT,
            source_file_path TEXT, source_hash TEXT, source_type TEXT,
            status TEXT);
        CREATE TABLE verdicts (
            verdict_id TEXT PRIMARY KEY, promise_id TEXT, verdict TEXT,
            reason TEXT, reading_used TEXT, decided_at TEXT, decided_by TEXT,
            model_id TEXT);
        CREATE TABLE sources (
            source_id TEXT PRIMARY KEY, promise_id TEXT, file_path TEXT,
            source_hash TEXT, source_type TEXT, source_url TEXT, fetched_at TEXT);
        CREATE TABLE relevance_checks (
            promise_id TEXT, criterion TEXT, score INTEGER);
        CREATE TABLE verifications (
            verification_id TEXT PRIMARY KEY, promise_id TEXT,
            check_type TEXT, passed INTEGER, reason TEXT, checked_at TEXT,
            checked_by TEXT, model_id TEXT, run_id TEXT);
        CREATE TABLE quarantined (
            quarantine_id TEXT PRIMARY KEY, promise_id TEXT, reason TEXT,
            quarantined_at TEXT, source_file_path TEXT, source_hash TEXT);
    """)
    cur.execute(
        "INSERT INTO entities VALUES ('E1', 'Whole Foods Market', 'company', 'corporation')")
    cur.execute(
        "INSERT INTO promises VALUES ('P83', 'E1', 'Whole Foods Market will open "
        "its new flagship store at Trinity Place on Thursday, March 10.', "
        "'2022-02-17', '2022-03-10', 'https://www.webwire.com/ViewPressRel.asp?aId=285415', "
        "'origins/P83.html', 'abc123', 'press_release', 'published')")
    # Append-only history: the original kept row is never mutated; the reopen
    # appends a second row with its own provenance.
    cur.execute(
        "INSERT INTO verdicts VALUES ('VER-P83-1', 'P83', 'KEPT', "
        "'official primary evidence confirms completion', 'delivery', "
        "'2022-03-11T00:00:00Z', 'arbitrator', 'model-a')")
    cur.execute(
        "INSERT INTO verdicts VALUES ('VER-P83-2', 'P83', 'KEPT_THEN_REVERSED', "
        "'Durability recheck: delivered on schedule, shuttered April 2023.', "
        "'survival', '2026-11-14T09:35:18Z', 'durability_cron', 'model-b')")
    cur.execute(
        "INSERT INTO sources VALUES ('S1', 'P83', 'origins/P83.html', 'abc123', "
        "'press_release', 'https://www.webwire.com/ViewPressRel.asp?aId=285415', "
        "'2022-02-17T00:00:00Z')")
    for i, (chk, passed, at, model, run) in enumerate([
        ("authenticity_domain", 1, "2022-03-11T00:00:00Z", "model-a", "RUN-1"),
        ("authenticity_hash", 1, "2022-03-11T00:00:01Z", "model-a", "RUN-1"),
        ("verdict_rubric", 1, "2022-03-11T00:00:02Z", "model-b", "RUN-2"),
    ]):
        cur.execute(
            "INSERT INTO verifications VALUES (?, 'P83', ?, ?, 'ok', ?, "
            "'arbitrator', ?, ?)", (f"V{i}", chk, passed, at, model, run))
    # A single-verdict record with no verifications rows: the honest-empty
    # path. P06 is an existing corpus id, so record ids stay realistic.
    cur.execute(
        "INSERT INTO promises VALUES ('P06', 'E1', 'Adopt Vision Zero.', "
        "'2014-01-01', '2024-12-31', 'https://www.sf.gov/vision-zero', "
        "'origins/P06.html', 'def456', 'sf_gov_page', 'published')")
    cur.execute(
        "INSERT INTO verdicts VALUES ('VER-P06-1', 'P06', 'BROKEN', "
        "'fatal collisions were not eliminated by 2024.', 'delivery', "
        "'2025-01-15T00:00:00Z', 'arbitrator', 'model-a')")
    cur.execute(
        "INSERT INTO sources VALUES ('S2', 'P06', 'origins/P06.html', 'def456', "
        "'sf_gov_page', 'https://www.sf.gov/vision-zero', '2014-01-01T00:00:00Z')")
    con.commit()
    con.close()


class VerdictHistoryExportTests(unittest.TestCase):
    """E2: verdict_history and verification_history in the DB-backed export."""

    @classmethod
    def setUpClass(cls):
        cls.exporter = _load_exporter_module()
        cls.directory = tempfile.TemporaryDirectory()
        db_path = str(Path(cls.directory.name) / "promises.db")
        _make_history_fixture_db(db_path)
        (cls.all_promises, _, _, _, _, _, _) = cls.exporter._load_from_db(db_path)
        cls.by_id = {p["promise_id"]: p for p in cls.all_promises}

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_every_record_exports_both_history_fields(self):
        for p in self.all_promises:
            self.assertIn("verdict_history", p)
            self.assertIn("verification_history", p)

    def test_reopened_record_has_two_step_ordered_history(self):
        vh = self.by_id["P83"]["verdict_history"]
        self.assertEqual(len(vh), 2)
        self.assertEqual(vh[0]["verdict"], "kept")
        self.assertEqual(vh[1]["verdict"], "kept_then_reversed")
        self.assertLess(vh[0]["decided_at"], vh[1]["decided_at"])

    def test_newest_history_entry_matches_the_record_verdict(self):
        for p in self.all_promises:
            vh = p["verdict_history"]
            self.assertGreaterEqual(len(vh), 1)
            self.assertEqual(vh[-1]["verdict"], p["verdict"])

    def test_db_provenance_is_carried_not_invented(self):
        vh = self.by_id["P83"]["verdict_history"]
        self.assertEqual(vh[0]["reviewer"], "arbitrator")
        self.assertEqual(vh[0]["model_id"], "model-a")
        self.assertEqual(vh[1]["reviewer"], "durability_cron")
        self.assertEqual(vh[1]["model_id"], "model-b")
        # The newest entry's reason is delta-encoded onto the record's own
        # verdict_reason (which is the reopen rationale) and consumers fall
        # back to it; the older entry's distinct reason is carried in full.
        self.assertTrue(
            self.by_id["P83"]["verdict_reason"].startswith("Durability recheck"))
        self.assertIn("official primary evidence", vh[0]["reason"])

    def test_newest_reason_is_deduplicated_against_the_record(self):
        # The newest entry repeats the record's current verdict_reason; the
        # delta encoding drops it and consumers fall back to the record.
        for p in self.all_promises:
            vh = p["verdict_history"]
            self.assertNotEqual(vh[-1].get("reason"), p.get("verdict_reason"))

    def test_original_kept_verdict_row_is_preserved_verbatim(self):
        # Append-only: the reopen never mutates the first row's verdict,
        # decided_at, or reason.
        vh = self.by_id["P83"]["verdict_history"]
        self.assertEqual(vh[0]["verdict"], "kept")
        self.assertEqual(vh[0]["decided_at"], "2022-03-11T00:00:00Z")
        self.assertEqual(
            vh[0]["reason"], "official primary evidence confirms completion")

    def test_verification_history_carries_per_check_provenance(self):
        vhist = self.by_id["P83"]["verification_history"]
        self.assertEqual(len(vhist), 3)
        self.assertEqual([e["check"] for e in vhist],
                         ["authenticity_domain", "authenticity_hash", "verdict_rubric"])
        self.assertTrue(all(e["passed"] for e in vhist))
        self.assertEqual(vhist[0]["model_id"], "model-a")
        self.assertEqual(vhist[0]["run_id"], "RUN-1")
        self.assertEqual(vhist[2]["model_id"], "model-b")
        self.assertLessEqual(vhist[0]["checked_at"], vhist[2]["checked_at"])

    def test_no_verification_rows_means_honest_empty_history(self):
        # P06 has no verifications rows: history stays empty instead of
        # padding null provenance; the latest check state rides in `checks`.
        self.assertEqual(self.by_id["P06"]["verification_history"], [])
        self.assertEqual(self.by_id["P06"]["verdict_history"][-1]["verdict"],
                         "broken")


class SnapshotHistoryAssertions(unittest.TestCase):
    """E2 assertions over the committed demo snapshot (when present)."""

    def test_committed_snapshot_carries_history_and_stays_compact(self):
        docs_json = Path("docs/data.json")
        if not docs_json.exists():
            self.skipTest("docs/data.json not present")
        data = json.loads(docs_json.read_text(encoding="utf-8"))
        promises = data.get("promises", [])
        self.assertGreater(len(promises), 0)
        history_bytes = 0
        for p in promises:
            self.assertIn("verdict_history", p)
            self.assertIn("verification_history", p)
            vh = p["verdict_history"]
            self.assertGreaterEqual(len(vh), 1)
            self.assertEqual(vh[-1]["verdict"], p["verdict"])
            history_bytes += len(json.dumps(vh)) + len(json.dumps(p["verification_history"]))
        # The history adds little: the whole corpus's history must stay a
        # small fraction of the snapshot rather than growing unchecked.
        self.assertLess(history_bytes, 40000)
        # Flat-or-smaller target: the full snapshot stays well under the
        # pre-history baseline plus a small history allowance.
        self.assertLess(docs_json.stat().st_size, 700000)


class CandidateExportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.source = archive_source(self.root, "P1", b"We will build a library.", ".txt")
        self.db = sqlite3.connect(":memory:")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(Path("src/schema.sql").read_text())
        self.db.execute("INSERT INTO candidates VALUES ('P1', 'library')")
        self.db.execute(
            "INSERT INTO promises VALUES ('P1', 'City', 'City Agency', 'Housing & Land Use', "
            "'Parkmerced', 'We will build a library.', '2024-01-01', '2025-01-01', "
            "'2024-01-02T00:00:00+00:00')"
        )
        self.db.execute(
            "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, "
            "local_source_path, content_sha256, verbatim_quote, quote_verified, "
            "verification_record_json, published_date, ingested_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("P1", "ORIGIN", "TIER1_GOV", "https://sf.gov/news/example",
             self.source["path"], self.source["sha256"],
             "We will build a library.", 1, "{}", "2024-01-02", "2024-01-02T00:00:00+00:00"),
        )
        self.db.execute(
            "INSERT INTO verdicts (promise_id, verdict, reason, decided_at) "
            "VALUES ('P1', 'IN_PROGRESS', 'pending', '2024-01-03T00:00:00+00:00')"
        )
        self.db.commit()
        self.as_of = datetime(2026, 1, 1, tzinfo=timezone.utc)
        record_relevance(
            self.db, assessment_id="initial", promise_id="P1",
            promise_text="We will build a library.",
            signals={"has_verbatim": True, "has_speaker": True, "has_date": True,
                     "names_sf_or_sf_address_agency_ordinance": True},
            evaluated_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )

    def tearDown(self):
        self.db.close()
        self.directory.cleanup()

    def test_selects_latest_applicable_verdict_and_derives_tally(self):
        self.db.executemany(
            "INSERT INTO verdicts (promise_id, verdict, reason, decided_at) VALUES (?, ?, ?, ?)",
            [
                ("P1", "KEPT", "opened", "2024-01-04T00:00:00+00:00"),
                ("P1", "BROKEN", "later", "2027-01-01T00:00:00+00:00"),
            ],
        )
        self.db.commit()
        result = build_snapshot(self.db, source_root=self.root, as_of=self.as_of)
        self.assertEqual(len(result["promises"]), 1)
        self.assertEqual(result["promises"][0]["verdict"], "KEPT")
        self.assertEqual(result["tallies"], {"KEPT": 1})
        self.assertEqual(result["snapshot_kind"], "candidate_not_published")
        self.assertEqual(result["promises"][0]["relevance"]["total"], 5)

    def test_modified_evidence_blocks_export(self):
        Path(self.source["path"]).write_text("tampered", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)

    def test_missing_verdict_blocks_export(self):
        self.db.execute("DELETE FROM verdicts")
        self.db.commit()
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)

    def test_promises_created_after_snapshot_are_not_included(self):
        self.db.execute("UPDATE promises SET created_at = '2027-01-01T00:00:00+00:00'")
        self.db.commit()
        snapshot = build_snapshot(self.db, source_root=self.root, as_of=self.as_of)
        self.assertEqual(snapshot["promises"], [])
        self.assertEqual(snapshot["tallies"], {})

    def test_evidence_ingested_after_cutoff_is_not_in_the_snapshot(self):
        self.db.execute(
            "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, "
            "local_source_path, content_sha256, verbatim_quote, quote_verified, "
            "verification_record_json, published_date, ingested_at) "
            "VALUES ('P1', 'DELIVERY', 'TIER1_GOV', 'https://sf.gov/example', "
            "'invalid', 'invalid', 'unverified', 0, '{}', '2024-01-03', "
            "'2027-01-01T00:00:00+00:00')"
        )
        self.db.commit()
        snapshot = build_snapshot(self.db, source_root=self.root, as_of=self.as_of)
        self.assertEqual(len(snapshot["promises"][0]["evidence"]), 1)

    def test_later_ingested_origin_does_not_support_an_earlier_snapshot(self):
        self.db.execute("UPDATE evidence_ledger SET ingested_at = '2027-01-01T00:00:00+00:00'")
        self.db.commit()
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)

    def test_promise_text_must_be_supported_by_origin_quote(self):
        self.db.execute("UPDATE promises SET promise_text = 'Different promise'")
        self.db.commit()
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)

    def test_verdict_order_uses_timezones_and_id_tiebreak(self):
        self.db.executemany(
            "INSERT INTO verdicts (promise_id, verdict, reason, decided_at) VALUES (?, ?, ?, ?)",
            [
                ("P1", "KEPT", "first", "2024-01-04T02:00:00+02:00"),
                ("P1", "BROKEN", "second", "2024-01-04T00:00:00+00:00"),
            ],
        )
        self.db.commit()
        snapshot = build_snapshot(self.db, source_root=self.root, as_of=self.as_of)
        self.assertEqual(snapshot["promises"][0]["verdict"], "BROKEN")

    def test_invalid_taxonomy_blocks_candidate_export(self):
        self.db.execute("UPDATE promises SET sector = 'Not a valid sector'")
        self.db.commit()
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)

    def test_short_horizon_or_missing_origin_date_blocks_export(self):
        self.db.execute("UPDATE promises SET date_deadline = '2024-02-01'")
        self.db.commit()
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)
        self.db.execute("UPDATE promises SET date_deadline = '2025-01-01'")
        self.db.execute("UPDATE evidence_ledger SET published_date = NULL")
        self.db.commit()
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)

    def test_latest_low_relevance_blocks_candidate_export(self):
        record_relevance(
            self.db, assessment_id="later", promise_id="P1",
            promise_text="We will build a library.", signals={},
            evaluated_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
        )
        with self.assertRaises(ValueError):
            build_snapshot(self.db, source_root=self.root, as_of=self.as_of)

    def test_candidate_json_is_database_derived_and_never_overwrites(self):
        destination = self.root / "candidate.json"
        write_candidate_snapshot(self.db, source_root=self.root, as_of=self.as_of, output=destination)
        document = json.loads(destination.read_text())
        self.assertEqual(document["snapshot_kind"], "candidate_not_published")
        self.assertEqual(document["promises"][0]["promise_text"], "We will build a library.")
        before = destination.read_bytes()
        with self.assertRaises(FileExistsError):
            write_candidate_snapshot(self.db, source_root=self.root, as_of=self.as_of, output=destination)
        self.assertEqual(destination.read_bytes(), before)

    def test_candidate_cannot_be_written_under_live_docs(self):
        with self.assertRaises(ValueError):
            write_candidate_snapshot(
                self.db, source_root=self.root, as_of=self.as_of,
                output=Path("docs") / "test-candidate.json",
            )

    def test_cli_writes_review_snapshot_from_read_only_database(self):
        database = self.root / "candidate.sqlite"
        with sqlite3.connect(database) as target:
            self.db.backup(target)
        output = self.root / "cli-candidate.json"
        subprocess.run(
            [sys.executable, "-m", "src.export", "--database", str(database),
             "--sources", str(self.root), "--output", str(output),
             "--as-of", self.as_of.isoformat()],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(json.loads(output.read_text())["tallies"], {"IN_PROGRESS": 1})

    def test_p83_is_the_sole_kept_then_reversed_record(self):
        """E1b: P83 (Whole Foods) is the only corpus record reopened to
        kept_then_reversed, and its gold-set consensus mirrors the flip."""
        docs_json = Path("docs/data.json")
        if not docs_json.exists():
            return
        data = json.loads(docs_json.read_text(encoding="utf-8"))
        promises = data.get("promises", [])
        reversed_records = [p for p in promises if p.get("verdict") == "kept_then_reversed"]
        self.assertEqual(len(reversed_records), 1)
        self.assertEqual(reversed_records[0].get("promise_id"), "P83")

        gold = json.loads(Path("data/gold_set.json").read_text(encoding="utf-8"))
        entries = gold if isinstance(gold, list) else gold.get("gold_promises", [])
        p83_gold = next(
            (g for g in entries if g.get("promise_id") == "P83"),
            None,
        )
        self.assertIsNotNone(p83_gold)
        self.assertEqual(p83_gold.get("consensus_verdict"), "kept_then_reversed")

    def test_live_docs_data_export_integrity(self):
        docs_json = Path("docs/data.json")
        if not docs_json.exists():
            return
        data = json.loads(docs_json.read_text(encoding="utf-8"))
        promises = data.get("promises", [])
        self.assertGreater(len(promises), 0)

        # 1. Category sums equal total promises
        from collections import Counter
        cat_counts = Counter(p.get("category") for p in promises)
        self.assertEqual(sum(cat_counts.values()), len(promises))
        self.assertNotIn("Energy & Infrastructure", cat_counts)
        self.assertIn("Environment & Energy", cat_counts)

        # 2. Verdict casing normalized to lowercase
        valid_verdicts = {"kept", "broken", "in_progress", "undecided", "stalled", "delayed_or_partial", "kept_then_reversed"}
        for p in promises:
            self.assertIn(p.get("verdict"), valid_verdicts)

        # 3. Every row has a source hash
        for p in promises:
            self.assertTrue(bool(p.get("source_hash")), f"Missing source hash for {p.get('promise_id')}")

        # 4. No future export dates in last_updated
        last_updated = data.get("metadata", {}).get("last_updated")
        if last_updated:
            try:
                dt = datetime.strptime(last_updated, "%b %d, %Y").replace(tzinfo=timezone.utc)
                self.assertLessEqual(dt, datetime.now(timezone.utc))
            except ValueError:
                pass

        # 5. Sandbox isolation is verified
        self.assertTrue(data.get("database_status", {}).get("sandbox_isolation_verified"))
        self.assertIn("verified", data.get("database_status", {}).get("sandbox_isolation_label", "").lower())

        # 6. P02 source is official sf.gov with verified hash
        p02 = next((p for p in promises if p.get("promise_id") == "P02"), None)
        self.assertIsNotNone(p02)
        self.assertIn("sf.gov", p02.get("source_url", ""))
        self.assertEqual(p02.get("source_hash"), "582955d5df783be72732eb5f4e9ccec6e02fe98ff730623861485ee39ddcddaa")

        # 7. P61 uses full sentence, not table fragment
        p61 = next((p for p in promises if p.get("promise_id") == "P61"), None)
        self.assertIsNotNone(p61)
        self.assertNotIn("2009 (Revised) July 28, 2009 $4,586M 12/04/15", p61.get("promise_text", ""))
        self.assertIn("approved a revised WSIP schedule", p61.get("promise_text", ""))

        # 8. All 12 planted test cases (N01-N12) are quarantined and none are in promises
        promise_ids = {p.get("promise_id") for p in promises}
        for i in range(1, 13):
            nid = f"N{i:02d}"
            self.assertNotIn(nid, promise_ids)

        quarantined_pids = {q.get("promise_id") for q in data.get("quarantined", [])}
        for i in range(1, 13):
            nid = f"N{i:02d}"
            self.assertIn(nid, quarantined_pids)

        # 9. No /home/ or /mnt/ in exported data
        json_raw = docs_json.read_text(encoding="utf-8")
        self.assertNotIn("/home/", json_raw, "Found /home/ path leak in docs/data.json")
        self.assertNotIn("/mnt/", json_raw, "Found /mnt/ path leak in docs/data.json")
        docs_js = Path("docs/data.js")
        if docs_js.exists():
            js_raw = docs_js.read_text(encoding="utf-8")
            self.assertNotIn("/home/", js_raw, "Found /home/ path leak in docs/data.js")
            self.assertNotIn("/mnt/", js_raw, "Found /mnt/ path leak in docs/data.js")

        # 10. Metadata has valid commit_sha and exported_at
        meta = data.get("metadata", {})
        self.assertTrue(bool(meta.get("commit_sha")), "Missing commit_sha in metadata")
        self.assertTrue(bool(meta.get("exported_at")), "Missing exported_at in metadata")
        self.assertEqual(meta.get("sqlite_file"), "promises.db")

        # 11. Featured stories configuration integrity
        featured_ids = ["P02", "SFO-01", "P05", "P06", "P37", "Q-N01"]
        p_map = {p.get("promise_id"): p for p in promises}
        q_map = {q.get("quarantine_id"): q for q in data.get("quarantined", [])}
        for fid in featured_ids:
            if fid.startswith("Q-") or fid.startswith("N"):
                self.assertIn(fid, q_map, f"Missing featured quarantine story {fid}")
            else:
                self.assertIn(fid, p_map, f"Missing featured promise story {fid}")

        # 12. Quarantine registry entries have required audit fields
        for q in data.get("quarantined", []):
            self.assertTrue(bool(q.get("quarantine_id")), "Quarantine row missing quarantine_id")
            self.assertTrue(bool(q.get("check_type")), "Quarantine row missing check_type")
            self.assertTrue(bool(q.get("failing_check")), "Quarantine row missing failing_check")
            self.assertTrue(bool(q.get("reason")), "Quarantine row missing reason")
            self.assertIn("Held back", q.get("destination", ""))
            self.assertTrue(bool(q.get("agent")), "Quarantine row missing agent")


if __name__ == "__main__":
    unittest.main()
