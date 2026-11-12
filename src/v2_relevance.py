"""Persist deterministic relevance scores for independently verified inputs."""

import json
from datetime import datetime, timezone

from src.relevance import score_relevance


_SIGNALS = frozenset({
    "has_verbatim", "has_speaker", "has_date",
    "is_proposal_or_aspiration_or_restated_vote", "has_number", "has_address",
    "has_vote_filing_opening_count_with_id", "names_sf_or_sf_address_agency_ordinance",
    "bay_area_with_sf_link", "has_named_entity",
})


def evaluate_relevance(promise_text, signals):
    if (not isinstance(promise_text, str) or not promise_text.strip()
            or not isinstance(signals, dict) or not set(signals) <= _SIGNALS
            or any(type(value) is not bool for value in signals.values())):
        raise ValueError("Invalid relevance signals")
    return score_relevance(promise_text, **signals)


def record_relevance(conn, *, assessment_id, promise_id, promise_text, signals, evaluated_at):
    """Score verified signals, retaining input and a stable retry identity."""
    if conn.in_transaction or not conn.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("A dedicated connection with foreign keys enabled is required")
    if (not isinstance(assessment_id, str) or not assessment_id.strip()
            or not isinstance(promise_id, str) or not promise_id.strip()
            or not isinstance(evaluated_at, datetime) or evaluated_at.utcoffset() is None):
        raise ValueError("Invalid relevance assessment input")
    scores = evaluate_relevance(promise_text, signals)
    payload = json.dumps({"promise_text": promise_text, "signals": signals}, sort_keys=True)
    timestamp = evaluated_at.astimezone(timezone.utc).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "INSERT INTO relevance_assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(assessment_id) DO NOTHING",
            (assessment_id, promise_id, payload, scores["real_promise"], scores["measurable"],
             scores["sf_relevant"], scores["interesting"], scores["total"],
             int(scores["publish"]), timestamp),
        )
        previous = conn.execute(
            "SELECT promise_id, input_json, evaluated_at FROM relevance_assessments "
            "WHERE assessment_id = ?", (assessment_id,),
        ).fetchone()
        if tuple(previous) != (promise_id, payload, timestamp):
            raise ValueError("Assessment ID reused with different input")
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    return scores
