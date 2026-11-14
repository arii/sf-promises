"""
CLI wrapper tests for the on-demand durability cycle
(python -m src.run_live --durability-cycle [--dry-run]).
"""

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.database import initialize_database
from src.run_live import DurabilityCycleError, durability_cycle
from src.sources import archive_source

REPO_ROOT = Path(__file__).resolve().parents[1]

CLOSURE_TEXT = (
    "Whole Foods Market confirmed the Trinity Place flagship store at "
    "1185 Market Street has remained closed since April 2023.\n"
)
CLOSURE_QUOTE = (
    "the Trinity Place flagship store at 1185 Market Street has "
    "remained closed since April 2023."
)


@pytest.fixture
def live_db(tmp_path):
    """A supported live-schema database with one due kept promise carrying
    SHUTTERED_OR_CLOSED survival evidence that passes the evidence bar."""
    database = initialize_database(tmp_path / "promises_v2.db")
    root = tmp_path / "sources"
    source = archive_source(root, "P36", CLOSURE_TEXT.encode("utf-8"), ".txt")
    conn = sqlite3.connect(database)
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO candidates (promise_id, canonical_slug) VALUES ('P36', 'p36-whole-foods')"
        )
        conn.execute(
            "INSERT INTO promises (promise_id, entity_name, entity_type, sector, neighborhood, "
            "promise_text, date_promised, date_deadline, created_at) "
            "VALUES ('P36', 'Whole Foods Market', 'Company', 'Retail', 'Mid-Market', "
            "'Open the flagship store', '2022-02-17', '2022-03-10', ?)",
            (now,),
        )
        # Decided 2026-06-01: the kept recheck window (+90 days) is overdue.
        conn.execute(
            "INSERT INTO verdicts (promise_id, verdict, reason, decided_at) "
            "VALUES ('P36', 'KEPT', 'Store opened on March 10, 2022', '2026-06-01T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO evidence_ledger (promise_id, phase, source_tier, url, published_date, "
            "local_source_path, content_sha256, verbatim_quote, quote_verified, "
            "verification_record_json, ingested_at) "
            "VALUES ('P36', 'SURVIVAL', 'TIER1_GOV', 'https://sf.gov/whole-foods-trinity-closure', "
            "'2023-04-12', ?, ?, ?, 1, '{}', ?)",
            (source["path"], source["sha256"], CLOSURE_QUOTE, now),
        )
        conn.commit()
    finally:
        conn.close()
    return database


class FakeCompletion:
    """Queue-free stand-in for the agent lane.

    One scripted value is returned for every call (both advocates agree);
    several values are consumed one per call, in order.
    """

    def __init__(self, *survival_values):
        self.values = list(survival_values)
        self.calls = []

    async def __call__(self, messages, **options):
        self.calls.append(messages)
        value = self.values.pop(0) if len(self.values) > 1 else self.values[0]
        return {"choices": [{"message": {
            "content": json.dumps({"current_survival": value}),
        }}]}


def test_durability_cycle_appends_reversed_verdict(live_db):
    probe = sqlite3.connect(live_db)
    try:
        before = probe.execute(
            "SELECT verdict_id, verdict, reason, decided_at FROM verdicts "
            "ORDER BY verdict_id LIMIT 1"
        ).fetchone()
    finally:
        probe.close()

    result = durability_cycle(live_db, completion=FakeCompletion("SHUTTERED_OR_CLOSED"))

    assert result["dry_run"] is False
    assert result["status_changes_count"] == 1
    assert result["errors"] == []
    assert result["transitions"][0]["old_status"] == "KEPT"
    assert result["transitions"][0]["new_status"] == "KEPT_THEN_REVERSED"

    conn = sqlite3.connect(live_db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT verdict_id, verdict, reason, decided_at FROM verdicts ORDER BY verdict_id"
    ).fetchall()
    # The original row is untouched; the reversal is a new appended row.
    assert len(rows) == 2
    assert tuple(rows[0]) == before
    assert rows[1]["verdict"] == "KEPT_THEN_REVERSED"
    log_rows = conn.execute(
        "SELECT old_status, new_status FROM change_log WHERE promise_id='P36'"
    ).fetchall()
    assert len(log_rows) == 1
    assert log_rows[0]["old_status"] == "KEPT"
    assert log_rows[0]["new_status"] == "KEPT_THEN_REVERSED"
    verifications = conn.execute(
        "SELECT check_type, model_id FROM verifications WHERE promise_id='P36' "
        "AND check_type='durability_recheck'"
    ).fetchall()
    assert len(verifications) == 1
    assert verifications[0]["model_id"] == "durability_cron"
    conn.close()


def test_durability_cycle_dry_run_writes_nothing(live_db):
    result = durability_cycle(
        live_db, completion=FakeCompletion("SHUTTERED_OR_CLOSED"), dry_run=True
    )

    assert result["dry_run"] is True
    assert result["status_changes_count"] == 1
    assert result["transitions"][0]["new_status"] == "KEPT_THEN_REVERSED"
    assert result["transitions"][0]["dry_run"] is True
    assert result["errors"] == []

    conn = sqlite3.connect(live_db)
    assert conn.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM change_log").fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM verifications WHERE check_type='durability_recheck'"
    ).fetchone()[0] == 0
    conn.close()


def test_durability_cycle_retains_verdict_when_survival_active(live_db):
    result = durability_cycle(live_db, completion=FakeCompletion("ACTIVE_OPERATIONAL"))

    assert result["status_changes_count"] == 0
    assert result["errors"] == []
    conn = sqlite3.connect(live_db)
    assert conn.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM change_log").fetchone()[0] == 0
    conn.close()


def test_durability_cycle_requires_advocate_agreement(live_db):
    result = durability_cycle(
        live_db,
        completion=FakeCompletion("SHUTTERED_OR_CLOSED", "ACTIVE_OPERATIONAL"),
    )

    assert result["status_changes_count"] == 0
    conn = sqlite3.connect(live_db)
    assert conn.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM change_log").fetchone()[0] == 0
    conn.close()


def test_durability_cycle_reports_evaluator_errors(live_db):
    def broken_evaluator(promise_id, current_verdict):
        raise ValueError("lane timeout")

    result = durability_cycle(live_db, evaluator_fn=broken_evaluator)

    assert result["status_changes_count"] == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["promise_id"] == "P36"
    assert "lane timeout" in result["errors"][0]["error"]


def test_durability_cycle_survival_evidence_must_pass_the_bar(live_db):
    # Corrupt the archived source: its hash no longer matches the ledger row,
    # so the evidence bar fails and the cycle retains the verdict.
    path = next((Path(live_db).parent / "sources" / "P36").glob("*.txt"))
    path.write_text("tampered", encoding="utf-8")

    result = durability_cycle(live_db, completion=FakeCompletion("SHUTTERED_OR_CLOSED"))

    assert result["status_changes_count"] == 0
    assert result["errors"] == []


def test_durability_cycle_rejects_unsupported_database(tmp_path):
    database = tmp_path / "not-ours.db"
    sqlite3.connect(database).close()

    with pytest.raises(DurabilityCycleError, match="not a supported SF Promises database"):
        durability_cycle(database)


def test_cli_offline_missing_database_exits_with_clear_error():
    missing = REPO_ROOT / "nonexistent" / "promises_v2.db"
    for extra in ([], ["--dry-run"]):
        result = subprocess.run(
            [sys.executable, "-m", "src.run_live", "--durability-cycle", *extra,
             "--db", str(missing)],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        assert result.returncode == 1
        assert result.stderr.startswith("error:")
        assert "does not exist" in result.stderr
        assert "Traceback" not in result.stderr
        assert result.stdout == ""


def test_cli_rejects_pipeline_options_with_durability_cycle():
    result = subprocess.run(
        [sys.executable, "-m", "src.run_live", "--durability-cycle", "--seed-id", "P36",
         "--db", "unused.db"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 2
    assert "Durability cycle cannot be combined" in result.stderr


def test_cli_dry_run_requires_durability_cycle():
    result = subprocess.run(
        [sys.executable, "-m", "src.run_live", "--dry-run", "--db", "unused.db"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 2
    assert "--dry-run requires --durability-cycle" in result.stderr
