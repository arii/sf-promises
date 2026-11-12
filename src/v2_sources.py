"""Archive source bytes and verify quotes against saved text."""

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from src.checks import check_hash


def is_verbatim_quote(quote, text):
    return isinstance(quote, str) and bool(quote.strip()) and isinstance(text, str) and quote in text


def _normalized_with_offsets(text):
    punctuation = str.maketrans({
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
        "\u2014": "-", "\u2015": "-", "\u2212": "-",
    })
    hidden = set()
    for link in re.finditer(r"\[([^\]\n]+)\]\([^\n)]*\)", text):
        hidden.update(range(link.start(), link.start(1)))
        hidden.update(range(link.end(1), link.end()))
    chars = []
    offsets = []
    for index, character in enumerate(text):
        if index in hidden or character in "*_`":
            continue
        character = character.translate(punctuation)
        if character.isspace():
            if not chars or chars[-1] == " ":
                continue
            character = " "
        chars.append(character)
        offsets.append(index)
    if chars and chars[-1] == " ":
        chars.pop()
        offsets.pop()
    return "".join(chars), offsets


def snap_quote(quote, text):
    """Return a literal source span for a formatting-equivalent quote."""
    if not isinstance(quote, str) or not quote.strip() or not isinstance(text, str):
        return None
    if quote in text:
        return quote
    normalized_quote, _ = _normalized_with_offsets(quote)
    normalized_text, offsets = _normalized_with_offsets(text)
    if not normalized_quote:
        return None
    start = normalized_text.find(normalized_quote)
    if start < 0:
        return None
    return text[offsets[start]:offsets[start + len(normalized_quote) - 1] + 1]


def archive_source(root: Path, promise_id: str, data: bytes, suffix: str) -> dict[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", promise_id) or suffix not in (".md", ".txt", ".pdf", ".json"):
        raise ValueError("Invalid source identifier or extension")
    digest = hashlib.sha256(data).hexdigest()
    directory = root / promise_id
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{digest}{suffix}"
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as file:
            temporary_path = file.name
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            if not check_hash(str(path), digest)[0]:
                raise ValueError("Existing source does not match its hash")
    finally:
        if temporary_path is not None:
            os.unlink(temporary_path)
    return {"path": str(path), "sha256": digest}


def verify_source(path: str, digest: str, quote: str) -> bool:
    if not check_hash(path, digest)[0]:
        return False
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return is_verbatim_quote(quote, text)


def _load_archived_bytes(root, promise_id, path, digest, suffixes, max_bytes=None):
    if (not isinstance(promise_id, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]+", promise_id)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)):
        raise ValueError("source_path_invalid")
    try:
        source = Path(path).resolve(strict=True)
        directory = Path(root).resolve(strict=True) / promise_id
    except (OSError, TypeError, ValueError) as exc:
        raise ValueError("source_unavailable") from exc
    if source.parent != directory or source.stem != digest:
        raise ValueError("source_path_invalid")
    if source.suffix not in suffixes:
        raise ValueError("source_format_unsupported")
    try:
        with source.open("rb") as file:
            data = file.read(max_bytes + 1) if max_bytes is not None else file.read()
    except OSError as exc:
        raise ValueError("source_unavailable") from exc
    if max_bytes is not None and len(data) > max_bytes:
        raise ValueError("source_too_large")
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("source_hash_mismatch")
    return data


def load_archived_pdf(root, promise_id, path, digest):
    """Read bounded, content-addressed PDF bytes without parsing them."""
    data = _load_archived_bytes(root, promise_id, path, digest, (".pdf",), 10 * 1024 * 1024)
    if not data.startswith(b"%PDF-"):
        raise ValueError("source_format_unsupported")
    return data


def load_archived_metadata(root, promise_id, path, digest):
    """Read bounded provenance metadata; it is not independent source proof."""
    data = _load_archived_bytes(root, promise_id, path, digest, (".json",), 64 * 1024)
    try:
        result = json.loads(data)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("metadata_invalid") from exc
    if not isinstance(result, dict):
        raise ValueError("metadata_invalid")
    return result


def load_archived_text(root, promise_id, path, digest):
    """Read one content-addressed UTF-8 source beneath its candidate directory."""
    data = _load_archived_bytes(root, promise_id, path, digest, (".md", ".txt"))
    try:
        return data.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("source_format_unsupported") from exc
