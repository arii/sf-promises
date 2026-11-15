"""One live discovery round through the four primary-source intake lanes.

Runs the document-led harvester over the three civic collections with
per-lane document caps, the campaign query lane over reviewed campaign
domains, builds lane leads from archived artifacts, screens each lead's
origin against the frozen evidence bar (src/evidence.screen_saved_source),
and writes round results (funnel rows, leads, denied leads) to results.json
under the round root — the rows a committed data PR appends to
data/window_funnel_rounds.json and data/denied_leads.json.

Usage: ROUND_ROOT=<dir> python3 scripts/run_intake_round.py
Requires SECRET_ARCHIL_API_KEY and SECRET_KEENABLE_API_KEY in the
environment.
"""

import asyncio
import hashlib
import itertools
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import archil

from src.candidate_sandbox import TEMPLATE, _resolve_template_id
from src.discovery import fetch_and_archive
from src.evidence import screen_saved_source
from src.keenable import RetryingKeenable
from src.lane_leads import build_lane_leads
from src.sourcing.document_harvester import (
    RawByteFetcher,
    default_specs,
    harvest_collections,
)
from src.sourcing.planner import SearchPlanner, reviewed_campaign_domains
from src.wayback import save_page_now
from src.worker_leases import WorkerLeases

WINDOW = "intake-20261115"
DOC_CAP_PER_LANE = 8
CAMPAIGN_ARCHIVED_CAP = 8
ROUND_ROOT = Path(os.environ.get("ROUND_ROOT", str(REPO.parent / "intake-round")))
ARCHIVE_ROOT = ROUND_ROOT / "sources"

LANE_ENTITY = {
    "bos_transcript": "SF Board of Supervisors",
    "budget": "SF Controller's Office",
    "ballot": "SF Department of Elections",
    "campaign_query": "daniellurie.com campaign fact sheets",
}


def pick_quote(text: str) -> str:
    """Deterministic verbatim quote candidate from an archived artifact."""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if len(sentence.split()) >= 6 and re.search(r"\b(19|20)\d{2}\b", sentence):
            return sentence.strip()
    for line in text.splitlines():
        if len(line.split()) >= 6:
            return line.strip()
    return " ".join(text.split())[:200]


def gate_lead(lead: dict, text_root: Path, source_tier: str) -> tuple[bool, list[str]]:
    origin = lead["origins"][0]
    failures = screen_saved_source(
        root=text_root, promise_id=lead["promise_id"], path=origin["path"],
        digest=origin["sha256"], quote=lead["promise_text"], url=origin["url"],
        source_tier=source_tier,
    )
    return not failures, failures


def doc_lane_row(channel: str, round_id: str, harvest: dict, leads: list[dict],
                 gate_passes: int, gate_failures: dict) -> dict:
    collection_key = {
        "bos_transcript": "bos_transcripts", "budget": "budget_documents",
        "ballot": "ballot_measures",
    }[channel]
    stats = harvest["collections"][collection_key]
    archived = stats["archived"]
    # Allowlisted stage: documents that cleared the dedupe union and entered
    # the archive path — archived, plus scanned documents denied at extraction.
    allowlisted = archived + sum(
        1 for d in harvest["denials"] if d["reason"] == "no_extractable_text"
    )
    return {
        "window": WINDOW,
        "round_id": round_id,
        "lane": channel,
        "counts": {
            "raw": stats["documents_found"],
            "allowlisted": allowlisted,
            "archived": archived,
            "leads": len(leads),
            "gate": gate_passes,
        },
        "dropped_reasons": harvest.get("dropped_by_collection", {}).get(collection_key, {}),
        "gate_failure_reasons": gate_failures,
        "denials": harvest["denials"],
        "document_cap": DOC_CAP_PER_LANE,
    }


async def run_document_lane(spec, client, golden_id, ledger, run_id, jobs, fetcher):
    job = f"job-{next(jobs)}"

    async def extract_pdf(**kw):
        call_job = f"job-{next(jobs)}"
        common = dict(
            client=client, golden_id=golden_id, ledger=ledger, run_id=run_id,
            job_id=call_job, root=ARCHIVE_ROOT,
            promise_id=kw["promise_id"], path=kw["path"], digest=kw["digest"],
            template_reviewed=True, network_reviewed=True,
        )
        if kw.get("page_from") is not None:
            from src.pdf import extract_archived_pdf_range
            return await extract_archived_pdf_range(
                page_from=kw["page_from"], page_to=kw["page_to"], **common)
        from src.pdf import extract_archived_pdf
        return await extract_archived_pdf(**common)

    async def inspect_pdf(**kw):
        from src.pdf import inspect_archived_pdf
        return await inspect_archived_pdf(
            client=client, golden_id=golden_id, ledger=ledger,
            run_id=run_id, job_id=f"job-{next(jobs)}", root=ARCHIVE_ROOT,
            promise_id=kw["promise_id"], path=kw["path"], digest=kw["digest"],
            template_reviewed=True, network_reviewed=True,
        )

    return await harvest_collections(
        specs=(spec,), archive_root=ARCHIVE_ROOT, repo_root=REPO,
        fetcher=fetcher, max_documents=DOC_CAP_PER_LANE,
        extract_pdf=extract_pdf, inspect_pdf=inspect_pdf,
    )


def leads_from_harvest(harvest: dict, channel: str) -> tuple[list[dict], dict]:
    leads, gate_failures = [], {}
    for doc in harvest["documents"]:
        text_path = doc.get("text_path")
        if doc.get("ranges"):
            artifacts = [
                {"path": r["path"], "sha256": r["sha256"]} for r in doc["ranges"]]
        elif text_path:
            artifacts = [{"path": text_path, "sha256": doc["text_sha256"]}]
        else:
            continue
        for artifact in artifacts:
            text = Path(artifact["path"]).read_text(encoding="utf-8", errors="replace")
            quote = pick_quote(text)
            doc_row = dict(doc)
            doc_row["text_path"], doc_row["text_sha256"] = artifact["path"], artifact["sha256"]
            doc_row.pop("ranges", None)
            leads.extend(build_lane_leads(
                doc_row, entity=LANE_ENTITY[channel], promise_text=quote))
    return leads, gate_failures


async def campaign_lane(client, run_id):
    planner = SearchPlanner()
    queries = planner.generate_campaign_fact_sheet_queries()
    domains = reviewed_campaign_domains()
    raw = 0
    allowlisted_hits = []
    denied = []
    for spec in queries:
        results = await client.search(
            spec.query_text, site=spec.target_domains[0] if spec.target_domains else None,
            max_results=8,
        )
        rows = list(results.results)
        raw += len(rows)
        for row in rows:
            url = getattr(row, "url", None) or (row.get("url") if isinstance(row, dict) else None)
            if not url:
                continue
            host = re.sub(r"^https?://", "", url).split("/")[0]
            if any(host == d or host.endswith("." + d) for d in domains):
                allowlisted_hits.append(url)
            else:
                denied.append({"url": url, "reason": "outside_reviewed_campaign_domains"})
        await asyncio.sleep(1.0)

    archived_docs = []
    for index, url in enumerate(allowlisted_hits[:CAMPAIGN_ARCHIVED_CAP]):
        promise_id = f"camp-{hashlib.sha256(url.encode()).hexdigest()[:12]}"
        try:
            saved = await fetch_and_archive(
                client, url, ARCHIVE_ROOT, promise_id, capture=save_page_now)
            archived_docs.append((saved, promise_id))
        except Exception as exc:
            denied.append({"url": url, "reason": f"fetch_failed:{type(exc).__name__}"})

    leads, gate_failures = [], {}
    for saved, promise_id in archived_docs:
        text = Path(saved["path"]).read_text(encoding="utf-8", errors="replace")
        quote = pick_quote(text)
        lead = {
            "promise_id": promise_id,
            "entity": LANE_ENTITY["campaign_query"],
            "promise_text": quote,
            "intake_channel": "campaign_query",
            "origins": [{
                "url": saved["url"], "path": saved["path"], "sha256": saved["sha256"],
                "published_at": saved.get("published_at"),
            }],
        }
        leads.append(lead)

    gate_passes = 0
    for lead in leads:
        ok, failures = gate_lead(lead, ARCHIVE_ROOT, "TIER2_NEWS")
        if ok:
            gate_passes += 1
        for failure in failures:
            gate_failures[failure] = gate_failures.get(failure, 0) + 1

    row = {
        "window": WINDOW,
        "round_id": "r6-intake-campaign_query",
        "lane": "campaign_query",
        "counts": {
            "raw": raw,
            "allowlisted": len(allowlisted_hits),
            "archived": len(archived_docs),
            "leads": len(leads),
            "gate": gate_passes,
        },
        "gate_failure_reasons": gate_failures,
        "denials": denied,
        "archived_cap": CAMPAIGN_ARCHIVED_CAP,
        "planned_queries": len(queries),
    }
    return row, leads


async def main():
    round_id_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"R6-{round_id_stamp}"
    ROUND_ROOT.mkdir(parents=True, exist_ok=True)
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    ledger_conn = sqlite3.connect(ROUND_ROOT / "worker-leases.sqlite")
    ledger = WorkerLeases(ledger_conn)
    jobs = iter(itertools.count())

    archil_client = archil.Archil(
        api_key=os.environ["SECRET_ARCHIL_API_KEY"], region="aws-us-east-1")
    golden_id = await _resolve_template_id(archil_client, TEMPLATE)

    specs = {spec.key: spec for spec in default_specs()}
    fetcher = RawByteFetcher()

    rows, all_denials, lead_totals = [], [], {}
    async with RetryingKeenable(api_key=os.environ["SECRET_KEENABLE_API_KEY"]) as kclient:
        for key, channel in (
            ("bos_transcripts", "bos_transcript"),
            ("budget_documents", "budget"),
            ("ballot_measures", "ballot"),
        ):
            harvest = await run_document_lane(
                specs[key], archil_client, golden_id, ledger, run_id, jobs, fetcher)
            leads, _ = leads_from_harvest(harvest, channel)
            gate_passes, gate_failures = 0, {}
            for lead in leads:
                ok, failures = gate_lead(lead, ARCHIVE_ROOT, "TIER1_GOV")
                if ok:
                    gate_passes += 1
                for failure in failures:
                    gate_failures[failure] = gate_failures.get(failure, 0) + 1
            row = doc_lane_row(channel, f"r6-intake-{channel}", harvest, leads,
                               gate_passes, gate_failures)
            rows.append(row)
            all_denials.extend(harvest["denials"])
            lead_totals[channel] = leads
            print(json.dumps(row["counts"]), flush=True)

        campaign_row, campaign_leads = await campaign_lane(kclient, run_id)
        rows.append(campaign_row)
        all_denials.extend(campaign_row["denials"])
        lead_totals["campaign_query"] = campaign_leads
        print(json.dumps(campaign_row["counts"]), flush=True)

    await fetcher.aclose()

    lead_dump = {
        channel: [dict(lead) for lead in leads]
        for channel, leads in lead_totals.items()
    }
    (ROUND_ROOT / "results.json").write_text(json.dumps({
        "run_id": run_id, "rows": rows, "leads": lead_dump,
        "denied_leads": all_denials,
    }, indent=2))
    print("WROTE", ROUND_ROOT / "results.json")


if __name__ == "__main__":
    asyncio.run(main())
