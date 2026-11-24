"""Deterministic commitment-date resolution, behind SF_PROMISES_DATE_RESOLUTION=1.

Rule, in priority order, never later than the source publication date:

1. "stated": one explicit full date in the quote segment, or within the two
   segments before it, or in a dateline in the first five segments.
2. "relative": a relative day term (today, yesterday, "on Tuesday", "last
   Tuesday") in the quote segment or within the two segments before it.
3. "publication": nothing better; the publication date is the day the
   commitment was reported, and an upper bound for when it was made.

Vague phrases ("last year", "recently", "earlier this month", "this week")
are not resolved to a day. They fall through to "publication".
Dates are plain `datetime.date` values, so no time zone is involved.
"""

import os
import re
from dataclasses import dataclass
from datetime import date, timedelta

FLAG = "SF_PROMISES_DATE_RESOLUTION"
BASES = ("stated", "relative", "publication")
_NEAR = 2
_DATELINE_SEGMENTS = 5

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|"
          r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
_DATE_PATTERNS = (
    (re.compile(rf"\b({_MONTH})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b", re.I), "mdy"),
    (re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({_MONTH})\.?,?\s+(\d{{4}})\b", re.I), "dmy"),
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), "iso"),
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"), "slash"),
)
# A date right after these words is a target, not the day the promise was made.
_DEADLINE_PREFIX = re.compile(
    r"\b(?:by|before|until|till|through|thru|than|prior to|due)\s+"
    r"(?:(?:the\s+)?end\s+of\s+)?$", re.I,
)
_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_WEEKDAY = r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
# A weekday after these words points forward or is ambiguous; leave it unresolved.
_FORWARD_PREFIX = re.compile(
    r"\b(?:next|this|by|before|until|till|through|thru|every|each|following|"
    r"coming|upcoming|than)\s+$", re.I,
)
_LAST_WEEKDAY = re.compile(rf"\blast\s+{_WEEKDAY}\b", re.I)
_BARE_WEEKDAY = re.compile(rf"\b{_WEEKDAY}\b", re.I)
_TODAY = re.compile(r"\b(?:today|tonight|this\s+(?:morning|afternoon|evening))\b", re.I)
_YESTERDAY = re.compile(r"\byesterday\b", re.I)


@dataclass(frozen=True)
class DateResolution:
    date: date
    basis: str
    phrase: str | None = None

    @property
    def derived(self):
        return self.basis != "stated"

    def describe(self, published):
        """Plain-language label for prompts and exports."""
        if self.basis == "stated":
            return "stated in the source"
        if self.basis == "relative":
            return (f"derived: '{self.phrase}' resolved against publication date "
                    f"{published.isoformat()}")
        return "derived: publication date of the source"


def date_resolution_enabled():
    return os.environ.get(FLAG) == "1"


def _is_date(value):
    return type(value) is date


def _dates_in(text, published):
    """Yield (start, date) for explicit full dates that are not deadlines."""
    found = []
    for pattern, kind in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            try:
                if kind == "mdy":
                    month, day, year = _MONTHS[match.group(1)[:3].lower()], int(match.group(2)), int(match.group(3))
                elif kind == "dmy":
                    day, month, year = int(match.group(1)), _MONTHS[match.group(2)[:3].lower()], int(match.group(3))
                elif kind == "iso":
                    year, month, day = (int(part) for part in match.groups())
                else:
                    month, day, year = (int(part) for part in match.groups())
                value = date(year, month, day)
            except ValueError:
                continue
            if value > published or _DEADLINE_PREFIX.search(text[:match.start()]):
                continue
            found.append((match.start(), value, match.group(0)))
    return found


def _join(segments, lo, hi):
    """Join segments[lo:hi]; return text and the start offset of each segment."""
    starts, parts, size = [], [], 0
    for segment in segments[lo:hi]:
        starts.append(size)
        parts.append(segment)
        size += len(segment) + 1
    return " ".join(parts), starts


def _segment_of(offset, starts):
    index = 0
    for position, start in enumerate(starts):
        if start <= offset:
            index = position
    return index


def _stated(segments, quote_index, published):
    if quote_index is not None:
        lo = max(0, quote_index - _NEAR)
        text, starts = _join(segments, lo, quote_index + 1)
        by_distance = {}
        for start, value, phrase in _dates_in(text, published):
            distance = quote_index - (lo + _segment_of(start, starts))
            by_distance.setdefault(distance, {})[value] = phrase
        for distance in sorted(by_distance):
            if len(by_distance[distance]) != 1:
                break  # two different dates at the same distance: ambiguous
            ((value, phrase),) = by_distance[distance].items()
            return DateResolution(value, "stated", phrase)
    text, starts = _join(segments, 0, _DATELINE_SEGMENTS)
    top = {}
    for start, value, phrase in _dates_in(text, published):
        top[value] = phrase
    if len(top) == 1:
        ((value, phrase),) = top.items()
        return DateResolution(value, "stated", phrase)
    return None


def _weekday_on_or_before(published, weekday, strict):
    delta = (published.weekday() - weekday) % 7
    if strict and delta == 0:
        delta = 7
    return published - timedelta(days=delta)


def _relative_in(text, published):
    """Return {date: phrase} for relative day terms in one piece of text."""
    found = {}
    for match in _TODAY.finditer(text):
        found[published] = match.group(0)
    for match in _YESTERDAY.finditer(text):
        found[published - timedelta(days=1)] = match.group(0)
    last_spans = []
    for match in _LAST_WEEKDAY.finditer(text):
        weekday = _WEEKDAYS.index(match.group(1).lower())
        found[_weekday_on_or_before(published, weekday, strict=True)] = match.group(0)
        last_spans.append(match.span())
    for match in _BARE_WEEKDAY.finditer(text):
        if any(lo <= match.start() < hi for lo, hi in last_spans):
            continue
        if _FORWARD_PREFIX.search(text[:match.start()]):
            continue
        weekday = _WEEKDAYS.index(match.group(1).lower())
        phrase = match.group(0)
        prefix = text[:match.start()]
        if re.search(r"\bon\s+$", prefix, re.I):
            phrase = f"on {phrase}"
        found[_weekday_on_or_before(published, weekday, strict=False)] = phrase
    return found


def _relative(segments, quote_index, published):
    if quote_index is None:
        return None
    for distance in range(_NEAR + 1):
        index = quote_index - distance
        if index < 0:
            break
        found = _relative_in(segments[index], published)
        if len(found) == 1:
            ((value, phrase),) = found.items()
            return DateResolution(value, "relative", phrase)
        if len(found) > 1:
            return None  # two different relative dates: ambiguous
    return None


def resolve_promise_date_detail(segments, quote_index, published):
    """Return a DateResolution, or None when published is missing or invalid."""
    if not _is_date(published):
        return None
    if not isinstance(segments, (list, tuple)) or not all(isinstance(s, str) for s in segments):
        segments = []
    if not (quote_index is None or (type(quote_index) is int and 0 <= quote_index < len(segments))):
        quote_index = None
    result = (_stated(segments, quote_index, published)
              or _relative(segments, quote_index, published)
              or DateResolution(published, "publication"))
    if result.date > published:  # defensive: never after publication
        return None
    return result


def resolve_promise_date(segments, quote_index, published):
    """Return (date, basis), or (None, None) when published is missing or invalid."""
    result = resolve_promise_date_detail(segments, quote_index, published)
    return (result.date, result.basis) if result else (None, None)


# --- deadline dates stated in a quote (used by outcome rule R2) ---------------

_MONTH_DAY = re.compile(rf"\b({_MONTH})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\b(?!\s*,?\s*\d{{4}})", re.I)
_TOMORROW = re.compile(r"\btomorrow\b", re.I)
_NEXT_WEEKDAY = re.compile(rf"\bnext\s+{_WEEKDAY}\b", re.I)


def _weekday_on_or_after(published, weekday, strict):
    delta = (weekday - published.weekday()) % 7
    if strict and delta == 0:
        delta = 7
    return published + timedelta(days=delta)


def quote_deadline_dates(quote, published):
    """Return the set of dates a quote itself states as a point in time.

    Covers explicit full dates (any position, including after "by"), a month and
    day without a year (the next such day on or after `published`), today /
    tonight / tomorrow, and weekday names resolved forward from `published`
    ("Friday", "this Friday", "on Friday" = first such day on or after
    `published`; "next Friday" = first such day after it). Nothing is inferred
    when `published` is not a date.
    """
    if not isinstance(quote, str) or not _is_date(published):
        return set()
    found = set()
    for pattern, kind in _DATE_PATTERNS:
        for match in pattern.finditer(quote):
            try:
                if kind == "mdy":
                    value = date(int(match.group(3)), _MONTHS[match.group(1)[:3].lower()],
                                 int(match.group(2)))
                elif kind == "dmy":
                    value = date(int(match.group(3)), _MONTHS[match.group(2)[:3].lower()],
                                 int(match.group(1)))
                elif kind == "iso":
                    value = date(*(int(part) for part in match.groups()))
                else:
                    month, day, year = (int(part) for part in match.groups())
                    value = date(year, month, day)
            except ValueError:
                continue
            found.add(value)
    for match in _MONTH_DAY.finditer(quote):
        month, day = _MONTHS[match.group(1)[:3].lower()], int(match.group(2))
        for year in (published.year, published.year + 1):
            try:
                value = date(year, month, day)
            except ValueError:
                continue
            if value >= published:
                found.add(value)
                break
    if _TODAY.search(quote):
        found.add(published)
    if _TOMORROW.search(quote):
        found.add(published + timedelta(days=1))
    next_spans = []
    for match in _NEXT_WEEKDAY.finditer(quote):
        found.add(_weekday_on_or_after(
            published, _WEEKDAYS.index(match.group(1).lower()), strict=True))
        next_spans.append(match.span())
    for match in _BARE_WEEKDAY.finditer(quote):
        if any(lo <= match.start() < hi for lo, hi in next_spans):
            continue
        found.add(_weekday_on_or_after(
            published, _WEEKDAYS.index(match.group(1).lower()), strict=False))
    return found
