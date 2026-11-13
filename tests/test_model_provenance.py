"""Model provenance: fulfilled model calls persist model_id in verifications.

Legacy rows (written before provenance) read back as an explicit NULL.
"""
import asyncio
import json
import sqlite3
from datetime import date
from types import SimpleNamespace

from src.candidate import audit_candidate
from src.database import initialize_database
from src.discovery import fetch_and_archive
from src.agent_lane import AGENT_MODEL_ID as MODEL_ID


def test_verification_rows_persist_lane_model_id(tmp_path):
    asyncio.run(_verification_rows_persist_lane_model_id(tmp_path))


def test_legacy_rows_read_back_as_null(tmp_path):
    database = tmp_path / "legacy.db"
    initialize_database(database)
    with sqlite3.connect(database) as conn:
        conn.execute(
            "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at) "
            "VALUES ('P00', 'deterministic', 1, 'pre-provenance row', '2020-01-01T00:00:00')"
        )
        model_id, = conn.execute("SELECT model_id FROM verifications").fetchone()
    assert model_id is None


def test_schema_default_leaves_model_id_null_for_deterministic_checks(tmp_path):
    database = tmp_path / "default.db"
    initialize_database(database)
    with sqlite3.connect(database) as conn:
        conn.execute(
            "INSERT INTO promises (promise_id, entity_name, entity_type, sector, neighborhood, "
            "promise_text, date_promised, date_deadline, created_at) VALUES "
            "('P00', 'San Francisco', 'City Agency', 'Governance & Finance', 'Citywide', 't', "
            "'2020-01-01', '2022-12-31', '2020-01-01T00:00:00')"
        )
        conn.execute(
            "INSERT INTO verifications (promise_id, check_type, passed, reason, checked_at) "
            "VALUES ('P00', 'quote_snapback', 1, 'ok', '2020-01-01T00:00:00')"
        )
        model_id, = conn.execute("SELECT model_id FROM verifications").fetchone()
    assert model_id is None


async def _verification_rows_persist_lane_model_id(tmp_path):
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
    names = []

    async def complete(messages, *, tools, tool_choice, **_kwargs):
        name = tool_choice["function"]["name"]
        names.append(name)
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
            result = {"action": True, "promise_date": True, "deadline": True,
                      "explanation": "Supported by the origin."}
        elif name == "verify_evidence":
            result = {
                "action": True, "promise_date": True, "deadline": True,
                "delivery": True, "survival": True, "entity_and_location": True,
                "explanation": "Verified from the archived text.",
            }
        else:
            raise AssertionError(name)
        return {"model": MODEL_ID, "choices": [{"message": {"tool_calls": [{"function": {
            "name": name, "arguments": json.dumps(result),
        }}]}}]}

    with sqlite3.connect(database) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        result = await audit_candidate(
            conn, root=root, staging_root=tmp_path / "staging", lead=lead,
            research=research, complete=complete, as_of=date(2026, 11, 11),
        )
        assert result["status"] == "published"
        rows = conn.execute(
            "SELECT check_type, model_id FROM verifications ORDER BY check_type"
        ).fetchall()
    judged = [(check, model_id) for check, model_id in rows
              if check != "preliminary_source"]
    # Deterministic checks (e.g. preliminary_source) carry no model identity.
    assert {check for check, _ in rows} == {
        "advocate_broken", "advocate_kept", "independent_verifier", "origin_verifier",
        "preliminary_source",
    }
    assert len(judged) == 4
    assert {check for check, _ in judged} == {
        "advocate_broken", "advocate_kept", "independent_verifier", "origin_verifier",
    }
    assert all(model_id == MODEL_ID for _, model_id in judged)
    # Every model-judgment stage emitted a call that the lane responded to.
    assert names.count("assess_outcome") == 2
    assert names.count("verify_origin") == 1
    assert names.count("verify_evidence") == 1
