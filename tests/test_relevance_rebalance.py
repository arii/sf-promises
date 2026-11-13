"""D4 relevance-gate rebalance: capped scoring rule + frozen-corpus strictness backtest.

The publish threshold (total >= 5 with real_promise >= 1) and the never-publish
rule for restated votes are unchanged by the rebalance; these tests hold that
line. The backtest half replays the frozen corpora through
scripts/backtest_relevance.py and asserts the strictness criteria from the
spec's D4 acceptance table.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.relevance import rebalance_interesting, score_relevance

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKTEST_JSON = REPO_ROOT / "data" / "relevance_rebalance_backtest.json"


def score(text, **signals):
    return score_relevance(text, **signals)


# --- Same-artifact cap -------------------------------------------------------

def test_cap_holds_interesting_at_1_when_address_drives_both_criteria():
    # The address drives measurable to 2 and pays interesting again; no dollar
    # amount or filing ID in the text, so interesting contributes at most 1.
    result = score(
        "24/7 crisis stabilization center at 822 Geary St, 16 beds",
        has_verbatim=True, has_speaker=True, has_date=True,
        has_number=True, has_address=True,
        names_sf_or_sf_address_agency_ordinance=True, has_named_entity=True,
    )
    assert result["measurable"] == 2
    assert result["interesting"] == 1
    assert result["total"] == 7
    assert result["publish"] is True


def test_cap_exempts_a_distinct_dollar_artifact():
    # Address drove measurable, but the text independently carries a dollar
    # amount: two distinct artifact classes, full interesting credit stays.
    result = score(
        "New shelter at 822 Geary St with a $16 million budget",
        has_verbatim=True, has_speaker=True, has_date=True,
        has_number=True, has_address=True,
        names_sf_or_sf_address_agency_ordinance=True, has_named_entity=True,
    )
    assert result["measurable"] == 2
    assert result["interesting"] == 2


def test_cap_exempts_a_distinct_filing_id_when_id_drives_measurable():
    # Filing ID drove measurable to 2; the text independently carries a street
    # address, a different artifact class, so interesting keeps full credit.
    result = score(
        "Housing filings 2025-0123 cover 1500 units at 822 Geary St",
        has_verbatim=True, has_speaker=True, has_date=True,
        has_number=True, has_vote_filing_opening_count_with_id=True,
        names_sf_or_sf_address_agency_ordinance=True, has_named_entity=True,
    )
    assert result["measurable"] == 2
    assert result["interesting"] == 2


def test_number_and_date_overlap_is_not_capped():
    # Quantified service commitments: number+date drives measurable, and their
    # digits pay interesting. The backtest rejected capping this overlap (it
    # cut service programs while capital records escaped via distinct
    # artifacts), so it stays at full credit.
    result = score(
        "We will open 1500 new shelter beds within six months",
        has_verbatim=True, has_speaker=True, has_date=True,
        has_number=True, names_sf_or_sf_address_agency_ordinance=True,
        has_named_entity=True,
    )
    assert result["measurable"] == 2
    assert result["interesting"] == 2
    assert result["total"] == 8


def test_cap_needs_measurable_already_at_2():
    result = score(
        "A facility at 822 Geary St",
        has_verbatim=True, has_speaker=True, has_date=True,
        has_address=True,
        names_sf_or_sf_address_agency_ordinance=True, has_named_entity=True,
    )
    # measurable is 1 here (address, no number or ID), so no cap applies.
    assert result["measurable"] == 1
    assert result["interesting"] == 2


# --- Attribution credit ------------------------------------------------------

def test_attribution_credit_lifts_digit_free_service_commitment_over_the_line():
    # Full attribution (verbatim quote + named speaker + date) with no concrete
    # artifact in the text. real_promise 2 forces measurable >= 1 (the date is
    # a measurable signal), so where the credit flips a pass rate is a record
    # with sf_relevant only 1: before, 2 + 1 + 1 + 0 = 4, quarantined; the
    # credit awards 1 and it clears the unchanged 5 threshold.
    result = score(
        "We will expand rental assistance to every eligible family in the city",
        has_verbatim=True, has_speaker=True, has_date=True,
        names_sf_or_sf_address_agency_ordinance=False,
        bay_area_with_sf_link=True, has_named_entity=True,
    )
    assert result["real_promise"] == 2
    assert result["measurable"] == 1
    assert result["sf_relevant"] == 1
    assert result["interesting"] == 1
    assert result["total"] == 5
    assert result["publish"] is True


def test_attribution_credit_requires_full_attribution():
    # Same digit-free text, but the date is missing: real_promise 1, credit
    # denied, stays below the threshold.
    result = score(
        "We will expand rental assistance to every eligible family in the city",
        has_verbatim=True, has_speaker=True,
        names_sf_or_sf_address_agency_ordinance=False,
        bay_area_with_sf_link=True, has_named_entity=True,
    )
    assert result["real_promise"] == 1
    assert result["interesting"] == 0
    assert result["total"] == 2
    assert result["publish"] is False


def test_attribution_credit_requires_a_named_entity():
    # Without the named entity the credit is denied and the record stays at
    # 2 + 1 + 1 + 0 = 4, below the unchanged threshold.
    result = score(
        "We will expand rental assistance to every eligible family in the city",
        has_verbatim=True, has_speaker=True, has_date=True,
        names_sf_or_sf_address_agency_ordinance=False,
        bay_area_with_sf_link=True,
    )
    assert result["real_promise"] == 2
    assert result["interesting"] == 0
    assert result["total"] == 4
    assert result["publish"] is False


def test_rebalance_interesting_is_total_over_raw_one():
    # raw_interesting == 1 (named entity + year, no concrete artifact) passes
    # through both the cap (which only trims raw 2) and the credit (raw 0).
    assert rebalance_interesting(
        "The program launched in 2025", 2, 2, 1,
        has_address=True, has_named_entity=True) == 1


# --- Unchanged gate semantics ------------------------------------------------

def test_threshold_and_real_promise_gate_are_unchanged():
    # Total 5 with real_promise 0 never publishes...
    result = score(
        "Board passed the Fentanyl ordinance 10 to 1",
        has_verbatim=True, has_speaker=True, has_date=True,
        is_proposal_or_aspiration_or_restated_vote=True, has_number=True,
        names_sf_or_sf_address_agency_ordinance=True, has_named_entity=True,
    )
    assert result["real_promise"] == 0
    assert result["total"] >= 5
    assert result["publish"] is False
    # ...and total 4 with full attribution still does not publish.
    result = score(
        "PayPal Park hosts Bay FC home opener",
        has_verbatim=True, has_speaker=True, has_date=True,
        names_sf_or_sf_address_agency_ordinance=False,
        bay_area_with_sf_link=False, has_named_entity=True,
    )
    assert result["real_promise"] == 2
    assert result["sf_relevant"] == 0
    assert result["total"] == 4
    assert result["publish"] is False


def test_restated_vote_never_publishes_under_the_rebalance():
    result = score(
        "Board passed the Fentanyl ordinance 10 to 1",
        has_verbatim=True, has_speaker=True, has_date=True,
        is_proposal_or_aspiration_or_restated_vote=True, has_number=True,
        has_address=True, names_sf_or_sf_address_agency_ordinance=True,
        has_named_entity=True,
    )
    assert result["real_promise"] == 0
    assert result["publish"] is False


# --- Frozen-corpus backtest (spec D4 acceptance criteria 1-3) ----------------

@pytest.fixture(scope="module")
def backtest_artifact():
    artifact_before = BACKTEST_JSON.read_text() if BACKTEST_JSON.exists() else None
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "backtest_relevance.py")],
        check=True, capture_output=True,
    )
    artifact = json.loads(BACKTEST_JSON.read_text())
    if artifact_before is not None:
        # The generator is deterministic: a rerun must reproduce the checked-in
        # artifact byte for byte.
        assert BACKTEST_JSON.read_text() == artifact_before, (
            "backtest artifact is stale: rerun scripts/backtest_relevance.py "
            "and commit the regenerated file"
        )
    return artifact


def test_backtest_no_decision_changes_on_the_frozen_corpora(backtest_artifact):
    # No published record loses its pass and no quarantined record gains one:
    # the rebalance moves the margin around the threshold, not decisions.
    strictness = backtest_artifact["strictness"]
    assert strictness["newly_published"] == []
    assert strictness["unpublished_by_rebalance"] == []
    assert backtest_artifact["flips_up"] == []
    assert backtest_artifact["flips_down"] == []


def test_backtest_zero_newly_published_without_full_attribution(backtest_artifact):
    # Criterion 3: zero records newly passing lack verbatim quote + named
    # speaker + date. Every flip-up must carry real_promise == 2, which for
    # this gate is exactly that attribution trio.
    for entry in backtest_artifact["flips_up"]:
        assert entry["real_promise_after"] == 2


def test_backtest_threshold_unchanged(backtest_artifact):
    assert backtest_artifact["threshold"] == {
        "total": 5, "real_promise": 1, "note": "unchanged by the rebalance",
    }


def test_backtest_service_style_gains_margin_and_loses_nothing(backtest_artifact):
    # Criterion 2: service/program pass rate does not decrease (on the frozen
    # corpora it structurally cannot increase: every fully attributed service
    # record already passes, and the frozen gate failures are attribution or
    # geography exclusions). The rebalance's measured effect is the margin:
    # service mean total rises while the capital mean falls.
    styles = backtest_artifact["per_style"]
    service, capital = styles["service_program"], styles["capital_project"]
    assert service["pass_rate_after"] >= service["pass_rate_before"]
    assert service["mean_total_after"] > service["mean_total_before"]
    assert capital["mean_total_after"] < capital["mean_total_before"]


def test_backtest_reconciles_with_a_live_replay(backtest_artifact):
    # Regenerating above already proved byte-identical determinism; here,
    # assert the checked-in artifact describes the same corpora sizes the
    # generator reads today, so a corpus edit cannot pass silently.
    doc = json.loads((REPO_ROOT / "docs" / "data.json").read_text())
    register = json.loads((REPO_ROOT / "data" / "intake_candidate_register.json").read_text())
    qualified = [c for c in register["candidates"] if c.get("qualification_status") == "qualified"]
    expected_n = len(doc["promises"]) + len(doc["quarantined"]) + len(qualified)
    assert sum(s["n"] for s in backtest_artifact["per_style"].values()) == expected_n
