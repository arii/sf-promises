"""Parse a saved PDF in a bounded local process and receive unverified text.

Three transfer shapes over the same disposable worker (spec OD-22 D2):
whole-document extraction, one page-range extraction, and a per-page
inspect summary used to build slicing plans for oversized documents.
"""

from src.local_worker import run_worker
from src.sources import load_archived_pdf


async def extract_archived_pdf(
    *, root, promise_id, path, digest,
):
    """Extract unverified page text in a disposable local process."""
    data = load_archived_pdf(root, promise_id, path, digest)

    return await _pdf_worker_call(data, digest, [], _validate_extract)


async def extract_archived_pdf_range(
    *, root, promise_id, path, digest,
    page_from, page_to,
):
    """Extract one page range of a saved PDF in a local process."""
    if (type(page_from) is not int or type(page_to) is not int
            or not 1 <= page_from <= page_to):
        raise ValueError("Invalid page range")
    data = load_archived_pdf(root, promise_id, path, digest)

    arguments = ["--from", str(page_from), "--to", str(page_to)]
    output = await _pdf_worker_call(data, digest, arguments, _validate_extract_range)
    if (output["page_from"] != page_from or output["page_to"] != page_to
            or len(output["pages"]) != page_to - page_from + 1):
        raise ValueError("PDF worker returned a different page range")
    return output


async def inspect_archived_pdf(
    *, root, promise_id, path, digest,
):
    """Per-page char counts and first lines for a saved PDF; no text body."""
    data = load_archived_pdf(root, promise_id, path, digest)

    return await _pdf_worker_call(data, digest, ["--inspect"], _validate_inspect)


async def _pdf_worker_call(data, digest, arguments, validate):
    output = await run_worker("src.pdf_worker", files={"source.pdf": data},
                              arguments=["source.pdf", *arguments])
    try:
        validate(output, digest)
    except (TypeError, KeyError, ValueError):
        raise ValueError("Invalid PDF worker result") from None
    return output


def _validate_extract(output, digest):
    pages = output["pages"]
    if (set(output) != {"sha256", "pages"} or output["sha256"] != digest
            or not isinstance(pages, list) or not 0 < len(pages) <= 100):
        raise ValueError
    for number, page in enumerate(pages, 1):
        if (not isinstance(page, dict) or set(page) != {"page", "text"}
                or type(page["page"]) is not int or page["page"] != number
                or not isinstance(page["text"], str)):
            raise ValueError
    if sum(len(page["text"]) for page in pages) > 500_000 or not any(
            page["text"].strip() for page in pages
    ):
        raise ValueError


def _validate_extract_range(output, digest):
    if (set(output) != {"sha256", "page_from", "page_to", "pages"}
            or output["sha256"] != digest
            or type(output["page_from"]) is not int
            or type(output["page_to"]) is not int
            or not 1 <= output["page_from"] <= output["page_to"]):
        raise ValueError
    pages = output["pages"]
    if not isinstance(pages, list) or not 0 < len(pages) <= 100:
        raise ValueError
    for offset, page in enumerate(pages):
        if (not isinstance(page, dict) or set(page) != {"page", "text"}
                or type(page["page"]) is not int
                or page["page"] != output["page_from"] + offset
                or not isinstance(page["text"], str)):
            raise ValueError
    if sum(len(page["text"]) for page in pages) > 500_000 or not any(
            page["text"].strip() for page in pages
    ):
        raise ValueError


def _validate_inspect(output, digest):
    pages = output["pages"]
    if (set(output) != {"sha256", "pages"} or output["sha256"] != digest
            or not isinstance(pages, list) or not 0 < len(pages) <= 5000):
        raise ValueError
    for number, page in enumerate(pages, 1):
        if (not isinstance(page, dict) or set(page) != {"page", "chars", "first_line"}
                or type(page["page"]) is not int or page["page"] != number
                or type(page["chars"]) is not int or page["chars"] < 0
                or not isinstance(page["first_line"], str)
                or len(page["first_line"]) > 200):
            raise ValueError
