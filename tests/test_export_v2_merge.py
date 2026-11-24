import copy
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.database import initialize_database
from src.relevance import record_relevance
from src.site_merge import V2DatabaseError, merge_v2, validate_v2_database
from src.sources import archive_source
from tests.test_export import _load_exporter_module

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.sf.gov/news/v2-library-announcement"
TEXT = "Mayor Example said: We will build a library on Mission Street by 2025."
PROMISE = "We will build a library on Mission Street by 2025."


def make_v2(directory, promises, *, source_text=TEXT):
    """Build a tiny v2 database; each spec is a dict overriding the defaults."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    db_path = initialize_database(directory / "promises.db")
    sources = directory / "sources"
    db = sqlite3.connect(db_path)
    db.execute("PRAGMA foreign_keys = ON")
    for spec in promises:
        pid = spec["pid"]
        text = spec.get("text", PROMISE)
        quote = spec.get("quote", TEXT)
        url = spec.get("url", URL)
        saved = archive_source(sources, pid, spec.get("source_text", source_text).encode(), ".md")
        db.execute("INSERT INTO candidates VALUES (?, ?)", (pid, f"slug-{pid.lower()}"))
        db.execute(
            "INSERT INTO promises VALUES (?, 'City Library Dept', 'City Agency', "
            "'Parks & Recreation', 'Citywide', ?, '2024-01-01', '2025-01-01', "
            "'2024-01-02T00:00:00+00:00')", (pid, text))
        db.execute(
            "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, "
            "local_source_path, content_sha256, verbatim_quote, quote_verified, "
            "verification_record_json, published_date, ingested_at) "
            "VALUES (?, 'ORIGIN', 'TIER1_GOV', ?, ?, ?, ?, 1, '{}', '2024-01-02', "
            "'2024-01-02T00:00:00+00:00')", (pid, url, saved["path"], saved["sha256"], quote))
        db.execute(
            "INSERT INTO verdicts (promise_id, verdict, reason, decided_at) VALUES (?, ?, ?, ?)",
            (pid, spec.get("verdict", "IN_PROGRESS"), "construction underway",
             "2024-06-01T00:00:00+00:00"))
        if spec.get("basis"):
            db.execute(
                "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at) "
                "VALUES (?, 'promise_date_basis', 1, ?, '2024-06-01T00:00:00+00:00')",
                (pid, json.dumps({"basis": spec["basis"], "note": "Dated from the page's byline",
                                  "promised_date": "2024-01-01", "published": "2024-01-02",
                                  "phrase": "today"})))
        db.commit()
        record_relevance(
            db, assessment_id=f"a-{pid}", promise_id=pid, promise_text=text,
            signals={"has_verbatim": True, "has_speaker": True, "has_date": True,
                     "names_sf_or_sf_address_agency_ordinance": True},
            evaluated_at=datetime(2024, 1, 2, tzinfo=timezone.utc))
    db.close()
    return db_path, sources


@pytest.fixture
def base():
    return json.loads((ROOT / "docs" / "data.json").read_text())


def run_merge(base, db_path, sources):
    payload = copy.deepcopy(base)
    return payload, merge_v2(payload, [(db_path, sources)])


def test_v2_record_is_added_with_mapped_fields(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901", "basis": "derived_from_publication"}])
    payload, report = run_merge(base, db, src)
    assert report["added"] == [{"promise_id": "P901", "verdict": "in_progress"}]
    record = payload["promises"][-1]
    assert record["promise_id"] == "P901" and record["pipeline"] == "v2"
    assert record["verdict"] == "in_progress"
    assert record["promise_text"] == PROMISE and record["entity"] == "City Library Dept"
    assert record["category"] == "Parks & Recreation" and record["neighborhood"] == "Citywide"
    assert record["source_url"] == URL and record["verbatim_quote"] == TEXT
    assert len(record["source_hash"]) == 64
    assert record["source_file_path"] == record["source_hash"] + ".md"
    assert record["promised_date"] == "2024-01-01" and record["due_date"] == "2025-01-01"
    assert record["decided_at"] == "2024-06-01T00:00:00+00:00"
    assert record["relevance"]["score"] >= 5
    # derived date reads as derived; verdict basis note rides along
    assert record["promise_date_derived"] is True
    assert record["promised_date_note"] == "Dated from the page's byline"
    assert record["verdict_reason"] == "construction underway"
    assert record["verdict_history"][-1]["verdict"] == "in_progress"
    assert any(v["check"] == "promise_date_basis" for v in record["verification_history"])
    # honest missingness, no invented geography
    assert "latitude" not in record and record["address_full"] is None
    assert record["address_status"] == "not_applicable"
    assert record["completion_date_status"] == "not_yet_known"
    assert record["advocate_bundles"] == {}


def test_stated_basis_is_not_derived(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901", "basis": "stated"}])
    payload, _ = run_merge(base, db, src)
    assert payload["promises"][-1]["promise_date_derived"] is False


def test_existing_records_unchanged_and_counts_updated(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}, {"pid": "P902", "verdict": "KEPT",
        "text": "We will build a clinic on Valencia Street by 2025.",
        "quote": "Mayor Example said: We will build a clinic on Valencia Street by 2025.",
        "url": "https://www.sf.gov/news/v2-clinic", "source_text":
        "Mayor Example said: We will build a clinic on Valencia Street by 2025."}])
    payload, report = run_merge(base, db, src)
    n = len(base["promises"])
    assert payload["promises"][:n] == base["promises"]
    assert [p["promise_id"] for p in payload["promises"][n:]] == ["P901", "P902"]
    status = payload["database_status"]
    assert status["tracked_count"] == n + 2 and status["v2_promises_added"] == 2
    assert status["counts"]["kept"] == base["database_status"]["counts"]["kept"] + 1
    assert status["counts"]["in_progress"] == base["database_status"]["counts"]["in_progress"] + 1
    assert sum(status["counts"].values()) == sum(base["database_status"]["counts"].values()) + 2
    assert status["v2_merge"]["added_by_verdict"] == {"in_progress": 1, "kept": 1}
    assert f"{n + 2} published (2 from v2 pipeline)" in status["id_reconciliation"]
    assert payload["metadata"]["v2_promises_added"] == 2
    assert payload["promises"][-1]["impact_rank"] == n + 2
    assert report["added_by_verdict"] == {"in_progress": 1, "kept": 1}


def test_colliding_id_gets_prefix(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P02"}])
    payload, report = run_merge(base, db, src)
    assert report["added"][0]["promise_id"] == "V2-P02"
    assert sum(p["promise_id"] == "P02" for p in payload["promises"]) == 1
    assert payload["promises"][-1]["v2_promise_id"] == "P02"


def test_tampered_source_is_rejected_and_not_published(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    next((src / "P901").glob("*.md")).write_text(TEXT + " (edited)")
    payload, report = run_merge(base, db, src)
    assert report["added"] == []
    assert report["rejected"][0]["promise_id"] == "P901"
    assert "source_hash_mismatch" in report["rejected"][0]["reason"]
    assert payload["promises"] == base["promises"]
    assert payload["database_status"]["v2_promises_added"] == 0


def test_missing_source_and_unfound_quote_are_rejected(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [
        {"pid": "P901"},
        {"pid": "P902", "quote": "Mayor Example said: We will build a library on Mission Street by 2025. Extra words",
         "source_text": TEXT}])
    next((src / "P901").glob("*.md")).unlink()
    _, report = run_merge(base, db, src)
    reasons = {r["promise_id"]: r["reason"] for r in report["rejected"]}
    assert "source_unavailable" in reasons["P901"]
    assert "quote_not_found" in reasons["P902"]
    assert report["added"] == []


def test_duplicate_of_existing_record_is_skipped(base, tmp_path):
    existing = base["promises"][0]
    db, src = make_v2(tmp_path / "v2", [
        {"pid": "P901", "text": existing["promise_text"],
         "quote": existing["promise_text"], "source_text": existing["promise_text"]},
    ])
    payload, report = run_merge(base, db, src)
    assert report["added"] == []
    assert report["duplicates"][0]["promise_id"] == "P901"
    assert report["duplicates"][0]["reason"] == "same_promise_text"
    assert payload["promises"] == base["promises"]


def test_same_url_with_overlapping_quote_is_skipped(base, tmp_path):
    first, first_src = make_v2(tmp_path / "a", [{"pid": "P901"}])
    payload, report = run_merge(base, first, first_src)
    assert len(report["added"]) == 1
    # A second database publishes a differently worded promise from the same page quote.
    second, second_src = make_v2(tmp_path / "b", [{"pid": "P950", "text": "We will build a library on Mission Street"}])
    report2 = merge_v2(payload, [(second, second_src)])
    assert report2["added"] == []
    assert report2["duplicates"][0]["reason"].startswith("same_source_overlapping_quote:P901")


def test_unsupported_database_is_refused(tmp_path):
    other = tmp_path / "other.db"
    sqlite3.connect(other).close()
    with pytest.raises(V2DatabaseError):
        validate_v2_database(other)
    db, _ = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 3")
    with pytest.raises(V2DatabaseError):
        validate_v2_database(db)


def test_v2_database_and_sources_are_not_modified(base, tmp_path):
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    before = {p: p.read_bytes() for p in [db, *src.rglob("*.md")]}
    run_merge(base, db, src)
    assert {p: p.read_bytes() for p in before} == before
    assert not Path(str(db) + "-wal").exists()


def test_apply_v2_merge_rewrites_only_the_staged_export(base, tmp_path):
    exporter = _load_exporter_module()
    staging = tmp_path / "staging"
    staging.mkdir()
    shutil.copyfile(ROOT / "docs" / "data.json", staging / "data.json")
    live_before = (ROOT / "docs" / "data.json").read_bytes()
    legacy_text = (staging / "data.json").read_text()
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    report = exporter.apply_v2_merge(staging, [(db, src)])
    assert len(report["added"]) == 1
    merged = json.loads((staging / "data.json").read_text())
    assert merged["promises"][-1]["promise_id"] == "P901"
    assert merged["promises"][:-1] == base["promises"]
    assert (staging / "data.js").read_text().startswith("/* SF Promises")
    assert (ROOT / "docs" / "data.json").read_bytes() == live_before
    assert legacy_text != (staging / "data.json").read_text()
    with pytest.raises(ValueError):
        exporter.apply_v2_merge(ROOT / "docs", [(db, src)])


def test_cli_merges_v2_after_legacy_export(tmp_path):
    import subprocess
    import sys
    from tests.test_export import _make_history_fixture_db
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    _make_history_fixture_db(legacy / "promises.db")
    db, _ = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, "docs/export_data.py", "--db", str(legacy / "promises.db"),
         "--output-dir", str(out), "--v2-db", str(db)],
        capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, result.stderr
    assert "v2 merge: added 1" in result.stdout
    data = json.loads((out / "data.json").read_text())
    assert data["promises"][-1]["pipeline"] == "v2"
    assert data["database_status"]["v2_promises_added"] == 1
    assert "P901" in (out / "data.js").read_text()
    bad = subprocess.run(
        [sys.executable, "docs/export_data.py", "--db", str(legacy / "promises.db"),
         "--output-dir", str(tmp_path / "out2"), "--v2-db", str(legacy / "promises.db")],
        capture_output=True, text=True, cwd=ROOT)
    assert bad.returncode != 0
    assert not (tmp_path / "out2" / "data.json").exists()
