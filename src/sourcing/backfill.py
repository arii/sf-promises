"""One-off backfill sweep mode (spec OD-20 H3).

Separate from the rolling round (which owns its config-sourced window): the
sweep's window is operator-set, measured in months, and must reach at least
12 months back from the run date. The planner's explicit-window override is
preserved — the sweep passes its own window and never reads
``config/discovery.json`` for dates.

The full dedupe union (``src.sourcing.dedupe``) runs on every lead BEFORE
any audit/qualification happens. The sweep returns kept and dropped leads
plus a summary; it performs no qualification, publishes nothing, and never
writes ``data/intake_ledger.csv`` or any other data file.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any, Iterable, Mapping

from src.sourcing.dedupe import (
    DedupeIndex,
    TOKEN_OVERLAP_THRESHOLD,
    build_dedupe_index,
    dedupe_verdict,
)
from src.sourcing.planner import SearchPlanner

MIN_SWEEP_MONTHS = 12

# The D6b convention at the backtest's reported cap setting: Keenable
# hard-caps results at 25 per call, so this is the widest useful page.
DEFAULT_SWEEP_MAX_RESULTS = 25


def sweep_time_window(months: int, today: date | None = None) -> str:
    """Keenable-style 'start..end' window spanning `months` back from the run date.

    Raises ValueError for anything below the 12-month minimum — the rolling
    round owns shorter windows; this mode exists only for the deep backfill.
    """
    if isinstance(months, bool) or not isinstance(months, int) or months < MIN_SWEEP_MONTHS:
        raise ValueError(
            f"sweep window must be an integer of at least {MIN_SWEEP_MONTHS} months, got {months!r}"
        )
    today = today or date.today()
    start = _subtract_months(today, months)
    return f"{start.isoformat()}..{today.isoformat()}"


def _subtract_months(day: date, months: int) -> date:
    """Same day-of-month `months` earlier, clamped to the target month's end."""
    total = day.year * 12 + (day.month - 1) - months
    year, month = divmod(total, 12)
    month += 1
    last_day = (date(year + (month // 12), month % 12 + 1, 1) - timedelta(days=1)).day
    return date(year, month, min(day.day, last_day))


def build_sweep_queries(planner: SearchPlanner | None = None, time_window: str = "") -> list:
    """The full 98-query set (stratified + diversified variants) at the sweep window.

    Uses the planner's explicit time_window override, so the sweep's window is
    the operator's, not the rolling config's.
    """
    planner = planner or SearchPlanner()
    window = time_window or sweep_time_window(MIN_SWEEP_MONTHS)
    return (
        planner.generate_stratified_queries(time_window=window)
        + planner.generate_diversified_variants(time_window=window)
    )


def _lead_from_result(result: Any, spec) -> dict[str, Any]:
    """Normalize a Keenable search result into a dedupe-checkable lead."""
    if isinstance(result, Mapping):
        return {
            "url": result.get("url", ""),
            "title": result.get("title", ""),
            "snippet": result.get("snippet", ""),
            "query_id": spec.query_id,
            "pillar": spec.pillar,
            "language": spec.language,
        }
    return {
        "url": getattr(result, "url", ""),
        "title": getattr(result, "title", ""),
        "snippet": getattr(result, "snippet", ""),
        "query_id": spec.query_id,
        "pillar": spec.pillar,
        "language": spec.language,
    }


async def run_backfill_sweep(
    client,
    *,
    months: int,
    repo_root,
    archive_root=None,
    quarantine_urls: Iterable[str] = (),
    known_sha256: Iterable[str] = (),
    today: date | None = None,
    max_results: int = DEFAULT_SWEEP_MAX_RESULTS,
    threshold: float = TOKEN_OVERLAP_THRESHOLD,
    planner: SearchPlanner | None = None,
) -> dict[str, Any]:
    """Run the one-off sweep: search the operator window, dedupe, return.

    The dedupe union runs on every lead BEFORE audit — nothing returned in
    ``leads_for_audit`` has touched qualification. No data file is written:
    in particular ``data/intake_ledger.csv`` is never touched.
    """
    window = sweep_time_window(months, today)
    queries = build_sweep_queries(planner, window)
    index: DedupeIndex = build_dedupe_index(
        repo_root,
        archive_root=archive_root,
        quarantine_urls=quarantine_urls,
        known_sha256=known_sha256,
    )

    seen_urls: set[str] = set()
    raw_leads: list[dict[str, Any]] = []
    in_sweep_duplicates = 0
    for spec in queries:
        results = await client.search(
            spec.query_text,
            published_after=window.split("..")[0],
            published_before=window.split("..")[1],
            max_results=max_results,
        )
        for result in results.results if hasattr(results, "results") else results:
            lead = _lead_from_result(result, spec)
            url = lead["url"]
            if url and url in seen_urls:
                in_sweep_duplicates += 1
                continue
            if url:
                seen_urls.add(url)
            raw_leads.append(lead)

    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for lead in raw_leads:
        match = dedupe_verdict(lead, index, threshold=threshold)
        if match is None:
            kept.append(lead)
        else:
            dropped.append(
                {
                    "url": lead.get("url", ""),
                    "query_id": lead.get("query_id", ""),
                    "reason": match.reason,
                    "matched_value": match.matched_value,
                }
            )

    return {
        "mode": "backfill_sweep",
        "window": window,
        "months": months,
        "query_count": len(queries),
        "leads_encountered": len(raw_leads) + in_sweep_duplicates,
        "in_sweep_duplicate_urls": in_sweep_duplicates,
        "deduped_leads_for_audit": len(kept),
        "dropped_before_audit": len(dropped),
        "dropped_reasons": dict(sorted(Counter(d["reason"] for d in dropped).items())),
        "leads_for_audit": kept,
        "dropped": dropped,
    }
