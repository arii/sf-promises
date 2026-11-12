"""Time-bounded Keenable discovery and saved-source handoff."""

import calendar
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from src.v2_evidence import is_allowlisted_url
from src.v2_sources import archive_source


async def search_window(client, query: str, after: str, before: str):
    results = await client.search(
        query, published_after=after, published_before=before, max_results=8
    )
    return results.results


async def discover_timeline(client, topic, *, promised, deadline, delivered, as_of):
    """Return bounded search leads, not evidence or inferred dates."""
    if (not isinstance(topic, str) or not topic.strip() or len(topic) > 500
            or type(promised) is not date or type(as_of) is not date
            or (deadline is not None and type(deadline) is not date)
            or (delivered is not None and type(delivered) is not date)):
        raise ValueError("Invalid discovery input")
    if (promised > as_of or (deadline is not None and deadline < promised)
            or (delivered is not None and not promised <= delivered <= as_of)):
        raise ValueError("Inconsistent discovery dates")
    origin_end = as_of if (as_of - promised).days <= 30 else promised + timedelta(days=30)
    delivery_end = as_of
    if deadline is not None and deadline < as_of:
        month = (deadline.month - 1 + 6) % 12 + 1
        year = deadline.year + (deadline.month - 1 + 6) // 12
        if year <= date.max.year:
            day = min(deadline.day, calendar.monthrange(year, month)[1])
            delivery_end = min(as_of, date(year, month, day))
    phases = (
        ("origin", f"Original public commitment and deadline for {topic}",
         max(date.min, promised - timedelta(days=min(14, (promised - date.min).days))), origin_end),
        ("delivery", f"Delivery, opening or completion of {topic}", promised, delivery_end),
        ("survival", f"Current status, closure or suspension of {topic}", delivered or promised, as_of),
    )
    results = {}
    for phase, query, after, before in phases:
        results[phase] = await search_window(client, query, after.isoformat(), before.isoformat())
    return results


async def fetch_and_archive(client, url: str, root: Path, promise_id: str) -> dict:
    if not is_allowlisted_url(url):
        raise ValueError("Source URL is not allowlisted")
    page = await client.fetch(url)
    if not is_allowlisted_url(page.url):
        raise ValueError("Fetched source URL is not allowlisted")
    if page.raw.get("truncated") is not False or not page.content:
        raise ValueError("Source is empty or completeness is unknown")
    if page.published_at is not None and not isinstance(page.published_at, str):
        raise ValueError("Source publication metadata is invalid")
    saved = archive_source(root, promise_id, page.content.encode("utf-8"), ".md")
    metadata = {
        **saved,
        "url": page.url,
        "requested_url": url,
        "published_at": page.published_at,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest = archive_source(
        root, promise_id,
        json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode("utf-8"),
        ".json",
    )
    return {**metadata, "metadata_path": manifest["path"], "metadata_sha256": manifest["sha256"]}


def pool_outcome_sources(phases, *, promised, as_of):
    """Pool dated outcome leads; their relevance and source tier still need review."""
    pooled = []
    seen = set()
    for phase in ("delivery", "survival"):
        for source in phases.get(phase, {}).get("sources", []):
            try:
                published = datetime.fromisoformat(source["published_at"]).date()
                key = (source["url"], source["sha256"])
                if (not is_allowlisted_url(source["url"])
                        or not promised < published <= as_of or key in seen):
                    continue
            except (KeyError, TypeError, ValueError):
                continue
            seen.add(key)
            pooled.append(source)
    return pooled


async def discover_and_archive(client, lead, *, root, as_of):
    """Search the three phases and archive complete allowlisted sources."""
    promise_id = lead["promise_id"]
    promised = date.fromisoformat(lead["promised_date"])
    deadline = date.fromisoformat(lead["due_date"]) if lead.get("due_date") else None
    results = await discover_timeline(
        client, f'{lead["entity"]}: {lead["promise_text"][:300]}',
        promised=promised, deadline=deadline, delivered=None, as_of=as_of,
    )
    saved = {}
    phases = {}
    for phase, entries in results.items():
        sources = []
        blocked = []
        seen = set()
        for entry in entries:
            url = getattr(entry, "url", None)
            if not isinstance(url, str) or url in seen or not is_allowlisted_url(url):
                continue
            seen.add(url)
            if url not in saved:
                try:
                    saved[url] = await fetch_and_archive(client, url, root, promise_id)
                except ValueError as exc:
                    saved[url] = str(exc)
            if isinstance(saved[url], dict):
                sources.append(saved[url])
            else:
                blocked.append({"url": url, "reason": saved[url]})
            if len(seen) >= 3:
                break
        phases[phase] = {"leads_found": len(entries), "sources": sources, "blocked": blocked}
    return {"promise_id": promise_id, "phases": phases,
            "outcome_sources": pool_outcome_sources(phases, promised=promised, as_of=as_of)}
