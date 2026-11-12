"""Build a non-published candidate snapshot from a database."""

import argparse
from collections import Counter
from contextlib import closing
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from src.evidence import screen_saved_source
from src.relevance import evaluate_relevance
from src.sources import is_verbatim_quote
from src.taxonomy import screen_taxonomy
from src.temporal import check_origin_dates, screen_forward_looking


def _utc_datetime(value):
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        raise ValueError("Timestamp must include a timezone") from None


def _rows(conn, query, parameters=()):
    cursor = conn.execute(query, parameters)
    fields = [column[0] for column in cursor.description]
    return [dict(zip(fields, row)) for row in cursor.fetchall()]


def _date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(value).date()
        except (TypeError, ValueError):
            return None


def build_snapshot(conn, *, source_root, as_of):
    """Build a review-only snapshot; this does not authorize publication."""
    if not isinstance(as_of, datetime) or as_of.utcoffset() is None:
        raise ValueError("Snapshot time must include a timezone")
    if conn.in_transaction:
        raise ValueError("Snapshot requires a dedicated read transaction")
    as_of = as_of.astimezone(timezone.utc)
    conn.execute("BEGIN")
    try:
        promises = [
            row for row in _rows(
                conn, "SELECT * FROM promises ORDER BY date_promised DESC, promise_id"
            )
            if _utc_datetime(row["created_at"]) <= as_of
        ]
        for promise in promises:
            pid = promise["promise_id"]
            if screen_taxonomy(
                entity_name=promise["entity_name"], entity_type=promise["entity_type"],
                sector=promise["sector"], neighborhood=promise["neighborhood"],
                quote=promise["promise_text"],
            ):
                raise ValueError(f"Unverified taxonomy for {pid}")
            assessments = _rows(
                conn, "SELECT rowid AS seq, * FROM relevance_assessments WHERE promise_id = ?",
                (pid,),
            )
            applicable = []
            for assessment in assessments:
                timestamp = _utc_datetime(assessment["evaluated_at"])
                if timestamp <= as_of:
                    applicable.append((timestamp, assessment["seq"], assessment))
            if not applicable:
                raise ValueError(f"Missing relevance assessment for {pid}")
            assessment = max(applicable, key=lambda row: (row[0], row[1]))[2]
            try:
                inputs = json.loads(assessment["input_json"])
                relevance = evaluate_relevance(inputs["promise_text"], inputs["signals"])
                if (inputs["promise_text"] != promise["promise_text"]
                        or not relevance["publish"]
                        or any(assessment[key] != relevance[key] for key in
                               ("real_promise", "measurable", "sf_relevant", "interesting", "total"))
                        or assessment["passed"] != 1):
                    raise ValueError
            except (TypeError, KeyError, ValueError):
                raise ValueError(f"Invalid relevance assessment for {pid}") from None
            verdicts = _rows(conn, "SELECT * FROM verdicts WHERE promise_id = ?", (pid,))
            eligible = []
            for verdict in verdicts:
                timestamp = _utc_datetime(verdict["decided_at"])
                if timestamp <= as_of:
                    eligible.append((timestamp, verdict["verdict_id"], verdict))
            if not eligible:
                raise ValueError(f"No applicable verdict for {pid}")
            verdict = max(eligible, key=lambda row: (row[0], row[1]))[2]
            evidence = [
                row for row in _rows(
                    conn, "SELECT * FROM evidence_ledger WHERE promise_id = ? ORDER BY evidence_id",
                    (pid,),
                )
                if _utc_datetime(row["ingested_at"]) <= as_of
            ]
            promised = _date(promise["date_promised"])
            deadline = _date(promise["date_deadline"])
            if promised is None or promised > as_of.date():
                raise ValueError(f"Invalid promise date for {pid}")
            if not any(
                item["phase"] == "ORIGIN"
                and is_verbatim_quote(promise["promise_text"], item["verbatim_quote"])
                and not screen_forward_looking(promise["promise_text"])
                and not check_origin_dates(promised, _date(item["published_date"]), deadline)
                and _date(item["published_date"]) <= as_of.date()
                for item in evidence
            ):
                raise ValueError(f"Missing valid origin evidence for {pid}")
            for item in evidence:
                published = _date(item["published_date"])
                if published is None or published > as_of.date():
                    raise ValueError(f"Invalid evidence date for {pid}")
                failures = screen_saved_source(
                    root=source_root, promise_id=pid, path=item["local_source_path"],
                    digest=item["content_sha256"], quote=item["verbatim_quote"],
                    url=item["url"], source_tier=item["source_tier"],
                )
                if item["quote_verified"] != 1 or failures:
                    raise ValueError(f"Unverified evidence for {pid}")
            promise.update({
                "verdict": verdict["verdict"],
                "verdict_reason": verdict["reason"],
                "decided_at": verdict["decided_at"],
                "evidence": evidence,
                "relevance": relevance,
            })
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    return {
        "snapshot_kind": "candidate_not_published",
        "as_of": as_of.isoformat(),
        "promises": promises,
        "tallies": dict(sorted(Counter(row["verdict"] for row in promises).items())),
    }


def write_candidate_snapshot(conn, *, source_root, as_of, output):
    """Write a new review-only JSON file outside the live site; never overwrite."""
    target = Path(output)
    if target.suffix != ".json":
        raise ValueError("Candidate output must be JSON")
    docs = (Path(__file__).resolve().parents[1] / "docs").resolve()
    parent = target.parent.resolve(strict=True)
    if parent == docs or docs in parent.parents:
        raise ValueError("Candidate output must be outside the live site")
    target = parent / target.name
    snapshot = build_snapshot(conn, source_root=source_root, as_of=as_of)
    content = (json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, delete=False) as file:
            temporary_path = file.name
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.link(temporary_path, target)
    finally:
        if temporary_path is not None:
            os.unlink(temporary_path)
    return target


def main():
    parser = argparse.ArgumentParser(description="Export a review-only candidate snapshot")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--as-of", type=datetime.fromisoformat, default=None)
    args = parser.parse_args()
    database_uri = args.database.resolve(strict=True).as_uri() + "?mode=ro"
    with closing(sqlite3.connect(database_uri, uri=True)) as conn:
        output = write_candidate_snapshot(
            conn, source_root=args.sources, as_of=args.as_of or datetime.now(timezone.utc),
            output=args.output,
        )
    print(f"Review-only snapshot written to {output}")


if __name__ == "__main__":
    main()
