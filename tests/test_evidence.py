import tempfile
import unittest
from pathlib import Path

from src.evidence import is_allowlisted_url, screen_saved_source
from src.sources import archive_source


class EvidenceScreenTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.saved = archive_source(self.root, "P1", b"We will build a library.", ".txt")

    def tearDown(self):
        self.directory.cleanup()

    def screen(self, **overrides):
        values = {
            "root": self.root,
            "promise_id": "P1",
            "path": self.saved["path"],
            "digest": self.saved["sha256"],
            "quote": "We will build a library.",
            "url": "https://sf.gov/news/example",
            "source_tier": "TIER1_GOV",
        }
        values.update(overrides)
        return screen_saved_source(**values)

    def test_valid_source_passes_preliminary_screen(self):
        self.assertEqual(self.screen(), [])

    def test_malicious_authority_and_non_https_are_rejected(self):
        for url in ("https://sf.gov:443@evil.example/path", "http://sf.gov/path"):
            with self.subTest(url=url):
                self.assertIn("source_domain_unlisted", self.screen(url=url))

    def test_news_or_unknown_host_cannot_self_declare_government_tier(self):
        for url in ("https://sfstandard.com/example", "https://sf.gov.evil.example/example",
                    "https://en.wikipedia.org/wiki/example"):
            with self.subTest(url=url):
                self.assertIn("government_source_unverified", self.screen(url=url))

    def test_city_official_hosts_pass_preliminary_tier_check(self):
        for url in ("https://sf.gov/news/example", "https://www.sfmta.com/example"):
            with self.subTest(url=url):
                self.assertNotIn("government_source_unverified", self.screen(url=url))

    def test_primary_news_and_denied_domains(self):
        for url in ("https://www.zoox.com/news", "https://research.example.edu/news",
                    "https://agency.example.mil/news"):
            with self.subTest(url=url):
                self.assertEqual(self.screen(url=url), [])
        self.assertEqual(self.screen(url="https://techcrunch.com/news",
                                     source_tier="TIER2_NEWS"), [])
        for url in ("https://en.wikipedia.org/page", "https://medium.com/post",
                    "https://techcrunch.com.evil.example/news", "https://127.0.0.1/"):
            with self.subTest(url=url):
                self.assertFalse(is_allowlisted_url(url))

    def test_tamper_missing_quote_and_canary_are_not_evidence(self):
        self.assertIn("quote_not_found", self.screen(quote="Different quote"))
        self.assertIn("canary_not_evidence", self.screen(source_tier="TIER3_CANARY"))
        Path(self.saved["path"]).write_text("Altered source", encoding="utf-8")
        self.assertIn("source_hash_mismatch", self.screen())

    def test_source_for_another_promise_is_rejected(self):
        self.assertIn("source_path_invalid", self.screen(promise_id="P2"))

    def test_non_string_quote_fails_closed(self):
        self.assertIn("quote_not_found", self.screen(quote={"text": "not a string"}))

    def test_case_or_spacing_changes_are_not_verbatim_quotes(self):
        for quote in ("we will build a library.", "We  will build a library."):
            with self.subTest(quote=quote):
                self.assertIn("quote_not_found", self.screen(quote=quote))

    def test_invalid_path_has_a_stable_failure_code(self):
        self.assertIn("source_unavailable", self.screen(path="bad\0path"))


if __name__ == "__main__":
    unittest.main()
