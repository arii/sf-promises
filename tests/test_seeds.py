import unittest

from src.seeds import build_leads


class SeedLeadTests(unittest.TestCase):
    def test_duplicates_are_flagged_without_merging_or_trusting_snapshot(self):
        snapshot = {"promises": [
            {"promise_id": "P1", "source_id": "S1", "promise_text": "Build a library"},
            {"promise_id": "P2", "source_id": "S1", "promise_text": "build  a library"},
        ]}
        result = build_leads(snapshot)
        self.assertEqual([x["promise_id"] for x in result["leads"]], ["P1", "P2"])
        self.assertEqual(result["duplicate_text_groups"], [["P1", "P2"]])
        self.assertEqual(result["shared_source_groups"], [["P1", "P2"]])
        self.assertTrue(result["discovery_only"])

    def test_missing_or_duplicate_identity_is_rejected(self):
        for records in (
            [{"promise_text": "x"}],
            [{"promise_id": "P1"}, {"promise_id": "P1"}],
        ):
            with self.subTest(records=records), self.assertRaises(ValueError):
                build_leads({"promises": records})


if __name__ == "__main__":
    unittest.main()
