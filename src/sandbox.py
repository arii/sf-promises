"""Run work in a disposable fork without changing the golden template."""


async def run_in_fork(
    client, golden_id, operation, *, ledger, run_id, job_id, template_reviewed=False,
    network_reviewed=False,
):
    """Run a uniquely recorded attempt after a secret-free template review.

    A lost fork response remains unresolved in the ledger and is never retried
    automatically. Recovery must not race a live coordinator.
    """
    if template_reviewed is not True:
        raise ValueError("Golden sandbox requires a secret-free template review")
    if network_reviewed is not True:
        raise ValueError("Golden sandbox requires a network policy review")
    golden = await client.sandboxes.get.aio(golden_id)
    if golden.status != "stopped":
        raise ValueError("Golden sandbox must be stopped before forking")
    if not isinstance(getattr(golden, "mounts", None), list):
        raise ValueError("Golden sandbox mounts unavailable")
    for mount in golden.mounts:
        if getattr(mount, "path", "") not in ("/mnt/archil", "/mnt/archil/workspace"):
            raise ValueError(f"Unauthorized golden mount path: {getattr(mount, 'path', None)}")
    name = ledger.claim(run_id, job_id)
    worker = await golden.fork.aio(name=name)
    worker_id = getattr(worker, "id", None)
    if (not isinstance(worker_id, str) or not worker_id.strip()
            or worker_id == golden_id or getattr(worker, "name", None) != name):
        raise ValueError("Fork identity could not be verified; manual review required")
    ledger.record_worker(run_id, job_id, worker_id)
    try:
        if getattr(worker, "status", None) != "running":
            raise ValueError("Fork must be running")
        for mount in getattr(worker, "mounts", []):
            if getattr(mount, "path", "") not in ("/mnt/archil", "/mnt/archil/workspace"):
                raise ValueError(f"Unauthorized worker mount path: {getattr(mount, 'path', None)}")
        return await operation(worker)
    finally:
        stopped = await worker.stop.aio()
        if getattr(stopped, "id", None) != worker_id:
            raise ValueError("Stopped sandbox identity changed; manual review required")
        await stopped.delete.aio()
        ledger.mark_cleaned(run_id, job_id)
