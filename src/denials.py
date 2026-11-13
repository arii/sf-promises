"""Per-domain denial analytics over recorded blocked-lead events.

Discovery records a deny row for every lead it rejects — the shape recorded in
``discover_and_archive``'s phase blocks: ``{"url": ..., "reason": ...}``. This
module aggregates those rows so later allowlist edits are evidence-driven; it
answers questions, it does not gate anything.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlparse

from src.allowlist import AllowlistEntry, entry_for_host, load_allowlist


def host_of(url: str) -> str:
    """Lowercased hostname without port; empty string when unparseable."""
    try:
        host = urlparse(url).hostname or ""
    except (TypeError, ValueError):
        return ""
    return host.lower()


def source_type_for_host(host: str, entries: tuple[AllowlistEntry, ...] | None = None) -> str:
    """The reviewed category of a denied host, or ``unlisted`` if not in the allowlist."""
    if entries is None:
        entries = load_allowlist()
    entry = entry_for_host(host, entries=entries)
    return entry.source_type if entry else "unlisted"


def summarize_denials(
    events: Iterable[Mapping[str, Any]],
    *,
    entries: tuple[AllowlistEntry, ...] | None = None,
) -> dict[str, Any]:
    """Aggregate recorded deny rows into a per-domain denial histogram.

    Each event is a recorded deny row (``{"url", "reason"}``; extra keys are
    ignored). The result attributes every denial to its domain and the domain's
    reviewed source category, so the histogram shows both what is blocked and
    what kind of source the block forecloses.
    """
    if entries is None:
        entries = load_allowlist()

    counts: Counter[str] = Counter()
    reasons: dict[str, Counter[str]] = {}
    source_types: dict[str, Counter[str]] = {}

    for event in events:
        url = event.get("url") if isinstance(event, Mapping) else None
        if not isinstance(url, str):
            continue
        reason = event.get("reason", "unknown")
        if not isinstance(reason, str) or not reason.strip():
            reason = "unknown"
        domain = host_of(url)
        if not domain:
            domain = "<unparseable>"
        counts[domain] += 1
        reasons.setdefault(domain, Counter())[reason] += 1
        source_types.setdefault(domain, Counter())[source_type_for_host(domain, entries)] += 1

    by_domain = {
        domain: {
            "count": count,
            "reasons": dict(sorted(reasons[domain].items())),
            "source_types": dict(sorted(source_types[domain].items())),
        }
        for domain, count in sorted(counts.items())
    }
    return {
        "total_denials": sum(counts.values()),
        "distinct_domains": len(counts),
        "by_domain": by_domain,
    }
