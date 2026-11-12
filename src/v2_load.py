"""Load extracted proposals into the separate v2 pending table, never promises."""

import argparse
from contextlib import closing
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.v2_database import APPLICATION_ID, SCHEMA_VERSION
from src.v2_evidence import is_allowlisted_url
from src.v2_extract import parse_extraction
from src.v2_sources import load_archived_metadata


def load_extraction(conn, *, root, promise_id, canonical_slug, source, response,
                    reopen_quarantined=False):
    """Load unverified proposals from saved material with their fetch metadata."""
    if conn.in_transaction or not conn.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("A dedicated connection with foreign keys enabled is required")
    if (not isinstance(canonical_slug, str)
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", canonical_slug)
            or not isinstance(source, dict)):
        raise ValueError("Invalid pending candidate input")
    metadata = load_archived_metadata(
        root, promise_id, source.get("metadata_path"), source.get("metadata_sha256")
    )
    expected = {"path", "sha256", "url", "requested_url", "published_at", "fetched_at"}
    if (set(metadata) != expected
            or any(metadata[key] != source.get(key) for key in expected)
            or not is_allowlisted_url(metadata["url"])
            or not is_allowlisted_url(metadata["requested_url"])
            or (metadata["published_at"] is not None
                and not isinstance(metadata["published_at"], str))):
        raise ValueError("Source provenance metadata does not match")
    try:
        fetched_at = datetime.fromisoformat(metadata["fetched_at"])
        if fetched_at.utcoffset() is None:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("Source fetch timestamp is invalid") from None
    candidates = parse_extraction(
        root=root, promise_id=promise_id, path=metadata["path"],
        digest=metadata["sha256"], response=response,
    )
    if not candidates:
        return []
    records = {}
    for candidate in candidates:
        proposal = json.dumps(candidate.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        material = json.dumps(
            [metadata["url"], metadata["sha256"], proposal], ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        records[hashlib.sha256(material).hexdigest()] = proposal
    timestamp = datetime.now(timezone.utc).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "INSERT INTO candidates (promise_id, canonical_slug) VALUES (?, ?) "
            "ON CONFLICT(promise_id) DO NOTHING", (promise_id, canonical_slug),
        )
        if conn.execute(
            "SELECT canonical_slug FROM candidates WHERE promise_id = ?", (promise_id,)
        ).fetchone()[0] != canonical_slug:
            raise ValueError("Candidate identity does not match")
        if conn.execute(
            "SELECT 1 FROM promises WHERE promise_id = ?", (promise_id,)
        ).fetchone():
            raise ValueError("Published candidate cannot be loaded as pending")
        for pending_id, proposal in records.items():
            conn.execute(
                """INSERT INTO promises_pending
                   (pending_id, promise_id, source_url, source_path, source_sha256,
                    metadata_path, metadata_sha256, proposal_json, loaded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(pending_id) DO NOTHING""",
                (pending_id, promise_id, metadata["url"], metadata["path"], metadata["sha256"],
                 source["metadata_path"], source["metadata_sha256"], proposal, timestamp),
            )
            previous = conn.execute(
                """SELECT promise_id, source_url, source_path, source_sha256,
                          metadata_path, metadata_sha256, proposal_json, status
                   FROM promises_pending WHERE pending_id = ?""", (pending_id,),
            ).fetchone()
            if (previous[0:4] != (promise_id, metadata["url"], metadata["path"], metadata["sha256"])
                    or previous[6] != proposal):
                raise ValueError("Pending proposal identity mismatch")
            if previous[7] != "pending":
                if previous[7] == "quarantined" and reopen_quarantined is True:
                    conn.execute(
                        "UPDATE promises_pending SET status='pending', quarantine_id=NULL "
                        "WHERE pending_id=? AND status='quarantined'", (pending_id,),
                    )
                else:
                    raise ValueError("Proposal has already been quarantined")
            saved_metadata = load_archived_metadata(root, promise_id, previous[4], previous[5])
            if any(saved_metadata.get(key) != metadata[key] for key in ("url", "path", "sha256")):
                raise ValueError("Pending source provenance mismatch")
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    return list(records)


def main():
    parser = argparse.ArgumentParser(description="Load saved extraction proposals into a v2 database")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--promise-id", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--metadata-sha256", required=True)
    parser.add_argument("--response", required=True, type=Path)
    args = parser.parse_args()
    metadata = load_archived_metadata(
        args.sources, args.promise_id, args.metadata, args.metadata_sha256
    )
    source = {**metadata, "metadata_path": str(args.metadata),
              "metadata_sha256": args.metadata_sha256}
    with args.response.open("rb") as file:
        response = file.read(128001)
    if len(response) > 128000:
        raise ValueError("Extraction response is too large")
    database_uri = args.database.resolve(strict=True).as_uri() + "?mode=rw"
    with closing(sqlite3.connect(database_uri, uri=True)) as conn:
        if (conn.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                or conn.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION):
            raise ValueError("Database is not an initialized, supported v2 database")
        conn.execute("PRAGMA foreign_keys = ON")
        identifiers = load_extraction(
            conn, root=args.sources, promise_id=args.promise_id, canonical_slug=args.slug,
            source=source, response=response.decode("utf-8"),
        )
    print(f"Loaded {len(identifiers)} unverified pending proposal(s).")


if __name__ == "__main__":
    main()
