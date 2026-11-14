"""Full dedupe union for the backfill sweep (spec OD-20 H3).

A sweep lead is dropped BEFORE audit when any of these matches:

- identity: its promise_id/candidate_id is already in the candidate register;
- sha256 byte-lock: the same page bytes are already archived (the harvester's
  ``ingest_raw_document``/``archive_source`` sha256 no-op is the same lock
  applied at write time; this check catches the lead before it gets there);
- URL match: the 54-record corpus, the candidate register, the D6b denials
  ledger, or a round-quarantine origin (P113-P118) already contains its URL;
- token overlap: >= 0.8 Jaccard overlap on entity+promise_text against the
  corpus or the register's statement previews.

``data/intake_ledger.csv`` is a frozen historical artifact: nothing here
reads or writes it. The live register is ``data/intake_candidate_register.json``.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

TOKEN_OVERLAP_THRESHOLD = 0.8

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_URL_RE = re.compile(r"https?://\S+")
# CJK characters carry no word boundaries, so single Han characters join the
# token set alongside whitespace-delimited words (mirrors qualification.py's
# per-language handling of forward-action patterns).
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_TOKEN_SPLIT_RE = re.compile(r"\w+", re.UNICODE)


def normalize_url(url: str) -> str:
    """Lowercased scheme+host, no trailing slash — enough to catch re-crawl variants."""
    if not isinstance(url, str):
        return ""
    url = url.strip().rstrip("/")
    try:
        parsed = urlparse(url)
    except ValueError:
        return url.lower()
    if not parsed.scheme and not parsed.netloc:
        return url.lower()
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path}{('?' + parsed.query) if parsed.query else ''}"


def normalize_tokens(text: str) -> frozenset[str]:
    """Lowercased word tokens plus Han characters for Chinese-language text."""
    if not isinstance(text, str):
        return frozenset()
    tokens = {match.group(0).lower() for match in _TOKEN_SPLIT_RE.finditer(text)}
    tokens.update(_CJK_RE.findall(text))
    tokens.discard("")
    return frozenset(tokens)


def token_overlap(a: frozenset[str], b: frozenset[str]) -> float:
    """Jaccard overlap between two token sets; two empty sets are not a match."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


@dataclass(frozen=True)
class DedupeMatch:
    """Why a lead was dropped, and what it collided with."""

    reason: str
    matched_value: str


@dataclass(frozen=True)
class DedupeIndex:
    corpus_urls: frozenset[str]
    register_urls: frozenset[str]
    denial_urls: frozenset[str]
    quarantine_urls: frozenset[str]
    archived_sha256: frozenset[str]
    known_ids: frozenset[str]
    corpus_tokens: tuple[frozenset[str], ...]
    register_tokens: tuple[frozenset[str], ...]


def _collect_urls(value: Any, into: set[str]) -> None:
    """Pull every http(s) URL out of a JSON-ish value (payloads are free-form)."""
    if isinstance(value, str):
        if value.startswith(("http://", "https://")):
            into.add(normalize_url(value))
        else:
            into.update(normalize_url(u) for u in _URL_RE.findall(value))
    elif isinstance(value, Mapping):
        for v in value.values():
            _collect_urls(v, into)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _collect_urls(v, into)


def quarantine_origins_from_db(db_path: Path) -> frozenset[str]:
    """Origin URLs of round-quarantined candidates (P113-P118), from the DB.

    Reads the ``quarantined`` table's ``candidate_payload_json``; the payload
    is free-form, so every http(s) URL it contains counts as an origin.
    """
    import sqlite3

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT candidate_payload_json FROM quarantined").fetchall()
    finally:
        conn.close()
    origins: set[str] = set()
    for (payload,) in rows:
        try:
            _collect_urls(json.loads(payload), origins)
        except (json.JSONDecodeError, TypeError):
            origins.update(normalize_url(u) for u in _URL_RE.findall(str(payload)))
    return frozenset(origins)


def build_dedupe_index(
    repo_root: Path,
    *,
    archive_root: Path | None = None,
    quarantine_urls: Iterable[str] = (),
    known_sha256: Iterable[str] = (),
) -> DedupeIndex:
    """Build the dedupe union from the reviewed data files.

    Reads (never writes) ``data/sf_promises_master.csv``,
    ``data/intake_candidate_register.json`` and ``data/denied_leads.json``.
    Quarantine origins come from the caller (the round database is not part
    of the repo); archived page digests come from the archive root, where
    files are named by their sha256.
    """
    corpus_urls: set[str] = set()
    corpus_token_sets: list[frozenset[str]] = []
    master_path = repo_root / "data" / "sf_promises_master.csv"
    if master_path.exists():
        with master_path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("primary_source_url"):
                    corpus_urls.add(normalize_url(row["primary_source_url"]))
                text = " ".join(
                    part for part in (row.get("entity"), row.get("promise_text")) if part
                )
                if text.strip():
                    corpus_token_sets.append(normalize_tokens(text))

    register_urls: set[str] = set()
    known_ids: set[str] = set()
    register_token_sets: list[frozenset[str]] = []
    register_path = repo_root / "data" / "intake_candidate_register.json"
    if register_path.exists():
        register = json.loads(register_path.read_text(encoding="utf-8"))
        candidates = register.get("candidates", []) if isinstance(register, dict) else register
        for cand in candidates:
            if not isinstance(cand, dict):
                continue
            if cand.get("source_url"):
                register_urls.add(normalize_url(cand["source_url"]))
            cid = cand.get("candidate_id") or cand.get("promise_id")
            if cid:
                known_ids.add(str(cid))
            text = " ".join(
                part for part in (cand.get("entity"), cand.get("statement_preview")) if part
            )
            if text.strip():
                register_token_sets.append(normalize_tokens(text))

    denial_urls: set[str] = set()
    denials_path = repo_root / "data" / "denied_leads.json"
    if denials_path.exists():
        denials = json.loads(denials_path.read_text(encoding="utf-8"))
        if isinstance(denials, list):
            for event in denials:
                if isinstance(event, dict) and event.get("url"):
                    denial_urls.add(normalize_url(event["url"]))

    archived: set[str] = {digest for digest in known_sha256 if _SHA256_RE.match(digest)}
    if archive_root is not None and Path(archive_root).exists():
        for path in Path(archive_root).rglob("*"):
            if path.is_file() and _SHA256_RE.match(path.stem):
                archived.add(path.stem)

    return DedupeIndex(
        corpus_urls=frozenset(corpus_urls),
        register_urls=frozenset(register_urls),
        denial_urls=frozenset(denial_urls),
        quarantine_urls=frozenset(normalize_url(u) for u in quarantine_urls if u),
        archived_sha256=frozenset(archived),
        known_ids=frozenset(known_ids),
        corpus_tokens=tuple(corpus_token_sets),
        register_tokens=tuple(register_token_sets),
    )


def _lead_url(lead: Mapping[str, Any]) -> str:
    return normalize_url(
        str(lead.get("url") or lead.get("source_url") or "")
    )


def _lead_tokens(lead: Mapping[str, Any]) -> frozenset[str]:
    text = " ".join(
        str(part)
        for part in (
            lead.get("entity"),
            lead.get("promise_text") or lead.get("text") or lead.get("title"),
            lead.get("snippet"),
        )
        if part
    )
    return normalize_tokens(text)


def _lead_ids(lead: Mapping[str, Any]) -> set[str]:
    return {
        str(lead[key])
        for key in ("promise_id", "candidate_id")
        if lead.get(key)
    }


def dedupe_verdict(
    lead: Mapping[str, Any],
    index: DedupeIndex,
    *,
    threshold: float = TOKEN_OVERLAP_THRESHOLD,
) -> DedupeMatch | None:
    """The first matching dedupe path for a lead, or None if it is novel.

    Check order is identity, sha256 byte-lock, URL match, then token
    overlap — cheapest and most specific first.
    """
    for id_value in _lead_ids(lead):
        if id_value in index.known_ids:
            return DedupeMatch("already_registered_id", id_value)

    digest = lead.get("content_sha256")
    if isinstance(digest, str) and _SHA256_RE.match(digest) and digest in index.archived_sha256:
        return DedupeMatch("sha256_archived", digest)

    url = _lead_url(lead)
    if url:
        if url in index.corpus_urls:
            return DedupeMatch("url_corpus", url)
        if url in index.register_urls:
            return DedupeMatch("url_register", url)
        if url in index.denial_urls:
            return DedupeMatch("url_denial", url)
        if url in index.quarantine_urls:
            return DedupeMatch("url_quarantine", url)

    tokens = _lead_tokens(lead)
    if tokens:
        for label, token_sets in (
            ("token_overlap_corpus", index.corpus_tokens),
            ("token_overlap_register", index.register_tokens),
        ):
            for known in token_sets:
                if token_overlap(tokens, known) >= threshold:
                    return DedupeMatch(label, f">={threshold}")

    return None


def filter_sweep_leads(
    leads: Iterable[Mapping[str, Any]],
    index: DedupeIndex,
    *,
    threshold: float = TOKEN_OVERLAP_THRESHOLD,
) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]]]:
    """Split leads into (kept, dropped) — the dedupe union applied before audit.

    Dropped entries pair the lead with its ``DedupeMatch``; nothing here
    writes to any data file.
    """
    kept: list[Mapping[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for lead in leads:
        match = dedupe_verdict(lead, index, threshold=threshold)
        if match is None:
            kept.append(lead)
        else:
            dropped.append({"lead": lead, "reason": match.reason, "matched_value": match.matched_value})
    return kept, dropped
