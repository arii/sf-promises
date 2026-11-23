import json
import os
import unittest
from pathlib import Path
from unittest import mock

from scripts.build_discovery_queue import build, search_keywords
from src import run_live


class QueueSelectionTests(unittest.TestCase):
    def test_default_queue_is_canonical_targets(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SF_PROMISES_QUEUE", None)
            self.assertEqual(run_live.queue_path(), Path("seeds/canonical_targets.json"))
            ids = [lead["promise_id"] for lead in run_live.load_queue()]
        canonical = json.loads(Path("seeds/canonical_targets.json").read_text())["leads"]
        self.assertEqual(ids, [lead["promise_id"] for lead in canonical])

    def test_env_selects_another_queue(self):
        with mock.patch.dict(os.environ, {"SF_PROMISES_QUEUE": "seeds/discovery_targets.json"}):
            self.assertEqual(run_live.queue_path(), Path("seeds/discovery_targets.json"))
            self.assertTrue(run_live.load_queue())


class LaneTimeoutTests(unittest.TestCase):
    def test_default_and_override(self):
        with mock.patch.dict(os.environ, {"SF_PROMISES_LANE_TIMEOUT": ""}):
            self.assertEqual(run_live.lane_timeout(), run_live.DEFAULT_TIMEOUT_SECONDS)
        with mock.patch.dict(os.environ, {"SF_PROMISES_LANE_TIMEOUT": "43200"}):
            self.assertEqual(run_live.lane_timeout(), 43200.0)

    def test_rejects_invalid_values(self):
        for value in ("abc", "0", "-5", "inf", "nan"):
            with self.subTest(value=value), mock.patch.dict(
                    os.environ, {"SF_PROMISES_LANE_TIMEOUT": value}):
                with self.assertRaises(ValueError):
                    run_live.lane_timeout()


class TransientFailureGateTests(unittest.TestCase):
    def test_connection_error_in_any_phase_blocks(self):
        phases = {
            "origin": {"sources": [{"url": "a"}], "blocked": []},
            "delivery": {"sources": [{"url": "b"}], "blocked": []},
            "survival": {"sources": [], "blocked": [{"url": "c", "reason": "fetch_connection_error"}]},
        }
        self.assertTrue(run_live.transient_fetch_failure(phases))

    def test_permanent_blocks_do_not_count(self):
        phases = {
            "origin": {"sources": [], "blocked": [{"url": "a", "reason": "http_404"}]},
            "delivery": {"sources": [], "blocked": [{"url": "b", "reason": "http_422_wrong_page"}]},
            "survival": {"sources": [], "blocked": []},
        }
        self.assertFalse(run_live.transient_fetch_failure(phases))


class BuildQueueTests(unittest.TestCase):
    def _register(self, tmp, candidates):
        path = Path(tmp) / "register.json"
        path.write_text(json.dumps({"candidates": candidates}))
        return path

    def _candidate(self, cid, **overrides):
        item = {
            "candidate_id": cid, "qualification_status": "qualified",
            "promised_date": "2024-01-02", "due_date": "2025-12-31",
            "entity": "SFMTA", "statement_preview": "SFMTA will open the Example Line by 2025.",
            "source_url": "https://www.sfmta.com/news/example-line-opening-plan",
        }
        item.update(overrides)
        return item

    def test_builds_leads_and_skips_imprecise_or_unqualified(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            register = self._register(tmp, [
                self._candidate("A"),
                self._candidate("B", promised_date="2024"),
                self._candidate("C", qualification_status="needs_review"),
            ])
            queue = build(register=register, rounds=())
        self.assertEqual([lead["promise_id"] for lead in queue["leads"]], ["A"])
        self.assertEqual(queue["skipped"], [{"promise_id": "B", "reason": "promised_date not day-precision"}])
        lead = queue["leads"][0]
        self.assertEqual(lead["promise_text"], "SFMTA will open the Example Line by 2025.")
        self.assertEqual(lead["keywords"], "San Francisco example line opening plan")

    def test_round_quote_replaces_preview(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            register = self._register(tmp, [self._candidate("A")])
            rounds = Path(tmp) / "round.json"
            rounds.write_text(json.dumps({"candidates": [{
                "candidate_id": "A", "quote_verbatim": True,
                "verbatim_quote": "The line opens in 2025.", "url": "https://www.sfmta.com/x",
            }]}))
            queue = build(register=register, rounds=(rounds,))
        self.assertEqual(queue["leads"][0]["promise_text"], "The line opens in 2025.")
        self.assertEqual(queue["leads"][0]["source_url"], "https://www.sfmta.com/x")

    def test_duplicate_ids_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            register = self._register(tmp, [self._candidate("A"), self._candidate("A")])
            with self.assertRaises(ValueError):
                build(register=register, rounds=())

    def test_keywords_decode_url_and_fall_back_to_quote(self):
        self.assertEqual(
            search_keywords("https://sfpuc.gov/sites/default/files/documents/Lower%20Alemany%20Stormwater.pdf",
                            "SFPUC", ""),
            "San Francisco Lower Alemany Stormwater",
        )
        self.assertEqual(
            search_keywords("https://sfport.com/seawall", "Port",
                            "The Embarcadero Seawall Program will invest"),
            "San Francisco seawall Embarcadero Program invest",
        )

    def test_committed_queue_matches_register(self):
        committed = json.loads(Path("seeds/discovery_targets.json").read_text())
        self.assertEqual(committed, build())


if __name__ == "__main__":
    unittest.main()
