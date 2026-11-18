"""Bounded fixture batch; no network, providers, or production publication."""

import argparse
import asyncio
from collections import Counter
import json
from pathlib import Path
import re
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

from src.discovery import fetch_and_archive
from src.run_live import candidate_batch
from src.workspace import database_path


DOCUMENTS = {
    "https://sf.gov/origin": (
        "January 1, 2020. San Francisco will build the library by 2022.", "2020-01-01",
    ),
    "https://sf.gov/delivery": ("The San Francisco library opened in 2022.", "2022-12-31"),
    "https://sf.gov/survival": ("The San Francisco library remains open in 2026.", "2026-01-01"),
}


async def complete(messages, *, tool_choice, **kwargs):
    name = tool_choice["function"]["name"]
    if name == "record_promise_evidence":
        pid = re.search(r"Promise ID: (\S+)", messages[-1]["content"])[1]
        result = {"candidates": [{
            "promise_id": pid, "quote_segment_id": 1, "speaker": "San Francisco",
            "promised_date": "2020-01-01", "deadline": "2022-12-31",
        }]}
    elif name == "assess_outcome":
        result = {
            "initial_delivery": "DELIVERED_ON_TIME", "current_survival": "ACTIVE_OPERATIONAL",
            "delivery": {"source_index": 0, "segment_id": 0},
            "survival": {"source_index": 1, "segment_id": 0},
            "entity_name": "San Francisco", "entity_type": "City Agency",
            "sector": "Governance & Finance", "neighborhood": "Citywide",
        }
    elif name == "verify_origin":
        result = {"action": True, "promise_date": True, "deadline": True,
                  "explanation": "Fixture origin supports the commitment."}
    elif name == "verify_evidence":
        result = {
            "action": True, "promise_date": True, "deadline": True, "delivery": True,
            "survival": True, "entity_and_location": True, "explanation": "Fixture evidence agrees.",
        }
    else:
        raise AssertionError(name)
    return {"choices": [{"message": {"tool_calls": [{"function": {
        "name": name, "arguments": json.dumps(result),
    }}]}}]}


async def research(database, pid, run_id=None):
    class Fetch:
        async def fetch(self, url):
            text, published = DOCUMENTS[url]
            return SimpleNamespace(url=url, content=text, published_at=published,
                                   raw={"truncated": False})

    sources = [await fetch_and_archive(Fetch(), url, database.parent / "sources", pid)
               for url in DOCUMENTS]
    return {"results": [{"phases": {
        "origin": {"sources": sources[:1], "blocked": []},
        "delivery": {"sources": sources[1:2], "blocked": []},
        "survival": {"sources": sources[2:], "blocked": []},
    }}]}


async def run(database, *, reject=False):
    async def discover(database, pid, run_id):
        result = await research(database, pid, run_id)
        if pid == "P03":
            result["results"][0]["phases"]["origin"]["sources"] = []
        if reject and pid == "P01":
            source = result["results"][0]["phases"]["delivery"]["sources"][0]
            Path(source["path"]).write_text("tampered")
        return result

    with (patch("src.run_live.credentials", return_value={}),
          patch("src.run_live.build_completion", return_value=complete),
          patch("src.run_live.discover_run", side_effect=discover)):
        return await candidate_batch(database, ["P01", "P03"])


def reconcile(staged, baseline):
    actual = {row["promise_id"] for row in staged["promises"]}
    expected = {row["promise_id"] for row in baseline["promises"]}
    return {
        "fixture_only": True,
        "staged_count": len(actual), "baseline_count": len(expected),
        "added_ids": sorted(actual - expected), "missing_ids": sorted(expected - actual),
        "staged_verdict_counts": dict(Counter(p["verdict"].lower() for p in staged["promises"])),
        "baseline_verdict_counts": dict(Counter(p["verdict"].lower() for p in baseline["promises"])),
        "historical_provenance": "Not recovered by this fixture run; no production evidence fetched",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=database_path())
    parser.add_argument("--reconcile", type=Path)
    args = parser.parse_args()
    if args.reconcile:
        print(json.dumps(reconcile(json.loads(args.reconcile.read_text()),
                                   json.loads(Path("docs/data.json").read_text())), indent=2))
        return
    result = asyncio.run(run(args.db))
    with sqlite3.connect(args.db) as conn:
        counts = {name: conn.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                  for name in ("promises", "verdicts", "quarantined")}
    print(json.dumps({"fixture_only": True, "statuses": [row["status"] for row in result],
                      "database_counts": counts}))


if __name__ == "__main__":
    main()
