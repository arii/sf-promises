"""Recovery rules under SF_PROMISES_OUTCOME_RULES=1: full-sentence quotes, wider
date lookup, and the "Not stated" location."""

import copy
import json
import sqlite3
from datetime import date

import pytest

from src.date_resolution import resolve_promise_date, resolve_promise_date_detail
from src.outcome_rules import FLAG
from src.sentences import display_sentence, sentence_span
from src.sources import is_verbatim_quote
from src.taxonomy import LOCATIONS, screen_taxonomy
from tests.test_outcome_rules import AS_OF, DATE_FLAG, run
from tests.test_export_v2_merge import ROOT, make_v2, run_merge


@pytest.fixture
def rules_on(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.delenv(DATE_FLAG, raising=False)


@pytest.fixture
def rules_off(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    monkeypatch.delenv(DATE_FLAG, raising=False)


# --- sentence_span ------------------------------------------------------------

BUILDINGS = "Of the 4,915 buildings, 4,648 (94%) have completed retrofits. The rest are pending."


def test_sentence_span_is_a_raw_exact_substring():
    quote = "4,648 (94%)"
    start, end = sentence_span(BUILDINGS, quote)
    assert BUILDINGS[start:end] == "Of the 4,915 buildings, 4,648 (94%) have completed retrofits."
    assert is_verbatim_quote(BUILDINGS[start:end], BUILDINGS)


def test_sentence_span_keeps_raw_line_breaks_but_display_collapses():
    text = "Intro.\n\nThe city will open\n  three clinics by\n2030 in total.\n\nNext."
    quote = "three clinics by"
    start, end = sentence_span(text, quote)
    assert text[start:end] == "The city will open\n  three clinics by\n2030 in total."
    assert display_sentence(text, quote) == "The city will open three clinics by 2030 in total."


def test_sentence_span_strips_bullets_and_respects_cap_and_missing():
    assert sentence_span("- The city will open clinics.", "city will") == (2, 29)
    assert sentence_span("Nothing here.", "absent") is None
    assert sentence_span("word " * 200 + "the quote " + "word " * 200, "the quote") is None


# --- audit: fragments are widened --------------------------------------------

ORIGIN_FRAGMENT = ("Mayor Lee said on Mar. 1, 2024 that San Francisco will open 3 new "
                   "neighborhood clinics by 2030.")
WIDE_ORIGIN = ORIGIN_FRAGMENT


def _origin_kwargs():
    return dict(origin_text=ORIGIN_FRAGMENT, origin_published="2024-03-01",
                promised="2024-03-01", deadline="2030-12-31")


def _evidence(conn):
    return {phase: quote for phase, quote in conn.execute(
        "SELECT phase, verbatim_quote FROM evidence_ledger")}


def test_fragment_origin_is_widened_to_the_full_sentence(tmp_path, rules_on):
    conn, _root, result, prompts = run(tmp_path, **_origin_kwargs())
    assert result["status"] == "published", result
    # The extraction fake picks segment 0, "Mayor Lee said on Mar.".
    assert _evidence(conn)["ORIGIN"] == WIDE_ORIGIN
    assert conn.execute("SELECT promise_text FROM promises").fetchone() == (WIDE_ORIGIN,)
    assert conn.execute("SELECT quote_verified FROM evidence_ledger").fetchone() == (1,)
    assert f"Proposed commitment: {WIDE_ORIGIN}" in prompts["verify_origin"][0][1]["content"]
    conn.close()


def test_fragment_origin_is_unchanged_with_the_flag_off(tmp_path, rules_off):
    conn, _root, result, _prompts = run(tmp_path, **_origin_kwargs())
    # flag off: the fragment stays a fragment (and is not published as a full sentence)
    assert [row[0] for row in conn.execute("SELECT promise_text FROM promises")] in (
        [], ["Mayor Lee said on Mar."])
    assert WIDE_ORIGIN not in _evidence(conn).values()
    conn.close()


OUTCOME_FRAGMENT = ("On Mar. 4, 2024 the city said that of the 3 clinics, 3 (100%) have opened and "
                    "are serving patients. Hours vary.")
OUTCOME_FULL = ("On Mar. 4, 2024 the city said that of the 3 clinics, 3 (100%) have opened and "
                "are serving patients.")


def test_fragment_outcome_is_widened_and_verbatim(tmp_path, rules_on):
    conn, root, result, prompts = run(
        tmp_path,
        origin_text="On March 5, 2024, San Francisco will open 3 new neighborhood clinics.",
        origin_published="2024-03-01", promised="2024-03-01", deadline="2024-03-05",
        outcome=[(OUTCOME_FRAGMENT, "2024-03-04")],
        # segments: [0] "On Mar." [1] "4, 2024 the city said ... patients." [2] "Hours vary."
        assessment={"initial_delivery": "DELIVERED_ON_TIME",
                    "delivery": {"source_index": 0, "segment_id": 1}},
        review={"delivery": True},
    )
    assert result == {"promise_id": "P99", "status": "published", "verdict": "KEPT"}
    assert _evidence(conn)["DELIVERY"] == OUTCOME_FULL
    assert conn.execute("SELECT quote_verified FROM evidence_ledger "
                        "WHERE phase='DELIVERY'").fetchone() == (1,)
    assert OUTCOME_FULL in prompts["verify_evidence"][0][1]["content"]
    conn.close()


def test_fragment_outcome_is_unchanged_with_the_flag_off(tmp_path, rules_off):
    selection = {"source_index": 0, "segment_id": 1}
    conn, _root, result, _prompts = run(
        tmp_path,
        origin_text="On March 1, 2024 the mayor said San Francisco will open 3 new "
                    "neighborhood clinics by 2030.",
        origin_published="2024-03-01", promised="2024-03-01", deadline="2030-12-31",
        outcome=[(OUTCOME_FRAGMENT, "2024-03-04")],
        assessment={"initial_delivery": "DELIVERED_ON_TIME", "current_survival": "ACTIVE_OPERATIONAL",
                    "delivery": selection, "survival": selection},
        review={"delivery": True, "survival": True},
    )
    assert result["status"] == "published", result
    assert _evidence(conn)["DELIVERY"] == "4, 2024 the city said that of the 3 clinics, 3 (100%) " \
        "have opened and are serving patients."
    conn.close()


# --- date resolution: paragraph and lede -----------------------------------------

PUB = date(2025, 1, 15)  # Wednesday
LEDE = ("The Board of Supervisors voted on Tuesday to approve the new housing plan after "
        "a long public hearing that lasted several hours.")


def _resolve(text, quote, monkeypatch, flag=True):
    if flag:
        monkeypatch.setenv(FLAG, "1")
    else:
        monkeypatch.delenv(FLAG, raising=False)
    from src.extract import _all_segments
    segments = _all_segments(text)
    index = next(i for i, s in enumerate(segments) if quote in s)
    detail = resolve_promise_date_detail(segments, index, PUB, text=text, quote=quote)
    return detail.date, detail.basis, detail.phrase


FAR = ("The plan will add 500 homes by 2030. " + "Filler sentence about nothing at all. " * 4)


def test_weekday_in_lede_far_from_quote(monkeypatch):
    text = LEDE + "\n\nBackground paragraph one. Another sentence here. And more.\n\n" \
        "Second background paragraph. More text. Yet more text.\n\n" + FAR
    assert _resolve(text, "The plan will add 500 homes by 2030.", monkeypatch) == (
        date(2025, 1, 14), "relative", "on Tuesday")


def test_weekday_in_same_paragraph(monkeypatch):
    text = ("Short lede.\n\nOfficials announced Wednesday that work begins. Filler one. "
            "Filler two. Filler three. The plan will add 500 homes by 2030.\n\nEnd.")
    assert _resolve(text, "The plan will add 500 homes by 2030.", monkeypatch) == (
        date(2025, 1, 15), "relative", "Wednesday")


def test_explicit_date_in_paragraph_is_stated(monkeypatch):
    text = ("Short lede.\n\nOn January 2, 2025 officials met. Filler one. Filler two. "
            "Filler three. The plan will add 500 homes by 2030.\n\nEnd.")
    assert _resolve(text, "The plan will add 500 homes by 2030.", monkeypatch) == (
        date(2025, 1, 2), "stated", "January 2, 2025")


def test_no_term_falls_back_to_publication(monkeypatch):
    text = "A lede with no day term at all but long enough to count as the first full paragraph here.\n\n" + FAR
    assert _resolve(text, "The plan will add 500 homes by 2030.", monkeypatch) == (
        PUB, "publication", None)


def test_explicit_later_date_is_ignored(monkeypatch):
    text = ("The board will meet on March 3, 2025 to vote, and the lede is long enough to count as "
            "a real paragraph.\n\n" + FAR)
    assert _resolve(text, "The plan will add 500 homes by 2030.", monkeypatch) == (
        PUB, "publication", None)


def test_wider_lookup_is_off_without_the_flag(monkeypatch):
    text = LEDE + "\n\nBackground one. Background two. Background three. Background four.\n\n" + FAR
    assert _resolve(text, "The plan will add 500 homes by 2030.", monkeypatch, flag=False) == (
        PUB, "publication", None)


def test_near_segment_still_wins_over_the_lede(monkeypatch):
    text = LEDE + "\n\nThe mayor said yesterday it works. The plan will add 500 homes by 2030."
    assert _resolve(text, "The plan will add 500 homes by 2030.", monkeypatch) == (
        date(2025, 1, 14), "relative", "yesterday")


# --- "Not stated" location --------------------------------------------------------

def test_not_stated_is_a_label_without_a_centroid():
    from src.geo_centroids import LOCATION_CENTROIDS
    assert "Not stated" in LOCATIONS and "Not stated" not in LOCATION_CENTROIDS


KWARGS = dict(entity_name="SFPUC", entity_type="City Agency", sector="Environment & Energy",
              neighborhood="Not stated", quote="The pump station will open in 2027.")


def test_taxonomy_accepts_not_stated_only_when_allowed():
    assert screen_taxonomy(**KWARGS) == ["neighborhood_invalid"]
    assert screen_taxonomy(**KWARGS, allow_not_stated=True) == []


def test_audit_publishes_not_stated_under_the_flag(tmp_path, rules_on):
    conn, _root, result, prompts = run(
        tmp_path, **_origin_kwargs(), assessment={"neighborhood": "Not stated"})
    assert result["status"] == "published", result
    assert conn.execute("SELECT neighborhood FROM promises").fetchone() == ("Not stated",)
    system = prompts["verify_evidence"][0][0]["content"]
    assert "'Not stated'" in system and "names no neighborhood" in system
    assert "'Not stated'" in prompts["assess_outcome"][0][0]["content"]
    conn.close()


def test_audit_rejects_not_stated_with_the_flag_off(tmp_path, rules_off):
    selection = {"source_index": 0, "segment_id": 0}
    conn, _root, result, prompts = run(
        tmp_path, **_origin_kwargs(),
        outcome=[("San Francisco opened 3 clinics in 2025.", "2025-01-01")],
        assessment={"neighborhood": "Not stated", "initial_delivery": "DELIVERED_ON_TIME",
                    "current_survival": "ACTIVE_OPERATIONAL",
                    "delivery": selection, "survival": selection})
    assert result == {"promise_id": "P99", "status": "quarantined", "reason": "INVALID_TAXONOMY"}
    assert "'Not stated'" not in prompts["assess_outcome"][0][0]["content"]
    conn.close()


@pytest.mark.parametrize("flag", ["1", None])
def test_extraction_prompt_tells_the_model_to_take_the_sources_own_sentence(
        tmp_path, monkeypatch, flag):
    if flag:
        monkeypatch.setenv(FLAG, flag)
    else:
        monkeypatch.delenv(FLAG, raising=False)
    conn, _root, _result, prompts = run(tmp_path, **_origin_kwargs())
    system = prompts["record_promise_evidence"][0][0]["content"]
    sentence = ("If the source states this project's commitment with different details "
                "than the target, extract the source's own sentence.")
    assert (sentence in system) is bool(flag)
    conn.close()


def test_site_record_for_not_stated_has_no_point(tmp_path):
    base = json.loads((ROOT / "docs" / "data.json").read_text())
    db, src = make_v2(tmp_path / "v2", [{"pid": "P901"}])
    conn = sqlite3.connect(db)
    conn.execute("UPDATE promises SET neighborhood='Not stated'")
    conn.commit()
    conn.close()
    payload, report = run_merge(base, db, src)
    assert report["added"], report
    record = payload["promises"][-1]
    assert record["neighborhood"] == "Location not stated"
    assert record["neighborhood_canonical"] == "Not stated"
    assert record["location_status"] == "not_stated"
    assert record["geographic_scope"] == "citywide" and record["is_citywide"] is False
    assert "latitude" not in record and "longitude" not in record
    assert record["address_status"] == "not_captured"
    assert record["district_status"] == "not_captured"


def test_app_js_lists_unlocated_records_outside_the_map():
    js = (ROOT / "docs" / "app.js").read_text()
    assert js.count("location_status === 'not_stated'") >= 3
