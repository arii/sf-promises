"""Outcome rules R1-R7 for the candidate audit, behind SF_PROMISES_OUTCOME_RULES=1.

Off by default. With the flag off nothing in this module changes behavior.

R1  A verified origin with no deadline is not quarantined; it is open-ended.
R2  `promise_horizon_short` is ignored only when the origin quote itself states the
    deadline (an explicit date, or a weekday/relative day term resolved against
    the publication date, equal to the deadline) and deadline >= promised date.
    Otherwise the short-horizon failure stays.
R3  Future deadline, no contrary evidence: IN_PROGRESS.
R4  Verified delivery sentence, survival unknown: KEPT (on time) or
    DELAYED_OR_PARTIAL (late or partial), noted "current status not checked".
R5  Deadline passed or none, no delivery or contrary evidence: UNDECIDED.
    BROKEN needs the contrary source to be published on or after the deadline.
R6  The semantic verifier only has to confirm the fields the verdict uses.
R7  The basis of every published verdict is recorded in a `outcome_basis` row.
"""

import json
import os
import re

from src.date_resolution import quote_deadline_dates
from src.lifecycle_rubric import decide_verdict

FLAG = "SF_PROMISES_OUTCOME_RULES"
NOT_CHECKED_NOTE = "current status not checked"
_DELIVERED = ("DELIVERED_ON_TIME", "DELIVERED_LATE", "PARTIALLY_DELIVERED")
_NO_SURVIVAL = ("UNKNOWN", "NOT_YET_OPEN")


def outcome_rules_enabled():
    return os.environ.get(FLAG) == "1"


class OutcomeRulesSchemaError(ValueError):
    """The database schema cannot store what the outcome rules publish."""


def check_schema_supports_outcome_rules(conn):
    """Fail fast unless the schema allows UNDECIDED verdicts and a NULL deadline.

    Inspects the stored CREATE TABLE text. A database created before the
    outcome rules rejects those rows at the final publish insert, after
    preliminary evidence was already written.
    """
    sql = {name: text or "" for name, text in conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' "
        "AND name IN ('promises', 'verdicts')")}
    problems = []
    column = re.search(r"\bdate_deadline\b([^,\n]*)", sql.get("promises", ""), re.I)
    if column is None or re.search(r"\bNOT\s+NULL\b", column.group(1), re.I):
        problems.append("promises.date_deadline must allow NULL")
    if "'UNDECIDED'" not in sql.get("verdicts", ""):
        problems.append("verdicts.verdict must allow 'UNDECIDED'")
    if problems:
        raise OutcomeRulesSchemaError(
            f"{FLAG}=1 needs a database whose schema allows open-ended and undecided "
            f"records, but this one does not ({'; '.join(problems)}). Create a new "
            "database with src.database or unset the flag.")


def require_flag_off_strictness(deadline, verdict):
    """Flag-off publish guard: no NULL deadline and no UNDECIDED verdict.

    The schema stays permissive so flagged runs can publish; with the flag off
    this guard restores the old NOT NULL / CHECK behavior in code.
    """
    if outcome_rules_enabled():
        return
    if deadline is None:
        raise ValueError(f"A NULL deadline needs {FLAG}=1")
    if verdict == "UNDECIDED":
        raise ValueError(f"An UNDECIDED verdict needs {FLAG}=1")


def recorded_outcome_rules(rows):
    """Rules named by the newest `outcome_basis` verification row, or None.

    `rows` are verification dicts for one promise, oldest first. Raises
    ValueError when the row is not valid JSON with a rules list.
    """
    if not rows:
        return None
    detail = json.loads(rows[-1]["reason"])
    rules = detail["rules"]
    if not isinstance(rules, list) or not all(isinstance(r, str) for r in rules):
        raise ValueError("outcome_basis rules must be a list")
    return set(rules)


def origin_date_failures(failures, promised, deadline, *, quote=None, published=None):
    """Split check_origin_dates output into (remaining failures, screening rules used).

    R2 needs the origin `quote` and its `published` date: the short-horizon
    failure is waived only when the quote itself states the deadline.
    """
    remaining, rules = [], []
    for failure in failures:
        if failure == "deadline_missing":
            rules.append("R1")
        elif (failure == "promise_horizon_short" and deadline is not None
              and promised is not None and deadline >= promised
              and deadline in quote_deadline_dates(quote, published)):
            rules.append("R2")
        else:
            remaining.append(failure)
    return remaining, rules


def recorded_origin_date_failures(failures, promised, deadline, *, quote, published, recorded):
    """Like origin_date_failures, but only for rules the database recorded.

    `recorded` is the set from recorded_outcome_rules, or None for a database
    with no outcome basis (flag-off), where every failure stands.
    """
    if not recorded:
        return list(failures)
    remaining, used = origin_date_failures(
        failures, promised, deadline, quote=quote, published=published)
    return remaining + [f"{rule}_not_recorded" for rule in used if rule not in recorded]


STALE_CONTRARY_NOTE = "the contrary source was published before the deadline"


def decide_outcome(deadline, as_of, delivery, survival, facts_verified, *,
                   delivery_published=None):
    """Return (verdict, rule, reason) or None when the facts support no verdict.

    `delivery` and `survival` are "UNKNOWN" unless a selected, verified sentence
    supports the state. `deadline` may be None (open-ended). Rule is one of
    STANDARD (the unchanged rubric decided), CONTRARY, R3, R4, R5.

    BROKEN needs `delivery_published`, the publication date of the selected
    NOT_DELIVERED source, to be on or after the deadline. A missing date or an
    earlier one cannot show the deadline was missed, so the contrary sentence
    is set aside and the existing rules decide (IN_PROGRESS or UNDECIDED).
    """
    result = _decide(deadline, as_of, delivery, survival, facts_verified)
    if result is None or result[0] != "BROKEN":
        return result
    if (deadline is not None and delivery_published is not None
            and delivery_published >= deadline):
        return result
    if delivery != "NOT_DELIVERED":
        return None
    fallback = _decide(deadline, as_of, "UNKNOWN", "UNKNOWN", True)
    if fallback is None:
        return None
    verdict, rule, reason = fallback
    return verdict, rule, f"{reason}; {STALE_CONTRARY_NOTE}"


def _decide(deadline, as_of, delivery, survival, facts_verified):
    if facts_verified is not True:
        return None
    future = deadline is not None and deadline > as_of
    standard = decide_verdict(deadline, as_of, delivery, survival, True)
    if standard is not None:
        return standard, "STANDARD", None
    if delivery == "NOT_DELIVERED" or survival == "REVOKED_OR_HALTED":
        # Contrary evidence follows the existing rules; only a passed deadline
        # with a selected NOT_DELIVERED sentence needs no survival sentence.
        if (delivery == "NOT_DELIVERED" and deadline is not None and not future
                and survival in _NO_SURVIVAL):
            return "BROKEN", "CONTRARY", "deadline passed and the outcome source says not delivered"
        return None
    if delivery in _DELIVERED:
        if survival != "UNKNOWN":
            return None
        if delivery == "PARTIALLY_DELIVERED" and future:
            return "IN_PROGRESS", "R3", "deadline in the future"
        if delivery == "DELIVERED_ON_TIME":
            return "KEPT", "R4", NOT_CHECKED_NOTE
        if delivery == "DELIVERED_LATE" and deadline is not None and not future:
            return "DELAYED_OR_PARTIAL", "R4", NOT_CHECKED_NOTE
        if delivery == "PARTIALLY_DELIVERED":
            return "DELAYED_OR_PARTIAL", "R4", NOT_CHECKED_NOTE
        return None
    if delivery in ("UNKNOWN", "PENDING_FUTURE_DEADLINE") and survival in _NO_SURVIVAL:
        if future:
            return "IN_PROGRESS", "R3", "deadline in the future"
        if delivery == "UNKNOWN":
            return "UNDECIDED", "R5", "no outcome evidence found"
    return None


def relied_phases(verdict, delivery, survival):
    """Evidence phases the verdict relies on; IN_PROGRESS and UNDECIDED use none."""
    if verdict in ("IN_PROGRESS", "UNDECIDED"):
        return ()
    phases = []
    if delivery != "UNKNOWN":
        phases.append("DELIVERY")
    if survival not in ("UNKNOWN", "NOT_YET_OPEN"):
        phases.append("SURVIVAL")
    return tuple(phases)
