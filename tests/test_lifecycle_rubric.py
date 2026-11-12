import unittest
from datetime import date

from src.lifecycle_rubric import decide_verdict


class VerdictTests(unittest.TestCase):
    def test_future_deadline_requires_evidence(self):
        today = date(2026, 1, 1)
        deadline = date(2028, 1, 1)
        self.assertIsNone(decide_verdict(deadline, today, "PENDING_FUTURE_DEADLINE",
                                         "NOT_YET_OPEN", False))
        self.assertEqual(decide_verdict(deadline, today, "PENDING_FUTURE_DEADLINE",
                                        "NOT_YET_OPEN", True), "IN_PROGRESS")

    def test_proven_early_completion_and_later_reversal(self):
        self.assertEqual(decide_verdict(date(2028, 1, 1), date(2026, 1, 1),
                                        "DELIVERED_ON_TIME", "ACTIVE_OPERATIONAL",
                                        True), "KEPT")
        self.assertEqual(decide_verdict(date(2022, 1, 1), date(2026, 1, 1),
                                        "DELIVERED_ON_TIME", "SHUTTERED_OR_CLOSED",
                                        True), "KEPT_THEN_REVERSED")

    def test_unverified_or_inconsistent_facts_are_not_verdicts(self):
        self.assertIsNone(decide_verdict(date(2020, 1, 1), date(2026, 1, 1),
                                         "NOT_DELIVERED", "ACTIVE_OPERATIONAL", True))
        self.assertIsNone(decide_verdict(date(2020, 1, 1), date(2026, 1, 1),
                                         "DELIVERED_LATE", "ACTIVE_OPERATIONAL", False))
        self.assertIsNone(decide_verdict(date(2020, 1, 1), date(2026, 1, 1),
                                         "PARTIALLY_DELIVERED", "SHUTTERED_OR_CLOSED", True))

    def test_abandonment_after_delivery_is_not_mislabeled_never_delivered(self):
        self.assertEqual(
            decide_verdict(date(2020, 1, 1), date(2026, 1, 1),
                           "DELIVERED_ON_TIME", "REVOKED_OR_HALTED", True,
                           explicitly_abandoned=True),
            "KEPT_THEN_REVERSED",
        )
        self.assertIsNone(
            decide_verdict(date(2020, 1, 1), date(2026, 1, 1),
                           "PARTIALLY_DELIVERED", "REVOKED_OR_HALTED", True,
                           explicitly_abandoned=True),
        )
        self.assertIsNone(
            decide_verdict(date(2020, 1, 1), date(2026, 1, 1),
                           "PENDING_FUTURE_DEADLINE", "REVOKED_OR_HALTED", True,
                           explicitly_abandoned=True),
        )


if __name__ == "__main__":
    unittest.main()
