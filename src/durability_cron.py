"""
SF Promises Durability Engine & Scheduled Re-check Runner.

Implements automated survival verification for kept promises (preventing Whole Foods
closure regressions) and periodic progress checks for in-progress commitments
using compute_next_check_at and append-only reopen_promise_verdict transactions.
"""

import json
import sqlite3
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from src.arbitrator import compute_next_check_at, reopen_promise_verdict

# Append-only transition log shared by reopen_promise_verdict callers. The live
# schema (src/schema.sql) predates it, so the durability cycle adds it on first
# use instead of bumping SCHEMA_VERSION for an additive table.
CHANGE_LOG_DDL = """
    CREATE TABLE IF NOT EXISTS change_log (
        log_id TEXT PRIMARY KEY,
        promise_id TEXT NOT NULL,
        change_date TEXT NOT NULL,
        old_status TEXT NOT NULL,
        new_status TEXT NOT NULL,
        reason TEXT NOT NULL,
        evidence_file_path TEXT
    )
"""


def ensure_change_log(conn: sqlite3.Connection) -> None:
    """Create the append-only change_log table when it is missing."""
    conn.execute(CHANGE_LOG_DDL)
    conn.commit()


def find_due_rechecks(
    conn: sqlite3.Connection,
    as_of: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Find all promises whose next scheduled verification date is <= as_of.
    """
    check_date = as_of or datetime.now(timezone.utc).date()
    cur = conn.cursor()
    # Query all published promises with their latest verdict. promises.status
    # and promises.due_date exist only on the legacy durability schema; the
    # live schema keeps the current status as the latest verdicts row.
    promise_columns = {row[1] for row in cur.execute("PRAGMA table_info(promises)")}
    status_column = "p.status" if "status" in promise_columns else "NULL"
    due_column = "p.due_date" if "due_date" in promise_columns else "NULL"
    rows = cur.execute(f"""
        SELECT p.promise_id, {status_column}, p.promise_text, {due_column},
               v.verdict, v.decided_at, v.reason
        FROM promises p
        LEFT JOIN (
            SELECT promise_id, verdict, decided_at, reason,
                   ROW_NUMBER() OVER (PARTITION BY promise_id ORDER BY decided_at DESC) as rn
            FROM verdicts
        ) v ON p.promise_id = v.promise_id AND v.rn = 1
    """).fetchall()

    due = []
    for r in rows:
        pid, status, text, due_date_val, verd, decided_at, reason = r
        verd = verd or status
        decided_date = None
        if decided_at:
            try:
                decided_date = datetime.fromisoformat(decided_at.split("T")[0]).date()
            except Exception:
                pass

        # The live schema stores uppercase verdicts ('KEPT'); the scheduling
        # windows are keyed on the lowercase vocabulary.
        verdict_key = verd.lower() if isinstance(verd, str) else verd
        next_check = compute_next_check_at(verdict_key, decided_date)
        if next_check and next_check <= check_date:
            due.append({
                "promise_id": pid,
                "status": status,
                "verdict": verd,
                "decided_at": decided_at,
                "next_check_at": next_check.isoformat(),
                "promise_text": text,
                "days_overdue_for_recheck": (check_date - next_check).days
            })

    return due


def _record_recheck_verification(conn, promise_id, record):
    """Record provenance for one transition in the live verifications table.

    Skipped on legacy fixtures without verifications/candidates; the durability
    reviewer identity travels in model_id like every other verification row.
    """
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    if "verifications" not in tables or "candidates" not in tables:
        return
    if not conn.execute("SELECT 1 FROM candidates WHERE promise_id = ?", (promise_id,)).fetchone():
        return
    conn.execute(
        "INSERT INTO verifications (promise_id, check_type, passed, reason, "
        "checked_at, model_id) VALUES (?, 'durability_recheck', 1, ?, ?, 'durability_cron')",
        (promise_id, json.dumps(record, sort_keys=True),
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def run_durability_cycle(
    conn: sqlite3.Connection,
    as_of: Optional[date] = None,
    evaluator_fn = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Execute durability re-checks for all overdue commitments.
    Appends transitions to change_log and verdicts without overwriting history.
    With dry_run the proposed transitions are reported but nothing is written.
    Per-promise evaluator failures are captured in `errors`; the cycle continues.
    """
    check_date = as_of or datetime.now(timezone.utc).date()
    due_items = find_due_rechecks(conn, check_date)
    transitions = []
    errors = []

    for item in due_items:
        pid = item["promise_id"]
        current_v = item["verdict"]

        new_v = current_v
        new_reason = "Durability check: Survival confirmed across official registries."
        if evaluator_fn:
            try:
                new_v, new_reason = evaluator_fn(pid, current_v)
            except Exception as exc:
                errors.append({"promise_id": pid,
                               "error": f"{type(exc).__name__}: {exc}"})
                continue

        if new_v != current_v:
            if dry_run:
                transitions.append({
                    "promise_id": pid,
                    "old_status": current_v,
                    "new_status": new_v,
                    "reason": new_reason,
                    "dry_run": True,
                })
            else:
                # Reopen promise verdict using append-only transaction
                record = reopen_promise_verdict(
                    conn,
                    promise_id=pid,
                    new_verdict=new_v,
                    reason=new_reason,
                    reviewer="durability_cron"
                )
                _record_recheck_verification(conn, pid, record)
                transitions.append(record)

    return {
        "cycle_date": check_date.isoformat(),
        "dry_run": dry_run,
        "total_due_checked": len(due_items),
        "status_changes_count": len(transitions),
        "transitions": transitions,
        "errors": errors
    }
