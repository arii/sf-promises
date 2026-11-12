import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from src.v2_discovery import discover_timeline, fetch_and_archive, pool_outcome_sources, search_window
from src.v2_sources import load_archived_text


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    def test_pool_dated_outcome_sources_from_both_searches(self):
        source = {"url": "https://sf.gov/report", "sha256": "abc",
                  "published_at": "2022-01-01"}
        phases = {
            "delivery": {"sources": [source]},
            "survival": {"sources": [
                source,
                {"url": "https://sf.gov/later", "sha256": "def",
                 "published_at": "2025-01-01"},
                {"url": "https://sf.gov/undated", "sha256": "ghi",
                 "published_at": None},
                {"url": "https://sf.gov/old", "sha256": "jkl",
                 "published_at": "2019-01-01"},
            ]},
        }
        pool = pool_outcome_sources(phases, promised=date(2020, 1, 1),
                                    as_of=date(2026, 1, 1))
        self.assertEqual([item["url"] for item in pool],
                         ["https://sf.gov/report", "https://sf.gov/later"])

    async def test_temporal_search_uses_documented_filters(self):
        class Client:
            async def search(self, query, **kwargs):
                self.args = query, kwargs
                return SimpleNamespace(results=["lead"])

        client = Client()
        result = await search_window(client, "library", "2020-01-01", "2020-02-01")
        self.assertEqual(result, ["lead"])
        self.assertEqual(client.args[1]["published_before"], "2020-02-01")
        self.assertEqual(client.args[1]["published_after"], "2020-01-01")
        self.assertEqual(client.args[1]["max_results"], 8)

    async def test_archive_full_response_but_not_truncated_page(self):
        class Client:
            async def fetch(self, url):
                return SimpleNamespace(content="Actual source", raw={"truncated": self.truncated},
                                       published_at="2020-01-01",
                                       url=getattr(self, "final_url", url))

        client = Client()
        with tempfile.TemporaryDirectory() as root:
            client.truncated = False
            source = await fetch_and_archive(client, "https://sf.gov/x", Path(root), "P01")
            self.assertEqual(Path(source["path"]).read_text(), "Actual source")
            metadata = Path(source["metadata_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(metadata).hexdigest(), source["metadata_sha256"])
            record = json.loads(metadata)
            self.assertEqual(record["url"], "https://sf.gov/x")
            self.assertEqual(record["requested_url"], "https://sf.gov/x")
            self.assertEqual(record["sha256"], source["sha256"])
            self.assertEqual(record["published_at"], "2020-01-01")
            with self.assertRaises(ValueError):
                load_archived_text(root, "P01", source["metadata_path"], source["metadata_sha256"])
            client.truncated = True
            with self.assertRaises(ValueError):
                await fetch_and_archive(client, "https://sf.gov/y", Path(root), "P01")

    async def test_unallowlisted_request_and_redirect_are_not_archived(self):
        class Client:
            calls = 0

            async def fetch(self, url):
                self.calls += 1
                return SimpleNamespace(content="Actual source", raw={"truncated": False},
                                       published_at=None, url="https://evil.example/x")

        client = Client()
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                await fetch_and_archive(client, "https://evil.example/x", Path(root), "P01")
            self.assertEqual(client.calls, 0)
            with self.assertRaises(ValueError):
                await fetch_and_archive(client, "https://sf.gov/x", Path(root), "P01")
            self.assertFalse((Path(root) / "P01").exists())

    async def test_three_phase_search_uses_bounded_temporal_windows(self):
        class Client:
            def __init__(self):
                self.calls = []

            async def search(self, query, **kwargs):
                self.calls.append((query, kwargs))
                return SimpleNamespace(results=[query])

        client = Client()
        results = await discover_timeline(
            client, "the library project", promised=date(2024, 1, 1),
            deadline=date(2024, 8, 31), delivered=date(2024, 8, 15),
            as_of=date(2025, 3, 1),
        )
        self.assertEqual(list(results), ["origin", "delivery", "survival"])
        windows = [(kwargs["published_after"], kwargs["published_before"])
                   for _, kwargs in client.calls]
        self.assertEqual(windows, [
            ("2023-12-18", "2024-01-31"),
            ("2024-01-01", "2025-02-28"),
            ("2024-08-15", "2025-03-01"),
        ])

    async def test_missing_deadline_or_delivery_does_not_invent_a_date(self):
        class Client:
            def __init__(self):
                self.calls = []

            async def search(self, query, **kwargs):
                self.calls.append(kwargs)
                return SimpleNamespace(results=[])

        client = Client()
        await discover_timeline(
            client, "library", promised=date(2024, 1, 1),
            deadline=None, delivered=None, as_of=date(2024, 4, 1),
        )
        self.assertEqual(client.calls[1]["published_before"], "2024-04-01")
        self.assertEqual(client.calls[2]["published_after"], "2024-01-01")


if __name__ == "__main__":
    unittest.main()
