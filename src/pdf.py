"""Transfer a saved PDF to an isolated worker and receive unverified text."""

import asyncio
import json
import tempfile
from pathlib import Path

from src.sandbox import run_in_fork
from src.sources import load_archived_pdf


async def extract_archived_pdf(
    client, golden_id, *, ledger, run_id, job_id, root, promise_id, path, digest,
    template_reviewed=False, network_reviewed=False,
):
    """Extract unverified page text only within a tracked disposable fork."""
    data = load_archived_pdf(root, promise_id, path, digest)
    async def operation(worker):
        return await _extract_pdf_on_worker(worker, data, digest)

    return await run_in_fork(
        client, golden_id, operation, ledger=ledger, run_id=run_id, job_id=job_id,
        template_reviewed=template_reviewed, network_reviewed=network_reviewed,
    )


async def _extract_pdf_on_worker(worker, data, digest):
    with tempfile.TemporaryDirectory() as directory:
        local_pdf = Path(directory) / "source.pdf"
        local_pdf.write_bytes(data)
        # https://docs.archil.com/sdks/python.md#persistent-sandboxes
        await worker.files.upload_file.aio(local_pdf, "/tmp/sf-promises-source.pdf")
        await worker.files.upload_file.aio(
            Path(__file__).with_name("pdf_worker.py"), "/tmp/sf-promises-pdf-worker.py"
        )
        result = await asyncio.wait_for(
            worker.exec.aio("python3 /tmp/sf-promises-pdf-worker.py /tmp/sf-promises-source.pdf"),
            timeout=120,
        )
    if (getattr(result, "exit_code", None) != 0
            or not isinstance(getattr(result, "stdout", None), str)
            or len(result.stdout) > 2_500_000):
        raise ValueError("PDF worker failed")
    try:
        output = json.loads(result.stdout)
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
    except (TypeError, KeyError, ValueError):
        raise ValueError("Invalid PDF worker result") from None
    return output
