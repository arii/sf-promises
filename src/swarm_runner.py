"""SF Promises v2: Hierarchical LangGraph Swarm Runner & Archil VM Orchestrator.

Orchestrates time-bounded Keenable discovery, model extraction via Nebius/OpenRouter,
and isolated per-promise verification gates inside Archil persistent worker microVMs
mounting the shared project disk (/mnt/archil/workspace).
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys

from src.v2_candidate_sandbox import TEMPLATE, audit_in_sandbox
from src.v2_database import initialize_database
from src.v2_export import build_snapshot
from src.v2_graph import build_audit_graph
from src.v2_run_live import candidate_batch, credentials

CANARY_SEEDS = ["P83", "P82", "P85", "P36"]


def sync_db_to_archil_disk(local_db: Path, disk_id: str | None = None, api_key: str | None = None):
    """Sync the local SQLite database to /mnt/archil/workspace/promises_v2.db on the Archil disk."""
    if not disk_id or not api_key:
        return
    import archil
    client = archil.Archil(api_key=api_key, region="aws-us-east-1")
    disk = client.disks.get(disk_id)
    # Revoke any orphaned delegations before writing
    for d in disk.list_delegations():
        if d.is_orphaned:
            disk.revoke_delegation(d)
    data = local_db.read_bytes()
    print(f"Syncing {len(data)} bytes to Archil disk {disk_id}...")
    disk.put_object("workspace/promises_v2.db", data)
    print("Database synced to /mnt/archil/workspace/promises_v2.db successfully.")


def export_to_docs(local_db: Path, export_path: Path):
    """Export verified v2 candidate results to docs/data.json for static demo rendering."""
    if not export_path.exists():
        print(f"Export target {export_path} does not exist; skipping demo update.")
        return

    conn = sqlite3.connect(local_db)
    conn.row_factory = sqlite3.Row
    try:
        promises = conn.execute(
            "SELECT * FROM promises ORDER BY date_promised DESC, promise_id"
        ).fetchall()
        verdicts = dict(conn.execute(
            "SELECT promise_id, verdict FROM verdicts"
        ).fetchall())

        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        existing_by_id = {p["promise_id"]: p for p in data.get("promises", [])}

        for row in promises:
            pid = row["promise_id"]
            verd = verdicts.get(pid, "IN_PROGRESS")
            if pid in existing_by_id:
                existing_by_id[pid]["verdict"] = verd
                existing_by_id[pid]["entity"] = row["entity_name"]
                existing_by_id[pid]["neighborhood"] = row["neighborhood"]
                existing_by_id[pid]["category"] = row["sector"]
            else:
                existing_by_id[pid] = {
                    "promise_id": pid,
                    "promise_text": row["promise_text"],
                    "entity": row["entity_name"],
                    "entity_type": row["entity_type"],
                    "category": row["sector"],
                    "neighborhood": row["neighborhood"],
                    "promised_date": row["date_promised"],
                    "due_date": row["date_deadline"],
                    "verdict": verd,
                    "verdict_reason": "Verified by v2 LangGraph swarm",
                    "display_no": pid,
                }

        data["promises"] = list(existing_by_id.values())
        data["database_status"]["v2_verified_count"] = len(promises)
        data["metadata"]["last_updated"] = datetime.now(timezone.utc).strftime("%b %d, %Y")

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(promises)} verified records to {export_path}.")

        # Also sync docs/data.js for client loading
        js_path = export_path.with_name("data.js")
        with open(js_path, "w", encoding="utf-8") as f:
            f.write("/* SF Promises - Dynamic SQLite Export */\nwindow.__DEMO_DATA__ = ")
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write(";\n")
        print(f"Exported synchronized JavaScript data to {js_path}.")
    finally:
        conn.close()


async def run_swarm(
    seeds_path: Path,
    db_path: Path,
    export_path: Path | None = None,
    canary_only: bool = False,
    seed_ids: list[str] | None = None,
    concurrency: int = 1,
):
    """Run the swarm across selected canonical targets."""
    print("=" * 80)
    print("SF PROMISES v2 SWARM RUNNER")
    print(f"Golden Template: {TEMPLATE}")
    print(f"Database: {db_path}")
    print(f"Concurrency: {concurrency}")
    print("=" * 80)

    with open(seeds_path, "r", encoding="utf-8") as f:
        targets_data = json.load(f)

    all_leads = targets_data["leads"]
    target_ids = []

    if seed_ids:
        target_ids = seed_ids
    elif canary_only:
        target_ids = [s for s in CANARY_SEEDS if any(l["promise_id"] == s for l in all_leads)]
    else:
        target_ids = [l["promise_id"] for l in all_leads]

    print(f"Running audit on {len(target_ids)} targets: {target_ids}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        initialize_database(db_path)

    # Run candidate batch through isolated Archil sandbox worker microVMs
    results = await candidate_batch(db_path, target_ids)

    print("\n--- Swarm Audit Results Summary ---")
    for r in results:
        status = r.get("status", "unknown")
        pid = r.get("promise_id", "")
        verd = r.get("verdict", "")
        reason = r.get("reason", "")
        print(f"[{status.upper()}] {pid}: verdict={verd} reason={reason}")

    # Sync to Archil shared disk
    creds = credentials()
    sync_db_to_archil_disk(
        db_path,
        disk_id=os.environ.get("ARCHIL_DISK_ID") or creds.get("ARCHIL_DISK_ID", "dsk-000000000018f6e1"),
        api_key=creds.get("ARCHIL_API_KEY"),
    )

    # Export to docs
    if export_path:
        export_to_docs(db_path, export_path)

    return results


def main():
    parser = argparse.ArgumentParser(description="SF Promises v2 Swarm Runner")
    parser.add_argument("--seeds", type=Path, default=Path("seeds/canonical_targets.json"))
    parser.add_argument("--canary-only", action="store_true", help="Run only the 4 canary benchmark cases")
    parser.add_argument("--seed-ids", nargs="+", help="Specific promise IDs to audit")
    parser.add_argument("--concurrency", type=int, default=1, help="Max worker VM concurrency")
    parser.add_argument("--db", type=Path, default=Path("data/promises_v2.db"))
    parser.add_argument("--export", type=Path, default=Path("docs/data.json"))
    args = parser.parse_args()

    asyncio.run(run_swarm(
        seeds_path=args.seeds,
        db_path=args.db,
        export_path=args.export,
        canary_only=args.canary_only,
        seed_ids=args.seed_ids,
        concurrency=args.concurrency,
    ))


if __name__ == "__main__":
    main()
