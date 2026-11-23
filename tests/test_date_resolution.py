"""Date resolution (SF_PROMISES_DATE_RESOLUTION): resolver, audit and mutations."""

import asyncio
import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.candidate import audit_candidate
from src.database import initialize_database
from src.date_resolution import (
    FLAG, date_resolution_enabled, resolve_promise_date, resolve_promise_date_detail,
)
from src.discovery import fetch_and_archive
from src.export import build_snapshot
from src.extract import _source_segments

PUBLISHED = date(2025, 1, 15)  # a Wednesday


def resolve(segments, index, published=PUBLISHED):
    return resolve_promise_date(segments, index, published)


# --- stated ---------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("The mayor said on November 10, 2024 the city will open beds.", date(2024, 11, 10)),
    ("The mayor said on Nov. 10, 2024 the city will open beds.", date(2024, 11, 10)),
    ("The mayor said on 10 November 2024 the city will open beds.", date(2024, 11, 10)),
    ("The mayor said on 2024-11-10 the city will open beds.", date(2024, 11, 10)),
    ("The mayor said on 11/10/2024 the city will open beds.", date(2024, 11, 10)),
    ("The mayor said on Sept. 3rd, 2024 the city will open beds.", date(2024, 9, 3)),
])
def test_stated_formats(text, expected):
    assert resolve([text], 0) == (expected, "stated")


def test_stated_date_in_segments_before_quote():
    segments = ["On November 10, 2024 the mayor spoke", "Housing was discussed",
                "The city will open 100 beds by 2026."]
    assert resolve(segments, 2) == (date(2024, 11, 10), "stated")


def test_stated_date_split_by_abbreviation_period():
    segments = _source_segments("Mayor Lurie said on Nov. 10, 2024 the city will open 100 beds by 2026.")
    assert len(segments) == 2
    assert resolve(segments, 1) == (date(2024, 11, 10), "stated")


def test_dateline_at_top_of_document():
    segments = ["SAN FRANCISCO November 10, 2024"] + [f"Filler {i}" for i in range(6)] \
        + ["The city will open 100 beds by 2026."]
    assert resolve(segments, 7) == (date(2024, 11, 10), "stated")


def test_dateline_after_five_segments_is_not_a_dateline():
    segments = [f"Filler {i}" for i in range(5)] + ["November 10, 2024"] \
        + ["Filler"] * 3 + ["The city will open 100 beds by 2026."]
    assert resolve(segments, 9) == (PUBLISHED, "publication")


def test_stated_date_after_published_is_ignored():
    assert resolve(["On January 20, 2025 the city will open beds."], 0) == (PUBLISHED, "publication")


def test_stated_beats_relative():
    assert resolve(["On Tuesday, November 10, 2024 the city said it will open beds."], 0) \
        == (date(2024, 11, 10), "stated")


def test_deadline_date_is_not_the_promise_date():
    segments = ["The city will open the shelter by March 1, 2025."]
    assert resolve(segments, 0, date(2025, 6, 1)) == (date(2025, 6, 1), "publication")


def test_two_different_dates_in_one_place_are_ambiguous():
    segments = ["Since June 1, 2024 and on July 2, 2024 the city said it will open beds."]
    assert resolve(segments, 0) == (PUBLISHED, "publication")


# --- relative -------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("The city said today it will open beds.", PUBLISHED),
    ("The mayor said this morning the city will open beds.", PUBLISHED),
    ("The mayor said tonight the city will open beds.", PUBLISHED),
    ("The mayor said yesterday the city will open beds.", date(2025, 1, 14)),
    ("The mayor said on Tuesday the city will open beds.", date(2025, 1, 14)),
    ("The mayor said Monday the city will open beds.", date(2025, 1, 13)),
    ("The mayor said last Tuesday the city will open beds.", date(2025, 1, 14)),
    ("The mayor said on Thursday the city will open beds.", date(2025, 1, 9)),
])
def test_relative_terms(text, expected):
    assert resolve([text], 0) == (expected, "relative")


def test_weekday_equal_to_published_weekday_is_same_day():
    assert resolve(["The mayor said on Wednesday the city will open beds."], 0) \
        == (PUBLISHED, "relative")


def test_last_weekday_is_strictly_before_published():
    assert resolve(["The mayor said last Wednesday the city will open beds."], 0) \
        == (date(2025, 1, 8), "relative")


def test_last_weekday_matches_bare_weekday_only_when_different():
    tuesday = date(2025, 1, 14)
    assert resolve(["She said on Tuesday the city will open beds."], 0, tuesday) \
        == (tuesday, "relative")
    assert resolve(["She said last Tuesday the city will open beds."], 0, tuesday) \
        == (date(2025, 1, 7), "relative")


def test_relative_term_in_segment_before_quote():
    segments = ["The mayor spoke on Tuesday", "Housing came up", "The city will open 100 beds."]
    assert resolve(segments, 2) == (date(2025, 1, 14), "relative")


def test_relative_term_three_segments_back_is_ignored():
    segments = ["The mayor spoke yesterday", "A", "B", "The city will open 100 beds."]
    assert resolve(segments, 3) == (PUBLISHED, "publication")


@pytest.mark.parametrize("text", [
    "The city will open beds next Tuesday.",
    "The city will open beds by Friday.",
    "The city will open beds this Friday.",
    "The city will open beds every Tuesday.",
    "The city will open beds on Tuesdays.",
])
def test_forward_or_recurring_weekdays_are_not_resolved(text):
    assert resolve([text], 0) == (PUBLISHED, "publication")


def test_relative_phrase_is_reported():
    detail = resolve_promise_date_detail(["She said on Tuesday the city will open beds."], 0, PUBLISHED)
    assert detail.phrase == "on Tuesday"
    assert detail.derived
    assert detail.describe(PUBLISHED) == (
        "derived: 'on Tuesday' resolved against publication date 2025-01-15")


@pytest.mark.parametrize("weekday_offset", range(14))
def test_weekday_resolution_never_after_published_and_within_a_week(weekday_offset):
    published = date(2025, 1, 1) + timedelta(days=weekday_offset)
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for weekday, name in enumerate(names):
        value, basis = resolve([f"She said on {name} the city will open beds."], 0, published)
        assert basis == "relative" and value.weekday() == weekday
        assert 0 <= (published - value).days <= 6
        value, _ = resolve([f"She said last {name} the city will open beds."], 0, published)
        assert value.weekday() == weekday and 1 <= (published - value).days <= 7


# --- publication, vague terms, invalid input ------------------------------

@pytest.mark.parametrize("text", [
    "The city said last year it will open beds.",
    "The city recently said it will open beds.",
    "The city said earlier this month it will open beds.",
    "The city said this week it will open beds.",
    "The city will open beds.",
])
def test_vague_terms_fall_back_to_publication(text):
    assert resolve([text], 0) == (PUBLISHED, "publication")


def test_unknown_quote_index_uses_publication():
    assert resolve(["The city will open beds."], None) == (PUBLISHED, "publication")
    assert resolve(["The city will open beds."], 5) == (PUBLISHED, "publication")


@pytest.mark.parametrize("published", [None, "2025-01-15", datetime(2025, 1, 15), 20250115])
def test_missing_or_invalid_published_returns_none(published):
    assert resolve(["She said on Tuesday the city will open beds."], 0, published) == (None, None)
    assert resolve_promise_date_detail(["x"], 0, published) is None


def test_flag_reads_environment(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    assert not date_resolution_enabled()
    for value in ("0", "", "true"):
        monkeypatch.setenv(FLAG, value)
        assert not date_resolution_enabled()
    monkeypatch.setenv(FLAG, "1")
    assert date_resolution_enabled()


# --- audit ----------------------------------------------------------------

ORIGINS = {
    "relative": ("On Tuesday, San Francisco will build the library by 2022.",
                 date(2019, 12, 31), "relative"),
    "publication": ("San Francisco will build the library by 2022.",
                    date(2020, 1, 2), "publication"),
}


async def _run_audit(tmp_path, origin_text):
    database = tmp_path / "candidate.db"
    initialize_database(database)
    root = tmp_path / "sources"
    documents = {
        "https://sf.gov/origin": (origin_text, "2020-01-02"),  # a Thursday
        "https://sf.gov/delivery": ("The San Francisco library opened in 2022.", "2022-12-31"),
        "https://sf.gov/survival": ("The San Francisco library remains open in 2026.", "2026-01-01"),
    }

    class Search:
        async def fetch(self, url):
            text, published = documents[url]
            return SimpleNamespace(url=url, content=text, published_at=published,
                                   raw={"truncated": False})

    sources = [await fetch_and_archive(Search(), url, root, "P99") for url in documents]
    research = {"phases": {
        "origin": {"sources": sources[:1], "blocked": []},
        "delivery": {"sources": sources[1:2], "blocked": []},
        "survival": {"sources": sources[2:], "blocked": []},
    }}
    lead = {"promise_id": "P99", "promise_text": "San Francisco library",
            "entity": "San Francisco", "promised_date": None, "due_date": "2022-12-31"}
    prompts = {}
    calls = []

    async def complete(messages, *, tools, tool_choice, **_kwargs):
        name = tool_choice["function"]["name"]
        calls.append(name)
        prompts.setdefault(name, []).append(messages)
        if name == "record_promise_evidence":
            result = {"candidates": [{
                "promise_id": "P99", "quote_segment_id": 0, "speaker": "San Francisco",
                "promised_date": None, "deadline": "2022-12-31",
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
            result = {"action": True, "promise_date": True, "deadline": True,
                      "delivery": True, "survival": True, "entity_and_location": True,
                      "explanation": "Verified from the archived text."}
        else:
            raise AssertionError(name)
        return {"choices": [{"message": {"tool_calls": [{"function": {
            "name": name, "arguments": json.dumps(result),
        }}]}}]}

    conn = sqlite3.connect(database)
    conn.execute("PRAGMA foreign_keys=ON")
    result = await audit_candidate(
        conn, root=root, staging_root=tmp_path / "staging", lead=lead,
        research=research, complete=complete, as_of=date(2026, 11, 11),
    )
    return conn, root, result, calls, prompts


@pytest.mark.parametrize("kind", ["relative", "publication"])
def test_audit_with_flag_derives_date_and_passes_origin(tmp_path, monkeypatch, kind):
    text, expected, basis = ORIGINS[kind]
    monkeypatch.setenv(FLAG, "1")
    conn, root, result, calls, prompts = asyncio.run(_run_audit(tmp_path, text))
    with conn:
        assert result["status"] == "published"
        assert calls.count("record_promise_evidence") == 1  # no retry needed
        assert conn.execute("SELECT date_promised FROM promises").fetchone()[0] == expected.isoformat()
        assert conn.execute("SELECT count(*) FROM evidence_ledger WHERE phase='ORIGIN' "
                            "AND quote_verified=1").fetchone()[0] == 1
        row = conn.execute("SELECT passed, reason FROM verifications "
                           "WHERE check_type='promise_date_basis'").fetchone()
        assert row[0] == 1 and json.loads(row[1])["basis"] == basis
        origin_user = prompts["verify_origin"][0][1]["content"]
        evidence_user = prompts["verify_evidence"][0][1]["content"]
        assert "derived" in origin_user and "derived" in evidence_user
        if kind == "relative":
            assert ("derived: 'on Tuesday' resolved against publication date 2020-01-02"
                    in origin_user)
        else:
            assert "derived: publication date of the source" in origin_user
        assert "accept it if the source publication date" in prompts["verify_origin"][0][0]["content"]
        assert "accept it if the source publication date" in prompts["verify_evidence"][0][0]["content"]
        snapshot = build_snapshot(
            conn, source_root=root, as_of=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
    exported = snapshot["promises"][0]
    assert exported["promise_date_basis"] == basis
    assert exported["promise_date_derived"] is True
    assert "derived" in exported["promise_date_note"]
    conn.close()


@pytest.mark.parametrize("kind", ["relative", "publication"])
def test_audit_without_flag_quarantines_as_before(tmp_path, monkeypatch, kind):
    monkeypatch.delenv(FLAG, raising=False)
    conn, _root, result, calls, prompts = asyncio.run(_run_audit(tmp_path, ORIGINS[kind][0]))
    with conn:
        assert result == {"promise_id": "P99", "status": "quarantined",
                          "reason": "INVALID_PROMISE_DATE_LATER_THAN_SOURCE"}
        assert calls == ["record_promise_evidence"] * 2  # retried once, still null
        assert "verify_origin" not in prompts
        assert conn.execute("SELECT count(*) FROM promises").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM verifications "
                            "WHERE check_type='promise_date_basis'").fetchone()[0] == 0
    conn.close()


def test_derived_date_still_needs_origin_verifier_and_quote(tmp_path, monkeypatch):
    """A verifier that rejects the derived date quarantines the candidate."""
    monkeypatch.setenv(FLAG, "1")

    async def run():
        from src import candidate as module
        original = module._structured

        async def reject_origin(complete, name, schema, system, content):
            if name == "verify_origin":
                value, model = await original(complete, name, schema, system, content)
                return value.model_copy(update={"promise_date": False}), model
            return await original(complete, name, schema, system, content)

        monkeypatch.setattr(module, "_structured", reject_origin)
        return await _run_audit(tmp_path, ORIGINS["relative"][0])

    conn, _root, result, _calls, _prompts = asyncio.run(run())
    with conn:
        assert result["status"] == "quarantined"
        assert conn.execute("SELECT count(*) FROM promises").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM verdicts").fetchone()[0] == 0
    conn.close()


# --- adversarial mutations with the flag on -------------------------------

def test_adversarial_mutations_with_flag_on(monkeypatch):
    from tests.test_adversarial_mutations import test_adversarial_mutations_false_accept_rate
    monkeypatch.setenv(FLAG, "1")
    test_adversarial_mutations_false_accept_rate()
