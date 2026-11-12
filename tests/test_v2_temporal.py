import unittest
from datetime import date

from src.v2_temporal import check_origin_dates, deadline_from_quote, screen_forward_looking


class TemporalGateTests(unittest.TestCase):
    def test_deadline_proposals_are_bounded_by_quoted_commitment(self):
        published = date(2025, 11, 18)
        self.assertEqual(deadline_from_quote(
            "Zoox said its goal is to remove the waitlist altogether in 2026.",
            published=published,
        ), date(2026, 12, 31))
        self.assertEqual(deadline_from_quote(
            "We will build a library by February 2028.", published=published,
        ), date(2028, 2, 29))
        self.assertEqual(deadline_from_quote(
            "We will build a library by the end of the year.", published=published,
        ), date(2025, 12, 31))
        self.assertIsNone(deadline_from_quote("The building opened in 2026."))
        self.assertIsNone(deadline_from_quote(
            "We will start in 2026 and finish in 2027."
        ))

    def test_historical_descriptive_deadlines_require_an_anchor(self):
        self.assertEqual(deadline_from_quote(
            "We will build a library by end of year.", published=date(2018, 3, 5),
        ), date(2018, 12, 31))
        self.assertEqual(deadline_from_quote(
            "We will build a library by end of 2021.", published=date(2018, 3, 5),
        ), date(2021, 12, 31))
        self.assertEqual(deadline_from_quote(
            "We will complete the project within five years.",
            promised=date(2018, 3, 5),
        ), date(2023, 12, 31))
        self.assertIsNone(deadline_from_quote(
            "We will complete the project within five years.",
            published=date(2018, 3, 5),
        ))
        self.assertIsNone(deadline_from_quote(
            "We will complete the project.", promised=date(2018, 3, 5),
        ))
        self.assertIsNone(deadline_from_quote(
            "We will start in 2020 and finish within five years.",
            promised=date(2018, 3, 5),
        ))

    def test_inclusive_publication_and_horizon_boundaries(self):
        self.assertEqual(
            check_origin_dates(date(2024, 1, 1), date(2024, 1, 31),
                               date(2024, 3, 1)),
            [],
        )

    def test_rejects_late_source_and_short_horizon(self):
        errors = check_origin_dates(date(2024, 1, 1), date(2024, 2, 1),
                                    date(2024, 2, 29))
        self.assertIn("origin_publication_late", errors)
        self.assertIn("promise_horizon_short", errors)

    def test_missing_and_predating_dates_fail_closed(self):
        self.assertIn(
            "origin_date_missing",
            check_origin_dates(date(2024, 1, 1), None, date(2024, 3, 1)),
        )
        self.assertNotIn(
            "origin_predates_promise",
            check_origin_dates(date(2024, 1, 1), date(2023, 12, 31),
                               date(2024, 3, 1)),
        )
        self.assertIn(
            "origin_predates_promise",
            check_origin_dates(date(2024, 1, 1), date(2023, 12, 17),
                               date(2024, 3, 1)),
        )

    def test_historical_exception_requires_saved_original_date_and_quote(self):
        kwargs = dict(
            historical_official=True,
            historical_origin_confirmed=True,
            quote="We will build a new library.",
            source_text="On 2020-01-01: We will build a new library.",
        )
        self.assertEqual(
            check_origin_dates(date(2020, 1, 1), date(2024, 1, 1),
                               date(2021, 1, 1), **kwargs),
            [],
        )
        kwargs["source_text"] = "The library was completed."
        self.assertIn(
            "historical_origin_unverified",
            check_origin_dates(date(2020, 1, 1), date(2024, 1, 1),
                               date(2021, 1, 1), **kwargs),
        )

    def test_historical_source_without_review_is_not_accepted(self):
        self.assertIn(
            "historical_origin_unverified",
            check_origin_dates(
                date(2020, 1, 1), date(2024, 1, 1), date(2021, 1, 1),
                historical_official=True, quote="We will build a library.",
                source_text="On 2020-01-01: We will build a library.",
            ),
        )

    def test_official_record_without_publication_date_is_blocked(self):
        self.assertIn(
            "origin_date_missing",
            check_origin_dates(
                date(2020, 1, 1), None, date(2021, 1, 1),
                historical_official=True, historical_origin_confirmed=True,
                quote="We will build a library.",
                source_text="On 2020-01-01: We will build a library.",
            ),
        )

    def test_retrospective_wording_is_not_a_forward_looking_origin(self):
        self.assertIn("retrospective_wording", screen_forward_looking(
            "The mayor had promised to build a library."
        ))
        self.assertEqual(screen_forward_looking("We will build a library."), [])
        self.assertIn("quote_missing", screen_forward_looking(None))


if __name__ == "__main__":
    unittest.main()
