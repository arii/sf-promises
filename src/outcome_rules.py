"""Outcome rules R1-R7 for the candidate audit, behind SF_PROMISES_OUTCOME_RULES=1.

Off by default. With the flag off nothing in this module changes behavior.

R1  A verified origin with no deadline is not quarantined; it is open-ended.
R2  `promise_horizon_short` is ignored when deadline >= promised date (a one-off
    dated event). A deadline before the promised date still fails.
R3  Future deadline, no contrary evidence: IN_PROGRESS.
R4  Verified delivery sentence, survival unknown: KEPT (on time) or
    DELAYED_OR_PARTIAL (late or partial), noted "current status not checked".
R5  Deadline passed or none, no delivery or contrary evidence: UNDECIDED.
R6  The semantic verifier only has to confirm the fields the verdict uses.
R7  The basis of every published verdict is recorded in a `outcome_basis` row.
"""

import os

from src.lifecycle_rubric import decide_verdict

FLAG = "SF_PROMISES_OUTCOME_RULES"
NOT_CHECKED_NOTE = "current status not checked"
_DELIVERED = ("DELIVERED_ON_TIME", "DELIVERED_LATE", "PARTIALLY_DELIVERED")
_NO_SURVIVAL = ("UNKNOWN", "NOT_YET_OPEN")


def outcome_rules_enabled():
    return os.environ.get(FLAG) == "1"


def origin_date_failures(failures, promised, deadline):
    """Split check_origin_dates output into (remaining failures, screening rules used)."""
    remaining, rules = [], []
    for failure in failures:
        if failure == "deadline_missing":
            rules.append("R1")
        elif (failure == "promise_horizon_short" and deadline is not None
              and promised is not None and deadline >= promised):
            rules.append("R2")
        else:
            remaining.append(failure)
    return remaining, rules


def decide_outcome(deadline, as_of, delivery, survival, facts_verified):
    """Return (verdict, rule, reason) or None when the facts support no verdict.

    `delivery` and `survival` are "UNKNOWN" unless a selected, verified sentence
    supports the state. `deadline` may be None (open-ended). Rule is one of
    STANDARD (the unchanged rubric decided), CONTRARY, R3, R4, R5.
    """
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
