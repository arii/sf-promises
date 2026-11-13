"""Deterministic relevance gate for the SF Promises Tracker.

Code only, 0 model calls, 0 LLM calls. One run per promise at Step 2.5,
sandbox D, no write access to promises. Scores real_promise,
measurable, sf_relevant, interesting, each 0 to 2, total 0 to 8,
publish only at 5 or above AND real_promise at least 1, below 5 or
real_promise 0 to quarantined with reason relevance_low. A restated
vote scores real_promise 0 and never publishes, however high the
other scores are; N12 is the test case. See 02 section 2.

D4 rebalance (see scripts/backtest_relevance.py and
data/relevance_rebalance_backtest.json): measurable and interesting
both rewarded concrete artifacts, so a record paid twice for one
physical artifact — an address or filing/opening/count ID drove
measurable to 2 and its digits paid again in interesting — which let
capital-project promises bank a point service commitments could not
earn. Two deterministic adjustments in rebalance_interesting close
that overlap without moving the threshold: the same-artifact cap
(interesting contributes at most 1 when measurable is already 2 from
the address or filing-ID artifact and no further distinct artifact —
dollar amount, filing ID, street address — is in the text) and the
attribution credit (a record with full attribution — verbatim quote,
named speaker, date — and no concrete artifact in its text earns 1
point of interesting). Capping the number+date overlap was prototyped
and rejected by the backtest: it cut quantified service programs,
whose number+date is their only concreteness, while capital records
escaped the cap through their addresses, dollars, and IDs, moving the
margin the wrong way. The publish threshold stays 5 total with
real_promise >= 1; the verification bar is unchanged.

Callers pass explicit booleans, extracted from the saved source file
by code, not by a model. No field is guessed: a missing field scores
the lower value, it is never invented.
"""

import json
import re
from datetime import datetime, timezone

NUMBER_RE = re.compile(r"\d")
DOLLAR_RE = re.compile(r"\$\s?\d")
ADDRESS_RE = re.compile(r"\b\d{1,5}\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(St|Street|Ave|Avenue|Blvd|Road|Dr|Drive|Way|Plaza)\b")
FILE_ID_RE = re.compile(r"\b(?:\d{6}|\b[A-Z]{2,}-\d+|\bProp\s+[A-Z]\b|\bFile\s+No\.?\s*\d+)", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def score_real_promise(has_verbatim, has_speaker, has_date, is_proposal_or_aspiration_or_restated_vote):
    """2 if verbatim text plus named speaker plus date, 1 if speaker or date missing, 0 if proposal, aspiration, or restated vote."""
    if is_proposal_or_aspiration_or_restated_vote:
        return 0
    if has_verbatim and has_speaker and has_date:
        return 2
    if has_verbatim and (has_speaker or has_date):
        return 1
    return 0


def score_measurable(has_number, has_date, has_address, has_vote_filing_opening_count_with_id):
    """2 if number plus date, number plus address, or vote/filing/opening/count with ID. 1 if one of those. 0 if none."""
    if has_vote_filing_opening_count_with_id:
        return 2
    if has_number and (has_date or has_address):
        return 2
    if has_number or has_date or has_address or has_vote_filing_opening_count_with_id:
        return 1
    return 0


def score_sf_relevant(names_sf_or_sf_address_agency_ordinance, bay_area_with_sf_link):
    """2 if it names San Francisco or an SF address, agency, or ordinance. 1 if Bay Area with an SF link. 0 if outside SF with no SF link. P68 and P72 score 0."""
    if names_sf_or_sf_address_agency_ordinance:
        return 2
    if bay_area_with_sf_link:
        return 1
    return 0


def score_interesting(promise_text, has_named_entity):
    """2 if concrete number, dollar amount, street address, or statutory ordinance/file ID. 1 if named entity and year. 0 otherwise."""
    text = promise_text or ""
    if NUMBER_RE.search(text) or DOLLAR_RE.search(text) or ADDRESS_RE.search(text) or FILE_ID_RE.search(text):
        return 2
    if has_named_entity and YEAR_RE.search(text):
        return 1
    return 0


def _distinct_artifact_beyond_driver(promise_text, has_address, has_vote_filing_opening_count_with_id):
    """True when the text independently carries a concrete artifact of a different class than the measurable driver."""
    text = promise_text or ""
    if has_address:
        return bool(DOLLAR_RE.search(text) or FILE_ID_RE.search(text))
    if has_vote_filing_opening_count_with_id:
        return bool(DOLLAR_RE.search(text) or ADDRESS_RE.search(text))
    return False


def rebalance_interesting(promise_text, measurable, real_promise, raw_interesting,
                          has_address=False, has_vote_filing_opening_count_with_id=False,
                          has_named_entity=False):
    """Close the measurable/interesting overlap, deterministically, without moving the threshold.

    Two adjustments, mutually exclusive:

    1. Same-artifact cap. When measurable is already 2 driven by the physical
       artifact (a street address or a filing/opening/count ID) and
       raw_interesting is 2, the same artifact paid both criteria — the
       compounding that tilted the gate toward capital projects. Cap
       interesting at 1 unless the text independently carries a distinct
       artifact of another class (dollar amount, filing ID, street address).
       The number+date overlap is deliberately not capped: the backtest
       rejected capping it (it cut quantified service programs while capital
       records escaped through their addresses, dollars, and IDs).
    2. Attribution credit. When the text carries no concrete artifact at all
       (raw_interesting == 0) but the record is fully attributed
       (real_promise == 2: verbatim quote, named speaker, date) and names an
       entity, award 1. A verbatim, dated, named commitment is concrete
       evidence even without digits; the unadjusted gate scored it 0. Because
       real_promise 2 forces measurable >= 1 (the date is itself a measurable
       signal), this is where the credit flips a pass rate: a Bay-Area-with-
       SF-link record (sf_relevant 1) moves from 4, quarantined, to 5,
       published; an SF record gains margin, not a decision.

    The credit is gated on real_promise == 2, so no record can newly pass the
    gate without verbatim quote + named speaker + date, and a restated vote
    (real_promise 0) can never receive it.
    """
    if raw_interesting == 0:
        if real_promise == 2 and has_named_entity:
            return 1
        return 0
    if (raw_interesting == 2 and measurable == 2
            and (has_address or has_vote_filing_opening_count_with_id)
            and not _distinct_artifact_beyond_driver(
                promise_text, has_address, has_vote_filing_opening_count_with_id)):
        return 1
    return raw_interesting


def score_relevance(promise_text, has_verbatim=False, has_speaker=False, has_date=False,
                     is_proposal_or_aspiration_or_restated_vote=False, has_number=False,
                     has_address=False, has_vote_filing_opening_count_with_id=False,
                     names_sf_or_sf_address_agency_ordinance=False,
                     bay_area_with_sf_link=False, has_named_entity=False):
    """Score all four criteria. Return dict with per-criterion scores, total, publish bool."""
    real = score_real_promise(has_verbatim, has_speaker, has_date, is_proposal_or_aspiration_or_restated_vote)
    meas = score_measurable(has_number, has_date, has_address, has_vote_filing_opening_count_with_id)
    sf = score_sf_relevant(names_sf_or_sf_address_agency_ordinance, bay_area_with_sf_link)
    intr = rebalance_interesting(
        promise_text, meas, real, score_interesting(promise_text, has_named_entity),
        has_address=has_address,
        has_vote_filing_opening_count_with_id=has_vote_filing_opening_count_with_id,
        has_named_entity=has_named_entity,
    )
    total = real + meas + sf + intr
    return {
        "real_promise": real,
        "measurable": meas,
        "sf_relevant": sf,
        "interesting": intr,
        "total": total,
        "publish": total >= 5 and real >= 1,
    }


_SIGNALS = frozenset({
    "has_verbatim", "has_speaker", "has_date",
    "is_proposal_or_aspiration_or_restated_vote", "has_number", "has_address",
    "has_vote_filing_opening_count_with_id", "names_sf_or_sf_address_agency_ordinance",
    "bay_area_with_sf_link", "has_named_entity",
})


def evaluate_relevance(promise_text, signals):
    if (not isinstance(promise_text, str) or not promise_text.strip()
            or not isinstance(signals, dict) or not set(signals) <= _SIGNALS
            or any(type(value) is not bool for value in signals.values())):
        raise ValueError("Invalid relevance signals")
    return score_relevance(promise_text, **signals)


def record_relevance(conn, *, assessment_id, promise_id, promise_text, signals, evaluated_at):
    """Score verified signals, retaining input and a stable retry identity."""
    if conn.in_transaction or not conn.execute("PRAGMA foreign_keys").fetchone()[0]:
        raise ValueError("A dedicated connection with foreign keys enabled is required")
    if (not isinstance(assessment_id, str) or not assessment_id.strip()
            or not isinstance(promise_id, str) or not promise_id.strip()
            or not isinstance(evaluated_at, datetime) or evaluated_at.utcoffset() is None):
        raise ValueError("Invalid relevance assessment input")
    scores = evaluate_relevance(promise_text, signals)
    payload = json.dumps({"promise_text": promise_text, "signals": signals}, sort_keys=True)
    timestamp = evaluated_at.astimezone(timezone.utc).isoformat()
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute(
            "INSERT INTO relevance_assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(assessment_id) DO NOTHING",
            (assessment_id, promise_id, payload, scores["real_promise"], scores["measurable"],
             scores["sf_relevant"], scores["interesting"], scores["total"],
             int(scores["publish"]), timestamp),
        )
        previous = conn.execute(
            "SELECT promise_id, input_json, evaluated_at FROM relevance_assessments "
            "WHERE assessment_id = ?", (assessment_id,),
        ).fetchone()
        if tuple(previous) != (promise_id, payload, timestamp):
            raise ValueError("Assessment ID reused with different input")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return scores


if __name__ == "__main__":
    # P02: verbatim, speaker, date, number plus address, SF address, concrete number.
    # Address drives measurable 2 and pays interesting too; no dollar or filing ID
    # in the text, so the same-artifact cap holds interesting at 1. Total 7.
    print(score_relevance("24/7 crisis stabilization center at 822 Geary St, 16 beds",
                          has_verbatim=True, has_speaker=True, has_date=True,
                          has_number=True, has_address=True,
                          names_sf_or_sf_address_agency_ordinance=True, has_named_entity=True))
    # N12 restated vote: proposal/restated vote, number plus date, SF, interesting 2,
    # total 4, no publish; real_promise 0 blocks publication regardless of total.
    print(score_relevance("Board passed the Fentanyl ordinance 10 to 1",
                          has_verbatim=True, has_speaker=True, has_date=True,
                          is_proposal_or_aspiration_or_restated_vote=True, has_number=True,
                          names_sf_or_sf_address_agency_ordinance=True, has_named_entity=True))
    # P68 PayPal Park, San Jose: sf_relevant 0; attribution credit lifts interesting
    # from 0 to 1, total 4, still below the 5 threshold and never published.
    print(score_relevance("PayPal Park hosts Bay FC home opener",
                          has_verbatim=True, has_speaker=True, has_date=True,
                          has_number=False, names_sf_or_sf_address_agency_ordinance=False,
                          bay_area_with_sf_link=False, has_named_entity=True))
