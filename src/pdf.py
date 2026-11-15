"""Transfer a saved PDF to an isolated worker and receive unverified text.

Three transfer shapes over the same disposable worker (spec OD-22 D2):
whole-document extraction, one page-range extraction, and a per-page
inspect summary used to build slicing plans for oversized documents.
"""

import asyncio
import json
import tempfile
from pathlib import Path

from src.sandbox import run_in_fork
from src.sources import load_archived_pdf

_WORKER_REMOTE = "/tmp/sf-promises-pdf-worker.py"
_SOURCE_REMOTE = "/tmp/sf-promises-source.pdf"


async def extract_archived_pdf(
    client, golden_id, *, ledger, run_id, job_id, root, promise_id, path, digest,
    template_reviewed=False, network_reviewed=False,
):
    """Extract unverified page text only within a tracked disposable fork."""
    data = load_archived_pdf(root, promise_id, path, digest)

    async def operation(worker):
        return await _pdf_worker_call(worker, data, digest, [], _validate_extract)

    return await run_in_fork(
        client, golden_id, operation, ledger=ledger, run_id=run_id, job_id=job_id,
        template_reviewed=template_reviewed, network_reviewed=network_reviewed,
    )


async def extract_archived_pdf_range(
    client, golden_id, *, ledger, run_id, job_id, root, promise_id, path, digest,
    page_from, page_to,
    template_reviewed=False, network_reviewed=False,
):
    """Extract one page range of a saved PDF within a tracked disposable fork."""
    if (type(page_from) is not int or type(page_to) is not int
            or not 1 <= page_from <= page_to):
        raise ValueError("Invalid page range")
    data = load_archived_pdf(root, promise_id, path, digest)

    async def operation(worker):
        arguments = ["--from", str(page_from), "--to", str(page_to)]
        return await _pdf_worker_call(worker, data, digest, arguments, _validate_extract_range)

    return await run_in_fork(
        client, golden_id, operation, ledger=ledger, run_id=run_id, job_id=job_id,
        template_reviewed=template_reviewed, network_reviewed=network_reviewed,
    )


async def inspect_archived_pdf(
    client, golden_id, *, ledger, run_id, job_id, root, promise_id, path, digest,
    template_reviewed=False, network_reviewed=False,
):
    """Per-page char counts and first lines for a saved PDF; no text body."""
    data = load_archived_pdf(root, promise_id, path, digest)

    async def operation(worker):
        return await _pdf_worker_call(worker, data, digest, ["--inspect"], _validate_inspect)

    return await run_in_fork(
        client, golden_id, operation, ledger=ledger, run_id=run_id, job_id=job_id,
        template_reviewed=template_reviewed, network_reviewed=network_reviewed,
    )


async def _pdf_worker_call(worker, data, digest, arguments, validate):
    with tempfile.TemporaryDirectory() as directory:
        local_pdf = Path(directory) / "source.pdf"
        local_pdf.write_bytes(data)
        # https://docs.archil.com/sdks/python.md#persistent-sandboxes
        await worker.files.upload_file.aio(local_pdf, _SOURCE_REMOTE)
        await worker.files.upload_file.aio(
            Path(__file__).with_name("pdf_worker.py"), _WORKER_REMOTE
        )
        command = " ".join(["python3", _WORKER_REMOTE, _SOURCE_REMOTE, *arguments])
        result = await asyncio.wait_for(
            worker.exec.aio(command),
            timeout=120,
        )
    if (getattr(result, "exit_code", None) != 0
            or not isinstance(getattr(result, "stdout", None), str)
            or len(result.stdout) > 2_500_000):
        raise ValueError("PDF worker failed")
    try:
        output = json.loads(result.stdout)
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
