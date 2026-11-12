"""Extract bounded PDF text inside an isolated disposable worker."""

import hashlib
import json
import sys
from pathlib import Path

import pdfplumber


def extract(path):
    data = Path(path).read_bytes()
    if len(data) > 10 * 1024 * 1024 or not data.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF input")
    pages = []
    length = 0
    # https://github.com/jsvine/pdfplumber#the-pdfplumberpdf-class
    with pdfplumber.open(path) as pdf:
        if not 0 < len(pdf.pages) <= 100:
            raise ValueError("Unsupported PDF page count")
        for number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            length += len(text)
            if length > 500_000:
                raise ValueError("PDF text exceeds limit")
            pages.append({"page": number, "text": text})
    if not any(item["text"].strip() for item in pages):
        raise ValueError("PDF has no extractable text")
    return {"sha256": hashlib.sha256(data).hexdigest(), "pages": pages}


if __name__ == "__main__":
    print(json.dumps(extract(sys.argv[1]), ensure_ascii=False))
