"""Temporal screening for candidates; provenance is checked separately."""

import calendar
from datetime import date
import re

from src.checks import normalize_whitespace
from src.sources import is_verbatim_quote


def deadline_from_quote(quote, *, published=None, promised=None):
    """Propose a conservative deadline only from an explicit commitment."""
    if not isinstance(quote, str) or not re.search(
        r"\b(?:will|shall|goal|plan|pledge|promise|commit|aim|target)\w*\b",
        quote, re.IGNORECASE,
    ):
        return None
    months = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
    month_pattern = "|".join(months)
    candidates = []
    for match in re.finditer(
        rf"\b(?:by|in|end of)\s+(?:the\s+end\s+of\s+)?({month_pattern})\s+(\d{{4}})\b",
        quote, re.IGNORECASE,
    ):
        month, year = months[match.group(1).lower()], int(match.group(2))
        if year:
            candidates.append(date(year, month, calendar.monthrange(year, month)[1]))
    for match in re.finditer(
        r"\b(?:by|in|end of)\s+(?:(?:the\s+)?end\s+of\s+)?(\d{4})\b",
        quote, re.IGNORECASE,
    ):
        year = int(match.group(1))
        if year:
            candidates.append(date(year, 12, 31))
    if (published is not None and type(published) is date
            and re.search(r"\bby\s+(?:the\s+)?end\s+of\s+(?:(?:the|this)\s+)?year\b",
                          quote, re.IGNORECASE)):
        candidates.append(date(published.year, 12, 31))
    duration = re.search(
        r"\bwithin\s+(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)"
        r"\s+years?\b", quote, re.IGNORECASE,
    )
    if duration and re.search(r"\b(?:19|20)\d{2}\b", quote):
        return None
    if duration and type(promised) is date:
        names = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        value = duration.group(1).lower()
        years = int(value) if value.isdigit() else names[value]
        if 1 <= years <= 30 and promised.year + years <= 9999:
            candidates.append(date(promised.year + years, 12, 31))
    return candidates[0] if candidates and len(set(candidates)) == 1 else None


def screen_forward_looking(quote):
    """Reject retrospective cues; passing does not prove a future commitment."""
    if not isinstance(quote, str) or not quote.strip():
        return ["quote_missing"]
    text = normalize_whitespace(quote)
    if any(phrase in text for phrase in (
        "didn't last long", "failed to", "had promised", "pledged in 20",
        "was originally scheduled", "sold out all", "opened with",
    )):
        return ["retrospective_wording"]
    return []


def check_origin_dates(
    promised: date | None,
    published: date | None,
    deadline: date | None,
    *,
    historical_official: bool = False,
    historical_origin_confirmed: bool = False,
    quote: str = "",
    source_text: str = "",
) -> list[str]:
    """Return failed temporal checks, never inferring missing dates."""
    errors = []
    if promised is None:
        errors.append("promise_date_missing")
    if deadline is None:
        errors.append("deadline_missing")
    if promised is None:
        return errors

    if deadline is not None and (deadline - promised).days < 60:
        errors.append("promise_horizon_short")

    if published is None:
        errors.append("origin_date_missing")
    elif (promised - published).days > 14:
        errors.append("origin_predates_promise")
    elif (published - promised).days > 30:
        if not historical_official:
            errors.append("origin_publication_late")
        elif (
            not historical_origin_confirmed
            or promised.isoformat() not in source_text
            or not is_verbatim_quote(quote, source_text)
        ):
            errors.append("historical_origin_unverified")
    return errors
