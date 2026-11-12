"""
Tests for Durability Cron, Scheduled Re-checks, and Append-Only Corrections.
"""

import sqlite3
from datetime import date
import pytest

from src.arbitrator import compute_next_check_at, reopen_promise_verdict
from src.durability_cron import find_due_rechecks, run_durability_cycle


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test_durability.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE promises (
            promise_id TEXT PRIMARY KEY,
            entity TEXT,
            promise_text TEXT,
            status TEXT,
            due_date TEXT,
            source_url TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE verdicts (
            verdict_id TEXT PRIMARY KEY,
            promise_id TEXT,
            verdict TEXT,
            reason TEXT,
            reading_used TEXT,
            decided_at TEXT,
            decided_by TEXT
        );
        CREATE TABLE change_log (
            log_id TEXT PRIMARY KEY,
            promise_id TEXT,
            change_date TEXT,
            old_status TEXT,
            new_status TEXT,
            reason TEXT,
            evidence_file_path TEXT
        );
    """)
    yield conn
    conn.close()


def test_compute_next_check_at():
    today = date(2026, 1, 1)
    # Kept: +90 days
    assert compute_next_check_at("kept", today) == date(2026, 4, 1)
    # In-progress: +30 days
    assert compute_next_check_at("in_progress", today) == date(2026, 1, 31)
    # Stalled: +30 days
    assert compute_next_check_at("stalled", today) == date(2026, 1, 31)
    # Undecided: +60 days
    assert compute_next_check_at("undecided", today) == date(2026, 3, 2)


def test_reopen_promise_verdict_append_only(test_db):
    # Insert initial promise & verdict
    test_db.execute("""
        INSERT INTO promises (promise_id, entity, promise_text, status, source_url, created_at, updated_at)
        VALUES ('P36', 'Whole Foods', 'Open grocery store at 8th and Market', 'kept', 'https://sf.gov/wf', '2022-03-10', '2022-03-10')
    """)
    test_db.execute("""
        INSERT INTO verdicts (verdict_id, promise_id, verdict, reason, decided_at, decided_by)
        VALUES ('VER-P36-001', 'P36', 'kept', 'Store opened on March 10, 2022', '2022-03-10', 'arbitrator')
    """)
    test_db.commit()

    # Reopen to broken due to 2023 closure
    res = reopen_promise_verdict(
        test_db,
        promise_id="P36",
        new_verdict="broken",
        reason="Whole Foods temporarily closed in April 2023 due to safety conditions; never reopened.",
        reviewer="durability_audit"
    )

    assert res["old_status"] == "kept"
    assert res["new_status"] == "broken"

    # Verify promises table status updated
    status = test_db.execute("SELECT status FROM promises WHERE promise_id='P36'").fetchone()[0]
    assert status == "broken"

    # Verify append-only verdicts table has 2 rows (historical preserved)
    verdict_rows = test_db.execute("SELECT verdict, reason FROM verdicts WHERE promise_id='P36' ORDER BY decided_at ASC").fetchall()
    assert len(verdict_rows) == 2
    assert verdict_rows[0][0] == "kept"
    assert verdict_rows[1][0] == "broken"

    # Verify change_log table recorded the transition
    log_rows = test_db.execute("SELECT old_status, new_status, reason FROM change_log WHERE promise_id='P36'").fetchall()
    assert len(log_rows) == 1
    assert log_rows[0][0] == "kept"
    assert log_rows[0][1] == "broken"


def test_find_due_rechecks_and_durability_cycle(test_db):
    # P01 kept on 2025-01-01 (+90 days -> 2025-04-01)
    test_db.execute("""
        INSERT INTO promises (promise_id, entity, promise_text, status, source_url, created_at, updated_at)
        VALUES ('P01', 'SFMTA', 'Open subway line', 'kept', 'https://sf.gov', '2025-01-01', '2025-01-01')
    """)
    test_db.execute("""
        INSERT INTO verdicts (verdict_id, promise_id, verdict, reason, decided_at, decided_by)
        VALUES ('V-01', 'P01', 'kept', 'Opened', '2025-01-01T00:00:00Z', 'arb')
    """)

    # P02 in_progress on 2025-05-01 (+30 days -> 2025-05-31)
    test_db.execute("""
        INSERT INTO promises (promise_id, entity, promise_text, status, source_url, created_at, updated_at)
        VALUES ('P02', 'City', 'Hire 50 staff', 'in_progress', 'https://sf.gov', '2025-05-01', '2025-05-01')
    """)
    test_db.execute("""
        INSERT INTO verdicts (verdict_id, promise_id, verdict, reason, decided_at, decided_by)
        VALUES ('V-02', 'P02', 'in_progress', 'Hiring', '2025-05-01T00:00:00Z', 'arb')
    """)
    test_db.commit()

    # As of 2025-04-15: P01 is due (+90d was 2025-04-01), but P02 is not yet due (+30d is 2025-05-31)
    due = find_due_rechecks(test_db, as_of=date(2025, 4, 15))
    assert len(due) == 1
    assert due[0]["promise_id"] == "P01"
    assert due[0]["days_overdue_for_recheck"] == 14

    # Run durability cycle with evaluator that finds P01 suffered a subsequent closure/breakage
    def mock_evaluator(pid, current_v):
        if pid == "P01":
            return "broken", "Subsequent inspection found line suspended due to track defect."
        return current_v, "Survival confirmed"

    cycle_res = run_durability_cycle(test_db, as_of=date(2025, 4, 15), evaluator_fn=mock_evaluator)
    assert cycle_res["total_due_checked"] == 1
    assert cycle_res["status_changes_count"] == 1
    assert cycle_res["transitions"][0]["new_status"] == "broken"

    # Verify P01 is now broken in database
    p01_status = test_db.execute("SELECT status FROM promises WHERE promise_id='P01'").fetchone()[0]
    assert p01_status == "broken"
