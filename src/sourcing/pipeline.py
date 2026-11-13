"""Orchestration CLI & library entry point for the 3-stage outcome-blind sourcing pipeline."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.denials import summarize_denials
from src.funnel import build_funnel_summary
from src.sourcing.planner import SearchPlanner
from src.sourcing.qualification import AuditableCandidate, QualificationIntakeAgent

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_existing_candidate_pools(repo_root: Path) -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []

    # 1. Outside-the-box 10-year trends & cultural figures (15 candidates)
    otb_path = repo_root / "seeds" / "outside_the_box_candidates.json"
    if otb_path.exists():
        raw_otb = json.loads(otb_path.read_text(encoding="utf-8"))
        items = raw_otb.get("promises", []) if isinstance(raw_otb, dict) else raw_otb
        for item in items:
            row = dict(item)
            row["_source_batch"] = "outside_the_box_10yr"
            row["_discovery_channel"] = "stratified_cultural_archive"
            pool.append(row)

    # 2. Autonomous discovery candidates (10 candidates)
    disc_path = repo_root / "seeds" / "candidates_discovered.json"
    if disc_path.exists():
        raw_disc = json.loads(disc_path.read_text(encoding="utf-8"))
        for item in raw_disc.get("candidates", []):
            row = dict(item)
            row["_source_batch"] = "keenable_discovery_sweep"
            row["_discovery_channel"] = "keenable_temporal_search"
            pool.append(row)

    # 3. 38 Pending seed IDs from data.json (check if Archil CSV or promises.db provides text, else transparent pending_hydration)
    data_json_path = repo_root / "docs" / "data.json"
    pending_ids: List[str] = []
    if data_json_path.exists():
        djson = json.loads(data_json_path.read_text(encoding="utf-8"))
        pending_ids = list(djson.get("database_status", {}).get("pending_intake_ids", []))

    csv_seed_rows: Dict[str, Dict[str, Any]] = {}
    for cp in (
        repo_root / "data" / "promises-P13-P112.csv",
        Path("/mnt/archil/workspace/staging/promises-P13-P112.csv"),
    ):
        if cp.exists():
            with cp.open(encoding="utf-8") as cf:
                for r in csv.DictReader(cf):
                    csv_seed_rows[r["promise_id"]] = r
            break

    for pid in pending_ids:
        if pid in csv_seed_rows:
            row = dict(csv_seed_rows[pid])
            row["pending_hydration"] = False
        else:
            row = {
                "promise_id": pid,
                "entity": "Pending Seed Record",
                "promise_text": "",
                "pending_hydration": True,
            }
        row["_source_batch"] = "pending_seed_queue"
        row["_discovery_channel"] = "initial_seed_register"
        pool.append(row)

    return pool


def run_sourcing_cycle(
    *,
    repo_root: Path = REPO_ROOT,
    max_per_pillar: int = 2,
    write_outputs: bool = True,
) -> Dict[str, Any]:
    planner = SearchPlanner()
    queries = planner.generate_stratified_queries(max_per_pillar=max_per_pillar)

    qualifier = QualificationIntakeAgent()
    raw_pool = _load_existing_candidate_pools(repo_root)

    register: List[AuditableCandidate] = []
    for raw in raw_pool:
        cid = str(raw.get("promise_id") or raw.get("candidate_id") or "")
        dual = False if raw.get("pending_hydration") else qualifier.should_dual_sample(cid, rate=0.20)
        evaluated = qualifier.evaluate_candidate(
            raw,
            source_batch=raw.get("_source_batch", "manual"),
            discovery_channel=raw.get("_discovery_channel", "direct_seed"),
            dual_sample=dual,
        )
        register.append(evaluated)

    status_counts = Counter(c.qualification_status for c in register)
    pillar_counts = Counter(c.pillar for c in register if c.qualification_status == "qualified")
    district_counts = Counter(
        f"D{c.supervisor_district}"
        for c in register
        if c.qualification_status == "qualified" and c.supervisor_district is not None
    )
    dual_items = [c for c in register if c.dual_review_sample]
    dual_agreed = sum(1 for c in dual_items if c.dual_review_agreed is True)
    dual_rate = round(dual_agreed / len(dual_items), 3) if dual_items else 1.0

    # D3 measurement: funnel stages the register itself can count (the
    # database-universe stages are supplied by the export, which owns DB
    # reconciliation), plus the per-domain denial histogram over recorded
    # deny rows. Live rounds append {"url", "reason"} rows to
    # data/denied_leads.json; its absence is an honest empty histogram.
    denied_leads_path = repo_root / "data" / "denied_leads.json"
    deny_events: List[Dict[str, Any]] = []
    if denied_leads_path.exists():
        try:
            loaded = json.loads(denied_leads_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                deny_events = loaded
        except ValueError:
            deny_events = []

    funnel = build_funnel_summary(
        leads_encountered=len(register),
        qualified=status_counts.get("qualified", 0),
    )
    denial_histogram = summarize_denials(deny_events)

    summary = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "planner_query_count": len(queries),
        "planner_pillars_covered": sorted({q.pillar for q in queries}),
        "planner_districts_covered": sorted({q.supervisor_district for q in queries}),
        "encountered_count": len(register),
        "qualified_count": status_counts.get("qualified", 0),
        "needs_review_count": status_counts.get("needs_review", 0),
        "rejected_count": status_counts.get("rejected", 0),
        "qualified_pillar_distribution": dict(pillar_counts),
        "qualified_district_distribution": dict(district_counts),
        "dual_review_sampled_count": len(dual_items),
        "dual_review_agreement_rate": dual_rate,
        "funnel": funnel,
        "denials": denial_histogram,
        "outcome_blind_enforced": True,
    }

    output_payload = {
        "summary": summary,
        "planned_queries": [
            {
                "query_id": q.query_id,
                "pillar": q.pillar,
                "supervisor_district": q.supervisor_district,
                "neighborhood": q.neighborhood,
                "query_text": q.query_text,
                "target_domains": q.target_domains,
            }
            for q in queries
        ],
        "candidates": [c.to_dict() for c in register],
    }

    if write_outputs:
        data_dir = repo_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "intake_candidate_register.json").write_text(
            json.dumps(output_payload, indent=2), encoding="utf-8"
        )

        csv_fields = [
            "candidate_id",
            "source_batch",
            "discovery_channel",
            "encounter_date",
            "entity",
            "pillar",
            "record_type",
            "statement_preview",
            "promised_date",
            "promise_date_precision",
            "due_date",
            "due_date_status",
            "geographic_scope",
            "is_centroid",
            "supervisor_district",
            "neighborhood",
            "source_url",
            "source_tier",
            "qualification_status",
            "rejection_reason",
            "dual_review_sample",
            "dual_review_agreed",
            "outcome_blind_verified",
        ]
        with (data_dir / "intake_ledger.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writeheader()
            for c in register:
                d = c.to_dict()
                writer.writerow({k: d.get(k, "") for k in csv_fields})

        # Attach sourcing_audit summary into docs/data.json & docs/data.js if present
        data_json_path = repo_root / "docs" / "data.json"
        data_js_path = repo_root / "docs" / "data.js"
        if data_json_path.exists():
            djson = json.loads(data_json_path.read_text(encoding="utf-8"))
            djson.setdefault("database_status", {})["sourcing_audit"] = summary
            data_json_path.write_text(json.dumps(djson, indent=2), encoding="utf-8")
            if data_js_path.exists():
                data_js_path.write_text(
                    "/* SF Promises - Dynamic SQLite Export */\nwindow.__DEMO_DATA__ = "
                    + json.dumps(djson, indent=2)
                    + ";\n",
                    encoding="utf-8",
                )

    return output_payload


def main():
    parser = argparse.ArgumentParser(description="Run 3-stage outcome-blind SF Promises sourcing pipeline.")
    parser.add_argument("--classify-existing", action="store_true", help="Classify existing seeds and candidate pools into the intake ledger.")
    parser.add_argument("--max-per-pillar", type=int, default=2)
    args = parser.parse_args()

    res = run_sourcing_cycle(max_per_pillar=args.max_per_pillar, write_outputs=True)
    s = res["summary"]
    print(f"Planned queries: {s['planner_query_count']} across {len(s['planner_pillars_covered'])} pillars & {len(s['planner_districts_covered'])} districts")
    print(f"Encountered candidates: {s['encountered_count']} -> qualified={s['qualified_count']}, needs_review={s['needs_review_count']}, rejected={s['rejected_count']}")
    print(f"Dual review sampled: {s['dual_review_sampled_count']} (agreement={s['dual_review_agreement_rate']})")


if __name__ == "__main__":
    main()
