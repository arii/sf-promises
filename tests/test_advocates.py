import json
import tempfile
import unittest
from pathlib import Path

from src.advocates import stage_advocate
from src.sources import archive_source


class AdvocateStagingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.sources = self.root / "sources"
        self.staging = self.root / "staging"
        source = archive_source(self.sources, "P1", b"The library opened.", ".txt")
        self.claim = {
            "statement": "The library opened.",
            "phase": "DELIVERY",
            "url": "https://sf.gov/news/example",
            "source_tier": "TIER1_GOV",
            "path": source["path"],
            "digest": source["sha256"],
            "quote": "The library opened.",
        }

    def tearDown(self):
        self.directory.cleanup()

    def stage(self, role, claim=None):
        return stage_advocate(
            staging_root=self.staging, source_root=self.sources, promise_id="P1",
            role=role, response=json.dumps({
                "promise_id": "P1", "role": role,
                "claims": [] if claim is None else [claim],
            }),
        )

    def test_kept_and_broken_are_separate_and_retry_safe(self):
        kept = self.stage("kept", self.claim)
        broken = self.stage("broken")
        self.assertEqual(self.stage("kept", self.claim), kept)
        self.assertEqual(kept.name, "kept_P1.json")
        self.assertEqual(broken.name, "broken_P1.json")
        self.assertEqual(json.loads(kept.read_text())["claims"][0]["quote"],
                         "The library opened.")
        self.assertEqual(json.loads(broken.read_text())["claims"], [])

    def test_unverified_quote_is_not_staged(self):
        with self.assertRaises(ValueError):
            self.stage("kept", self.claim | {"quote": "Fabricated"})
        self.assertFalse((self.staging / "kept_P1.json").exists())

    def test_existing_bundle_is_not_overwritten(self):
        path = self.stage("kept", self.claim)
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            self.stage("kept")
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
