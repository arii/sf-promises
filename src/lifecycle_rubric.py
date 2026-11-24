"""Deterministic lifecycle rubric for independently verified facts."""

from datetime import date


def decide_verdict(
    deadline: date | None,
    as_of: date,
    delivery: str,
    survival: str,
    facts_verified: bool,
    *,
    explicitly_abandoned: bool = False,
) -> str | None:
    """Return no verdict when facts are unsupported or contradictory.

    The caller must independently verify every supplied fact and its evidence.
    `deadline` is None for an open-ended commitment: it is never in the future,
    and without a deadline nothing is late or provably broken by time alone.
    """
    if facts_verified is not True:
        return None

    future = deadline is not None and deadline > as_of
    no_deadline = deadline is None
    if explicitly_abandoned:
        if survival != "REVOKED_OR_HALTED":
            return None
        if delivery == "NOT_DELIVERED" or (delivery == "PENDING_FUTURE_DEADLINE" and future):
            return "BROKEN"
        if delivery == "DELIVERED_ON_TIME" or (
                delivery == "DELIVERED_LATE" and not future and not no_deadline):
            return "KEPT_THEN_REVERSED"
        return None
    if delivery == "PENDING_FUTURE_DEADLINE":
        return "IN_PROGRESS" if future and survival == "NOT_YET_OPEN" else None
    if delivery == "NOT_DELIVERED":
        return "BROKEN" if (
            not future and not no_deadline and survival == "NOT_YET_OPEN") else None
    if delivery not in ("DELIVERED_ON_TIME", "DELIVERED_LATE", "PARTIALLY_DELIVERED"):
        return None
    if delivery == "DELIVERED_LATE" and (future or no_deadline):
        return None
    if survival in ("SHUTTERED_OR_CLOSED", "REVOKED_OR_HALTED"):
        return "KEPT_THEN_REVERSED" if delivery != "PARTIALLY_DELIVERED" else None
    if survival != "ACTIVE_OPERATIONAL":
        return None
    if delivery != "DELIVERED_ON_TIME":
        return "DELAYED_OR_PARTIAL"
    return "KEPT"
