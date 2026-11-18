import asyncio
from datetime import date
import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from src.candidate_sandbox import audit_in_sandbox, WorkerAuditError
from src.database import initialize_database
from src.local_worker import run_worker
from tests.offline_pipeline import complete, research


@pytest.mark.parametrize("fault", ["metadata", "url", "hash"])
def test_local_gate_blocks_invalid_source_provenance(tmp_path, fault):
    async def check():
        database = tmp_path / "promises.db"
        initialize_database(database)
        root = tmp_path / "sources"
        material = (await research(database, "P01"))["results"][0]
        source = material["phases"]["origin"]["sources"][0]
        if fault == "metadata":
            Path(source["metadata_path"]).write_text("{}")
        elif fault == "url":
            source["requested_url"] = "https://untrusted.invalid/source"
        else:
            source["sha256"] = "0" * 64
        with sqlite3.connect(database) as conn:
            with pytest.raises(WorkerAuditError):
                await audit_in_sandbox(
                    conn, root=root, staging_root=tmp_path / "staging",
                    lead={"promise_id": "P01"}, research=material, complete=complete,
                    as_of=date(2026, 11, 11),
                )
            assert conn.execute("SELECT count(*) FROM promises").fetchone()[0] == 0
    asyncio.run(check())


@pytest.mark.parametrize("fault", [None, "quote", "url", "date", "empty"])
def test_real_local_candidate_worker_checks_quotes_urls_and_time(fault):
    text = b"San Francisco will build a library by 2022."
    digest = hashlib.sha256(text).hexdigest()
    request = {"sources": [{
        "sha256": digest, "quote": text.decode(), "url": "https://sf.gov/origin",
        "tier": "TIER1_GOV",
    }], "origin": {"quote": text.decode(), "promised": "2020-01-01",
                    "published": "2020-01-01", "deadline": "2022-12-31"}}
    if fault == "quote":
        request["sources"][0]["quote"] = "invented quotation"
    elif fault == "url":
        request["sources"][0]["url"] = "https://untrusted.invalid/source"
    elif fault == "date":
        request["origin"]["promised"] = "2021-01-01"
    elif fault == "empty":
        request = {"sources": [], "origin": None}
    result = asyncio.run(run_worker("src.candidate_worker", files={
        f"sources/job/{digest}.md": text, "request.json": json.dumps(request).encode(),
    }))
    assert bool(result["failures"]) == (fault in ("quote", "url", "date"))
