"""Forward-looking weekday terms name the deadline, not the promise date."""

from datetime import date

import pytest

from src.date_resolution import (
    quote_deadline_dates, resolve_promise_date, resolve_promise_date_detail,
)

PUB = date(2006, 9, 24)  # a Sunday


@pytest.mark.parametrize("text", [
    "Westfield San Francisco Centre opens Thursday.",
    "The mall will open on Thursday.",
    "The store is scheduled to open Thursday.",
    "The city plans to start work on Friday.",
    "Construction is expected to begin Monday.",
])
def test_forward_weekday_falls_back_to_publication(text):
    assert resolve_promise_date([text], 0, PUB) == (PUB, "publication")


def test_past_tense_weekday_before_later_will_is_kept():
    text = "Supervisors voted on Tuesday to approve a garage which will open in 2027."
    assert resolve_promise_date([text], 0, PUB) == (date(2006, 9, 19), "relative")


def test_announced_wednesday_that_it_will_is_kept():
    text = "The agency announced Wednesday that it will finish the line by 2026."
    assert resolve_promise_date([text], 0, PUB) == (date(2006, 9, 20), "relative")


@pytest.mark.parametrize("text", ["The mayor said Wednesday.", "Board approved Tuesday.",
                                  "The agency unveiled the plan Friday."])
def test_past_tense_terms_still_resolve(text):
    assert resolve_promise_date([text], 0, PUB)[1] == "relative"


def test_forward_term_skipped_other_relative_term_used():
    text = "The board voted Tuesday; the mall opens Thursday."
    assert resolve_promise_date([text], 0, PUB) == (date(2006, 9, 19), "relative")


def test_deadline_dates_agree_with_forward_weekday():
    assert date(2006, 9, 28) in quote_deadline_dates("Westfield opens Thursday.", PUB)


def test_paragraph_and_lede_search_ignore_forward_terms(monkeypatch):
    monkeypatch.setenv("SF_PROMISES_OUTCOME_RULES", "1")
    text = ("The mall opens Thursday, officials said in a long opening paragraph that "
            "runs past fifteen words so it counts as the lede of the article.\n\n"
            "Officials promised the garage would be done.")
    detail = resolve_promise_date_detail(
        ["Officials promised the garage would be done."], 0, PUB,
        text=text, quote="Officials promised the garage would be done.")
    assert (detail.date, detail.basis) == (PUB, "publication")


def test_paragraph_search_still_uses_past_term(monkeypatch):
    monkeypatch.setenv("SF_PROMISES_OUTCOME_RULES", "1")
    text = "Officials said Tuesday that the garage is promised.\n\nOther text."
    quote = "Officials said Tuesday that the garage is promised."
    detail = resolve_promise_date_detail([], None, PUB, text=text, quote=quote)
    assert detail.date == date(2006, 9, 19)
