import asyncio
import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.v2_database import initialize_database
from src.v2_discovery import fetch_and_archive
from src.v2_candidate import audit_candidate
from src.v2_export import build_snapshot
from src.v2_model import ModelResponseError
from src.v2_run_live import candidate_batch


@pytest.mark.parametrize("supported", [True, False])
def test_candidate_requires_independent_entailment(tmp_path, supported):
    asyncio.run(_candidate_requires_independent_entailment(tmp_path, supported))


def test_unverified_origin_date_retries_then_quarantines(tmp_path):
    asyncio.run(_candidate_requires_independent_entailment(tmp_path, True, invalid_date=True))


def test_verdict_write_failure_rolls_back_promise(tmp_path):
    asyncio.run(_candidate_requires_independent_entailment(tmp_path, True, reject_write=True))


@pytest.mark.parametrize("reject_worker", [True, False])
def test_candidate_requires_worker_gate_before_commit(tmp_path, reject_worker):
    asyncio.run(_candidate_requires_independent_entailment(
        tmp_path, True, use_worker=True, reject_worker=reject_worker,
    ))


def test_batch_continues_after_malformed_model_output(tmp_path, monkeypatch):
    async def discover(_database, pid, _run_id):
        return {"results": [{"promise_id": pid, "phases": {
            "origin": {"sources": ["source"], "blocked": []},
            "delivery": {"sources": ["source"], "blocked": []},
            "survival": {"sources": [], "blocked": []},
        }}]}

    async def audit(_conn, *, lead, **_kwargs):
        if lead["promise_id"] == "P01":
            raise ModelResponseError("Malformed response")
        return {"promise_id": lead["promise_id"], "status": "quarantined"}

    monkeypatch.setattr("src.v2_run_live.credentials", lambda: {
        "OPENROUTER_API_KEY": "test", "KEENABLE_API_KEY": "test",
    })
    monkeypatch.setattr("src.v2_run_live.discover_run", discover)
    monkeypatch.setattr("src.v2_run_live.audit_in_sandbox", audit)
    results = asyncio.run(candidate_batch(tmp_path / "candidates.db", ["P01", "P03"]))
    assert [row["status"] for row in results] == ["blocked", "quarantined"]


async def _candidate_requires_independent_entailment(
    tmp_path, supported, *, invalid_date=False, reject_write=False,
    use_worker=False, reject_worker=False,
):
    database = tmp_path / "candidate.db"
    initialize_database(database)
    root = tmp_path / "sources"
    documents = {
        "https://sf.gov/origin": (
            "January 1, 2020. San Francisco will build the library by 2022.",
            "2020-01-01",
        ),
        "https://sf.gov/delivery": (
            "The San Francisco library opened in 2022.", "2022-12-31",
        ),
        "https://sf.gov/survival": (
            "The San Francisco library remains open in 2026.", "2026-01-01",
        ),
    }

    class Search:
        async def fetch(self, url):
            text, published = documents[url]
            return SimpleNamespace(
                url=url, content=text, published_at=published, raw={"truncated": False},
            )

    sources = [await fetch_and_archive(Search(), url, root, "P99") for url in documents]
    research = {"phases": {
        "origin": {"sources": sources[:1], "blocked": []},
        "delivery": {"sources": sources[1:2], "blocked": []},
        "survival": {"sources": sources[2:], "blocked": []},
    }}
    lead = {"promise_id": "P99", "promise_text": "San Francisco library",
            "entity": "San Francisco", "promised_date": "2020-01-01",
            "due_date": "2022-12-31"}
    calls = []

    async def complete(messages, *, tools, tool_choice, **_kwargs):
        name = tool_choice["function"]["name"]
        calls.append(name)
        if name == "record_promise_evidence":
            result = {"candidates": [{
                "promise_id": "P99", "quote_segment_id": 1, "speaker": "San Francisco",
                "promised_date": "2020-01-01", "deadline": "2022-12-31",
            }]}
        elif name == "assess_outcome":
            result = {
                "initial_delivery": "DELIVERED_ON_TIME",
                "current_survival": "ACTIVE_OPERATIONAL",
                "delivery": {"source_index": 0, "segment_id": 0},
                "survival": {"source_index": 1, "segment_id": 0},
                "entity_name": "San Francisco", "entity_type": "City Agency",
                "sector": "Governance & Finance", "neighborhood": "Citywide",
            }
        elif name == "verify_origin":
            result = {"action": True, "promise_date": not invalid_date, "deadline": True,
                      "explanation": "Supported by the origin."}
        elif name == "verify_evidence":
            result = {
                "action": supported, "promise_date": True, "deadline": True,
                "delivery": True, "survival": True, "entity_and_location": True,
                "explanation": "Verified from the archived text." if supported else "Ambiguous action.",
            }
        else:
            raise AssertionError(name)
        return {"choices": [{"message": {"tool_calls": [{"function": {
            "name": name, "arguments": json.dumps(result),
        }}]}}]}

    with sqlite3.connect(database) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        worker_calls = []

        async def worker_gate(evidence, origin):
            worker_calls.append((evidence, origin))
            if reject_worker:
                raise ValueError("worker rejected evidence")

        if reject_write:
            conn.execute(
                "CREATE TRIGGER reject_verdict BEFORE INSERT ON verdicts "
                "BEGIN SELECT RAISE(ABORT, 'rejected'); END"
            )
            conn.commit()
        if reject_write:
            with pytest.raises(sqlite3.IntegrityError):
                await audit_candidate(
                    conn, root=root, staging_root=tmp_path / "staging", lead=lead,
                    research=research, complete=complete, as_of=date(2026, 11, 11),
                )
            assert conn.execute("SELECT count(*) FROM promises").fetchone()[0] == 0
            assert conn.execute("SELECT count(*) FROM verdicts").fetchone()[0] == 0
            assert conn.execute("SELECT status FROM promises_pending").fetchone()[0] == "pending"
            return
        if reject_worker:
            with pytest.raises(ValueError, match="worker rejected"):
                await audit_candidate(
                    conn, root=root, staging_root=tmp_path / "staging", lead=lead,
                    research=research, complete=complete, as_of=date(2026, 11, 11),
                    worker_gate=worker_gate,
                )
            assert len(worker_calls) == 1
            assert conn.execute("SELECT count(*) FROM promises").fetchone()[0] == 0
            return
        result = await audit_candidate(
            conn, root=root, staging_root=tmp_path / "staging", lead=lead,
            research=research, complete=complete, as_of=date(2026, 11, 11),
            worker_gate=worker_gate if use_worker else None,
        )
        if use_worker:
            assert len(worker_calls) == 1
            assert len(worker_calls[0][0]) == 3
        if invalid_date:
            assert result["status"] == "quarantined"
            assert result["reason"] == "INVALID_PROMISE_DATE_LATER_THAN_SOURCE"
            assert conn.execute("SELECT status FROM promises_pending").fetchone()[0] == "quarantined"
            assert calls.count("record_promise_evidence") == 2
            assert calls.count("verify_origin") == 2
            invalid_date = False
            retried = await audit_candidate(
                conn, root=root, staging_root=tmp_path / "staging", lead=lead,
                research=research, complete=complete, as_of=date(2026, 11, 11),
                retry_quarantined=True,
            )
            assert retried["status"] == "published"
            assert conn.execute("SELECT status FROM promises_pending").fetchone()[0] == "published"
            assert conn.execute("SELECT count(*) FROM quarantined").fetchone()[0] == 1
            return
        if supported:
            assert result["status"] == "published"
            assert conn.execute("SELECT verdict FROM verdicts").fetchone()[0] == "KEPT"
            assert conn.execute("SELECT count(*) FROM evidence_ledger").fetchone()[0] == 3
            assert conn.execute("SELECT status FROM promises_pending").fetchone()[0] == "published"
            snapshot = build_snapshot(
                conn, source_root=root, as_of=datetime(2030, 1, 1, tzinfo=timezone.utc),
            )
            assert snapshot["tallies"] == {"KEPT": 1}
        else:
            assert result["status"] == "quarantined"
            assert conn.execute("SELECT count(*) FROM promises").fetchone()[0] == 0
            assert conn.execute("SELECT count(*) FROM quarantined").fetchone()[0] == 1
        assert calls.count("assess_outcome") == 2
        assert calls.count("verify_evidence") >= 1
