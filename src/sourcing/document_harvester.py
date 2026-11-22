"""Document-led collection harvester for enumerable civic records (OD-22 D2).

Three collections, each enumerated from public index pages:

- ``bos_transcripts`` — sfgov.legistar.com Calendar.aspx (per year) meeting
  detail pages and their View.ashx transcript documents;
- ``budget_documents`` — Controller's Office budget PDFs;
- ``ballot_measures`` — SF Election ballot-measure PDFs.

Documents are fetched as RAW BYTES over httpx — never Keenable fetch, whose
markdown conversion truncates — then archived content-addressed via
``src.sources.archive_source``. Every document's URL and digest is checked
against the dedupe union (``build_dedupe_index``, which contains the
63-candidate register) BEFORE any extraction runs; collisions surface in the
``dropped_reasons`` histogram. Documents exceeding the extraction caps are
sliced by their own TOC chapter boundaries — or an operator override — into
page ranges that each fit; every range is archived and hashed as its own
artifact so quote verification resolves against one archived document.
Scanned documents with no text layer fail loudly.

Live-semantics notes (probed 2026-11-15, UA ``SF-Promises-Research/1.0``):
Legistar Calendar.aspx lists ``MeetingDetail.aspx?ID=…&GUID=…`` links and
``View.ashx?M=IC|A&ID=…&GUID=…`` document links directly, and ``?year=YYYY``
paginates by year (13 meetings returned for 2025) — verified live. The other
two hosts did not serve a usable index to the probe (sfcontroller.org
returned a bot-check 202 interstitial; sfelections.sfgov.org redirects its
root to sf.gov), so their listing URLs are operator data, not code. All
listing URLs are data: a live-semantics change edits the spec factories, not
the parsers.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass, field
from html import unescape as _html_unescape
from pathlib import Path
from typing import Awaitable, Callable
from urllib.parse import urljoin, urlparse

import httpx

from src.checks import check_hash
from src.keenable import _retry_delay
from src.pdf_worker import CHAR_CAP
from src.sourcing.dedupe import build_dedupe_index, dedupe_verdict, normalize_url
from src.sourcing.page_ranges import (
    chapter_boundaries,
    exceeds_caps,
    plan_ranges,
)
from src.sources import archive_source

BYTE_CAP = 10 * 1024 * 1024
DEFAULT_MAX_DOCUMENTS = 20
# Polite default pause between document fetches; Retry-After is honored
# above this on 429 responses.
DEFAULT_FETCH_DELAY = 1.0
USER_AGENT = "SF-Promises-Harvester/1.0"

LEGISTAR_BASE = "https://sfgov.legistar.com"
LEGISTAR_DEFAULT_YEARS = (2025, 2026)


class FetchDenial(Exception):
    """A fetch-level refusal (status, rate limit, empty, oversized)."""

    def __init__(self, url: str, reason: str):
        super().__init__(f"{reason}: {url}")
        self.url = url
        self.reason = reason


class ScannedDocumentError(Exception):
    """A document with no extractable text — loud, never silent loss."""

    def __init__(self, urls: tuple[str, ...]):
        super().__init__("no extractable text: " + "; ".join(urls))
        self.urls = urls


class UnsupportedSourceFormat(ValueError):
    """The archived bytes are not a PDF (Legistar serves doc/html attachments)."""

    def __init__(self, url: str):
        super().__init__(f"source_format_unsupported: {url}")
        self.url = url


@dataclass(frozen=True)
class CollectionSpec:
    """One enumerable collection: listing URLs plus pure link parsers."""

    key: str
    label: str
    listing_urls: tuple[str, ...]
    # (listing_url, page_text) -> {"documents": [...], "pages": [...]}:
    # documents are archived, pages are fetched once more and parsed for
    # further documents (Legistar meeting detail pages).
    parse_documents: Callable[[str, str], dict[str, list[str]]]


@dataclass(frozen=True)
class HarvestedDocument:
    collection: str
    url: str
    path: str
    sha256: str
    size: int
    text_path: str | None
    text_sha256: str | None
    ranges: tuple[dict, ...] = field(default_factory=tuple)


def _links(html: str, pattern: str) -> list[str]:
    return [match.group(1) for match in re.finditer(pattern, html, re.IGNORECASE)]


def _absolute(base_url: str, href: str) -> str:
    return urljoin(base_url, _html_unescape(href.strip()))


def parse_legistar_documents(listing_url: str, html: str) -> dict[str, list[str]]:
    """Meeting detail pages and View.ashx document URLs from Legistar pages."""
    documents: list[str] = []
    pages: list[str] = []
    seen: set[str] = set()
    for href in _links(html, r'href="([^"]*View\.ashx\?[^"]*)"'):
        url = _absolute(listing_url, href)
        if url not in seen:
            seen.add(url)
            documents.append(url)
    for href in _links(html, r'href="([^"]*MeetingDetail\.aspx\?[^"]*)"'):
        url = _absolute(listing_url, href)
        if url not in seen:
            seen.add(url)
            pages.append(url)
    return {"documents": documents, "pages": pages}


def parse_pdf_documents(listing_url: str, html: str, *, keyword: str | None = None) -> dict[str, list[str]]:
    """Absolute .pdf links, optionally filtered by a keyword in the URL."""
    documents: list[str] = []
    seen: set[str] = set()
    for href in _links(html, r'href="([^"]+\.pdf(?:\?[^"]*)?)"'):
        url = _absolute(listing_url, href)
        if url in seen:
            continue
        if keyword is not None and keyword not in url.lower():
            continue
        seen.add(url)
        documents.append(url)
    return {"documents": documents, "pages": []}


def legistar_calendar_urls(years: tuple[int, ...] = LEGISTAR_DEFAULT_YEARS) -> tuple[str, ...]:
    """Per-year Legistar calendar listing URLs (year pagination verified live)."""
    return tuple(f"{LEGISTAR_BASE}/Calendar.aspx?year={year}" for year in years)


def default_specs() -> tuple[CollectionSpec, ...]:
    """The three D2 collections with live-verified listing URLs where known."""
    return (
        CollectionSpec(
            key="bos_transcripts",
            label="Board of Supervisors meeting transcripts",
            listing_urls=legistar_calendar_urls(),
            parse_documents=parse_legistar_documents,
        ),
        CollectionSpec(
            key="budget_documents",
            label="Controller's Office budget documents",
            listing_urls=("https://sfcontroller.org/",),
            parse_documents=lambda url, html: parse_pdf_documents(url, html, keyword="budget"),
        ),
        CollectionSpec(
            key="ballot_measures",
            label="SF Election ballot-measure documents",
            listing_urls=("https://sfelections.sfgov.org/",),
            parse_documents=lambda url, html: parse_pdf_documents(url, html, keyword="ballot"),
        ),
    )


class RawByteFetcher:
    """Raw-byte HTTP GETs with bounded, header-aware rate-limit retries.

    Mirrors RetryingKeenable's Retry-After discipline (src/keenable.py) but
    returns the response body untouched: no markdown conversion, no
    truncation. Fetch-level problems raise FetchDenial so the runner records
    them as denial rows instead of losing them.
    """

    def __init__(
        self,
        *,
        transport=None,
        timeout: float = 30,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        max_attempts: int = 3,
        max_retry_delay: float = 30,
        byte_cap: int = BYTE_CAP,
    ):
        self._retry_after: ContextVar = ContextVar("harvest_retry_after", default=None)
        self._sleep = sleep
        self._max_attempts = max_attempts
        self._max_retry_delay = max_retry_delay
        self._byte_cap = byte_cap
        self._http = httpx.AsyncClient(
            timeout=timeout, transport=transport, follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
            event_hooks={"response": [self._capture_retry_after]},
        )

    async def _capture_retry_after(self, response):
        self._retry_after.set(
            response.headers.get("Retry-After") if response.status_code == 429 else None
        )

    async def fetch_bytes(self, url: str) -> bytes:
        for attempt in range(self._max_attempts):
            self._retry_after.set(None)
            response = await self._http.get(url)
            if response.status_code == 429:
                # Same header grammar as RetryingKeenable.
                delay = _retry_delay(self._retry_after.get())
                if attempt == self._max_attempts - 1 or delay is None or delay > self._max_retry_delay:
                    raise FetchDenial(url, "rate_limited")
                await self._sleep(delay)
                continue
            if response.status_code != 200:
                raise FetchDenial(url, f"http_{response.status_code}")
            data = response.content
            if not data:
                raise FetchDenial(url, "empty_response")
            if len(data) > self._byte_cap:
                # Never truncate: an oversized body is denied whole.
                raise FetchDenial(url, "byte_cap_exceeded")
            return data
        raise FetchDenial(url, "rate_limited")

    async def aclose(self):
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()


def _pages_text(pages: list[dict]) -> str:
    """Page bodies joined by form feeds — the page-break marker quote checks see."""
    return "\f".join(page["text"] for page in pages)


async def _extract_document(
    *,
    url: str,
    promise_id: str,
    saved: dict,
    archive_root: Path,
    extract_pdf,
    inspect_pdf,
    range_boundaries: dict[str, tuple[int, ...]] | None,
    lane_key: str | None = None,
    max_chars: int = CHAR_CAP,
) -> HarvestedDocument:
    """Extract one archived document; slice into ranges when caps force it."""
    size = Path(saved["path"]).stat().st_size
    try:
        result = await extract_pdf(path=saved["path"], digest=saved["sha256"], promise_id=promise_id)
    except ValueError:
        # Distinguish caps (slice), scanned (loud), and unknown (loud).
        try:
            inspection = await inspect_pdf(path=saved["path"], digest=saved["sha256"], promise_id=promise_id)
        except ValueError as exc:
            # Non-PDF bytes are a routine Legistar attachment (doc/html),
            # denied and recorded by the runner — not an unknown failure.
            if "source_format_unsupported" in str(exc):
                raise UnsupportedSourceFormat(url) from None
            raise
        if not exceeds_caps(inspection["pages"], max_chars=max_chars):
            if not any(page["chars"] for page in inspection["pages"]):
                raise ScannedDocumentError((url,)) from None
            raise
        # Operator override: keyed by document URL or by the collection's
        # listing URL (the lane the operator knows); TOC detection otherwise.
        boundaries = tuple((range_boundaries or {}).get(url, ()))
        if not boundaries and lane_key is not None:
            boundaries = tuple((range_boundaries or {}).get(lane_key, ()))
        if not boundaries:
            boundaries = tuple(chapter_boundaries(inspection["pages"]))
        ranges = plan_ranges(inspection["pages"], boundaries=boundaries, max_chars=max_chars)
        range_records = []
        for page_from, page_to in ranges:
            extracted = await extract_pdf(
                path=saved["path"], digest=saved["sha256"], promise_id=promise_id,
                page_from=page_from, page_to=page_to,
            )
            text = _pages_text(extracted["pages"])
            range_saved = archive_source(
                archive_root, f"{promise_id}-p{page_from}-{page_to}",
                text.encode("utf-8"), ".txt",
            )
            range_records.append({
                "page_from": page_from,
                "page_to": page_to,
                "path": range_saved["path"],
                "sha256": range_saved["sha256"],
                "chars": len(text),
            })
        return HarvestedDocument(
            collection="", url=url, path=saved["path"], sha256=saved["sha256"],
            size=size, text_path=None, text_sha256=None, ranges=tuple(range_records),
        )

    text = _pages_text(result["pages"])
    text_saved = archive_source(archive_root, promise_id, text.encode("utf-8"), ".txt")
    return HarvestedDocument(
        collection="", url=url, path=saved["path"], sha256=saved["sha256"],
        size=size, text_path=text_saved["path"], text_sha256=text_saved["sha256"],
    )


async def harvest_collections(
    *,
    specs: tuple[CollectionSpec, ...],
    archive_root: Path,
    repo_root: Path | None = None,
    fetcher: RawByteFetcher | None = None,
    dedupe_index=None,
    max_documents: int = DEFAULT_MAX_DOCUMENTS,
    range_boundaries: dict[str, tuple[int, ...]] | None = None,
    max_chars: int = CHAR_CAP,
    extract_pdf=None,
    inspect_pdf=None,
    fetch_delay: float = DEFAULT_FETCH_DELAY,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    strict: bool = True,
) -> dict:
    """Harvest every collection: fetch, dedupe, archive, extract — offline-testable.

    ``extract_pdf``/``inspect_pdf`` are async callables
    ``(path=, digest=, promise_id=, page_from=, page_to=)`` /
    ``(path=, digest=, promise_id=)``. Callers supply the bounded local
    process callbacks from src/pdf.py with archive_root bound as root.

    In ``strict`` mode (the default) a scanned document raises
    ScannedDocumentError after the run records its denial row; a rejected
    scanned document never silently disappears.
    """
    if fetcher is None:
        fetcher = RawByteFetcher(sleep=sleep)
    if dedupe_index is None:
        if repo_root is None:
            raise ValueError("harvest_collections needs repo_root or a dedupe_index")
        dedupe_index = build_dedupe_index(repo_root, archive_root=archive_root)

    dropped: list[dict] = []
    denials: list[dict] = []
    documents: list[HarvestedDocument] = []
    collections: dict[str, dict] = {}
    seen_digests: set[str] = set()
    scanned: list[str] = []
    budget = max_documents

    def deny(url: str, reason: str):
        denials.append({"url": url, "reason": reason})

    def drop(url: str, collection: str, reason: str, matched_value: str):
        dropped.append({
            "url": url, "collection": collection,
            "reason": reason, "matched_value": matched_value,
        })

    async def fetch_raw(url: str) -> bytes | None:
        try:
            return await fetcher.fetch_bytes(url)
        except FetchDenial as exc:
            deny(url, exc.reason)
        except httpx.HTTPError:
            deny(url, "transport_error")
        return None

    for spec in specs:
        stats = {"documents_found": 0, "archived": 0, "dropped": 0, "denied": 0}
        collections[spec.key] = stats
        for listing_url in spec.listing_urls:
            # Phase 1: walk listing pages breadth-first. Pages are navigation,
            # not documents; a document re-listed on a detail page is the same
            # document, so cross-page repeats collapse here, not into drops.
            pending_pages = [listing_url]
            seen_page_urls: set[str] = set()
            doc_urls: list[str] = []
            seen_doc_urls: set[str] = set()
            while pending_pages:
                page_url = pending_pages.pop(0)
                normalized_page = normalize_url(page_url)
                if normalized_page in seen_page_urls:
                    continue
                seen_page_urls.add(normalized_page)
                page_bytes = await fetch_raw(page_url)
                if page_bytes is None:
                    continue
                parsed = spec.parse_documents(page_url, page_bytes.decode("utf-8", errors="replace"))
                pending_pages.extend(parsed["pages"])
                for url in parsed["documents"]:
                    normalized = normalize_url(url)
                    if normalized not in seen_doc_urls:
                        seen_doc_urls.add(normalized)
                        doc_urls.append(url)
            stats["documents_found"] += len(doc_urls)
            for url in doc_urls:
                normalized = normalize_url(url)
                if budget <= 0:
                    deny(url, "run_document_cap")
                    stats["denied"] += 1
                    continue
                budget -= 1

                data = await fetch_raw(url)
                if data is None:
                    stats["denied"] += 1
                    continue
                digest = hashlib.sha256(data).hexdigest()
                if digest in seen_digests:
                    drop(url, spec.key, "sha256_harvested_this_run", digest)
                    stats["dropped"] += 1
                    continue
                # Dedupe BEFORE extraction: URL and digest against the
                # union (corpus, 63-candidate register, denials, archive).
                verdict = dedupe_verdict({"url": url, "content_sha256": digest}, dedupe_index)
                if verdict is not None:
                    drop(url, spec.key, verdict.reason, verdict.matched_value)
                    stats["dropped"] += 1
                    continue
                seen_digests.add(digest)

                promise_id = f"harv-{spec.key}-{digest[:12]}"
                saved = archive_source(archive_root, promise_id, data, ".pdf")
                verified, _ = check_hash(saved["path"], saved["sha256"])
                if not verified:
                    raise RuntimeError(f"archived document failed sha256 re-verification: {url}")
                try:
                    document = await _extract_document(
                        url=url, promise_id=promise_id, saved=saved,
                        archive_root=archive_root, extract_pdf=extract_pdf,
                        inspect_pdf=inspect_pdf, range_boundaries=range_boundaries,
                        lane_key=listing_url, max_chars=max_chars,
                    )
                except UnsupportedSourceFormat:
                    deny(url, "unsupported_source_format")
                    stats["denied"] += 1
                    continue
                except ScannedDocumentError:
                    deny(url, "no_extractable_text")
                    scanned.append(url)
                    stats["denied"] += 1
                    continue
                document = HarvestedDocument(
                    collection=spec.key, url=url, path=document.path,
                    sha256=document.sha256, size=document.size,
                    text_path=document.text_path, text_sha256=document.text_sha256,
                    ranges=document.ranges,
                )
                documents.append(document)
                stats["archived"] += 1
                await sleep(fetch_delay)

    if scanned and strict:
        raise ScannedDocumentError(tuple(scanned))

    return {
        "mode": "document_led_harvest",
        "documents": [
            {
                "collection": doc.collection, "url": doc.url, "path": doc.path,
                "sha256": doc.sha256, "size": doc.size,
                "text_path": doc.text_path, "text_sha256": doc.text_sha256,
                "ranges": list(doc.ranges),
            }
            for doc in documents
        ],
        "collections": collections,
        "dropped_reasons": dict(sorted(Counter(d["reason"] for d in dropped).items())),
        # Lane-aware reporting only: the same drop rows, histogrammed per
        # collection so a register collision is explainable per lane. The
        # dedupe union itself (build_dedupe_index / dedupe_verdict above) is
        # untouched.
        "dropped_by_collection": dict(sorted(
            (collection, dict(sorted(Counter(
                d["reason"] for d in dropped if d["collection"] == collection
            ).items())))
            for collection in {d["collection"] for d in dropped}
        )),
        "dropped": dropped,
        "denials": denials,
        "max_documents": max_documents,
    }
