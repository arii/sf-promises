"""Outcome rules R1-R7 (SF_PROMISES_OUTCOME_RULES): rubric, screening, audit, export."""

from tests.keenable_stubs import fetch_response
import asyncio
import itertools
import json
import sqlite3
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from src.candidate import audit_candidate
from src.database import initialize_database
from src.date_resolution import FLAG as DATE_FLAG
from src.discovery import fetch_and_archive
from src.export import build_snapshot
from src.lifecycle_rubric import decide_verdict
from src.outcome_rules import (
    FLAG, NOT_CHECKED_NOTE, STALE_CONTRARY_NOTE, OutcomeRulesSchemaError,
    check_schema_supports_outcome_rules, decide_outcome, origin_date_failures,
    outcome_rules_enabled, relied_phases, require_flag_off_strictness,
)

AS_OF = date(2026, 11, 11)
PAST = date(2024, 12, 31)
FUTURE = date(2030, 12, 31)
DELIVERY_STATES = ("DELIVERED_ON_TIME", "DELIVERED_LATE", "PARTIALLY_DELIVERED",
                   "NOT_DELIVERED", "PENDING_FUTURE_DEADLINE", "UNKNOWN")
SURVIVAL_STATES = ("ACTIVE_OPERATIONAL", "SHUTTERED_OR_CLOSED", "REVOKED_OR_HALTED",
                   "NOT_YET_OPEN", "UNKNOWN")


# --- flag -------------------------------------------------------------------

def test_flag_reads_environment(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    assert not outcome_rules_enabled()
    for value in ("0", "", "true"):
        monkeypatch.setenv(FLAG, value)
        assert not outcome_rules_enabled()
    monkeypatch.setenv(FLAG, "1")
    assert outcome_rules_enabled()


# --- rubric -----------------------------------------------------------------

def test_decide_verdict_accepts_no_deadline():
    # Previously a TypeError. No deadline means nothing is late or broken by time.
    assert decide_verdict(None, AS_OF, "DELIVERED_ON_TIME", "ACTIVE_OPERATIONAL", True) == "KEPT"
    assert decide_verdict(None, AS_OF, "DELIVERED_LATE", "ACTIVE_OPERATIONAL", True) is None
    assert decide_verdict(None, AS_OF, "NOT_DELIVERED", "NOT_YET_OPEN", True) is None
    assert decide_verdict(None, AS_OF, "PENDING_FUTURE_DEADLINE", "NOT_YET_OPEN", True) is None
    assert decide_verdict(None, AS_OF, "NOT_DELIVERED", "REVOKED_OR_HALTED", True,
                          explicitly_abandoned=True) == "BROKEN"
    assert decide_verdict(None, AS_OF, "DELIVERED_LATE", "REVOKED_OR_HALTED", True,
                          explicitly_abandoned=True) is None


def test_decide_verdict_with_deadline_is_unchanged():
    assert decide_verdict(PAST, AS_OF, "DELIVERED_ON_TIME", "ACTIVE_OPERATIONAL", True) == "KEPT"
    assert decide_verdict(PAST, AS_OF, "DELIVERED_LATE", "ACTIVE_OPERATIONAL", True) == "DELAYED_OR_PARTIAL"
    assert decide_verdict(PAST, AS_OF, "NOT_DELIVERED", "NOT_YET_OPEN", True) == "BROKEN"
    assert decide_verdict(FUTURE, AS_OF, "PENDING_FUTURE_DEADLINE", "NOT_YET_OPEN", True) == "IN_PROGRESS"
    assert decide_verdict(FUTURE, AS_OF, "UNKNOWN", "UNKNOWN", True) is None


ONE_OFF_QUOTE = "On March 5, 2024, San Francisco will open 3 new neighborhood clinics."


def test_r1_r2_screening_filter():
    promised = date(2024, 3, 1)
    published = date(2024, 3, 1)
    assert origin_date_failures(["deadline_missing"], promised, None) == ([], ["R1"])
    one_off = date(2024, 3, 5)
    # R2 now needs the origin quote to state the deadline itself.
    assert origin_date_failures(
        ["promise_horizon_short"], promised, one_off,
        quote=ONE_OFF_QUOTE, published=published) == ([], ["R2"])
    # Same day is a one-off event too.
    assert origin_date_failures(
        ["promise_horizon_short"], promised, promised,
        quote="Today San Francisco will open 3 clinics.", published=published) == ([], ["R2"])
    # A deadline before the promise is a real failure.
    before = date(2024, 2, 1)
    assert origin_date_failures(
        ["promise_horizon_short"], promised, before,
        quote="On February 1, 2024 San Francisco will open clinics.", published=published) == (
        ["promise_horizon_short"], [])
    # Every other failure is kept.
    others = ["promise_date_missing", "origin_publication_late", "origin_predates_promise"]
    assert origin_date_failures(others + ["deadline_missing"], None, None) == (others, ["R1"])


@pytest.mark.parametrize("quote", [
    "San Francisco will open 3 new neighborhood clinics.",             # no date at all
    "San Francisco will open 3 new neighborhood clinics within 30 days.",  # duration only
    "On March 9, 2024, San Francisco will open 3 new neighborhood clinics.",  # other date
    "On March 5, 2025, San Francisco will open 3 new neighborhood clinics.",  # other year
    "Soon, in 2024, San Francisco will open 3 new neighborhood clinics.",
])
def test_r2_does_not_apply_when_the_quote_does_not_state_the_deadline(quote):
    promised = published = date(2024, 3, 1)
    assert origin_date_failures(
        ["promise_horizon_short"], promised, date(2024, 3, 5),
        quote=quote, published=published) == (["promise_horizon_short"], [])
    # No quote or publication date supplied: nothing is waived.
    assert origin_date_failures(
        ["promise_horizon_short"], promised, date(2024, 3, 5)) == (["promise_horizon_short"], [])


@pytest.mark.parametrize("quote,published,deadline", [
    ("San Francisco will open 3 clinics on March 5, 2024.", "2024-03-01", "2024-03-05"),
    ("San Francisco will open 3 clinics on 2024-03-05.", "2024-03-01", "2024-03-05"),
    ("San Francisco will open 3 clinics on March 5.", "2024-03-01", "2024-03-05"),
    ("San Francisco will open 3 clinics on Friday.", "2024-03-01", "2024-03-01"),    # published is a Friday
    ("San Francisco will open 3 clinics this Sunday.", "2024-03-01", "2024-03-03"),
    ("San Francisco will open 3 clinics next Tuesday.", "2024-03-01", "2024-03-05"),
    ("San Francisco will open 3 clinics tomorrow.", "2024-03-01", "2024-03-02"),
    ("San Francisco opens 3 clinics today.", "2024-03-01", "2024-03-01"),
])
def test_r2_resolves_weekday_and_relative_terms_against_publication(quote, published, deadline):
    published, deadline = date.fromisoformat(published), date.fromisoformat(deadline)
    promised = published
    assert origin_date_failures(
        ["promise_horizon_short"], promised, deadline, quote=quote, published=published,
    ) == ([], ["R2"])
    # The same words do not waive a different deadline.
    other = date.fromordinal(deadline.toordinal() + 3)
    assert origin_date_failures(
        ["promise_horizon_short"], promised, other, quote=quote, published=published,
    ) == (["promise_horizon_short"], [])


def test_r3_future_deadline_is_in_progress_without_delivery_or_survival():
    for delivery, survival in itertools.product(
            ("UNKNOWN", "PENDING_FUTURE_DEADLINE"), ("UNKNOWN", "NOT_YET_OPEN")):
        assert decide_outcome(FUTURE, AS_OF, delivery, survival, True)[0] == "IN_PROGRESS"
    assert decide_outcome(FUTURE, AS_OF, "UNKNOWN", "UNKNOWN", True) == (
        "IN_PROGRESS", "R3", "deadline in the future")
    # Partial delivery before the deadline is still in progress, not delayed.
    assert decide_outcome(FUTURE, AS_OF, "PARTIALLY_DELIVERED", "UNKNOWN", True)[0] == "IN_PROGRESS"


def test_r3_contrary_evidence_blocks_in_progress():
    assert decide_outcome(FUTURE, AS_OF, "NOT_DELIVERED", "UNKNOWN", True) is None
    assert decide_outcome(FUTURE, AS_OF, "UNKNOWN", "REVOKED_OR_HALTED", True) is None
    assert decide_outcome(FUTURE, AS_OF, "NOT_DELIVERED", "NOT_YET_OPEN", True) is None


def test_r4_delivery_only():
    assert decide_outcome(PAST, AS_OF, "DELIVERED_ON_TIME", "UNKNOWN", True) == (
        "KEPT", "R4", NOT_CHECKED_NOTE)
    assert decide_outcome(None, AS_OF, "DELIVERED_ON_TIME", "UNKNOWN", True) == (
        "KEPT", "R4", NOT_CHECKED_NOTE)
    assert decide_outcome(date(2024, 3, 5), AS_OF, "DELIVERED_ON_TIME", "UNKNOWN", True)[0] == "KEPT"
    assert decide_outcome(PAST, AS_OF, "DELIVERED_LATE", "UNKNOWN", True) == (
        "DELAYED_OR_PARTIAL", "R4", NOT_CHECKED_NOTE)
    assert decide_outcome(PAST, AS_OF, "PARTIALLY_DELIVERED", "UNKNOWN", True) == (
        "DELAYED_OR_PARTIAL", "R4", NOT_CHECKED_NOTE)
    assert decide_outcome(FUTURE, AS_OF, "DELIVERED_LATE", "UNKNOWN", True) is None
    assert decide_outcome(None, AS_OF, "DELIVERED_LATE", "UNKNOWN", True) is None


def test_r4_shuttered_and_revoked_need_their_own_selected_evidence():
    # Without a survival sentence the state is UNKNOWN and nothing reversed.
    assert decide_outcome(PAST, AS_OF, "DELIVERED_ON_TIME", "UNKNOWN", True)[0] == "KEPT"
    assert decide_outcome(PAST, AS_OF, "DELIVERED_ON_TIME", "SHUTTERED_OR_CLOSED", True) == (
        "KEPT_THEN_REVERSED", "STANDARD", None)
    assert decide_outcome(PAST, AS_OF, "DELIVERED_ON_TIME", "REVOKED_OR_HALTED", True)[0] == \
        "KEPT_THEN_REVERSED"
    assert decide_outcome(PAST, AS_OF, "DELIVERED_ON_TIME", "NOT_YET_OPEN", True) is None


def test_r5_unknown_outcome_is_undecided():
    for deadline in (PAST, None):
        assert decide_outcome(deadline, AS_OF, "UNKNOWN", "UNKNOWN", True) == (
            "UNDECIDED", "R5", "no outcome evidence found")
    assert decide_outcome(PAST, AS_OF, "UNKNOWN", "NOT_YET_OPEN", True)[0] == "UNDECIDED"
    # A past deadline with a selected "still pending" sentence is contradictory.
    assert decide_outcome(PAST, AS_OF, "PENDING_FUTURE_DEADLINE", "UNKNOWN", True) is None
    assert decide_outcome(None, AS_OF, "PENDING_FUTURE_DEADLINE", "UNKNOWN", True) is None


def test_decide_outcome_broken_needs_a_contrary_source_on_or_after_the_deadline():
    after = dict(delivery_published=date(2025, 6, 1))
    assert decide_outcome(PAST, AS_OF, "NOT_DELIVERED", "NOT_YET_OPEN", True, **after)[0] == "BROKEN"
    assert decide_outcome(PAST, AS_OF, "NOT_DELIVERED", "UNKNOWN", True, **after) == (
        "BROKEN", "CONTRARY", "deadline passed and the outcome source says not delivered")
    # Published on the deadline itself still counts.
    assert decide_outcome(PAST, AS_OF, "NOT_DELIVERED", "UNKNOWN", True,
                          delivery_published=PAST)[0] == "BROKEN"
    assert decide_outcome(None, AS_OF, "NOT_DELIVERED", "UNKNOWN", True, **after) is None
    assert decide_outcome(PAST, AS_OF, "UNKNOWN", "REVOKED_OR_HALTED", True, **after) is None


@pytest.mark.parametrize("survival", ["UNKNOWN", "NOT_YET_OPEN"])
@pytest.mark.parametrize("published", [None, date(2024, 12, 30), date(2024, 1, 1)])
def test_broken_is_not_issued_from_an_early_or_undated_contrary_source(survival, published):
    verdict, rule, reason = decide_outcome(
        PAST, AS_OF, "NOT_DELIVERED", survival, True, delivery_published=published)
    assert (verdict, rule) == ("UNDECIDED", "R5")
    assert reason.endswith(STALE_CONTRARY_NOTE)
    # With a future deadline the contrary sentence was never enough (unchanged).
    assert decide_outcome(FUTURE, AS_OF, "NOT_DELIVERED", survival, True,
                          delivery_published=published) is None


def test_unverified_facts_decide_nothing():
    for delivery, survival in itertools.product(DELIVERY_STATES, SURVIVAL_STATES):
        for facts in (False, None, 1):
            assert decide_outcome(PAST, AS_OF, delivery, survival, facts) is None


def test_relied_phases():
    assert relied_phases("IN_PROGRESS", "PENDING_FUTURE_DEADLINE", "NOT_YET_OPEN") == ()
    assert relied_phases("UNDECIDED", "UNKNOWN", "UNKNOWN") == ()
    assert relied_phases("KEPT", "DELIVERED_ON_TIME", "UNKNOWN") == ("DELIVERY",)
    assert relied_phases("KEPT", "DELIVERED_ON_TIME", "ACTIVE_OPERATIONAL") == ("DELIVERY", "SURVIVAL")
    assert relied_phases("BROKEN", "NOT_DELIVERED", "NOT_YET_OPEN") == ("DELIVERY",)


@pytest.mark.parametrize("deadline", [None, PAST, AS_OF, FUTURE])
def test_exhaustive_safety_of_rubric(deadline):
    """No combination publishes KEPT without delivery or BROKEN without contrary evidence."""
    kept_ok = ("DELIVERED_ON_TIME",)
    for delivery, survival in itertools.product(DELIVERY_STATES, SURVIVAL_STATES):
        result = decide_outcome(deadline, AS_OF, delivery, survival, True)
        assert result is None or result[0] != "BROKEN"  # never without a dated source
        result = decide_outcome(deadline, AS_OF, delivery, survival, True,
                                delivery_published=AS_OF)
        if result is None:
            continue
        verdict, rule, reason = result
        future = deadline is not None and deadline > AS_OF
        if verdict == "KEPT":
            assert delivery in kept_ok
            assert survival in ("ACTIVE_OPERATIONAL", "UNKNOWN")
        if verdict in ("KEPT_THEN_REVERSED", "DELAYED_OR_PARTIAL"):
            assert delivery in ("DELIVERED_ON_TIME", "DELIVERED_LATE", "PARTIALLY_DELIVERED")
        if verdict == "BROKEN":
            assert delivery == "NOT_DELIVERED" or survival == "REVOKED_OR_HALTED"
            assert not future
        if verdict == "IN_PROGRESS":
            assert future
            assert delivery in ("UNKNOWN", "PENDING_FUTURE_DEADLINE", "PARTIALLY_DELIVERED")
        if verdict == "UNDECIDED":
            assert delivery == "UNKNOWN" and not future and rule == "R5"
            assert reason == "no outcome evidence found"
        # Outcome rules never produce a verdict the strict rubric calls impossible
        # when they are not R3-R5 or CONTRARY.
        if rule == "STANDARD":
            assert decide_verdict(deadline, AS_OF, delivery, survival, True) == verdict
        # KEPT must have a delivery sentence relied on.
        if verdict == "KEPT":
            assert "DELIVERY" in relied_phases(verdict, delivery, survival)


# --- audit ------------------------------------------------------------------

PROMISE = "San Francisco will open 3 new neighborhood clinics"


def _response(name, result):
    return {"choices": [{"message": {"tool_calls": [{"function": {
        "name": name, "arguments": json.dumps(result)}}]}}]}


async def _audit(tmp_path, *, origin_text, origin_published, promised, deadline,
                 outcome=None, assessment=None, review=None, origin_review=None,
                 as_of=AS_OF):
    """Run audit_candidate with a fake completion; outcome = [(text, published)]."""
    database = tmp_path / "candidate.db"
    initialize_database(database)
    root = tmp_path / "sources"
    documents = {"https://sf.gov/origin": (origin_text, origin_published)}
    for i, (text, published) in enumerate(outcome or []):
        documents[f"https://sf.gov/outcome{i}"] = (text, published)

    class Search:
        async def fetch(self, url, **kwargs):
            text, published = documents[url]
            return fetch_response(url, text, published)

    sources = [await fetch_and_archive(Search(), url, root, "P99") for url in documents]
    research = {"phases": {
        "origin": {"sources": sources[:1], "blocked": []},
        "delivery": {"sources": sources[1:], "blocked": []},
        "survival": {"sources": [], "blocked": []},
    }}
    lead = {"promise_id": "P99", "promise_text": "San Francisco clinics",
            "entity": "San Francisco", "promised_date": promised, "due_date": deadline}
    base = {"initial_delivery": "UNKNOWN", "current_survival": "UNKNOWN",
            "delivery": None, "survival": None,
            "entity_name": "San Francisco", "entity_type": "City Agency",
            "sector": "Governance & Finance", "neighborhood": "Citywide"}
    base.update(assessment or {})
    verified = {"action": True, "promise_date": True, "deadline": True, "delivery": False,
                "survival": False, "entity_and_location": True,
                "explanation": "Verified from the archived text."}
    verified.update(review or {})
    origin = {"action": True, "promise_date": True, "deadline": True,
              "explanation": "Supported by the origin."}
    origin.update(origin_review or {})
    prompts = {}

    async def complete(messages, *, tools, tool_choice, **_kwargs):
        name = tool_choice["function"]["name"]
        prompts.setdefault(name, []).append(messages)
        if name == "record_promise_evidence":
            return _response(name, {"candidates": [{
                "promise_id": "P99", "quote_segment_id": 0, "speaker": "San Francisco",
                "promised_date": promised, "deadline": deadline}]})
        if name == "assess_outcome":
            return _response(name, base)
        if name == "verify_origin":
            return _response(name, origin)
        if name == "verify_evidence":
            return _response(name, verified)
        raise AssertionError(name)

    conn = sqlite3.connect(database)
    conn.execute("PRAGMA foreign_keys=ON")
    result = await audit_candidate(
        conn, root=root, staging_root=tmp_path / "staging", lead=lead,
        research=research, complete=complete, as_of=as_of,
    )
    return conn, root, result, prompts


def run(tmp_path, **kwargs):
    return asyncio.run(_audit(tmp_path, **kwargs))


def basis(conn):
    row = conn.execute("SELECT passed, reason FROM verifications "
                       "WHERE check_type='outcome_basis'").fetchone()
    return None if row is None else json.loads(row[1])


@pytest.fixture
def rules_on(monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.delenv(DATE_FLAG, raising=False)


@pytest.fixture
def rules_off(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    monkeypatch.delenv(DATE_FLAG, raising=False)


OPEN_ENDED = dict(
    origin_text="On March 1, 2024 the mayor said San Francisco will open 3 new neighborhood clinics.",
    origin_published="2024-03-01", promised="2024-03-01", deadline=None,
)
ONE_OFF = dict(
    origin_text="On March 5, 2024, San Francisco will open 3 new neighborhood clinics.",
    origin_published="2024-03-01", promised="2024-03-01", deadline="2024-03-05",
)
FUTURE_DEADLINE = dict(
    origin_text="On March 1, 2024 the mayor said San Francisco will open 3 new neighborhood clinics by 2030.",
    origin_published="2024-03-01", promised="2024-03-01", deadline="2030-12-31",
)
PAST_DEADLINE = dict(
    origin_text="On March 1, 2024 the mayor said San Francisco will open 3 new neighborhood clinics by 2024.",
    origin_published="2024-03-01", promised="2024-03-01", deadline="2024-12-31",
)


def test_open_ended_commitment_is_undecided(tmp_path, rules_on):
    conn, _root, result, prompts = run(tmp_path, **OPEN_ENDED)
    assert result == {"promise_id": "P99", "status": "published", "verdict": "UNDECIDED"}
    assert conn.execute("SELECT date_deadline FROM promises").fetchone() == (None,)
    assert conn.execute("SELECT verdict FROM verdicts").fetchone() == ("UNDECIDED",)
    detail = basis(conn)
    assert detail["rules"] == ["R1", "R5"] and detail["open_ended"] is True
    assert detail["deadline"] is None and detail["reason"] == "no outcome evidence found"
    assert [r[0] for r in conn.execute("SELECT phase FROM evidence_ledger")] == ["ORIGIN"]
    assert conn.execute("SELECT quote_verified FROM evidence_ledger").fetchone() == (1,)
    assert "deadline: none stated" in prompts["verify_evidence"][0][1]["content"]
    assert "Fields to evaluate: action, promise_date, entity_and_location" in \
        prompts["verify_evidence"][0][1]["content"]
    conn.close()


def test_one_off_dated_event_delivered_is_kept_with_delivery_only(tmp_path, rules_on):
    conn, _root, result, prompts = run(
        tmp_path, **ONE_OFF,
        outcome=[("San Francisco opened 3 new neighborhood clinics on March 5.", "2024-03-06")],
        assessment={"initial_delivery": "DELIVERED_ON_TIME",
                    "delivery": {"source_index": 0, "segment_id": 0}},
        review={"delivery": True},
    )
    assert result["verdict"] == "KEPT"
    assert basis(conn)["rules"] == ["R2", "R4"]
    assert "current status not checked" in conn.execute("SELECT reason FROM verdicts").fetchone()[0]
    assert sorted(r[0] for r in conn.execute("SELECT phase FROM evidence_ledger")) == [
        "DELIVERY", "ORIGIN"]
    user = prompts["verify_evidence"][0][1]["content"]
    assert "Survival" not in user and "Fields to evaluate: action, promise_date, " \
        "entity_and_location, deadline, delivery" in user
    conn.close()


def test_kept_still_needs_a_verified_delivery_sentence(tmp_path, rules_on):
    conn, _root, result, _ = run(
        tmp_path, **ONE_OFF,
        outcome=[("San Francisco opened 3 new neighborhood clinics on March 5.", "2024-03-06")],
        assessment={"initial_delivery": "DELIVERED_ON_TIME",
                    "delivery": {"source_index": 0, "segment_id": 0}},
        review={"delivery": False},
    )
    assert result == {"promise_id": "P99", "status": "quarantined", "reason": "AMBIGUOUS_EVIDENCE"}
    assert conn.execute("SELECT count(*) FROM verdicts").fetchone() == (0,)
    conn.close()


def test_claimed_delivery_without_selected_sentence_is_never_kept(tmp_path, rules_on):
    conn, _root, result, _ = run(
        tmp_path, **ONE_OFF, assessment={"initial_delivery": "DELIVERED_ON_TIME"},
    )
    assert result["verdict"] == "UNDECIDED"
    assert basis(conn)["rules"] == ["R2", "R5"]
    conn.close()


def test_future_deadline_is_in_progress(tmp_path, rules_on):
    conn, _root, result, _ = run(
        tmp_path, **FUTURE_DEADLINE, assessment={"initial_delivery": "PENDING_FUTURE_DEADLINE"},
    )
    assert result["verdict"] == "IN_PROGRESS"
    detail = basis(conn)
    assert detail["rules"] == ["R3"] and detail["reason"] == "deadline in the future"
    assert detail["open_ended"] is False and detail["deadline"] == "2030-12-31"
    assert conn.execute("SELECT date_deadline FROM promises").fetchone() == ("2030-12-31",)
    conn.close()


def test_past_deadline_nothing_found_is_undecided(tmp_path, rules_on):
    conn, _root, result, _ = run(tmp_path, **PAST_DEADLINE)
    assert result["verdict"] == "UNDECIDED"
    detail = basis(conn)
    assert detail["rules"] == ["R5"] and detail["reason"] == "no outcome evidence found"
    conn.close()


@pytest.mark.parametrize("with_survival", [False, True])
def test_contrary_evidence_after_deadline_is_broken(tmp_path, rules_on, with_survival):
    assessment = {"initial_delivery": "NOT_DELIVERED",
                  "delivery": {"source_index": 0, "segment_id": 0}}
    if with_survival:
        assessment.update(current_survival="NOT_YET_OPEN",
                          survival={"source_index": 0, "segment_id": 0})
    conn, _root, result, _ = run(
        tmp_path, **PAST_DEADLINE,
        outcome=[("The San Francisco neighborhood clinics have not opened.", "2025-06-01")],
        assessment=assessment, review={"delivery": True},
    )
    assert result["verdict"] == "BROKEN"
    assert [r[0] for r in conn.execute(
        "SELECT phase FROM evidence_ledger WHERE phase != 'ORIGIN'")] == ["DELIVERY"]
    conn.close()


def test_contrary_evidence_with_future_deadline_is_not_in_progress(tmp_path, rules_on):
    conn, _root, result, _ = run(
        tmp_path, **FUTURE_DEADLINE,
        outcome=[("The San Francisco neighborhood clinics have not opened.", "2025-06-01")],
        assessment={"initial_delivery": "NOT_DELIVERED",
                    "delivery": {"source_index": 0, "segment_id": 0}},
        review={"delivery": True},
    )
    assert result == {"promise_id": "P99", "status": "quarantined",
                      "reason": "INSUFFICIENT_OUTCOME_EVIDENCE"}
    conn.close()


@pytest.mark.parametrize("field,verifier", [
    ("action", "review"), ("action", "origin_review"),
    ("promise_date", "review"), ("promise_date", "origin_review"),
    ("entity_and_location", "review"),
])
def test_verifier_failures_still_quarantine(tmp_path, rules_on, field, verifier):
    conn, _root, result, _ = run(tmp_path, **OPEN_ENDED, **{verifier: {field: False}})
    assert result["status"] == "quarantined"
    assert conn.execute("SELECT count(*) FROM promises").fetchone() == (0,)
    assert conn.execute("SELECT count(*) FROM verdicts").fetchone() == (0,)
    conn.close()


def test_origin_deadline_check_applies_when_a_deadline_exists(tmp_path, rules_on):
    conn, _root, result, _ = run(tmp_path, **PAST_DEADLINE, origin_review={"deadline": False})
    assert result["reason"] == "NO_VERIFIABLE_DEADLINE"
    conn.close()


def test_deadline_before_promise_date_still_quarantines(tmp_path, rules_on):
    conn, _root, result, _ = run(tmp_path, **{**ONE_OFF, "deadline": "2024-02-01"})
    assert result["status"] == "quarantined"
    assert result["reason"] == "NO_VERIFIABLE_DEADLINE"
    conn.close()


def test_missing_promise_date_still_quarantines(tmp_path, rules_on):
    conn, _root, result, _ = run(tmp_path, **{**OPEN_ENDED, "promised": None})
    assert result["status"] == "quarantined"
    conn.close()


def test_taxonomy_still_required(tmp_path, rules_on):
    conn, _root, result, _ = run(tmp_path, **OPEN_ENDED, assessment={"sector": "Nonsense"})
    assert result == {"promise_id": "P99", "status": "quarantined", "reason": "INVALID_TAXONOMY"}
    conn.close()


def test_snapshot_exports_open_ended_undecided(tmp_path, rules_on):
    conn, root, result, _ = run(tmp_path, **OPEN_ENDED)
    assert result["verdict"] == "UNDECIDED"
    snapshot = build_snapshot(
        conn, source_root=root, as_of=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    exported = snapshot["promises"][0]
    assert exported["verdict"] == "UNDECIDED" and exported["date_deadline"] is None
    assert exported["outcome_basis"]["rules"] == ["R1", "R5"]
    assert snapshot["tallies"] == {"UNDECIDED": 1}
    conn.close()


def test_flagged_database_exports_with_the_flag_unset(tmp_path, monkeypatch):
    """The exporter reads the rule set from the database, not the environment."""
    monkeypatch.setenv(FLAG, "1")
    conn, root, _result, _ = run(tmp_path, **OPEN_ENDED)
    monkeypatch.delenv(FLAG)
    snapshot = build_snapshot(conn, source_root=root,
                              as_of=datetime(2030, 1, 1, tzinfo=timezone.utc))
    assert snapshot["tallies"] == {"UNDECIDED": 1}
    assert snapshot["promises"][0]["outcome_basis"]["rules"] == ["R1", "R5"]
    conn.close()


def test_flag_off_database_still_rejects_open_ended_even_with_the_flag_set(tmp_path, monkeypatch):
    """No outcome_basis row means no rule was recorded, so R1 cannot be waived.

    Replaces the old flag-off premise (flagged DB + unset env rejects): the
    decision now follows the rows in the database, so a database without an
    outcome_basis row is the flag-off case, whatever the environment says.
    """
    monkeypatch.setenv(FLAG, "1")
    conn, root, _result, _ = run(tmp_path, **OPEN_ENDED)
    conn.execute("DELETE FROM verifications WHERE check_type = 'outcome_basis'")
    conn.commit()
    for value in ("1", None):
        if value is None:
            monkeypatch.delenv(FLAG)
        with pytest.raises(ValueError, match="Missing valid origin evidence"):
            build_snapshot(conn, source_root=root,
                           as_of=datetime(2030, 1, 1, tzinfo=timezone.utc))
    conn.close()


def test_snapshot_rejects_a_rule_the_database_did_not_record(tmp_path, monkeypatch):
    monkeypatch.setenv(FLAG, "1")
    conn, root, _result, _ = run(tmp_path, **ONE_OFF)
    monkeypatch.delenv(FLAG)
    assert "R2" in basis(conn)["rules"]
    as_of = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert build_snapshot(conn, source_root=root, as_of=as_of)["promises"]
    row = conn.execute("SELECT verification_id, reason FROM verifications "
                       "WHERE check_type='outcome_basis'").fetchone()
    conn.execute("UPDATE verifications SET reason=? WHERE verification_id=?",
                 (json.dumps({**json.loads(row[1]), "rules": ["R3"]}), row[0]))
    conn.commit()
    with pytest.raises(ValueError, match="Missing valid origin evidence"):
        build_snapshot(conn, source_root=root, as_of=as_of)
    conn.close()


# --- R2 is bounded to a deadline the origin quote states ----------------------

def test_short_horizon_with_the_deadline_in_the_quote_is_published(tmp_path, rules_on):
    conn, _root, result, _ = run(tmp_path, **ONE_OFF)
    assert result["status"] == "published"
    assert "R2" in basis(conn)["rules"]
    conn.close()


def test_short_horizon_without_the_deadline_in_the_quote_stays_quarantined(tmp_path, rules_on):
    undated = dict(ONE_OFF, origin_text="San Francisco will open 3 new neighborhood clinics.")
    conn, _root, result, _ = run(tmp_path, **undated)
    assert result == {"promise_id": "P99", "status": "quarantined",
                      "reason": "NO_VERIFIABLE_DEADLINE"}
    assert conn.execute("SELECT count(*) FROM promises").fetchone() == (0,)
    conn.close()


# --- BROKEN needs a contrary source dated on or after the deadline ------------

@pytest.mark.parametrize("published", ["2024-06-01", "2024-12-30"])
def test_contrary_source_before_the_deadline_is_not_broken(tmp_path, rules_on, published):
    conn, _root, result, _ = run(
        tmp_path, **PAST_DEADLINE,
        outcome=[("The San Francisco neighborhood clinics have not opened.", published)],
        assessment={"initial_delivery": "NOT_DELIVERED",
                    "delivery": {"source_index": 0, "segment_id": 0}},
        review={"delivery": True},
    )
    assert result["verdict"] == "UNDECIDED"
    detail = basis(conn)
    assert detail["rules"] == ["R5"] and STALE_CONTRARY_NOTE in detail["reason"]
    assert detail["relied_on"] == []
    assert [r[0] for r in conn.execute(
        "SELECT phase FROM evidence_ledger WHERE phase != 'ORIGIN'")] == []
    conn.close()


def test_contrary_source_on_the_deadline_day_is_broken(tmp_path, rules_on):
    conn, _root, result, _ = run(
        tmp_path, **PAST_DEADLINE,
        outcome=[("The San Francisco neighborhood clinics have not opened.", "2024-12-31")],
        assessment={"initial_delivery": "NOT_DELIVERED",
                    "delivery": {"source_index": 0, "segment_id": 0}},
        review={"delivery": True},
    )
    assert result["verdict"] == "BROKEN"
    conn.close()


# --- schema preflight (item 2) and flag-off strictness (item 8) -----------------

def old_schema_database(path):
    """A database as created before the outcome rules: NOT NULL deadline, no UNDECIDED."""
    from src.database import APPLICATION_ID, SCHEMA_VERSION
    from pathlib import Path
    schema = (Path(__file__).resolve().parents[1] / "src" / "schema.sql").read_text()
    schema = schema.replace("date_deadline TEXT,", "date_deadline TEXT NOT NULL,")
    schema = schema.replace("'DELAYED_OR_PARTIAL', 'BROKEN', 'IN_PROGRESS', 'UNDECIDED')",
                            "'DELAYED_OR_PARTIAL', 'BROKEN', 'IN_PROGRESS')")
    assert "NOT NULL," in schema and "'UNDECIDED'" not in schema
    conn = sqlite3.connect(path)
    conn.executescript(schema)
    conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    conn.commit()
    return conn


def test_preflight_accepts_the_current_schema(tmp_path):
    database = tmp_path / "new.db"
    initialize_database(database)
    with sqlite3.connect(database) as conn:
        check_schema_supports_outcome_rules(conn)


def test_preflight_rejects_an_old_schema_with_a_clear_message(tmp_path):
    conn = old_schema_database(tmp_path / "old.db")
    with pytest.raises(OutcomeRulesSchemaError) as raised:
        check_schema_supports_outcome_rules(conn)
    message = str(raised.value)
    assert FLAG in message and "date_deadline must allow NULL" in message
    assert "'UNDECIDED'" in message
    conn.close()


def test_preflight_names_only_the_missing_capability(tmp_path):
    conn = old_schema_database(tmp_path / "old.db")
    conn.execute("DROP TABLE promises")
    conn.execute("CREATE TABLE promises (promise_id TEXT PRIMARY KEY, date_deadline TEXT)")
    with pytest.raises(OutcomeRulesSchemaError) as raised:
        check_schema_supports_outcome_rules(conn)
    assert "date_deadline" not in str(raised.value)
    assert "verdicts.verdict must allow 'UNDECIDED'" in str(raised.value)
    conn.close()


def test_audit_fails_fast_on_an_old_schema_before_any_write(tmp_path, rules_on):
    database = tmp_path / "candidate.db"
    conn = old_schema_database(database)
    conn.close()

    async def go():
        import src.candidate as candidate
        conn = sqlite3.connect(database)
        with pytest.raises(OutcomeRulesSchemaError):
            await candidate.audit_candidate(
                conn, root=tmp_path / "sources", staging_root=tmp_path / "staging",
                lead={"promise_id": "P99", "promise_text": "x"},
                research={"phases": {}}, complete=None, as_of=AS_OF)
        for table in ("evidence_ledger", "relevance_assessments", "promises", "quarantined"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)
        conn.close()
    asyncio.run(go())


def test_old_schema_is_not_checked_when_the_flag_is_off(tmp_path, rules_off):
    from src.candidate import audit_candidate
    database = tmp_path / "candidate.db"
    conn = old_schema_database(database)
    conn.execute("PRAGMA foreign_keys=ON")
    result = asyncio.run(audit_candidate(
        conn, root=tmp_path / "sources", staging_root=tmp_path / "staging",
        lead={"promise_id": "P99", "promise_text": "x"},
        research={"phases": {"origin": {"sources": []}}}, complete=None, as_of=AS_OF))
    assert result["reason"] == "NO_VERIFIABLE_ORIGIN"  # reached the audit, no preflight error
    conn.close()


def test_candidate_batch_fails_fast_on_an_old_schema(tmp_path, monkeypatch):
    from src.run_live import candidate_batch
    database = tmp_path / "candidates.db"
    old_schema_database(database).close()
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setattr("src.run_live.credentials", lambda: {
        "OPENROUTER_API_KEY": "test", "KEENABLE_API_KEY": "test"})

    async def discover(*_args):
        raise AssertionError("discovery must not start")

    monkeypatch.setattr("src.run_live.discover_run", discover)
    with pytest.raises(OutcomeRulesSchemaError, match="date_deadline must allow NULL"):
        asyncio.run(candidate_batch(database, ["P01"]))


def test_flag_off_publish_rejects_null_deadline_and_undecided(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    require_flag_off_strictness(date(2025, 1, 1), "KEPT")
    with pytest.raises(ValueError, match="NULL deadline"):
        require_flag_off_strictness(None, "KEPT")
    with pytest.raises(ValueError, match="UNDECIDED"):
        require_flag_off_strictness(date(2025, 1, 1), "UNDECIDED")
    monkeypatch.setenv(FLAG, "1")
    require_flag_off_strictness(None, "UNDECIDED")


def test_flag_off_audit_cannot_publish_undecided_or_null_deadline(tmp_path, rules_off, monkeypatch):
    """The permissive schema no longer backstops the flag; the publish step does."""
    monkeypatch.setattr("src.candidate.decide_verdict", lambda *a, **k: "UNDECIDED")
    with pytest.raises(ValueError, match="UNDECIDED"):
        run(tmp_path, **PAST_DEADLINE,
            outcome=[("The San Francisco neighborhood clinics opened in 2024.", "2024-12-01"),
                     ("The San Francisco neighborhood clinics remain open in 2026.", "2026-01-01")],
            assessment={"initial_delivery": "DELIVERED_ON_TIME",
                        "current_survival": "ACTIVE_OPERATIONAL",
                        "delivery": {"source_index": 0, "segment_id": 0},
                        "survival": {"source_index": 1, "segment_id": 0}},
            review={"delivery": True, "survival": True})
    database = tmp_path / "candidate.db"
    with sqlite3.connect(database) as conn:
        for table in ("promises", "verdicts", "evidence_ledger"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone() == (0,)


def test_current_schema_stays_permissive_for_flagged_runs(tmp_path):
    database = tmp_path / "new.db"
    initialize_database(database)
    sql = dict(sqlite3.connect(database).execute(
        "SELECT name, sql FROM sqlite_master WHERE name IN ('promises','verdicts')"))
    assert "NOT NULL" not in sql["promises"].split("date_deadline")[1].split(",")[0]
    assert "'UNDECIDED'" in sql["verdicts"]


# --- flag off: unchanged quarantine reasons ---------------------------------

@pytest.mark.parametrize("case,kwargs,reason", [
    ("open-ended", OPEN_ENDED, "NO_VERIFIABLE_DEADLINE"),
    ("one-off", ONE_OFF, "NO_VERIFIABLE_DEADLINE"),
    ("future deadline", FUTURE_DEADLINE, "INSUFFICIENT_OUTCOME_EVIDENCE"),
    ("past deadline", PAST_DEADLINE, "INSUFFICIENT_OUTCOME_EVIDENCE"),
])
def test_flag_off_quarantines_as_before(tmp_path, rules_off, case, kwargs, reason):
    conn, _root, result, prompts = run(tmp_path, **kwargs)
    assert result == {"promise_id": "P99", "status": "quarantined", "reason": reason}, case
    assert conn.execute("SELECT count(*) FROM promises").fetchone() == (0,)
    assert conn.execute("SELECT count(*) FROM verifications WHERE "
                        "check_type='outcome_basis'").fetchone() == (0,)
    conn.close()


def test_flag_off_with_selected_sentences_matches_old_prompts(tmp_path, rules_off):
    conn, _root, result, prompts = run(
        tmp_path, **PAST_DEADLINE,
        outcome=[("The San Francisco neighborhood clinics opened in 2024.", "2024-12-01"),
                 ("The San Francisco neighborhood clinics remain open in 2026.", "2026-01-01")],
        assessment={"initial_delivery": "DELIVERED_ON_TIME", "current_survival": "ACTIVE_OPERATIONAL",
                    "delivery": {"source_index": 0, "segment_id": 0},
                    "survival": {"source_index": 1, "segment_id": 0}},
        review={"delivery": True, "survival": True},
    )
    assert result["verdict"] == "KEPT"
    system = prompts["verify_evidence"][0][0]["content"]
    user = prompts["verify_evidence"][0][1]["content"]
    assert "Delivery must establish the outcome and its timing; survival must establish " \
        "the current state." in system
    assert "Only the delivery and survival sentences" not in system
    assert "Fields to evaluate" not in user and "Survival ACTIVE_OPERATIONAL" in user
    assert conn.execute("SELECT count(*) FROM verifications WHERE "
                        "check_type='outcome_basis'").fetchone() == (0,)
    conn.close()


# --- adversarial mutations and gold agreement with both flags on ------------

@pytest.mark.parametrize("rules,dates", [("1", "1"), ("1", None), (None, "1")])
def test_mutations_and_gold_hold_with_flags(monkeypatch, rules, dates):
    from tests.test_adversarial_mutations import test_adversarial_mutations_false_accept_rate
    from tests.test_gold_agreement import test_gold_set_agreement
    for name, value in ((FLAG, rules), (DATE_FLAG, dates)):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    test_adversarial_mutations_false_accept_rate()
    test_gold_set_agreement()
