"""Wayback Machine Save-Page-Now capture at fetch time (OD-22 D4).

Captures are selective and per-page: one SPN request per fetched document,
never bulk, because Wayback is rate-limited. A capture is corroborating
metadata only — it proves public availability at a time, not authorship —
so its outcome never changes a verdict and never blocks an otherwise-valid
fetch. The manifest records the honest result either way.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote, urlsplit

import httpx

from src.allowlist import (
    WAYBACK_HOST,
    entry_for_host,
    is_canary_replay,
    replay_target_host,
)

SAVE_PAGE_NOW_URL = f"https://{WAYBACK_HOST}/save/"


def wayback_replay_url(target_url: str, timestamp: str) -> str:
    """The replay URL for a captured page."""
    return f"https://{WAYBACK_HOST}/web/{timestamp}/{target_url}"


def _capture_target_host(url: str) -> Optional[str]:
    """The host a capture would preserve: the replay target for Wayback URLs,
    else the URL host. None when no parseable host exists."""
    return replay_target_host(url) or (urlsplit(url).hostname or "").lower() or None


def capture_permitted(url: str) -> bool:
    """True when the URL's target host is an approved, non-canary allowlist entry.

    Canaries stay hard-blocked on the capture path too (D1's guard): an
    archived copy of a blocked host must never be manufactured by us.
    """
    host = _capture_target_host(url)
    if not host:
        return False
    entry = entry_for_host(host)
    return entry is not None and not entry.canary


def _timestamp_from_location(location: str) -> Optional[str]:
    """The capture timestamp in an SPN /web/<ts>/... location header, if any."""
    segments = (location or "").split("/")
    for segment in segments:
        if len(segment) == 14 and segment.isdigit():
            return segment
    return None


async def save_page_now(
    url: str,
    *,
    http_get=None,
    timeout: float = 30.0,
) -> Optional[str]:
    """Submit a Save-Page-Now capture for url and return its replay URL.

    Best effort by design: permit denials, rate limits, and network failures
    return None rather than raising, so a Wayback outage never blocks an
    otherwise-valid fetch — the manifest's null capture URL records it.
    `http_get` is injectable for offline tests; it receives the full SPN URL
    and returns an object with `.status_code` and `.headers`.
    """
    if not capture_permitted(url):
        return None

    async def _default_get(request_url: str):
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            return await client.get(request_url)

    try:
        response = await (http_get or _default_get)(
            SAVE_PAGE_NOW_URL + quote(url, safe=":/?=&")
        )
        timestamp = (
            _timestamp_from_location(response.headers.get("Content-Location", ""))
            or _timestamp_from_location(response.headers.get("Location", ""))
            or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        )
        return wayback_replay_url(url, timestamp)
    except Exception:
        # Recorded as a null capture URL in the manifest — surfaced there,
        # never treated as a successful capture.
        return None
