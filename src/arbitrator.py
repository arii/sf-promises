import re
import sqlite3
from datetime import date, datetime, timezone
from typing import Any

from src.checks import (
    check_date,
    check_domain,
    check_evidence_type,
    check_hash,
    check_promise_id,
    check_quote,
    check_speaker,
)

TIER_WEIGHTS = {
    "vote": 4,
    "ordinance": 4,
    "budget_line": 4,
    "contract_milestone": 4,
    "regulator_order": 4,
    "filing": 4,
    "opening": 3,
    "count": 3,
    "news_report": 2,
    "press_release": 1,
    "announcement": 1,
}


def get_tier(evidence_type: str) -> int:
    """Return the tier weight for an evidence type (1-4). Defaults to 1."""
    return TIER_WEIGHTS.get(evidence_type.lower(), 1)


def decide_verdict(
    kept_claims: list[dict[str, Any]],
    broken_claims: list[dict[str, Any]],
    due_date_str: str | None = None,
    promised_date_str: str | None = None,
    numeric_target: bool = False,
    ambiguous_wording: bool = False,
    reading_used: str | None = None,
    interim_progress: bool = False,
) -> tuple[str, str]:
    """
    Arbitrate verdict based on the deterministic rubric in 02-technical-design.md:
    Returns (verdict, reason).
    """
    today = date.today()

    due_date = None
    if due_date_str:
        try:
            due_date = datetime.strptime(due_date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            pass

    promised_date = None
    if promised_date_str:
        try:
            promised_date = datetime.strptime(promised_date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            pass

    kept_tiers = [get_tier(c.get("evidence_type", "")) for c in kept_claims]
    broken_tiers = [get_tier(c.get("evidence_type", "")) for c in broken_claims]

    kept_max = max(kept_tiers) if kept_tiers else 0
    broken_max = max(broken_tiers) if broken_tiers else 0

    # Rule 1: Broken if due date passed with no passing kept evidence
    if due_date and today > due_date and kept_max == 0:
        return "broken", "due date passed with no passing kept evidence"

    # Rule 2: Stalled if 90 days with no action, zero passing claims of any kind, due date not passed
    if (not due_date or today <= due_date) and promised_date:
        days_since = (today - promised_date).days
        if days_since >= 90 and kept_max == 0 and broken_max == 0:
            return "stalled", "90 days with no action, zero passing claims"

    # Rule 3: Numeric target plus deadline: broken side has passing claim >= tier 2 showing actual below target or plan abandonment
    if numeric_target and broken_max >= 2:
        return "broken", "numeric target not met or plan abandoned"

    # Rule 4: Kept if kept_max >= 3 and 0 passing broken claims
    if kept_max >= 3 and broken_max == 0:
        return "kept", "official primary evidence confirms completion with zero contradicting claims"

    # Rule 5: Broken if broken_max >= 2 and kept_max < 3
    if broken_max >= 2 and kept_max < 3:
        return "broken", "contradicting primary evidence outranks affirmative claims"

    # Rule 6: In progress if due date in future and no side settles it
    if due_date and today <= due_date and kept_max < 3 and broken_max < 2:
        return "in_progress", "due date in future and no definitive resolution yet"

    # Rule 6b: In progress if kept evidence proves genuine partial completion
    # of a larger commitment (interim_progress) with no completion and no
    # contradiction. Covers dateless phased rollouts (P10 Mission Rock);
    # never fires when either side settles the verdict above.
    if interim_progress and kept_max < 3 and broken_max < 2:
        return "in_progress", "genuine partial completion, full scope unresolved"

    # Rule 7: Undecided if wording ambiguous
    if ambiguous_wording:
        reason = f"wording ambiguous, reading used: {reading_used}" if reading_used else "wording ambiguous"
        return "undecided", reason

    # Rule 8: Otherwise undecided
    return "undecided", "both sides have competing claims or insufficient evidence to decide"


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_source_text(file_path: str) -> str | None:
    """Read a saved source file; None when unreadable (hash check reports it)."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def arbitrate_claim(
    claim: dict[str, Any],
    promise_id: str,
    speaker: str,
    roll_call: list[str],
    promised_date: str | None,
    due_date: str | None = None,
) -> tuple[bool, list[tuple[str, int, str]]]:
    """Run the ordered checks on one advocate claim.

    Order: domain → hash → quote → speaker → date → evidence type →
    promise_id. Returns (all_passed, [(check_type, passed, reason), ...]).
    Every check runs even after a failure so each gets a verifications row.
    """
    results: list[tuple[str, int, str]] = []
    source_text = load_source_text(claim.get("source_file_path", ""))

    passed, reason = check_domain(claim.get("source_url", ""))
    results.append(("authenticity_domain", int(passed), reason))

    passed, reason = check_hash(
        claim.get("source_file_path", ""), claim.get("source_hash", "")
    )
    results.append(("authenticity_hash", int(passed), reason))

    passed, reason = (
        check_quote(claim.get("quote", ""), source_text)
        if source_text is not None
        else (False, "quote none")
    )
    results.append(("accuracy_quote", int(passed), reason))

    passed, reason = check_speaker(speaker, roll_call)
    if not passed:
        # Fallback: the speaker's distinctive token (longest word >= 4 chars,
        # e.g. "Lurie" for "Mayor Daniel Lurie", "Francisco" for an SF body)
        # must be named in the cited source. A wrong speaker (N02) matches
        # neither the full name nor the token.
        tokens = [w for w in re.split(r"\W+", speaker.lower()) if len(w) >= 4]
        if tokens:
            token = max(tokens, key=len)
            # Whole-word match only: substring would let "jane" match "Janet".
            hit = any(
                re.search(r"\b" + re.escape(token) + r"\b", (m or "").lower())
                for m in roll_call
            )
            if hit:
                passed, reason = True, "pass (distinctive token)"
            else:
                passed, reason = False, "speaker not in roll call"
    results.append(("authenticity_speaker", int(passed), reason))

    passed, reason = check_date(
        claim.get("evidence_date"), promised_date, due_date
    )
    results.append(("accuracy_date", int(passed), reason))

    passed, reason = check_evidence_type(claim.get("evidence_type"))
    results.append(("accuracy_evidence", int(passed), f"evidence_type: {reason}"))

    passed, reason = check_promise_id(claim.get("promise_id"), promise_id)
    results.append(("accuracy_evidence", int(passed), reason))

    all_passed = all(p == 1 for _, p, _ in results)
    return all_passed, results


def write_verdict_transaction(
    conn: sqlite3.Connection,
    pending_row: dict[str, Any],
    verdict: str | None,
    reason: str,
    reading_used: str | None,
    verification_rows: list[tuple[str, int, str]],
    relevance_scores: dict[str, tuple[int, str]] | None = None,
    quarantine_reason: str | None = None,
) -> dict[str, str]:
    """Write the full verdict outcome in ONE transaction.

    Publish path (quarantine_reason None): insert promises row (moved from
    pending, status = verdict) + verdicts row + verifications rows +
    relevance_checks rows + change_log row, delete the pending row.
    Quarantine path: quarantined row + verifications rows +
    relevance_checks rows + change_log row, delete the pending row, no
    promises/verdicts rows. Raises if this promise was already written.

    FK contract (parent decision): the publish path runs with
    PRAGMA foreign_keys=ON (cities/entities are seeded; promises is
    inserted before its children). The quarantine path runs with FK OFF:
    quarantined/relevance_checks/change_log all declare a promises parent
    that a quarantined row must NOT have ("no failed row appears in
    promises"), so ON would reject every quarantine write by design.
    """
    pid = pending_row["promise_id"]
    now = utcnow()

    # PRAGMA foreign_keys is a no-op inside a transaction: set it before BEGIN.
    conn.execute("PRAGMA foreign_keys = ON" if quarantine_reason is None else "PRAGMA foreign_keys = OFF")

    cur = conn.execute("SELECT 1 FROM promises WHERE promise_id = ?", (pid,))
    if cur.fetchone():
        raise ValueError(f"{pid} already in promises")
    cur = conn.execute("SELECT 1 FROM verdicts WHERE promise_id = ?", (pid,))
    if cur.fetchone():
        raise ValueError(f"{pid} already has a verdict")
    cur = conn.execute("SELECT 1 FROM quarantined WHERE promise_id = ?", (pid,))
    if cur.fetchone():
        raise ValueError(f"{pid} already quarantined")

    with conn:
        conn.execute("PRAGMA busy_timeout = 30000")
        if quarantine_reason is None:
            if verdict not in ("kept", "in_progress", "broken", "stalled", "undecided"):
                raise ValueError(f"bad verdict: {verdict!r}")
            conn.execute(
                """INSERT INTO promises (promise_id, city_id, entity_id, promise_text,
                   promised_date, due_date, status, source_file_path, source_hash,
                   source_url, source_type, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pid,
                    pending_row["city_id"],
                    pending_row["entity_id"],
                    pending_row["promise_text"],
                    pending_row["promised_date"],
                    pending_row["due_date"],
                    verdict,
                    pending_row["source_file_path"],
                    pending_row["source_hash"],
                    pending_row["source_url"],
                    pending_row["source_type"],
                    pending_row["created_at"],
                    now,
                ),
            )
            conn.execute(
                """INSERT INTO verdicts (verdict_id, promise_id, verdict, reason,
                   reading_used, decided_at, decided_by)
                   VALUES (?, ?, ?, ?, ?, ?, 'arbitrator')""",
                (f"VER-{pid}", pid, verdict, reason, reading_used, now),
            )
            new_status = verdict
        else:
            conn.execute(
                """INSERT INTO quarantined (quarantine_id, promise_id, reason,
                   quarantined_at, source_file_path, source_hash)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    f"Q-{pid}",
                    pid,
                    quarantine_reason,
                    now,
                    pending_row["source_file_path"],
                    pending_row["source_hash"],
                ),
            )
            new_status = "quarantined"

        for i, (check_type, passed, check_reason) in enumerate(verification_rows):
            conn.execute(
                """INSERT INTO verifications (verification_id, promise_id,
                   evidence_id, check_type, passed, reason, checked_at, checked_by)
                   VALUES (?, ?, NULL, ?, ?, ?, ?, 'arbitrator')""",
                (f"VFY-{pid}-{i:02d}", pid, check_type, passed, check_reason, now),
            )

        if relevance_scores:
            for criterion, (score, score_reason) in relevance_scores.items():
                conn.execute(
                    """INSERT INTO relevance_checks (check_id, promise_id, criterion,
                       score, reason, source_file_path, source_hash, checked_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"REL-{pid}-{criterion}",
                        pid,
                        criterion,
                        score,
                        score_reason,
                        pending_row["source_file_path"],
                        pending_row["source_hash"],
                        now,
                    ),
                )

        conn.execute(
            """INSERT INTO change_log (log_id, promise_id, change_date,
               old_status, new_status, reason, evidence_file_path)
               VALUES (?, ?, ?, 'pending', ?, ?, ?)""",
            (
                f"LOG-{pid}-{new_status}",
                pid,
                now,
                new_status,
                reason if quarantine_reason is None else quarantine_reason,
                pending_row["source_file_path"],
            ),
        )
        conn.execute("DELETE FROM promises_pending WHERE promise_id = ?", (pid,))

    return {"promise_id": pid, "new_status": new_status}


def run_rubric_check(
    kept_passing: list[dict[str, Any]],
    broken_passing: list[dict[str, Any]],
    **rubric_kwargs: Any,
) -> tuple[tuple[str, int, str], str, str]:
    """Decide the verdict and return its verdict_rubric verifications row
    plus (verdict, reason)."""
    verdict, reason = decide_verdict(kept_passing, broken_passing, **rubric_kwargs)
    return ("verdict_rubric", 1, reason), verdict, reason


# ==============================================================================
# v2 Deterministic Verdict Gate (PLAN.md Gate 2)
# ==============================================================================

TODAY = date(2026, 11, 11)


def compute_deterministic_verdict(
    date_deadline: date,
    initial_delivery: str,
    current_survival: str,
    explicitly_abandoned: bool = False,
    as_of: date | None = None,
) -> str:
    """Gate 2: Temporal Arithmetic & Future Deadline Gate.
    Eliminates future deadline marked KEPT or premature BROKEN.
    Computes final lifecycle verdict based on initial delivery and survival.
    """
    cutoff = as_of or TODAY

    # Future deadlines cannot be BROKEN (unless explicitly cancelled) or KEPT (unless already achieved & verified)
    if date_deadline > cutoff:
        if explicitly_abandoned:
            return "BROKEN"
        if initial_delivery == "DELIVERED_ON_TIME" and current_survival == "ACTIVE_OPERATIONAL":
            return "KEPT"
        return "IN_PROGRESS"

    # Past deadlines
    if initial_delivery == "NOT_DELIVERED":
        return "BROKEN"
    if initial_delivery in ("DELIVERED_ON_TIME", "DELIVERED_LATE", "PARTIALLY_DELIVERED"):
        if current_survival in ("SHUTTERED_OR_CLOSED", "REVOKED_OR_HALTED"):
            return "KEPT_THEN_REVERSED"
        if initial_delivery in ("DELIVERED_LATE", "PARTIALLY_DELIVERED"):
            return "DELAYED_OR_PARTIAL"
        return "KEPT"
    return "IN_PROGRESS"

