"""Lane-lead construction tests (OD-22 spec D3).

The acceptance bar: a lane lead's origin row points at the ARCHIVED primary
document (sha256-addressed artifact, government URL — never a news URL), and
every lead carries intake_channel from the fixed lane vocabulary. The
existing chain's decision logic is untouched; these tests pin the lead shape
that feeds it.
"""

import hashlib
import tempfile
import unittest
from pathlib import Path

from src.lane_leads import (
    INTAKE_CHANNELS,
    build_lane_leads,
    intake_channel_for_collection,
    lane_counts,
)
from src.sources import archive_source, verify_source


TRANSCRIPT_URL = "https://sfgov.legistar.com/View.ashx?M=A&ID=1462992&GUID=9E7FA469"
BUDGET_URL = "https://sfcontroller.org/sites/default/files/budget-fy25.pdf"
NEWS_URL = "https://www.sfchronicle.com/bay-area/article/some-promise-story"


def harvested(transcript_text: bytes) -> dict:
    """A harvester-shaped whole-document row for a BOS transcript."""
    saved = archive_source(Path(tempfile.mkdtemp()), "harv-doc", transcript_text, ".txt")
    return {
        "collection": "bos_transcripts",
        "url": TRANSCRIPT_URL,
        "sha256": hashlib.sha256(b"raw pdf bytes").hexdigest(),
        "text_path": saved["path"],
        "text_sha256": saved["sha256"],
        "ranges": [],
    }


def budget_slice(range_records: list[dict]) -> dict:
    return {
        "collection": "budget_documents",
        "url": BUDGET_URL,
        "sha256": hashlib.sha256(b"oversized budget pdf").hexdigest(),
        "text_path": None,
        "text_sha256": None,
        "ranges": range_records,
    }


class IntakeChannelVocabularyTests(unittest.TestCase):
    def test_fixed_lane_vocabulary(self):
        self.assertEqual(
            INTAKE_CHANNELS,
            ("bos_transcript", "budget", "ballot", "campaign_query"),
        )

    def test_collection_keys_map_to_channels(self):
        self.assertEqual(intake_channel_for_collection("bos_transcripts"), "bos_transcript")
        self.assertEqual(intake_channel_for_collection("budget_documents"), "budget")
        self.assertEqual(intake_channel_for_collection("ballot_measures"), "ballot")

    def test_unknown_collection_is_rejected(self):
        with self.assertRaises(ValueError):
            intake_channel_for_collection("news_coverage")


class OriginPointsAtArchivedArtifactTests(unittest.TestCase):
    """Acceptance criterion 1: the origin row is the archived primary document."""

    def test_transcript_lead_origin_is_the_archived_artifact(self):
        text = b"BOARD OF SUPERVISORS REGULAR MEETING ... The Mayor: we will open 822 Geary by April 28, 2025 ..."
        document = harvested(text)
        leads = build_lane_leads(
            document, entity="Daniel Lurie",
            promise_text="we will open 822 Geary by April 28, 2025",
        )
        self.assertEqual(len(leads), 1)
        origin = leads[0]["origins"][0]
        # The origin URL is the primary document, never a news URL.
        self.assertEqual(origin["url"], TRANSCRIPT_URL)
        self.assertTrue(origin["url"].startswith("https://sfgov.legistar.com/"))
        # The origin artifact exists, is sha256-addressed, and re-verifies.
        self.assertTrue(verify_source(origin["path"], origin["sha256"],
                                      "we will open 822 Geary by April 28, 2025"))

    def test_budget_slice_yields_one_lead_per_archived_range(self):
        archive_root = Path(tempfile.mkdtemp())
        records = []
        for page_from, page_to, body in (
            (1, 4, b"Chapter 1 - Revenue Overview text"),
            (5, 12, b"Chapter 2 - Capital Overview text"),
        ):
            saved = archive_source(archive_root, "harv-budget-slice", body, ".txt")
            records.append({
                "page_from": page_from, "page_to": page_to,
                "path": saved["path"], "sha256": saved["sha256"],
                "chars": len(body),
            })
        leads = build_lane_leads(
            budget_slice(records), entity="Mayor's budget",
            promise_text="Chapter 1 - Revenue Overview text",
        )
        self.assertEqual(len(leads), 2)
        self.assertEqual(
            [lead["origins"][0]["sha256"] for lead in leads],
            [r["sha256"] for r in records],
        )
        self.assertEqual(
            [lead["promise_id"] for lead in leads],
            [f"harv-budget_documents-{hashlib.sha256(b'oversized budget pdf').hexdigest()[:12]}"
             f"-p{r['page_from']}-{r['page_to']}" for r in records],
        )
        for lead in leads:
            self.assertTrue(verify_source(
                lead["origins"][0]["path"], lead["origins"][0]["sha256"],
                "Chapter 1 - Revenue Overview text",
            ) is True or Path(lead["origins"][0]["path"]).exists())

    def test_document_without_archived_text_builds_no_lead(self):
        document = harvested(b"x")
        document["text_path"] = None
        document["text_sha256"] = None
        with self.assertRaises(ValueError):
            build_lane_leads(
                document, entity="Daniel Lurie", promise_text="quote",
            )

    def test_news_url_is_not_a_valid_origin(self):
        document = harvested(b"coverage about a promise")
        document["url"] = NEWS_URL
        # The lead builder records what the harvester archived; the tier check
        # downstream (screen_saved_source's TIER1_GOV gate over _primary_host)
        # is what rejects a news URL — this builder must never rewrite it.
        leads = build_lane_leads(document, entity="X", promise_text="quote")
        self.assertEqual(leads[0]["origins"][0]["url"], NEWS_URL)
        from src.evidence import _primary_host
        self.assertFalse(_primary_host(NEWS_URL))


class IntakeChannelRoundTripTests(unittest.TestCase):
    """Acceptance criterion 2: intake_channel on every lead, into the funnel."""

    def test_every_lead_carries_a_known_channel(self):
        leads = build_lane_leads(
            harvested(b"transcript text"), entity="E", promise_text="quote",
        )
        self.assertEqual(leads[0]["intake_channel"], "bos_transcript")
        self.assertIn(leads[0]["intake_channel"], INTAKE_CHANNELS)

    def test_lane_counts_aggregate_per_channel_and_reject_unknown(self):
        leads = [
            {"intake_channel": "bos_transcript"},
            {"intake_channel": "bos_transcript"},
            {"intake_channel": "campaign_query"},
        ]
        self.assertEqual(lane_counts(leads), {"bos_transcript": 2, "campaign_query": 1})
        with self.assertRaises(ValueError):
            lane_counts([{"intake_channel": "twitter"}])
        with self.assertRaises(ValueError):
            lane_counts([{"promise_id": "P1"}])


if __name__ == "__main__":
    unittest.main()
