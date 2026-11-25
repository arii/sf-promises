import asyncio
import hashlib
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from keenable import KeenableAPIError, KeenableRateLimitError

from scripts import discovery_round as dr
from tests.keenable_stubs import fetch_response

AS_OF = date(2026, 11, 24)
GOV = "https://www.sf.gov/news-seawall-update"
NEWS = "https://www.sfchronicle.com/sf/article/muni-extension"
BAD = "https://example.invalid/page"

PAGE = (
    "# Mayor Lurie Announces Seawall Funding\n\n"
    "San Francisco Mayor Daniel Lurie announced new funding today.\n\n"
    "The Port will complete the first phase of seawall repairs by December 2028.\n\n"
    "The Embarcadero station opened in 2019 after years of delay.\n\n"
    "SFMTA plans to open the new Muni Metro platform in 2027.\n\n"
    "Residents said they hope things will get better.\n\n"
    "Thanks for reading.\n"
)


def cfg():
    return dr.load_config()


def search_response(*items):
    return SimpleNamespace(results=[
        SimpleNamespace(url=u, title=t, published_at="2026-05-01T00:00:00Z", acquired_at=None)
        for u, t in items])


class FakeClient:
    def __init__(self, searches=None, pages=None, search_error=None):
        self.searches, self.fetches = [], []
        self._search_results = searches or {}
        self._pages = pages or {}
        self._search_error = search_error

    async def search(self, query, **kwargs):
        self.searches.append((query, kwargs))
        if self._search_error:
            raise self._search_error
        return self._search_results.get(kwargs.get("site") or "open", search_response())

    async def fetch(self, url, **kwargs):
        self.fetches.append(url)
        content = self._pages.get(url)
        if content is None:
            raise KeenableAPIError("gone", status_code=404)
        return fetch_response(url, content, "2026-05-01T00:00:00Z")


def windows():
    return dr.make_windows(cfg(), as_of=AS_OF)


class QueryPlanTests(unittest.TestCase):
    def test_cap_and_windows(self):
        for cap in (0, 1, 7, 200):
            plan = dr.build_query_plan(cfg(), windows(), cap)
            self.assertEqual(len(plan), cap)
        plan = dr.build_query_plan(cfg(), windows(), 200)
        self.assertEqual({q["window"] for q in plan}, {"recent", "historical"})
        self.assertEqual(plan[0]["after"], "2025-01-01")
        self.assertEqual(plan[0]["before"], "2026-11-24")
        hist = next(q for q in plan if q["window"] == "historical")
        self.assertEqual((hist["after"], hist["before"]), ("2016-01-01", "2023-12-31"))

    def test_deterministic_and_covers_many_actors_under_default_cap(self):
        a = dr.build_query_plan(cfg(), windows(), 200)
        self.assertEqual(a, dr.build_query_plan(cfg(), windows(), 200))
        self.assertGreaterEqual(len({q["actor_id"] for q in a}), 30)

    def test_site_queries_use_actor_domains_and_open_query_exists(self):
        plan = dr.build_query_plan(cfg(), windows(), 5000)
        sfmta = [q for q in plan if q["actor_id"] == "sfmta" and q["window"] == "recent"]
        self.assertTrue(any(q["site"] is None for q in sfmta))
        self.assertEqual({q["site"] for q in sfmta} - {None}, {"sfmta.com"})
        bos = {q["site"] for q in plan if q["actor_id"] == "board_of_supervisors"} - {None}
        self.assertEqual(bos, {"sfbos.org", "sfgov.legistar.com"})

    def test_commitment_phrasing_and_no_unfilled_placeholders(self):
        plan = dr.build_query_plan(cfg(), windows(), 5000)
        for q in plan:
            self.assertNotIn("{", q["text"])
        texts = " ".join(q["text"] for q in plan)
        for phrase in ("expected to be completed by", " will ", "plans to"):
            self.assertIn(phrase, texts)
        years = {q["text"][-4:] for q in plan if " by 20" in q["text"]}
        self.assertTrue({"2027", "2018"} <= years)

    def test_config_actors_are_complete(self):
        names = " ".join(a["name"] + " " + " ".join(a["aliases"]) for a in cfg()["actors"])
        for name in ("SFMTA", "SFPUC", "Waymo", "Cruise", "PG&E", "UCSF", "CCSF", "BART", "Caltrain",
                     "Warriors", "Giants", "49ers", "Salesforce", "Treasure Island", "Arts Commission"):
            self.assertIn(name, names)


class SentenceMiningTests(unittest.TestCase):
    def mine(self, text=PAGE, published="2026-05-01T00:00:00Z", tier="TIER1_GOV", title=""):
        return dr.mine_page(text, title=title, published=published, tier=tier,
                            find_actor=dr.actor_matcher(cfg()),
                            query_actor=next(a for a in cfg()["actors"] if a["id"] == "port_of_sf"))

    def test_positive_sentences_are_verbatim(self):
        found = self.mine()
        quotes = [c["sentence"] for c in found]
        self.assertIn("The Port will complete the first phase of seawall repairs by December 2028.", quotes)
        self.assertIn("SFMTA plans to open the new Muni Metro platform in 2027.", quotes)
        for c in found:
            self.assertIn(c["sentence"], PAGE)
            self.assertEqual(PAGE[c["span"][0]:c["span"][1]], c["sentence"])

    def test_negatives_rejected(self):
        quotes = [c["sentence"] for c in self.mine()]
        self.assertFalse(any("opened in 2019" in q for q in quotes))
        self.assertFalse(any("hope things will get better" in q for q in quotes))
        self.assertFalse(any("Thanks for reading" in q for q in quotes))

    def test_reject_reasons(self):
        r = dr.reject_reason
        pub = date(2026, 5, 1)
        self.assertEqual(r("The station opened in 2019 and serves San Francisco riders daily.", published=pub),
                         "no_commitment_verb")
        self.assertEqual(r("It will open soon.", published=pub), "length")
        self.assertEqual(r("The city will say more about the plan but gave no timeline for it yet.", published=pub),
                         "no_deadline_signal")
        self.assertEqual(r("The city had promised that it will finish the San Francisco project by 2022, officials said.",
                           published=None), "retrospective_wording")
        self.assertEqual(r("The agency will finish the long-delayed San Francisco project by 2019 as planned.",
                           published=pub), "deadline_before_publication")
        self.assertEqual(r("Will the city finish the San Francisco project by 2028?", published=pub), "question")
        self.assertEqual(r("x" * 500 + " will by 2028", published=pub), "length")
        self.assertIsNone(r("The city plans to add 200 shelter beds within two years of the vote.", published=pub))
        self.assertIsNone(r("The program will end by the end of fiscal year 2027 in San Francisco.", published=pub))

    def test_actor_or_sf_required(self):
        text = "The company will finish its new office tower by 2028 after long delays."
        self.assertEqual(self.mine(text, title="Quarterly results"), [])
        self.assertEqual(len(self.mine(text, title="San Francisco office news")), 1)
        text2 = "Waymo will launch service at the airport by 2027 under the new permit."
        found = self.mine(text2, title="Business")
        self.assertEqual(found[0]["actor"], "Waymo")
        self.assertTrue(found[0]["actor_in_sentence"])

    def test_query_actor_fallback_and_deadline_guess(self):
        text = "# San Francisco news\n\nThe repairs will be completed by December 2028 at a cost of $5 million."
        found = self.mine(text)
        self.assertEqual(found[0]["actor"], "Port of San Francisco")
        self.assertEqual(found[0]["deadline_guess"], "2028-12-31")
        self.assertFalse(found[0]["actor_in_sentence"])

    def test_scoring_prefers_official_named_dated(self):
        text = ("The council will review it by 2030 during hearings late next season.\n\n"
                "SFMTA will open the Van Ness station by December 2027 for $40 million.\n")
        found = self.mine(text, tier="TIER2_NEWS", title="San Francisco news")
        self.assertTrue(found[0]["sentence"].startswith("SFMTA"))
        self.assertGreater(found[0]["score"], found[1]["score"])

    def test_top_three_per_page_and_context(self):
        sentences = [f"SFMTA will open line {n} in San Francisco by 2027 as planned." for n in range(6)]
        text = "SFMTA update.\n\n" + "\n\n".join(sentences)
        found = self.mine(text)
        self.assertEqual(len(found), 6)  # mining keeps all, selection caps at 3
        self.assertEqual(found[0]["context_before"], "SFMTA update.")
        self.assertIn("line 1", found[0]["context_after"])

    def test_splitter_keeps_exact_substrings(self):
        text = "- Item costs $1.5 million. Mr. Smith said the Dr. will go.\nNext line wraps\nacross. End!"
        for a, b in dr.split_sentences(text):
            self.assertEqual(text[a:b], text[a:b].strip())
            self.assertIn(text[a:b], text)
        spans = [text[a:b] for a, b in dr.split_sentences(text)]
        self.assertEqual(spans[0], "Item costs $1.5 million.")


class DedupeTests(unittest.TestCase):
    def test_existing_and_between_candidates(self):
        existing = {"texts": [dr.normalize("The Port will complete seawall repairs by December 2028 across the waterfront.")],
                    "urls": {dr.canonical_url("https://sf.gov/known/")}, "ids": set()}
        d = dr.Deduper(existing)
        self.assertEqual(d.admit("The Port will complete seawall repairs by December 2028 across the waterfront!",
                                 "https://a.gov/x"), "existing_text")
        self.assertEqual(d.admit("Anything will open by 2028 in San Francisco.", "https://www.sf.gov/known"),
                         "existing_url")
        self.assertIsNone(d.admit("SFMTA will open the Van Ness station by December 2027 for riders.", "https://a.gov/1"))
        self.assertEqual(d.admit("sfmta will open the van ness station by december 2027 for riders", "https://b.gov/2"),
                         "duplicate_text")
        self.assertIsNone(d.admit("The Library will reopen the Mission branch in 2028 after the renovation.",
                                  "https://a.gov/1"))
        self.assertEqual(d.admit("The Library will reopen the Mission branch in 2028 after renovation.",
                                 "https://a.gov/1/"), "duplicate_same_url")
        self.assertEqual(d.reasons["duplicate_text"], 1)

    def test_load_existing_reads_repo_data(self):
        existing = dr.load_existing()
        self.assertTrue(existing["texts"] and existing["urls"] and existing["ids"])
        self.assertIn("SEISMIC-01", existing["ids"])


class RoundTests(unittest.TestCase):
    def run_round(self, client, **kw):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "sources"
        slept = []

        async def sleep(s):
            slept.append(s)

        existing = kw.pop("existing", {"texts": [], "urls": set(), "ids": set()})
        result = asyncio.run(dr.run_round(
            client, cfg(), windows=windows(), root=root, as_of=AS_OF, existing=existing,
            sleep=sleep, **{"max_queries": 4, "max_fetches": 10, "domain_delay": 1.0, **kw}))
        return result, root, slept

    def test_end_to_end_filters_allowlist_and_archives(self):
        client = FakeClient(
            searches={"open": search_response((GOV, "Seawall funding"), (BAD, "x"), (NEWS, "Muni"),
                                              (GOV, "dup"))},
            pages={GOV: PAGE, NEWS: "San Francisco Muni will open the extension by 2029 after delays."})
        (record, candidates, counts), root, _ = self.run_round(client)
        self.assertEqual(counts["searches"], 4)
        self.assertEqual(len(client.searches), 4)
        self.assertEqual(counts["urls_unique"], 3)
        self.assertEqual(counts["urls_allowlisted"], 2)
        self.assertEqual(counts["urls_not_allowlisted"], 1)
        self.assertEqual(record["non_allowlisted_hosts_top"], {"example.invalid": 1})
        self.assertEqual(sorted(client.fetches), sorted([GOV, NEWS]))
        self.assertEqual(client.fetches[0], GOV)  # official tier first
        self.assertEqual(counts["fetch_ok"], 2)
        self.assertEqual(client.searches[0][1]["max_results"], 50)
        self.assertTrue(client.searches[0][1]["disable_cards"])
        self.assertIn("objective", client.searches[0][1])
        self.assertIn("published_after", client.searches[0][1])
        by_url = {}
        for c in candidates:
            by_url.setdefault(c["url"], []).append(c)
            saved = Path(root.parent / c["saved_path"])
            data = saved.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), c["sha256"])
            self.assertIn(c["verbatim_quote"], data.decode("utf-8"))
            self.assertEqual(c["lead_id"], dr.page_lead_id(c["requested_url"]))
            self.assertEqual(saved.parent.name, c["lead_id"])
            self.assertTrue(c["candidate_id"].startswith(c["lead_id"] + "-"))
            self.assertEqual(c["gate_failures"], [])
        self.assertLessEqual(max(len(v) for v in by_url.values()), 3)
        self.assertEqual(by_url[GOV][0]["source_tier"], "TIER1_GOV")
        self.assertEqual(by_url[NEWS][0]["source_tier"], "TIER2_NEWS")
        self.assertEqual(json.loads(json.dumps(record))["candidates"][0]["candidate_id"].startswith("R3-"), True)
        self.assertNotIn("context_before", record["candidates"][0])

    def test_fetch_budget_and_politeness(self):
        urls = [f"https://www.sf.gov/news-{n}" for n in range(5)]
        client = FakeClient(searches={"open": search_response(*[(u, "t") for u in urls])},
                            pages={u: PAGE for u in urls})
        (record, _, counts), _, slept = self.run_round(client, max_fetches=3, domain_delay=2.0,
                                                       max_queries=1)
        self.assertEqual(counts["fetches"], 3)
        self.assertEqual(len(client.fetches), 3)
        self.assertTrue(counts["fetch_budget_exhausted"])
        self.assertEqual(len(slept), 2)  # same host: waits between fetches

    def test_fetch_errors_are_counted_not_fatal(self):
        client = FakeClient(searches={"open": search_response((GOV, "a"), (NEWS, "b"))},
                            pages={NEWS: "San Francisco Muni will open the extension by 2029 after delays."})
        (_, candidates, counts), _, _ = self.run_round(client, max_queries=1)
        self.assertEqual(counts["fetch_blocked"], 1)
        self.assertEqual(counts["fetch_ok"], 1)
        self.assertEqual(len(candidates), 1)

    def test_search_budget_zero_and_rate_limit_stop(self):
        client = FakeClient()
        (_, _, counts), _, _ = self.run_round(client, max_queries=0)
        self.assertEqual((counts["searches"], counts["fetches"]), (0, 0))
        limited = FakeClient(search_error=KeenableRateLimitError("slow", status_code=429))
        (_, _, counts), _, _ = self.run_round(limited, max_queries=10)
        self.assertEqual(counts["searches"], dr.RATE_LIMIT_STOP)
        self.assertTrue(counts["stopped_rate_limited"])

    def test_existing_url_and_text_are_dropped(self):
        client = FakeClient(searches={"open": search_response((GOV, "a"))}, pages={GOV: PAGE})
        existing = {"texts": [], "urls": {dr.canonical_url(GOV)}, "ids": set()}
        (_, candidates, _), _, _ = self.run_round(client, max_queries=1, existing=existing)
        self.assertEqual(candidates, [])
        existing = {"texts": [dr.normalize("The Port will complete the first phase of seawall repairs by December 2028.")],
                    "urls": set(), "ids": set()}
        client = FakeClient(searches={"open": search_response((GOV, "a"))}, pages={GOV: PAGE})
        (record, candidates, _), _, _ = self.run_round(client, max_queries=1, existing=existing)
        self.assertFalse(any("seawall repairs" in c["verbatim_quote"] for c in candidates))
        self.assertEqual(record["mining"]["dedupe_existing_text"], 1)


class QueueTests(unittest.TestCase):
    def reviewed(self, **over):
        item = {
            "candidate_id": "R3-abc1234567-1", "decision": "accept",
            "url": "https://www.sf.gov/news-seawall-update", "published_at": "2026-05-01T00:00:00Z",
            "saved_path": "sources/R3-abc1234567/x.md", "actor": "Port of San Francisco",
            "deadline_guess": "2028-12-31",
            "verbatim_quote": "The Port will complete the first phase of seawall repairs by December 2028.",
        }
        item.update(over)
        return {"round_id": "discovery-round-3-20261124", "candidates": [item]}

    def build(self, reviewed, existing=None):
        return dr.build_queue(reviewed, existing or {"texts": [], "urls": set(), "ids": {"P01"}})

    def test_accepted_candidate_becomes_lead(self):
        queue = self.build(self.reviewed())
        lead = queue["leads"][0]
        self.assertEqual(lead, {
            "promise_id": "R3-abc1234567-1",
            "promise_text": "The Port will complete the first phase of seawall repairs by December 2028.",
            "entity": "Port of San Francisco", "promised_date": "2026-05-01", "due_date": "2028-12-31",
            "source_id": None, "source_url": "https://www.sf.gov/news-seawall-update",
            "keywords": lead["keywords"]})
        self.assertTrue(lead["keywords"].startswith("San Francisco"))
        self.assertIn("seawall", lead["keywords"])
        self.assertIn("Port of San Francisco", lead["keywords"])
        self.assertEqual(queue["skipped"], [])

    def test_only_accepted_and_skips(self):
        self.assertEqual(self.build(self.reviewed(decision="reject"))["leads"], [])
        self.assertEqual(self.build(self.reviewed(decision=None))["leads"], [])
        for over, reason in (
                ({"published_at": None}, "published_date_missing"),
                ({"published_at": "2026-05"}, "published_date_missing"),
                ({"deadline_guess": "2020-01-01"}, "deadline_before_promised_date"),
                ({"verbatim_quote": ""}, "missing_fields")):
            queue = self.build(self.reviewed(**over))
            self.assertEqual(queue["leads"], [], over)
            self.assertEqual(queue["skipped"][0]["reason"], reason)
        self.assertEqual(self.build(self.reviewed(deadline_guess=None))["leads"][0]["due_date"], None)

    def test_id_collision_and_duplicates(self):
        queue = self.build(self.reviewed(candidate_id="P01"))
        self.assertEqual(queue["skipped"][0]["reason"], "id_collision")
        both = self.reviewed()
        both["candidates"].append({**both["candidates"][0], "candidate_id": "R3-abc1234567-2"})
        queue = self.build(both)
        self.assertEqual(len(queue["leads"]), 1)
        self.assertEqual(queue["skipped"][0]["reason"], "duplicate_text")
        existing = {"texts": [dr.normalize(both["candidates"][0]["verbatim_quote"])], "urls": set(), "ids": set()}
        self.assertEqual(self.build(self.reviewed(), existing)["skipped"][0]["reason"], "existing_text")

    def test_quote_must_still_be_in_saved_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources = Path(tmp) / "sources"
            saved = sources / "R3-abc1234567" / "x.md"
            saved.parent.mkdir(parents=True)
            saved.write_text("something else entirely", encoding="utf-8")
            queue = dr.build_queue(self.reviewed(), {"texts": [], "urls": set(), "ids": set()},
                                   sources_root=sources)
            self.assertEqual(queue["skipped"][0]["reason"], "quote_not_in_saved_bytes")

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            reviewed = Path(tmp) / "reviewed.json"
            reviewed.write_text(json.dumps(self.reviewed()), encoding="utf-8")
            out = Path(tmp) / "queue.json"
            self.assertEqual(dr.main(["--build-queue", str(reviewed), "--queue-output", str(out),
                                      "--workspace", tmp]), 0)
            self.assertEqual(json.loads(out.read_text())["leads"][0]["promise_id"], "R3-abc1234567-1")

    def test_lead_ids_never_collide_with_existing(self):
        # This round's own record and queue never count as existing. Round-3
        # promises already PUBLISHED on the site do, so they are not re-queued.
        import json
        existing = dr.load_existing()
        published = {p["promise_id"] for p in json.loads(
            (dr.REPO_ROOT / "docs" / "data.json").read_text(encoding="utf-8"))["promises"]}
        self.assertFalse({i for i in existing["ids"] if i.startswith("R3-")} - published)


class CliTests(unittest.TestCase):
    def test_dry_run_needs_no_network_or_key(self):
        self.assertEqual(dr.main(["--dry-run", "--max-queries", "3"]), 0)

    def test_full_run_writes_record_and_review(self):
        client = FakeClient(searches={"open": search_response((GOV, "Seawall"))}, pages={GOV: PAGE})
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "round.json"
            review = Path(tmp) / "staging" / "review.json"
            code = dr.main(["--workspace", tmp, "--max-queries", "2", "--max-fetches", "5",
                            "--domain-delay", "0", "--as-of", "2026-11-24", "--output", str(out),
                            "--review-output", str(review)], client_factory=lambda: _Ctx(client))
            self.assertEqual(code, 0)
            record = json.loads(out.read_text())
            self.assertEqual(record["round_id"], "discovery-round-3-20261124")
            self.assertTrue(record["candidates"])
            doc = json.loads(review.read_text())
            self.assertEqual(len(doc["candidates"]), len(record["candidates"]))
            self.assertIsNone(doc["candidates"][0]["decision"])
            self.assertTrue(doc["candidates"][0]["context_before"] or doc["candidates"][0]["context_after"])


class _Ctx:
    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):
        return getattr(self.client, name)

    async def __aenter__(self):
        return self.client

    async def __aexit__(self, *_):
        return False


if __name__ == "__main__":
    unittest.main()


def test_own_round_record_does_not_block_its_queue(tmp_path):
    import json
    from scripts import discovery_round as dr
    (tmp_path / "data").mkdir()
    (tmp_path / "seeds").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "data.json").write_text(json.dumps({"promises": []}))
    quote = "The Port will open the new plaza to the public by December 2027."
    record = {"candidates": [{"candidate_id": "R3-abc-1", "verbatim_quote": quote}]}
    (tmp_path / "data" / "discovery_round_3_20990101.json").write_text(json.dumps(record))
    existing = dr.load_existing(tmp_path)
    assert "R3-abc-1" not in existing["ids"]
    reviewed = {"candidates": [{"candidate_id": "R3-abc-1", "decision": "accept",
                                "verbatim_quote": quote, "url": "https://sf.gov/news-plaza",
                                "published_at": "2026-05-01T00:00:00Z", "actor": "Port of San Francisco",
                                "deadline_guess": "2027-12-31"}]}
    queue = dr.build_queue(reviewed, existing)
    assert [lead["promise_id"] for lead in queue["leads"]] == ["R3-abc-1"]
