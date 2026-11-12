"""Verdict-lane quarantine writes for the database."""

import json
from datetime import datetime, timezone


def quarantine_candidate(conn, promise_id, canonical_slug, stage, reasons, payload):
    if conn.in_transaction:
        raise ValueError("Quarantine requires a dedicated transaction")
    if not conn.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("Foreign keys must be enabled")
    if (not promise_id or not canonical_slug or not stage
            or not isinstance(reasons, list) or not reasons
            or any(not isinstance(reason, str) or not reason.strip() for reason in reasons)
            or len(set(reasons)) != len(reasons)):
        raise ValueError("Quarantine requires an identity, stage and reasons")
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "INSERT INTO candidates (promise_id, canonical_slug) VALUES (?, ?) "
            "ON CONFLICT(promise_id) DO NOTHING",
            (promise_id, canonical_slug),
        )
        existing_slug = conn.execute(
            "SELECT canonical_slug FROM candidates WHERE promise_id = ?", (promise_id,)
        ).fetchone()[0]
        if existing_slug != canonical_slug:
            raise ValueError("Candidate identity does not match")
        if conn.execute(
            "SELECT 1 FROM promises WHERE promise_id = ?", (promise_id,)
        ).fetchone():
            raise ValueError("Published candidate cannot be quarantined")
        reasons_json = json.dumps(reasons, sort_keys=True)
        payload_json = json.dumps(payload, sort_keys=True)
        if not conn.execute(
            "SELECT 1 FROM quarantined WHERE promise_id = ? AND stage = ? "
            "AND reason_codes_json = ? AND candidate_payload_json = ?",
            (promise_id, stage, reasons_json, payload_json),
        ).fetchone():
            timestamp = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO quarantined (promise_id, stage, reason_codes_json, "
                "candidate_payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (promise_id, stage, reasons_json, payload_json, timestamp),
            )
            conn.executemany(
                "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at) "
                "VALUES (?, ?, 0, ?, ?)",
                [(promise_id, reason, reason, timestamp) for reason in reasons],
            )
        quarantine_id = conn.execute(
            "SELECT quarantine_id FROM quarantined WHERE promise_id = ? AND stage = ? "
            "AND reason_codes_json = ? AND candidate_payload_json = ? ORDER BY quarantine_id DESC LIMIT 1",
            (promise_id, stage, reasons_json, payload_json),
        ).fetchone()[0]
        conn.execute(
            "UPDATE promises_pending SET status = 'quarantined', quarantine_id = ? "
            "WHERE promise_id = ? AND status = 'pending'",
            (quarantine_id, promise_id),
        )
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
