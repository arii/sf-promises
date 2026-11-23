import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from keenable import KeenableAPIError, KeenableConnectionError

from keenable_stubs import fetch_response
from src.discovery import (
    discover_and_archive, discover_timeline, fetch_and_archive, pool_outcome_sources, search_window,
)
from src.sources import load_archived_text


class DiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_retains_original_news_lead_and_distinguishes_origin_rejections(self):
        original = "https://missionlocal.org/pledge"
        denied = "https://en.wikipedia.org/wiki/project"
        incomplete = [f"https://sf.gov/incomplete-{i}" for i in range(3)]
        another = "https://sf.gov/announcement"

        class Client:
            def __init__(self):
                self.fetched = []

            async def search(self, query, **kwargs):
                urls = [denied, *incomplete, another, original] if "pledged" in query else []
                return SimpleNamespace(results=[SimpleNamespace(url=url) for url in urls])

            async def fetch(self, url, **options):
                self.fetched.append(url)
                return fetch_response(url, "Archived statement", "2024-01-01",
                                      truncated=url in incomplete)

        client = Client()
        with tempfile.TemporaryDirectory() as root:
            result = await discover_and_archive(
                client, {"promise_id": "P01", "promised_date": "2024-01-01",
                         "source_url": original, "entity": "Library",
                         "promise_text": "Open a library branch"},
                root=Path(root), as_of=date(2025, 1, 1),
            )
            origin = result["phases"]["origin"]
            self.assertEqual([item["url"] for item in origin["sources"]], [original, another])
            self.assertEqual(client.fetched, [original, *incomplete, another])
            self.assertEqual([item["url"] for item in origin["blocked"]], incomplete)
            self.assertEqual(origin["denied"], [{"url": denied, "reason": "source_url_not_allowlisted"}])

    async def test_dead_original_url_does_not_block_search_hits(self):
        original = "https://missionlocal.org/removed"
        fallback = "https://sf.gov/original-announcement"
        outcome = "https://sf.gov/project-opening"

        class Client:
            async def search(self, query, **kwargs):
                url = fallback if "pledged" in query else outcome
                return SimpleNamespace(results=[SimpleNamespace(url=url)])

            async def fetch(self, url, **options):
                if url == original:
                    raise KeenableAPIError("Page not found", status_code=404)
                return fetch_response(url, "Archived statement", "2024-01-02")

        with tempfile.TemporaryDirectory() as root:
            result = await discover_and_archive(
                Client(), {"promise_id": "P01", "promised_date": "2024-01-01",
                           "source_url": original, "entity": "Library",
                           "promise_text": "Open a library branch"},
                root=Path(root), as_of=date(2025, 1, 1),
            )

        origin = result["phases"]["origin"]
        self.assertEqual([item["url"] for item in origin["sources"]], [fallback])
        self.assertEqual(origin["blocked"], [{"url": original, "reason": "http_404"}])
        self.assertEqual([item["url"] for item in result["outcome_sources"]], [outcome])

    async def test_wrong_page_fetch_is_blocked_not_raised(self):
        original = "https://sf.gov/redirected-page"
        fallback = "https://sf.gov/original-announcement"

        class Client:
            async def search(self, query, **kwargs):
                return SimpleNamespace(results=[SimpleNamespace(url=fallback)])

            async def fetch(self, url, **options):
                if url == original:
                    raise KeenableAPIError(
                        "The fetch returned a different page, not the requested one", status_code=422)
                return fetch_response(url, "Archived statement", "2024-01-02")

        with tempfile.TemporaryDirectory() as root:
            result = await discover_and_archive(
                Client(), {"promise_id": "P01", "promised_date": "2024-01-01",
                           "source_url": original, "entity": "Library",
                           "promise_text": "Open a library branch"},
                root=Path(root), as_of=date(2025, 1, 1),
            )

        origin = result["phases"]["origin"]
        self.assertEqual([item["url"] for item in origin["sources"]], [fallback])
        self.assertEqual(origin["blocked"], [{"url": original, "reason": "http_422_wrong_page"}])

    async def test_other_422_propagates(self):
        class Client:
            async def search(self, query, **kwargs):
                return SimpleNamespace(results=[])

            async def fetch(self, url, **options):
                raise KeenableAPIError("Invalid request parameter", status_code=422)

        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(KeenableAPIError):
                await discover_and_archive(
                    Client(), {"promise_id": "P01", "promised_date": "2024-01-01",
                               "source_url": "https://sf.gov/a", "entity": "Library",
                               "promise_text": "Open a library branch"},
                    root=Path(root), as_of=date(2025, 1, 1),
                )

    async def test_unreachable_url_is_blocked_not_raised(self):
        original = "https://sf.gov/slow-page"
        fallback = "https://sf.gov/original-announcement"

        class Client:
            async def search(self, query, **kwargs):
                return SimpleNamespace(results=[SimpleNamespace(url=fallback)])

            async def fetch(self, url, **options):
                if url == original:
                    raise KeenableConnectionError("could not reach the Keenable API: ReadTimeout('')")
                return fetch_response(url, "Archived statement", "2024-01-02")

        with tempfile.TemporaryDirectory() as root:
            result = await discover_and_archive(
                Client(), {"promise_id": "P01", "promised_date": "2024-01-01",
                           "source_url": original, "entity": "Library",
                           "promise_text": "Open a library branch"},
                root=Path(root), as_of=date(2025, 1, 1),
            )

        origin = result["phases"]["origin"]
        self.assertEqual([item["url"] for item in origin["sources"]], [fallback])
        self.assertEqual(origin["blocked"], [{"url": original, "reason": "fetch_connection_error"}])

    async def test_provider_fetch_error_propagates(self):
        class Client:
            async def search(self, query, **kwargs):
                return SimpleNamespace(results=[])

            async def fetch(self, url, **options):
                raise KeenableAPIError("Fetch service unavailable", status_code)

        with tempfile.TemporaryDirectory() as root:
            for status_code in (402, 503):
                with self.subTest(status_code=status_code), self.assertRaises(KeenableAPIError):
                    await discover_and_archive(
                        Client(), {"promise_id": "P01", "promised_date": "2024-01-01",
                                   "source_url": "https://missionlocal.org/pledge",
                                   "promise_text": "Open a library branch"},
                        root=Path(root), as_of=date(2025, 1, 1),
                    )

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
        self.assertEqual(client.args[1]["max_results"], 25)

    async def test_archive_full_response_but_not_truncated_page(self):
        class Client:
            async def fetch(self, url, **options):
                return fetch_response(getattr(self, "final_url", url), "Actual source",
                                      "2020-01-01", truncated=self.truncated)

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

            async def fetch(self, url, **options):
                self.calls += 1
                return fetch_response("https://evil.example/x", "Actual source")

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

    async def test_search_passes_phase_options_from_config(self):
        from src.discovery_config import load_discovery_config, load_exclude_domains

        config = load_discovery_config()
        excluded = list(load_exclude_domains())
        self.assertIn("reddit.com", excluded)

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
        self.assertEqual(len(client.calls), 3)
        for phase, kwargs in zip(("origin", "delivery", "survival"), client.calls):
            self.assertEqual(kwargs["max_results"], config.search_max_results)
            self.assertEqual(kwargs["max_results"], 25)
            self.assertIs(kwargs["disable_cards"], True)
            self.assertEqual(kwargs["exclude_domains"], excluded)
            self.assertEqual(kwargs["objective"], config.objective(phase))
            self.assertTrue(kwargs["objective"])
        self.assertEqual(len({kwargs["objective"] for kwargs in client.calls}), 3)

    async def test_search_options_follow_a_custom_config(self):
        from src.discovery_config import search_options

        with tempfile.TemporaryDirectory() as root:
            cfg = Path(root) / "d.json"
            cfg.write_text(json.dumps({
                "rolling_days": 10, "added_reason": "r", "added_by": "t", "added_at": "x",
                "search_max_results": 7, "objectives": {"origin": "custom origin"},
            }))
            ex = Path(root) / "e.json"
            ex.write_text(json.dumps({"domains": ["example.org"]}))
            options = search_options("origin", path=str(cfg), exclude_path=str(ex))
        self.assertEqual(options, {"max_results": 7, "disable_cards": True,
                                   "exclude_domains": ["example.org"],
                                   "objective": "custom origin"})

    async def test_fetch_passes_max_chars_and_records_retrieval(self):
        from src.discovery_config import load_discovery_config

        class Client:
            async def fetch(self, url, **options):
                self.options = options
                return fetch_response(url, "Agenda text", "2024-01-01")

        client = Client()
        with tempfile.TemporaryDirectory() as root:
            source = await fetch_and_archive(
                client, "https://sf.gov/agenda", Path(root), "P01",
                acquired_at="2024-01-05T00:00:00Z")
            self.assertEqual(client.options, {"max_chars": 400000})
            self.assertEqual(client.options["max_chars"],
                             load_discovery_config().fetch_max_chars)
            record = json.loads(Path(source["metadata_path"]).read_bytes())
            self.assertEqual(record["acquired_at"], "2024-01-05T00:00:00Z")
            self.assertEqual(record["retrieval"], "indexed")
            live = await fetch_and_archive(
                client, "https://sf.gov/agenda", Path(root), "P01", max_age_hours=0)
            self.assertEqual(client.options["max_age_hours"], 0)
            record = json.loads(Path(live["metadata_path"]).read_bytes())
            self.assertIsNone(record["acquired_at"])
            self.assertEqual(record["retrieval"], "live")

    async def test_per_page_error_is_a_blocked_url_not_a_crash(self):
        bad = "https://sf.gov/gone"
        wrong = "https://sf.gov/redirected"
        good = "https://sf.gov/original-announcement"

        class Client:
            async def search(self, query, **kwargs):
                return SimpleNamespace(results=[SimpleNamespace(url=good)])

            async def fetch(self, url, **options):
                if url == bad:
                    return fetch_response(url, "", error={"status": 404, "error": "not found"})
                if url == wrong:
                    return fetch_response(url, "", error={
                        "status": 422, "error": "The fetch returned a different page"})
                return fetch_response(url, "Archived statement", "2024-01-02")

        for url, reason in ((bad, "http_404"), (wrong, "http_422_wrong_page")):
            with tempfile.TemporaryDirectory() as root:
                result = await discover_and_archive(
                    Client(), {"promise_id": "P01", "promised_date": "2024-01-01",
                               "source_url": url, "entity": "Library",
                               "promise_text": "Open a library branch"},
                    root=Path(root), as_of=date(2025, 1, 1),
                )
            origin = result["phases"]["origin"]
            self.assertEqual(origin["blocked"], [{"url": url, "reason": reason}])
            self.assertEqual([item["url"] for item in origin["sources"]], [good])

    async def test_empty_fetch_batch_is_blocked(self):
        class Client:
            async def fetch(self, url, **options):
                return SimpleNamespace(results=[])

        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                await fetch_and_archive(Client(), "https://sf.gov/x", Path(root), "P01")

    async def test_search_acquired_at_reaches_the_manifest(self):
        url = "https://sf.gov/original-announcement"

        class Client:
            async def search(self, query, **kwargs):
                return SimpleNamespace(results=[SimpleNamespace(
                    url=url, acquired_at="2024-02-02T00:00:00Z")])

            async def fetch(self, url, **options):
                return fetch_response(url, "Archived statement", "2024-01-02")

        with tempfile.TemporaryDirectory() as root:
            result = await discover_and_archive(
                Client(), {"promise_id": "P01", "promised_date": "2024-01-01",
                           "source_url": url, "entity": "Library",
                           "promise_text": "Open a library branch"},
                root=Path(root), as_of=date(2025, 1, 1),
            )
        self.assertEqual(result["phases"]["origin"]["sources"][0]["acquired_at"],
                         "2024-02-02T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
