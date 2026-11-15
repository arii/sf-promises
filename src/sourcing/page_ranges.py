"""Slicing plans that bring oversized PDFs under the extraction caps.

Pure functions: given a worker ``--inspect`` summary (per-page char counts and
first lines), decide whether the document exceeds the extraction caps and, if
so, produce page ranges that each fit. Chapter boundaries from the document's
own TOC are preferred cut points, but the caps always win — a boundary is only
used when the range ending there still fits.

Spec assumption on record: TOC detection is heuristic. When it proves
unreliable for a document, the operator passes explicit boundaries (the
manual override) and this module applies them unchanged.
"""

from __future__ import annotations

import re

# Must match src/pdf_worker.py, the sole consumer of these plans.
PAGE_CAP = 100
CHAR_CAP = 500_000
INSPECT_PAGE_LIMIT = 5000

# "Chapter 3", "CHAPTER 12", "Chapter IV" at the top of a page.
_CHAPTER_RE = re.compile(r"^\s*chapter\s+([0-9]{1,3}|[ivxlcdm]{1,7})\b", re.IGNORECASE)


def chapter_boundaries(inspect_pages: list[dict]) -> list[int]:
    """1-based page numbers whose first line opens a numbered chapter."""
    return [
        page["page"]
        for page in inspect_pages
        if _CHAPTER_RE.match(str(page.get("first_line", "")))
    ]


def exceeds_caps(
    inspect_pages: list[dict],
    *,
    max_pages: int = PAGE_CAP,
    max_chars: int = CHAR_CAP,
) -> bool:
    return len(inspect_pages) > max_pages or sum(page["chars"] for page in inspect_pages) > max_chars


def _fit_end(start: int, chars: dict[int, int], last_page: int, max_pages: int, max_chars: int) -> int:
    """The last page such that [start, end] fits both caps; start-1 if none."""
    total = 0
    end = start - 1
    for page in range(start, min(start + max_pages, last_page + 1)):
        total += chars[page]
        if total > max_chars:
            break
        end = page
    return end


def plan_ranges(
    inspect_pages: list[dict],
    *,
    boundaries: list[int] | tuple[int, ...] = (),
    max_pages: int = PAGE_CAP,
    max_chars: int = CHAR_CAP,
) -> list[tuple[int, int]]:
    """A greedy slice plan [(page_from, page_to), ...] covering every page.

    Each plan is the smallest set of ranges whose members each fit within
    both caps. When a cap forces a cut, the largest chapter boundary that
    still fits is preferred over the bare cap limit; boundaries never
    introduce extra cuts.
    """
    pages = [page["page"] for page in inspect_pages]
    if pages != list(range(1, len(pages) + 1)):
        raise ValueError("inspect pages must be contiguous 1-based")
    chars = {page["page"]: page["chars"] for page in inspect_pages}
    cuts = sorted({boundary for boundary in boundaries if 2 <= boundary <= len(pages)})

    plan: list[tuple[int, int]] = []
    start = 1
    last_page = len(pages)
    while start <= last_page:
        end = _fit_end(start, chars, last_page, max_pages, max_chars)
        if end < start:
            raise ValueError(f"page {start} alone exceeds the {max_chars}-char cap")
        if end < last_page:
            # Prefer ending just before a chapter that starts inside the window.
            preferred = max((b for b in cuts if start < b <= end), default=None)
            if preferred is not None:
                end = preferred - 1
        plan.append((start, end))
        start = end + 1
    return plan
