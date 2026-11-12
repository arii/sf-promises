"""Run candidate audits with tracked isolated source checks."""

import asyncio
import json
import tempfile
from pathlib import Path

import archil

from src.v2_candidate import audit_candidate
from src.v2_evidence import _primary_host, is_allowlisted_url
from src.v2_sandbox import run_in_fork
from src.v2_sources import load_archived_metadata, load_archived_text

TEMPLATE = "01a1ccce-3dd3-7c3e-b7e2-1219d264594e"
REMOTE = "/tmp/sf-promises-audit"


class WorkerAuditError(RuntimeError):
    """Worker checks could not be completed safely."""


async def audit_in_sandbox(conn, *, api_key, ledger, run_id, job_id, root, lead,
                           research, **kwargs):
    if not api_key:
        raise WorkerAuditError("ARCHIL_API_KEY missing")
    client = archil.Archil(api_key=api_key, region="aws-us-east-1")
    template = await client.sandboxes.get.aio(TEMPLATE)
    policy = (await template.get_network.aio()).egress
    if (template.status != "stopped" or template.mounts != []
            or policy is None or policy.default != "deny" or policy.allow):
        raise WorkerAuditError("Template state, mounts or deny-all policy changed")

    async def operation(worker):
        network = (await worker.get_network.aio()).egress
        if network is None or network.default != "deny" or network.allow:
            raise WorkerAuditError("Worker does not have deny-all egress")
        result = await asyncio.wait_for(worker.exec.aio(
            "mkdir -p /tmp/sf-promises-audit/src /tmp/sf-promises-audit/sources/job",
            timeout_seconds=30,
        ), timeout=40)
        if result.exit_code != 0:
            raise WorkerAuditError("Worker initialization failed")
        for name in ("checks.py", "v2_sources.py", "v2_evidence.py",
                     "v2_temporal.py", "v2_candidate_worker.py"):
            await worker.files.upload_file.aio(
                Path(__file__).with_name(name), f"{REMOTE}/src/{name}"
            )
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            uploaded = set()

            async def gate(evidence, origin=None):
                sources = []
                for source, quote in evidence:
                    metadata = load_archived_metadata(
                        root, lead["promise_id"], source["metadata_path"],
                        source["metadata_sha256"],
                    )
                    keys = ("path", "sha256", "url", "requested_url", "published_at", "fetched_at")
                    if (set(metadata) != set(keys) or any(metadata[k] != source.get(k) for k in keys)
                            or not is_allowlisted_url(metadata["requested_url"])):
                        raise WorkerAuditError("Source provenance mismatch")
                    text = load_archived_text(root, lead["promise_id"], source["path"], source["sha256"])
                    data = text.encode("utf-8")
                    if len(data) > 2_000_000:
                        raise WorkerAuditError("Source exceeds worker transfer limit")
                    digest = source["sha256"]
                    if digest not in uploaded:
                        local = temporary / (digest + ".md")
                        local.write_bytes(data)
                        await worker.files.upload_file.aio(
                            local, f"{REMOTE}/sources/job/{digest}.md"
                        )
                        uploaded.add(digest)
                    sources.append({
                        "sha256": digest, "quote": quote, "url": source["url"],
                        "tier": "TIER1_GOV" if _primary_host(source["url"]) else "TIER2_NEWS",
                    })
                request = temporary / "request.json"
                request.write_text(json.dumps({"sources": sources, "origin": origin}), encoding="utf-8")
                await worker.files.upload_file.aio(request, f"{REMOTE}/request.json")
                result = await asyncio.wait_for(worker.exec.aio(
                    "python3 -m src.v2_candidate_worker", cwd=REMOTE, timeout_seconds=60,
                ), timeout=70)
                try:
                    output = json.loads(result.stdout)
                    if (result.exit_code != 0 or set(output) != {"failures"}
                            or output["failures"] != []):
                        raise ValueError
                except (TypeError, ValueError):
                    raise WorkerAuditError("Worker source or temporal checks failed") from None

            sources = [source for phase in research["phases"].values()
                       for source in phase["sources"]]
            initial = []
            for source in sources:
                text = load_archived_text(root, lead["promise_id"], source["path"], source["sha256"])
                initial.append((source, next((char for char in text if not char.isspace()), "")))
            await gate(initial)
            return await audit_candidate(conn, root=root, lead=lead, research=research,
                                         worker_gate=gate, **kwargs)

    return await run_in_fork(
        client, TEMPLATE, operation, ledger=ledger, run_id=run_id, job_id=job_id,
        template_reviewed=True, network_reviewed=True,
    )
