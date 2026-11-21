"""OD-20 H2: the relevance gate is horizon-agnostic — recency is neither a cutoff nor a factor.

Acceptance (issue #33, OD-20 H2): a dated fixture shows an older but strongly
evidenced commitment outranking a recent but weak one, a recent-strong one
still scoring at the top, and deterministic ordering.

The implementation reaches that outcome by construction: score_relevance takes
only evidence booleans extracted from the saved source (has_verbatim,
has_speaker, has_date, ...) — no absolute date, age, window, or recency input
exists anywhere in the scoring path. These tests pin that behavior with dated
fixtures so a future change cannot reintroduce a recency cutoff, or quietly
lower the evidence bar for older backfilled items, undetected.

Fixture narrative dates are relative to a 2026-11-20 run date: the older
items sit in the 6-12 month backfill band, the recent ones inside the rolling
183-day window.
"""

import inspect

import pytest

from src.relevance import _SIGNALS, evaluate_relevance, score_relevance

# --- Dated fixtures ----------------------------------------------------------
# Strong: verbatim quote, named speaker, promise date, concrete number, SF
# agency, named entity. Weak: an aspiration with no concrete artifact.

OLDER_STRONG = {
    "promise_id": "P-OLDER-STRONG",
    # Promise made 2026-01-14, ~10 months before the run date (backfill band).
    "promise_text": (
        '"We will open 150 shelter beds in the Tenderloin by June," '
        "Mayor Daniel Lurie said on January 14, 2026."
    ),
    "signals": {
        "has_verbatim": True,
        "has_speaker": True,
        "has_date": True,
        "has_number": True,
        "names_sf_or_sf_address_agency_ordinance": True,
        "has_named_entity": True,
    },
}

RECENT_STRONG = {
    "promise_id": "P-RECENT-STRONG",
    # Promise made 2026-11-18, two days before the run date (rolling window).
    "promise_text": (
        '"We will add 40 navigation-center beds in the Mission by March," '
        "Supervisor Jane Fielder said on November 18, 2026."
    ),
    "signals": dict(OLDER_STRONG["signals"]),
}

RECENT_WEAK = {
    "promise_id": "P-RECENT-WEAK",
    # Floated 2026-11-19, one day before the run date: an aspiration, no
    # verbatim quote, no date, no concrete artifact.
    "promise_text": "The Mayor said the city will explore ways to keep neighborhood streets safer.",
    "signals": {
        "has_speaker": True,
        "is_proposal_or_aspiration_or_restated_vote": True,
        "has_named_entity": True,
    },
}

OLDER_WEAK = {
    "promise_id": "P-OLDER-WEAK",
    # Same aspiration, floated 2025-12-09, ~11 months before the run date.
    "promise_text": "The Mayor said the city would study the proposal further.",
    "signals": dict(RECENT_WEAK["signals"]),
}

FIXTURES = [OLDER_STRONG, RECENT_STRONG, RECENT_WEAK, OLDER_WEAK]


def _score(fixture):
    return score_relevance(fixture["promise_text"], **fixture["signals"])


SCORES = {fixture["promise_id"]: _score(fixture) for fixture in FIXTURES}


# --- H2 acceptance: older-strong outranks recent-weak -------------------------

def test_older_strong_outranks_recent_weak():
    older = SCORES[OLDER_STRONG["promise_id"]]
    weaker = SCORES[RECENT_WEAK["promise_id"]]
    assert older["publish"] is True
    assert weaker["publish"] is False
    assert older["total"] > weaker["total"]


def test_recent_strong_still_top():
    recent = SCORES[RECENT_STRONG["promise_id"]]
    assert recent["publish"] is True
    assert recent["total"] == max(s["total"] for s in SCORES.values())


def test_ordering_is_deterministic():
    def ordered():
        return [
            f["promise_id"]
            for f in sorted(FIXTURES, key=lambda f: (-_score(f)["total"], f["promise_id"]))
        ]

    first, second = ordered(), ordered()
    assert first == second
    assert first.index(OLDER_STRONG["promise_id"]) < first.index(RECENT_WEAK["promise_id"])
    # Scoring is a pure function: repeated evaluation is byte-identical.
    for fixture in FIXTURES:
        assert _score(fixture) == SCORES[fixture["promise_id"]]


# --- One evidence bar across the horizon --------------------------------------

def test_identical_evidence_scores_identically_at_any_age():
    """Same evidence profile, different promise age: identical scores."""
    assert SCORES[OLDER_STRONG["promise_id"]] == SCORES[RECENT_STRONG["promise_id"]]
    assert SCORES[OLDER_WEAK["promise_id"]] == SCORES[RECENT_WEAK["promise_id"]]


def test_bar_is_not_lowered_for_older_items():
    """An older weak item fails the gate exactly like a recent weak one —
    backfill cannot produce mass verdict upgrades."""
    for fixture in (OLDER_WEAK, RECENT_WEAK):
        scores = SCORES[fixture["promise_id"]]
        assert scores["real_promise"] == 0
        assert scores["publish"] is False


# --- Structural pin: no recency input can enter scoring ------------------------

def test_scoring_signature_has_no_recency_input():
    """score_relevance takes only the promise text and the documented evidence
    booleans. has_date records that the promise carries a date, never how old
    it is; no parameter may carry an age, window, or absolute date."""
    params = set(inspect.signature(score_relevance).parameters)
    assert params == {"promise_text"} | _SIGNALS
    forbidden = {"age", "recency", "window", "horizon", "published", "encountered", "evaluated"}
    for name in params:
        tokens = set(name.split("_"))
        assert not tokens & forbidden, f"recency-like input {name!r} entered scoring"


def test_evaluate_relevance_rejects_a_window_like_signal():
    """An injected window/horizon signal fails closed instead of scoring."""
    with pytest.raises(ValueError):
        evaluate_relevance(
            "Build 10 new homes in San Francisco",
            {"has_verbatim": True, "published_after": True},
        )
