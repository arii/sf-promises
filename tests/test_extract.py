import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from src.extract import parse_extraction
from src.sources import archive_source


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.saved = archive_source(
            self.root, "P1", b"Mayor: We will build a library.", ".txt"
        )
        self.candidate = {
            "promise_id": "P1", "promise_text": "We will build a library.",
            "speaker": "Mayor", "promised_date": "2024-01-01",
            "deadline": None,
        }

    def tearDown(self):
        self.directory.cleanup()

    def parse(self, candidate=None):
        return parse_extraction(
            root=self.root, promise_id="P1", path=self.saved["path"],
            digest=self.saved["sha256"],
            response=json.dumps({"candidates": [candidate or self.candidate]}),
        )

    def test_extracts_only_verbatim_text_without_inventing_missing_date(self):
        candidate = self.parse()[0]
        self.assertEqual(candidate.promise_text, "We will build a library.")
        self.assertIsNone(candidate.deadline)

    def test_rejects_hallucinated_quote_or_cross_promise_id(self):
        for update in ({"promise_text": "A made up promise."}, {"promise_id": "P2"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.parse(self.candidate | update)

    def test_rejects_unexpected_fields_and_invalid_dates(self):
        for update in ({"unexpected": "x"}, {"promised_date": "2024-02-31"}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.parse(self.candidate | update)

    def test_case_or_spacing_changes_are_not_verbatim_extractions(self):
        for quote in ("we will build a library.", "We  will build a library."):
            with self.subTest(quote=quote), self.assertRaises(ValueError):
                self.parse(self.candidate | {"promise_text": quote})

    def test_refuses_changed_saved_source(self):
        Path(self.saved["path"]).write_text("Altered.", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.parse()

    def test_year_only_deadline_overrides_invented_start_of_year(self):
        quote = "Zoox said its goal is to remove the waitlist altogether in 2026."
        saved = archive_source(self.root, "P1", quote.encode(), ".txt")
        candidate = self.candidate | {
            "promise_text": quote, "promised_date": "2025-11-18",
            "deadline": "2026-01-01",
        }
        result = parse_extraction(
            root=self.root, promise_id="P1", path=saved["path"], digest=saved["sha256"],
            response=json.dumps({"candidates": [candidate]}), published=date(2025, 11, 18),
        )
        self.assertEqual(result[0].deadline, date(2026, 12, 31))

    def test_explicit_day_is_not_replaced_by_year_end(self):
        quote = "We will open January 1, 2026 and complete the project by 2026."
        saved = archive_source(self.root, "P1", quote.encode(), ".txt")
        candidate = self.candidate | {
            "promise_text": quote, "promised_date": "2024-01-01",
            "deadline": "2026-01-01",
        }
        result = parse_extraction(
            root=self.root, promise_id="P1", path=saved["path"], digest=saved["sha256"],
            response=json.dumps({"candidates": [candidate]}),
        )
        self.assertEqual(result[0].deadline, date(2026, 1, 1))


if __name__ == "__main__":
    unittest.main()
