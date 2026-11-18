"""Run candidate audits with bounded local source checks."""

import json

from src.candidate import audit_candidate
from src.evidence import _primary_host, is_allowlisted_url
from src.local_worker import run_worker
from src.sources import FETCH_METADATA_FIELDS, is_fetch_metadata, load_archived_metadata, load_archived_text


class WorkerAuditError(RuntimeError):
    """Worker checks could not be completed safely."""


async def audit_in_sandbox(conn, *, root, lead, research, **kwargs):
    async def gate(evidence, origin=None):
        sources, files = [], {}
        try:
            for source, quote in evidence:
                metadata = load_archived_metadata(
                    root, lead["promise_id"], source["metadata_path"], source["metadata_sha256"],
                )
                if (not is_fetch_metadata(metadata)
                        or any(metadata[k] != source.get(k) for k in FETCH_METADATA_FIELDS)
                        or not is_allowlisted_url(metadata["requested_url"])):
                    raise ValueError("Source provenance mismatch")
                text = load_archived_text(root, lead["promise_id"], source["path"], source["sha256"])
                data = text.encode("utf-8")
                if len(data) > 2_000_000:
                    raise ValueError("Source exceeds worker transfer limit")
                files[f"sources/job/{source['sha256']}.md"] = data
                sources.append({
                    "sha256": source["sha256"], "quote": quote, "url": source["url"],
                    "tier": "TIER1_GOV" if _primary_host(source["url"]) else "TIER2_NEWS",
                })
            files["request.json"] = json.dumps({"sources": sources, "origin": origin}).encode()
            output = await run_worker("src.candidate_worker", files=files, timeout=60)
            if not isinstance(output, dict) or output != {"failures": []}:
                raise ValueError("Worker source or temporal checks failed")
        except (ValueError, OSError, KeyError, TypeError) as exc:
            raise WorkerAuditError("Worker source or provenance checks failed") from exc

    sources = [source for phase in research["phases"].values() for source in phase["sources"]]
    initial = []
    try:
        for source in sources:
            text = load_archived_text(root, lead["promise_id"], source["path"], source["sha256"])
            initial.append((source, next((char for char in text if not char.isspace()), "")))
    except (ValueError, OSError) as exc:
        raise WorkerAuditError("Invalid archived source") from exc
    await gate(initial)
    return await audit_candidate(conn, root=root, lead=lead, research=research,
                                 worker_gate=gate, **kwargs)
