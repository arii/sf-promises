"""Extract bounded PDF text in a disposable local process.

Three modes (spec OD-22 D2):

- default: extract the whole document under the 10 MiB / 100-page /
  500k-char caps;
- ``--from N --to M``: extract one page range under the same caps applied
  to the range, so an oversized document can be sliced into independently
  archived, hashable ranges;
- ``--inspect``: per-page char counts and first lines only — the bounded
  summary a slicing plan needs, with no text body in the output.
"""

import argparse
import hashlib
import json
from pathlib import Path

import pdfplumber

BYTE_CAP = 10 * 1024 * 1024
PAGE_CAP = 100
CHAR_CAP = 500_000
# Inspect summaries are ~30 bytes per page; 5000 pages stays well bounded.
INSPECT_PAGE_LIMIT = 5000
FIRST_LINE_CAP = 200


def _read_pdf(path):
    data = Path(path).read_bytes()
    if len(data) > BYTE_CAP or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF input")
    return data


def extract(path):
    data = _read_pdf(path)
    pages = []
    length = 0
    # https://github.com/jsvine/pdfplumber#the-pdfplumberpdf-class
    with pdfplumber.open(path) as pdf:
        if not 0 < len(pdf.pages) <= PAGE_CAP:
            raise ValueError("Unsupported PDF page count")
        for number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            length += len(text)
            if length > CHAR_CAP:
                raise ValueError("PDF text exceeds limit")
            pages.append({"page": number, "text": text})
    if not any(item["text"].strip() for item in pages):
        raise ValueError("PDF has no extractable text")
    return {"sha256": hashlib.sha256(data).hexdigest(), "pages": pages}


def extract_pages(path, page_from, page_to):
    """Extract pages [page_from, page_to] inclusive; caps apply to the range."""
    if (not isinstance(page_from, int) or not isinstance(page_to, int)
            or not 1 <= page_from <= page_to):
        raise ValueError("Invalid page range")
    data = _read_pdf(path)
    if page_to - page_from + 1 > PAGE_CAP:
        raise ValueError("Unsupported PDF page count")
    pages = []
    length = 0
    with pdfplumber.open(path) as pdf:
        if page_to > len(pdf.pages):
            raise ValueError("Page range beyond document")
        for number, page in enumerate(pdf.pages[page_from - 1:page_to], page_from):
            text = page.extract_text() or ""
            length += len(text)
            if length > CHAR_CAP:
                raise ValueError("PDF text exceeds limit")
            pages.append({"page": number, "text": text})
    if not any(item["text"].strip() for item in pages):
        raise ValueError("PDF has no extractable text")
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "page_from": page_from,
        "page_to": page_to,
        "pages": pages,
    }


def inspect(path):
    """Per-page char counts and first lines, without any text body."""
    data = _read_pdf(path)
    pages = []
    with pdfplumber.open(path) as pdf:
        if not 0 < len(pdf.pages) <= INSPECT_PAGE_LIMIT:
            raise ValueError("Unsupported PDF page count")
        for number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
            pages.append({
                "page": number,
                "chars": len(text),
                "first_line": first_line[:FIRST_LINE_CAP],
            })
    return {"sha256": hashlib.sha256(data).hexdigest(), "pages": pages}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("--inspect", action="store_true", help="Emit a per-page summary, not text")
    parser.add_argument("--from", dest="page_from", type=int, help="First page of a range extract")
    parser.add_argument("--to", dest="page_to", type=int, help="Last page of a range extract")
    arguments = parser.parse_args()
    if arguments.inspect:
        print(json.dumps(inspect(arguments.path), ensure_ascii=False))
    elif arguments.page_from is not None or arguments.page_to is not None:
        if arguments.page_from is None or arguments.page_to is None:
            parser.error("--from and --to must be given together")
        print(json.dumps(
            extract_pages(arguments.path, arguments.page_from, arguments.page_to),
            ensure_ascii=False,
        ))
    else:
        print(json.dumps(extract(arguments.path), ensure_ascii=False))
