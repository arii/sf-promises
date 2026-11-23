"""D4: campaign query lane scoping + Wayback Save-Page-Now capture.

Offline fixture tests only (PR #15 CI isolation): the planner is exercised
against the real reviewed allowlist and a temp allowlist file, the capture
hook is injected, and no test opens a socket.
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pytest

from keenable_stubs import fetch_response
from src.allowlist import load_allowlist
from src.discovery import fetch_and_archive
from src.sources import (
    FETCH_METADATA_FIELDS,
    RETRIEVAL_METADATA_FIELDS,
    WAYBACK_METADATA_FIELDS,
    is_fetch_metadata,
)
from src.sourcing.planner import (
    CAMPAIGN_FACT_SHEET_DOMAIN_CANDIDATES,
    SearchPlanner,
    reviewed_campaign_domains,
    validate_outcome_blind_query,
)
from src.wayback import capture_permitted, save_page_now


class Client:
    async def fetch(self, url, **_options):
        return fetch_response(url, "Actual source", "2026-01-01")


@pytest.fixture(name="planner_specs")
def _planner_specs():
    return SearchPlanner().generate_campaign_fact_sheet_queries()


def test_campaign_queries_emit_only_reviewed_domains(planner_specs):
    entries = {e.domain: e for e in load_allowlist()}
    assert planner_specs, "campaign lane must produce queries"
    emitted = {d for spec in planner_specs for d in spec.target_domains}
    assert emitted, "campaign lane must target at least one reviewed domain"
    for domain in emitted:
        entry = entries[domain]
        assert entry.review_status == "approved"
        assert entry.canary is False
    # The reviewed campaign candidate is the lane's anchor target.
    assert "daniellurie.com" in emitted
    for spec in planner_specs:
        assert set(spec.target_domains) == emitted
        assert spec.lane == "campaign"
        assert validate_outcome_blind_query(spec.query_text) == []


def _allowlist_fixture(path, review_status="approved", canary=False):
    path.write_text(json.dumps([{
        "domain": "daniellurie.com",
        "source_type": "official_government",
        "groups": ["checks_allowlist"],
        "added_reason": "fixture",
        "added_by": "fixture",
        "added_at": "2026-11-15",
        "review_status": review_status,
        "canary": canary,
    }]), encoding="utf-8")
    return str(path)


def test_unreviewed_campaign_candidate_is_dropped(tmp_path):
    """A candidate domain without an approved, non-canary allowlist entry never
    reaches target_domains — reviewed data, not the candidate list, decides.
    One file per review state: load_allowlist caches on the path string."""
    assert reviewed_campaign_domains(
        _allowlist_fixture(tmp_path / "approved.json")
    ) == ["daniellurie.com"]
    assert reviewed_campaign_domains(
        _allowlist_fixture(tmp_path / "pending.json", review_status="pending")
    ) == []
    assert reviewed_campaign_domains(
        _allowlist_fixture(tmp_path / "canaried.json", canary=True)
    ) == []

    # An unknown candidate (not on the allowlist at all) is dropped too.
    assert "not-on-allowlist.example" not in CAMPAIGN_FACT_SHEET_DOMAIN_CANDIDATES
    assert reviewed_campaign_domains() == [d for d in CAMPAIGN_FACT_SHEET_DOMAIN_CANDIDATES]


def test_fetch_manifest_matches_the_canonical_shape():
    """The writer and the provenance readers share one shape definition:
    the six fetch fields plus the D4 Wayback capture pair."""
    with tempfile.TemporaryDirectory() as root:
        source = asyncio_run(fetch_and_archive(Client(), "https://sf.gov/x", Path(root), "P01"))
        record = json.loads(Path(source["metadata_path"]).read_bytes())
        assert is_fetch_metadata(record)
        assert frozenset(record) == (
            frozenset(FETCH_METADATA_FIELDS) | frozenset(WAYBACK_METADATA_FIELDS)
            | frozenset(RETRIEVAL_METADATA_FIELDS)
        )


class CaptureTests(unittest.IsolatedAsyncioTestCase):
    def test_capture_url_is_recorded_in_the_manifest(self):
        async def capture(url):
            return f"https://web.archive.org/web/20261115000000/{url}"

        with tempfile.TemporaryDirectory() as root:
            source = asyncio_run(
                fetch_and_archive(Client(), "https://sf.gov/x", Path(root), "P01", capture=capture)
            )
            self.assertEqual(
                source["wayback_capture_url"],
                "https://web.archive.org/web/20261115000000/https://sf.gov/x",
            )
            record = json.loads(Path(source["metadata_path"]).read_bytes())
            self.assertEqual(
                record["wayback_capture_url"],
                "https://web.archive.org/web/20261115000000/https://sf.gov/x",
            )
            self.assertIsNone(record["wayback_capture_error"])

    def test_no_capture_hook_records_a_null_capture(self):
        with tempfile.TemporaryDirectory() as root:
            source = asyncio_run(
                fetch_and_archive(Client(), "https://sf.gov/x", Path(root), "P01")
            )
            self.assertIsNone(source["wayback_capture_url"])
            record = json.loads(Path(source["metadata_path"]).read_bytes())
            self.assertIsNone(record["wayback_capture_url"])
            self.assertIsNone(record["wayback_capture_error"])

    def test_failed_capture_is_recorded_and_does_not_block_the_fetch(self):
        async def failing_capture(url):
            raise RuntimeError("wayback rate limited")

        with tempfile.TemporaryDirectory() as root:
            source = asyncio_run(
                fetch_and_archive(Client(), "https://sf.gov/x", Path(root), "P01", capture=failing_capture)
            )
            self.assertIsNone(source["wayback_capture_url"])
            self.assertIn("RuntimeError", source["wayback_capture_error"])
            record = json.loads(Path(source["metadata_path"]).read_bytes())
            self.assertIsNone(record["wayback_capture_url"])
            self.assertIn("rate limited", record["wayback_capture_error"])
            self.assertEqual(Path(source["path"]).read_text(), "Actual source")

    def test_canary_urls_are_blocked_at_fetch(self):
        class CountingClient(Client):
            calls = 0

            async def fetch(self, url, **_options):
                self.calls += 1
                return await super().fetch(url, **_options)

        canary_urls = [
            "https://www.reddit.com/r/sanfrancisco",
            # A canary replayed through the Wayback host is still a canary.
            "https://web.archive.org/web/20260101000000/https://www.reddit.com/r/sanfrancisco",
            "https://web.archive.org/web/20260101000000/https://x.com/someone/status/1",
        ]
        with tempfile.TemporaryDirectory() as root:
            client = CountingClient()
            for url in canary_urls:
                with self.assertRaises(ValueError):
                    asyncio_run(fetch_and_archive(client, url, Path(root), "P01", capture=None))
            self.assertEqual(client.calls, 0)
            self.assertFalse((Path(root) / "P01").exists())


def asyncio_run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


class SavePageNowTests(unittest.IsolatedAsyncioTestCase):
    async def test_canary_and_unlisted_hosts_are_never_captured(self):
        async def must_not_be_called(url):
            raise AssertionError(f"SPN called for non-permitted URL {url}")

        for url in (
            "https://www.reddit.com/r/sanfrancisco",
            "https://web.archive.org/web/20260101000000/https://www.reddit.com/r/sanfrancisco",
            "https://example.com/never-allowlisted",
        ):
            self.assertFalse(capture_permitted(url))
            self.assertIsNone(await save_page_now(url, http_get=must_not_be_called))

    async def test_successful_capture_returns_the_replay_url(self):
        async def fake_get(url):
            self.requested = url
            return SimpleNamespace(
                status_code=200,
                headers={"Location": "/web/20261115090102/https://sf.gov/x"},
            )

        result = await save_page_now("https://sf.gov/x", http_get=fake_get)
        self.assertEqual(result, "https://web.archive.org/web/20261115090102/https://sf.gov/x")
        self.assertIn("web.archive.org/save/", self.requested)

    async def test_transport_failure_returns_none(self):
        async def broken_get(url):
            raise OSError("network unreachable")

        self.assertIsNone(await save_page_now("https://sf.gov/x", http_get=broken_get))


if __name__ == "__main__":
    unittest.main()
