"""
SF Promises Durability Engine & Scheduled Re-check Runner.

Implements automated survival verification for kept promises (preventing Whole Foods
closure regressions) and periodic progress checks for in-progress commitments
using compute_next_check_at and append-only reopen_promise_verdict transactions.
"""

import sqlite3
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from src.arbitrator import compute_next_check_at, reopen_promise_verdict


def find_due_rechecks(
    conn: sqlite3.Connection,
    as_of: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Find all promises whose next scheduled verification date is <= as_of.
    """
    check_date = as_of or datetime.now(timezone.utc).date()
    cur = conn.cursor()
    # Query all published promises with their latest verdict
    rows = cur.execute("""
        SELECT p.promise_id, p.status, p.promise_text, p.due_date,
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

        next_check = compute_next_check_at(verd, decided_date)
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


def run_durability_cycle(
    conn: sqlite3.Connection,
    as_of: Optional[date] = None,
    evaluator_fn = None
) -> Dict[str, Any]:
    """
    Execute durability re-checks for all overdue commitments.
    Appends transitions to change_log and verdicts without overwriting history.
    """
    check_date = as_of or datetime.now(timezone.utc).date()
    due_items = find_due_rechecks(conn, check_date)
    transitions = []

    for item in due_items:
        pid = item["promise_id"]
        current_v = item["verdict"]

        new_v = current_v
        new_reason = "Durability check: Survival confirmed across official registries."
        if evaluator_fn:
            new_v, new_reason = evaluator_fn(pid, current_v)

        if new_v != current_v:
            # Reopen promise verdict using append-only transaction
            record = reopen_promise_verdict(
                conn,
                promise_id=pid,
                new_verdict=new_v,
                reason=new_reason,
                reviewer="durability_cron"
            )
            transitions.append(record)

    return {
        "cycle_date": check_date.isoformat(),
        "total_due_checked": len(due_items),
        "status_changes_count": len(transitions),
        "transitions": transitions
    }
