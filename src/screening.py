"""Offline preliminary origin screening, without publication authority."""

import hashlib
import json
from datetime import date, datetime

from pydantic import ValidationError

from src.evidence import _government_host, is_allowlisted_url, screen_saved_source
from src.extract import Candidate
from src.quarantine import quarantine_candidate
from src.sources import load_archived_metadata
from src.temporal import check_origin_dates, screen_forward_looking


def screen_pending_origin(conn, *, root, pending_id, source_tier, search_exhausted):
    """Screen a stored proposal; caller-provided tier and dates still need review."""
    if conn.in_transaction:
        raise ValueError("Screening requires a dedicated connection")
    row = conn.execute(
        """SELECT p.promise_id, c.canonical_slug, p.source_url, p.source_path,
                  p.source_sha256, p.metadata_path, p.metadata_sha256, p.proposal_json, p.status
           FROM promises_pending p JOIN candidates c ON c.promise_id = p.promise_id
           WHERE p.pending_id = ?""", (pending_id,),
    ).fetchone()
    if row is None or row[8] != "pending":
        raise ValueError("Pending proposal not found")
    promise_id, slug, url, path, digest, metadata_path, metadata_sha, proposal, _ = row

    def failed(reason):
        if search_exhausted is True:
            quarantine_candidate(
                conn, promise_id, slug, "origin", [reason],
                {"promise_id": promise_id, "canonical_slug": slug},
            )
            status = "quarantined"
        else:
            status = "retry_discovery"
        return {"status": status, "failures": [reason]}

    material = json.dumps([url, digest, proposal], ensure_ascii=False, separators=(",", ":"))
    try:
        candidate = Candidate.model_validate_json(proposal)
        if (candidate.promise_id != promise_id
                or hashlib.sha256(material.encode("utf-8")).hexdigest() != pending_id):
            raise ValueError
    except (TypeError, ValueError, ValidationError):
        return failed("pending_proposal_invalid")
    try:
        metadata = load_archived_metadata(root, promise_id, metadata_path, metadata_sha)
        expected = {"path", "sha256", "url", "requested_url", "published_at", "fetched_at"}
        if (set(metadata) != expected or metadata["path"] != path
                or metadata["sha256"] != digest or metadata["url"] != url
                or not is_allowlisted_url(metadata["requested_url"])):
            raise ValueError
        fetched = datetime.fromisoformat(metadata["fetched_at"])
        if fetched.utcoffset() is None:
            raise ValueError
    except (TypeError, ValueError):
        return failed("source_metadata_invalid")
    try:
        published = date.fromisoformat(metadata["published_at"])
    except (TypeError, ValueError):
        try:
            published = datetime.fromisoformat(metadata["published_at"]).date()
        except (TypeError, ValueError):
            published = None
    return screen_origin(
        conn=conn, root=root, promise_id=promise_id, canonical_slug=slug,
        source={"path": path, "digest": digest, "quote": candidate.promise_text,
                "url": url, "source_tier": source_tier},
        promised=candidate.promised_date, published=published, deadline=candidate.deadline,
        search_exhausted=search_exhausted,
    )


def screen_origin(*, conn, root, promise_id, canonical_slug, source,
                  promised, published, deadline, search_exhausted):
    """Screen a saved source. A passing result still requires full review.

    The caller must attest that bounded rediscovery was attempted before
    setting search_exhausted. Historical official claims need separate review.
    """
    failures = screen_saved_source(
        root=root, promise_id=promise_id, path=source.get("path"),
        digest=source.get("digest"), quote=source.get("quote"),
        url=source.get("url"), source_tier=source.get("source_tier"),
    )
    failures.extend(screen_forward_looking(source.get("quote")))
    temporal = check_origin_dates(promised, published, deadline)
    historical_review = (
        source.get("source_tier") == "TIER1_GOV"
        and _government_host(source.get("url"))
        and "origin_publication_late" in temporal
    )
    if historical_review:
        temporal.remove("origin_publication_late")
    failures.extend(temporal)
    if failures:
        if search_exhausted is True:
            quarantine_candidate(
                conn, promise_id, canonical_slug, "origin", failures,
                {"promise_id": promise_id, "canonical_slug": canonical_slug},
            )
            status = "quarantined"
        else:
            status = "retry_discovery"
        return {"status": status, "failures": failures}
    if historical_review:
        return {"status": "review_required", "failures": ["historical_origin_requires_review"]}
    return {"status": "review_required", "failures": []}
