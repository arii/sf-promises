"""Time-bounded Keenable discovery and saved-source handoff."""

import calendar
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from keenable import KeenableAPIError, KeenableConnectionError

from src.evidence import is_allowlisted_url
from src.sources import archive_source


async def search_window(client, query: str, after: str, before: str):
    results = await client.search(
        query, published_after=after, published_before=before, max_results=8
    )
    return results.results


async def discover_timeline(client, topic, *, promised, deadline, delivered, as_of,
                            entity: str | None = None, keywords: str | None = None):
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

    ent = f'"{entity}" ' if entity else ""
    kw = f'"{keywords}"' if keywords else f'"{topic}"'

    origin_q = f'{ent}{kw} ("pledged" OR "promised" OR "announced" OR "will open" OR "contract")' if (entity or keywords) else f"Original public commitment and deadline for {topic}"
    delivery_q = f'{ent}{kw} ("opened" OR "completed" OR "launched" OR "failed" OR "delayed")' if (entity or keywords) else f"Delivery, opening or completion of {topic}"
    survival_q = f'{ent}{kw} ("closed" OR "shuttered" OR "suspended" OR "halted" OR "vacant" OR "paused" OR "closure")' if (entity or keywords) else f"Current status, closure or suspension of {topic}"

    phases = (
        ("origin", origin_q,
         max(date.min, promised - timedelta(days=min(14, (promised - date.min).days))), origin_end),
        ("delivery", delivery_q, promised, delivery_end),
        ("survival", survival_q, delivered or promised, as_of),
    )
    results = {}
    for phase, query, after, before in phases:
        results[phase] = await search_window(client, query, after.isoformat(), before.isoformat())
    return results


async def fetch_and_archive(
    client, url: str, root: Path, promise_id: str, *, capture=None
) -> dict:
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
    # D4: selective per-page Wayback capture (Save-Page-Now) so the bytes
    # survive site death. Captures are corroborating provenance only — public
    # availability at a time, never authorship — so a failed or refused capture
    # never blocks an otherwise-valid fetch; the manifest records the outcome.
    capture_url = None
    capture_error = None
    if capture is not None:
        try:
            capture_url = await capture(url)
        except Exception as exc:
            capture_error = f"{type(exc).__name__}: {exc}"
    metadata = {
        **saved,
        "url": page.url,
        "requested_url": url,
        "published_at": page.published_at,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "wayback_capture_url": capture_url,
        "wayback_capture_error": capture_error,
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


async def discover_and_archive(client, lead, *, root, as_of, capture=None):
    """Search the three phases and archive complete allowlisted sources."""
    promise_id = lead["promise_id"]
    promised = date.fromisoformat(lead["promised_date"])
    deadline = date.fromisoformat(lead["due_date"]) if lead.get("due_date") else None
    entity = lead.get("entity")
    promise_text = lead.get("promise_text", "")
    
    # Extract focused keywords from the promise text to avoid long query degradations
    keywords = lead.get("keywords")
    if not keywords:
        clean_words = [w for w in re.findall(r"\b[A-Za-z0-9'-]+\b", promise_text)
                       if len(w) > 3 and w.lower() not in {"will", "open", "this", "that", "with", "from", "have", "been", "they", "their", "about", "also", "under"}]
        keywords = " ".join(clean_words[:5]) if clean_words else promise_text[:60]

    results = await discover_timeline(
        client, f'{entity or "Civic"}: {promise_text[:120]}',
        promised=promised, deadline=deadline, delivered=None, as_of=as_of,
        entity=entity, keywords=keywords,
    )
    saved = {}
    phases = {}
    for phase, entries in results.items():
        urls = [getattr(entry, "url", None) for entry in entries]
        if phase == "origin":
            urls.insert(0, lead.get("source_url"))
        sources = []
        blocked = []
        denied = []
        seen = set()
        for url in urls:
            if not isinstance(url, str) or not url or url in seen:
                continue
            seen.add(url)
            if not is_allowlisted_url(url):
                denied.append({"url": url, "reason": "source_url_not_allowlisted"})
                continue
            if url not in saved:
                try:
                    saved[url] = await fetch_and_archive(client, url, root, promise_id, capture=capture)
                except KeenableAPIError as exc:
                    if exc.status_code not in (404, 410):
                        raise
                    saved[url] = f"http_{exc.status_code}"
                except KeenableConnectionError:
                    # Still unreachable after the client's bounded retries: record
                    # the URL as blocked so the seed ends FETCH_INCOMPLETE instead
                    # of crashing the whole batch.
                    saved[url] = "fetch_connection_error"
                except ValueError as exc:
                    saved[url] = str(exc)
            if isinstance(saved[url], dict):
                sources.append(saved[url])
                if len(sources) >= 3:
                    break
            else:
                blocked.append({"url": url, "reason": saved[url]})
        phases[phase] = {
            "leads_found": len(entries), "sources": sources, "blocked": blocked, "denied": denied,
        }
    return {"promise_id": promise_id, "phases": phases,
            "outcome_sources": pool_outcome_sources(phases, promised=promised, as_of=as_of)}
