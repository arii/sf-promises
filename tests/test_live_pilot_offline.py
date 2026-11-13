from datetime import date
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.extract import Candidate
from src.run_live import URLS, run


class OfflineLivePilotTests(unittest.IsolatedAsyncioTestCase):
    async def test_p36_pipeline_archives_reviews_publishes_and_exports(self):
        seed = next(
            item for item in json.loads(
                Path("seeds/canonical_targets.json").read_text(encoding="utf-8")
            )["leads"]
            if item["promise_id"] == "P36"
        )
        content = {
            "ORIGIN": (
                "Thursday, April 20, 2017\n" + seed["promise_text"]
            ),
            "DELIVERY": (
                "2020 POWER CONTENT LABEL\nEnergy Resources\nGreen\nSuperGreen\n"
                "2020 CA\nPower Mix\nEligible Renewable1\n54.5%"
            ),
            "SURVIVAL": (
                "Power Content Label\n2025\nGreen SuperGreen Saver\n"
                "RPS Eligible Renewables - Subtotal 84%"
            ),
        }
        dates = {
            "ORIGIN": "2017-04-20T12:00:00Z",
            "DELIVERY": "2021-09-16T18:37:21Z",
            "SURVIVAL": "2026-10-16T17:56:37Z",
        }

        class FakeSearch:
            def __init__(self, **_kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return None

            async def fetch(self, url):
                phase = next(key for key, value in URLS.items() if value == url)
                return SimpleNamespace(
                    url=url, content=content[phase], published_at=dates[phase],
                    raw={"truncated": False},
                )

        async def extract(_client, api_key, models, **kwargs):
            self.assertEqual(api_key, "openrouter-test-key")
            self.assertTrue(models)
            self.assertTrue(all(model.endswith(":free") for model in models))
            self.assertEqual(kwargs["provider"], "openrouter")
            return [Candidate(
                promise_id="P36", promise_text=seed["promise_text"], speaker="Ed Lee",
                promised_date=date(2017, 4, 20), deadline=date(2020, 12, 31),
            )]

        async def assess(*_args, **_kwargs):
            facts = {
                "initial_delivery": "DELIVERED_ON_TIME",
                "current_survival": "ACTIVE_OPERATIONAL",
                "delivery_percent": 54.5,
                "survival_percent": 84.0,
            }
            return {"choices": [{"message": {"content": json.dumps(facts)}}]}

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "promises_v2.db"
            with (
                patch.dict(os.environ, {"MODEL_PROVIDER": "openrouter"}),
                patch("src.run_live.credentials", return_value={
                    "KEENABLE_API_KEY": "test-key",
                    "OPENROUTER_API_KEY": "openrouter-test-key",
                }),
                patch("src.run_live.RetryingKeenable", FakeSearch),
                patch("src.run_live.extract_with_model", extract),
                # The pilot exercises the OpenRouter/Nebius provider path; the
                # agent lane is the default lane and is covered by
                # tests/test_agent_lane.py.
                patch("src.run_live.completion_with_fallback", assess),
            ):
                result = await run(database, "P36")

            self.assertEqual(result["verdict"]["verdict"], "KEPT")
            self.assertEqual(
                {row["phase"] for row in result["evidence"]},
                {"ORIGIN", "DELIVERY", "SURVIVAL"},
            )
            self.assertEqual(result["export"]["tallies"], {"KEPT": 1})
            self.assertTrue((Path(directory) / "staging" / "kept_P36.json").exists())
            self.assertTrue((Path(directory) / "staging" / "broken_P36.json").exists())
            with sqlite3.connect(database) as conn:
                self.assertEqual(
                    conn.execute(
                        "SELECT status FROM promises_pending WHERE promise_id='P36'"
                    ).fetchone()[0],
                    "published",
                )
                self.assertEqual(
                    conn.execute("SELECT COUNT(*) FROM promises").fetchone()[0], 1
                )


if __name__ == "__main__":
    unittest.main()
