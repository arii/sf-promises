"""Offline fixture tests for the document-led collection harvester (OD-22 D2).

No live sockets: every HTTP interaction runs over httpx.MockTransport and the
PDF fixtures are generated in-process, per the PR #15 CI isolation.
"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import httpx

from src.checks import check_hash
from src.sourcing import document_harvester as harvester
from src.sourcing.dedupe import build_dedupe_index
from src.sourcing.page_ranges import plan_ranges
from src.sources import verify_source


BUDGET_PDF = "https://sfcontroller.org/sites/default/files/budget-fy25.pdf"
OTHER_PDF = "https://sfcontroller.org/sites/default/files/report-fy25.pdf"
BALLOT_PDF = "https://sfelections.sfgov.org/sites/default/files/ballot-measure-m.pdf"
TRANSCRIPT_PDF = "https://sfgov.legistar.com/View.ashx?M=A&ID=1462992&GUID=9E7FA469"
TRANSCRIPT_PDF_ESCAPED = TRANSCRIPT_PDF.replace("&", "&amp;")
MEETING_DETAIL = "https://sfgov.legistar.com/MeetingDetail.aspx?ID=1462992&GUID=9E7FA469&Options=info|"
MEETING_DETAIL_ESCAPED = MEETING_DETAIL.replace("&", "&amp;")


def transcript_bytes():
    return harvester  # placeholder replaced below


def one_page_pdf(text):
    from tests.test_pdf import multi_page_pdf
    return multi_page_pdf([text])


def chapter_budget_pages():
    """12 pages of 8k chars; chapters open on pages 5 and 9 (96k total)."""
    pages = []
    for number in range(1, 13):
        prefix = ""
        if number == 5:
            prefix = "Chapter 1 - Revenue Overview "
        elif number == 9:
            prefix = "Chapter 2 - Capital Overview "
        pages.append(prefix + "x" * (8_000 - len(prefix)))
    return pages


def budget_pages_pdf():
    from tests.test_pdf import multi_page_pdf
    return multi_page_pdf(chapter_budget_pages())


class FakeFork:
    """Extraction callables that run the real worker in-process (no fork)."""

    def __init__(self, override_extract=None):
        self.override_extract = override_extract
        self.full_extract_calls = 0
        self.range_calls = []
        self.inspect_calls = 0

    async def extract_pdf(self, *, path, digest, promise_id, page_from=None, page_to=None):
        from src.pdf_worker import extract, extract_pages
        if self.override_extract is not None:
            return await self.override_extract(
                path=path, digest=digest, promise_id=promise_id,
                page_from=page_from, page_to=page_to,
            )
        if page_from is None:
            self.full_extract_calls += 1
            return extract(path)
        self.range_calls.append((page_from, page_to))
        return extract_pages(path, page_from, page_to)

    async def inspect_pdf(self, *, path, digest, promise_id):
        from src.pdf_worker import inspect
        self.inspect_calls += 1
        return inspect(path)


class HarvesterTestBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.archive_root = self.root / "archive"
        self.repo_root = self.root / "repo"
        (self.repo_root / "data").mkdir(parents=True)
        self.sleeps = []

        async def sleep(seconds):
            self.sleeps.append(seconds)

        self.sleep = sleep

    def register_candidate(self, source_url):
        register = {"candidates": [{
            "candidate_id": "C1", "source_url": source_url,
            "entity": "City of SF", "statement_preview": "A commitment.",
        }]}
        (self.repo_root / "data" / "intake_candidate_register.json").write_text(
            json.dumps(register), encoding="utf-8")

    def http_fetcher(self, handler):
        async def noop_sleep(seconds):
            pass
        return harvester.RawByteFetcher(
            transport=httpx.MockTransport(handler), sleep=noop_sleep)

    @staticmethod
    def response(status, body=b""):
        return httpx.Response(status, content=body)


class TranscriptLaneTests(HarvesterTestBase):
    async def test_raw_bytes_archived_and_sha256_reverifies(self):
        pdf = one_page_pdf("Board of Supervisors transcript, page one.")
        fetched = []

        def handler(request):
            fetched.append(str(request.url))
            url = str(request.url)
            if url.startswith("https://sfgov.legistar.com/Calendar.aspx"):
                page = (
                    f'<a href="{MEETING_DETAIL_ESCAPED}">Meeting</a>'
                    f'<a href="{TRANSCRIPT_PDF_ESCAPED}">Transcript</a>'
                )
                return self.response(200, page.encode())
            if url.startswith("https://sfgov.legistar.com/MeetingDetail.aspx"):
                page = f'<a href="{TRANSCRIPT_PDF_ESCAPED}">Video transcript</a>'
                return self.response(200, page.encode())
            if url == TRANSCRIPT_PDF:
                return self.response(200, pdf)
            return self.response(404)

        spec = harvester.CollectionSpec(
            key="bos_transcripts", label="BOS transcripts",
            listing_urls=("https://sfgov.legistar.com/Calendar.aspx?year=2026",),
            parse_documents=harvester.parse_legistar_documents,
        )
        fork = FakeFork()
        result = await harvester.harvest_collections(
            specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=self.http_fetcher(handler), extract_pdf=fork.extract_pdf,
            inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
        )

        # Calendar listing, meeting detail page, then the raw document.
        self.assertEqual(fetched, [
            "https://sfgov.legistar.com/Calendar.aspx?year=2026",
            MEETING_DETAIL,
            TRANSCRIPT_PDF,
        ])
        self.assertEqual(len(result["documents"]), 1)
        document = result["documents"][0]
        self.assertEqual(document["url"], TRANSCRIPT_PDF)
        self.assertEqual(document["sha256"], hashlib.sha256(pdf).hexdigest())
        verified, _ = check_hash(document["path"], document["sha256"])
        self.assertTrue(verified)
        # Extracted text is its own archived artifact for quote verification.
        self.assertTrue(document["text_path"])
        text_verified, _ = check_hash(document["text_path"], document["text_sha256"])
        self.assertTrue(text_verified)
        self.assertEqual(result["dropped_reasons"], {})
        self.assertEqual(result["collections"]["bos_transcripts"]["archived"], 1)

    async def test_view_ashx_quote_resolves_against_one_archived_document(self):
        text = "Board of Supervisors transcript, page one."
        pdf = one_page_pdf(text)

        def handler(request):
            return self.response(200, pdf)

        spec = harvester.CollectionSpec(
            key="bos_transcripts", label="BOS transcripts",
            listing_urls=("https://sfgov.legistar.com/View.ashx?M=A&ID=1",),
            parse_documents=lambda url, html: {"documents": [url], "pages": []},
        )
        fork = FakeFork()
        result = await harvester.harvest_collections(
            specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=self.http_fetcher(handler), extract_pdf=fork.extract_pdf,
            inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
        )
        document = result["documents"][0]
        # The evidence path used by screening: a verbatim quote verifies
        # against exactly one archived, hash-checked document.
        self.assertTrue(verify_source(document["text_path"], document["text_sha256"], text))


class BudgetSliceTests(HarvesterTestBase):
    async def test_oversized_budget_pdf_slices_at_toc_chapter_boundaries(self):
        pdf = budget_pages_pdf()

        def handler(request):
            if request.url.path.endswith(".pdf"):
                return self.response(200, pdf)
            page = f'<a href="{BUDGET_PDF}">FY 2025 budget document</a>'
            return self.response(200, page.encode())

        spec = harvester.CollectionSpec(
            key="budget_documents", label="Budget documents",
            listing_urls=("https://sfcontroller.org/budget",),
            parse_documents=lambda url, html: harvester.parse_pdf_documents(url, html, keyword="budget"),
        )
        fork = FakeFork()
        # The worker's real CHAR_CAP (500k) is the slicing trigger; patching it
        # down keeps the fixture small while exercising the identical path.
        # max_chars=50_000 mirrors the patched cap in the slice planner.
        with mock.patch("src.pdf_worker.CHAR_CAP", 50_000):
            result = await harvester.harvest_collections(
                specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
                fetcher=self.http_fetcher(handler), extract_pdf=fork.extract_pdf,
                inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
                max_chars=50_000,
            )

        document = result["documents"][0]
        self.assertEqual(len(document["ranges"]), 3)
        # TOC chapter boundaries detected at pages 5 and 9; every range
        # within the character cap.
        self.assertEqual(
            [(r["page_from"], r["page_to"]) for r in document["ranges"]],
            [(1, 4), (5, 8), (9, 12)],
        )
        for record in document["ranges"]:
            self.assertLessEqual(record["chars"], 50_000)
            verified, _ = check_hash(record["path"], record["sha256"])
            self.assertTrue(verified)
        # Every range archived as its own artifact under its own identity.
        self.assertEqual(
            len({Path(record["path"]).parent for record in document["ranges"]}),
            len(document["ranges"]),
        )

    async def test_operator_override_boundaries_replace_toc_detection(self):
        pdf = budget_pages_pdf()

        def handler(request):
            if request.url.path.endswith(".pdf"):
                return self.response(200, pdf)
            page = f'<a href="{BUDGET_PDF}">FY 2025 budget document</a>'
            return self.response(200, page.encode())

        spec = harvester.CollectionSpec(
            key="budget_documents", label="Budget documents",
            listing_urls=("https://sfcontroller.org/budget",),
            parse_documents=lambda url, html: harvester.parse_pdf_documents(url, html),
        )
        fork = FakeFork()
        with mock.patch("src.pdf_worker.CHAR_CAP", 50_000):
            await harvester.harvest_collections(
                specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
                fetcher=self.http_fetcher(handler), extract_pdf=fork.extract_pdf,
                inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
                max_chars=50_000,
                range_boundaries={"https://sfcontroller.org/budget": (3, 7, 11)},
            )
        # Boundaries refine cap-forced cuts (they never introduce extra
        # cuts): ranges end at pages 2 and 6; the remainder fits whole.
        self.assertEqual(fork.range_calls, [(1, 2), (3, 6), (7, 12)])


class BallotLaneTests(HarvesterTestBase):
    async def test_ballot_measure_pdf_archived_from_listing(self):
        pdf = one_page_pdf("Ballot measure M, full text and digest.")

        def handler(request):
            if request.url.path.endswith(".pdf"):
                return self.response(200, pdf)
            page = (
                f'<a href="{BALLOT_PDF}">Ballot measure M</a>'
                f'<a href="https://sfelections.sfgov.org/sites/default/files/calendar.pdf">Calendar</a>'
            )
            return self.response(200, page.encode())

        spec = harvester.CollectionSpec(
            key="ballot_measures", label="Ballot measures",
            listing_urls=("https://sfelections.sfgov.org/",),
            parse_documents=lambda url, html: harvester.parse_pdf_documents(url, html, keyword="ballot"),
        )
        fork = FakeFork()
        result = await harvester.harvest_collections(
            specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=self.http_fetcher(handler), extract_pdf=fork.extract_pdf,
            inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
        )
        self.assertEqual(len(result["documents"]), 1)
        self.assertEqual(result["documents"][0]["url"], BALLOT_PDF)
        self.assertEqual(result["documents"][0]["sha256"], hashlib.sha256(pdf).hexdigest())


class DenialAndCapTests(HarvesterTestBase):
    def spec_with(self, doc_urls):
        urls = list(doc_urls)

        def parse(url, html):
            return {"documents": urls, "pages": []}

        return harvester.CollectionSpec(
            key="budget_documents", label="Budget documents",
            listing_urls=("https://sfcontroller.org/budget",),
            parse_documents=parse,
        )

    async def test_truncation_and_empty_results_record_denials(self):
        listing = (
            '<a href="https://sfcontroller.org/ok.pdf">Ok</a>'
            '<a href="https://sfcontroller.org/big.pdf">Big</a>'
            '<a href="https://sfcontroller.org/empty.pdf">Empty</a>'
        )

        def handler(request):
            if request.url.path.endswith("empty.pdf"):
                return self.response(200, b"")
            if request.url.path.endswith("big.pdf"):
                return self.response(200, b"x" * 500)
            if request.url.path.endswith(".pdf"):
                return self.response(404)
            return self.response(200, listing.encode())

        fork = FakeFork()
        # byte_cap=300: the listing (~190 bytes) passes, but big.pdf (500
        # bytes) would have to be truncated and is denied whole — the raw
        # fetcher never truncates.
        async def noop_sleep(seconds):
            pass
        fetcher = harvester.RawByteFetcher(
            transport=httpx.MockTransport(handler), sleep=noop_sleep, byte_cap=300)
        result = await harvester.harvest_collections(
            specs=(self.spec_with([
                "https://sfcontroller.org/ok.pdf",
                "https://sfcontroller.org/big.pdf",
                "https://sfcontroller.org/empty.pdf",
            ]),), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=fetcher, extract_pdf=fork.extract_pdf,
            inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
        )
        reasons = {d["url"]: d["reason"] for d in result["denials"]}
        self.assertEqual(reasons["https://sfcontroller.org/ok.pdf"], "http_404")
        self.assertEqual(reasons["https://sfcontroller.org/big.pdf"], "byte_cap_exceeded")
        self.assertEqual(reasons["https://sfcontroller.org/empty.pdf"], "empty_response")
        self.assertEqual(result["documents"], [])

    async def test_per_run_document_cap_bounds_volume(self):
        def handler(request):
            return self.response(200, one_page_pdf("Some document body."))

        fork = FakeFork()
        result = await harvester.harvest_collections(
            specs=(self.spec_with([
                f"https://sfcontroller.org/doc-{n}.pdf" for n in range(3)
            ]),), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=self.http_fetcher(handler), extract_pdf=fork.extract_pdf,
            inspect_pdf=fork.inspect_pdf, sleep=self.sleep, max_documents=1,
        )
        self.assertEqual(len(result["documents"]), 1)
        cap_denials = [d for d in result["denials"] if d["reason"] == "run_document_cap"]
        self.assertEqual(len(cap_denials), 2)

    async def test_rate_limited_fetch_honors_retry_after(self):
        attempts = []
        sleeps = []

        async def real_sleep(seconds):
            sleeps.append(seconds)

        def handler(request):
            attempts.append(str(request.url))
            if len(attempts) == 1:
                return httpx.Response(429, headers={"Retry-After": "2"})
            return self.response(200, one_page_pdf("Some document body."))

        spec = self.spec_with(["https://sfcontroller.org/doc-0.pdf"])
        fork = FakeFork()
        fetcher = harvester.RawByteFetcher(
            transport=httpx.MockTransport(handler), sleep=real_sleep)
        result = await harvester.harvest_collections(
            specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=fetcher, extract_pdf=fork.extract_pdf,
            inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
        )
        self.assertEqual(sleeps, [2])
        self.assertEqual(len(result["documents"]), 1)

    async def test_scanned_document_fails_loudly(self):
        scanned = one_page_pdf("x")  # text stripped below

        def handler(request):
            if request.url.path.endswith(".pdf"):
                return self.response(200, scanned)
            page = '<a href="https://sfcontroller.org/scanned.pdf">Scanned</a>'
            return self.response(200, page.encode())

        async def scanned_extract(*, path, digest, promise_id, page_from=None, page_to=None):
            raise ValueError("PDF has no extractable text")

        async def scanned_inspect(*, path, digest, promise_id):
            return {"sha256": digest, "pages": [{"page": 1, "chars": 0, "first_line": ""}]}

        spec = self.spec_with(["https://sfcontroller.org/scanned.pdf"])
        with self.assertRaises(harvester.ScannedDocumentError) as caught:
            await harvester.harvest_collections(
                specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
                fetcher=self.http_fetcher(handler), extract_pdf=scanned_extract,
                inspect_pdf=scanned_inspect, sleep=self.sleep,
            )
        self.assertIn("no extractable text", str(caught.exception))

        # Non-strict mode still records the denial row — never silent loss.
        # Fresh archive root: the first run's bytes are archived, so a shared
        # root would drop this document as sha256_archived before extraction.
        result = await harvester.harvest_collections(
            specs=(spec,), archive_root=self.archive_root / "second", repo_root=self.repo_root,
            fetcher=self.http_fetcher(handler), extract_pdf=scanned_extract,
            inspect_pdf=scanned_inspect, sleep=self.sleep, strict=False,
        )
        self.assertEqual(
            result["denials"],
            [{"url": "https://sfcontroller.org/scanned.pdf", "reason": "no_extractable_text"}],
        )


class DedupeHistogramTests(HarvesterTestBase):
    async def test_register_collision_appears_in_dropped_reasons_histogram(self):
        pdf = one_page_pdf("A budget document body.")

        def handler(request):
            if request.url.path.endswith(".pdf"):
                return self.response(200, pdf)
            page = f'<a href="{BUDGET_PDF}">Budget document</a>'
            return self.response(200, page.encode())

        self.register_candidate(BUDGET_PDF)
        dedupe_index = build_dedupe_index(self.repo_root, archive_root=self.archive_root)

        spec = harvester.CollectionSpec(
            key="budget_documents", label="Budget documents",
            listing_urls=("https://sfcontroller.org/budget",),
            parse_documents=lambda url, html: harvester.parse_pdf_documents(url, html),
        )
        fork = FakeFork()
        result = await harvester.harvest_collections(
            specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=self.http_fetcher(handler), dedupe_index=dedupe_index,
            extract_pdf=fork.extract_pdf, inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
        )
        self.assertEqual(result["dropped_reasons"], {"url_register": 1})
        # Lane-aware reporting only: the same union verdicts, histogrammed
        # per collection. The union itself is unchanged.
        self.assertEqual(
            result["dropped_by_collection"], {"budget_documents": {"url_register": 1}}
        )
        self.assertEqual(result["dropped"][0]["matched_value"], BUDGET_PDF)

    async def test_identical_bytes_from_a_second_url_are_dropped_not_archived_twice(self):
        pdf = one_page_pdf("The same document served under two URLs.")

        def handler(request):
            return self.response(200, pdf)

        spec = harvester.CollectionSpec(
            key="budget_documents", label="Budget documents",
            listing_urls=("https://sfcontroller.org/budget",),
            parse_documents=lambda url, html: {"documents": [
                "https://sfcontroller.org/same.pdf",
                "https://sfcontroller.org/same-copy.pdf",
            ], "pages": []},
        )
        fork = FakeFork()
        result = await harvester.harvest_collections(
            specs=(spec,), archive_root=self.archive_root, repo_root=self.repo_root,
            fetcher=self.http_fetcher(handler), extract_pdf=fork.extract_pdf,
            inspect_pdf=fork.inspect_pdf, sleep=self.sleep,
        )
        self.assertEqual(result["dropped_reasons"], {"sha256_harvested_this_run": 1})
        self.assertEqual(len(result["documents"]), 1)


class PlanRangeUnitTests(unittest.TestCase):
    def test_boundaries_preferred_but_caps_win(self):
        pages = [{"page": n, "chars": 10} for n in range(1, 6)]
        self.assertEqual(plan_ranges(pages, boundaries=(3,)), [(1, 5)])

    def test_cap_cut_prefers_a_boundary_within_the_window(self):
        # 8 pages of 70k chars: the cap cut lands after page 7, but a chapter
        # starts on page 5, so the plan ends the first range there.
        pages = [{"page": n, "chars": 70_000} for n in range(1, 9)]
        self.assertEqual(plan_ranges(pages, boundaries=(5,)), [(1, 4), (5, 8)])

    def test_no_boundaries_falls_back_to_cap_driven_cuts(self):
        pages = [{"page": n, "chars": 60_000} for n in range(1, 13)]
        self.assertEqual(plan_ranges(pages), [(1, 8), (9, 12)])

    def test_single_page_over_the_char_cap_is_loud(self):
        pages = [{"page": 1, "chars": 500_001}]
        with self.assertRaises(ValueError):
            plan_ranges(pages)


if __name__ == "__main__":
    unittest.main()
