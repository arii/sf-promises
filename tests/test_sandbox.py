import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.sandbox import run_in_fork
from src.worker_leases import WorkerLeases


class AsyncMethod:
    def __init__(self, func):
        self.aio = func


class SandboxTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.connection = sqlite3.connect(Path(self.directory.name) / "runner.sqlite")
        self.addCleanup(self.connection.close)
        self.ledger = WorkerLeases(self.connection)

    def options(self):
        return {"ledger": self.ledger, "run_id": "run", "job_id": "job",
                "network_reviewed": True}

    async def test_stops_and_deletes_fork_after_failure(self):
        events = []
        fork = SimpleNamespace(id="worker", status="running", mounts=[])

        async def stop():
            events.append("stop")
            return fork

        async def delete():
            events.append("delete")

        async def create_fork(*, name):
            events.append("fork")
            fork.name = name
            return fork

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        fork.stop = AsyncMethod(stop)
        fork.delete = AsyncMethod(delete)
        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))

        async def operation(_):
            raise RuntimeError("failed")

        with self.assertRaises(RuntimeError):
            await run_in_fork(client, "golden", operation, template_reviewed=True, **self.options())
        self.assertEqual(events, ["fork", "stop", "delete"])
        self.assertEqual(self.ledger.get("run", "job")["state"], "cleaned")

    async def test_running_template_is_not_forked(self):
        async def get(_):
            return SimpleNamespace(status="running")

        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(ValueError):
            await run_in_fork(client, "golden", lambda _: None, template_reviewed=True, **self.options())

    async def test_shared_or_unknown_mounts_are_not_forked(self):
        for mounts in ([{"disk_id": "shared"}], None):
            events = []

            async def create_fork():
                events.append("fork")

            async def get(_):
                return SimpleNamespace(status="stopped", mounts=mounts,
                                       fork=AsyncMethod(create_fork))

            client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
            with self.subTest(mounts=mounts), self.assertRaises(ValueError):
                await run_in_fork(client, "golden", lambda _: None, template_reviewed=True, **self.options())
            self.assertEqual(events, [])

    async def test_unreviewed_template_is_not_forked(self):
        events = []

        async def create_fork():
            events.append("fork")

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(ValueError):
            await run_in_fork(client, "golden", lambda _: None, **self.options())
        self.assertEqual(events, [])

    async def test_unreviewed_network_is_not_forked(self):
        events = []

        async def get(_):
            events.append("get")

        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        options = self.options()
        options["network_reviewed"] = False
        with self.assertRaises(ValueError):
            await run_in_fork(client, "golden", lambda _: None, template_reviewed=True, **options)
        self.assertEqual(events, [])

    async def test_lost_fork_response_blocks_retry(self):
        async def create_fork(*, name):
            raise TimeoutError("unknown outcome")

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(TimeoutError):
            await run_in_fork(client, "golden", lambda _: None, template_reviewed=True, **self.options())
        self.assertEqual(self.ledger.get("run", "job")["state"], "creating")
        with self.assertRaises(ValueError):
            await run_in_fork(client, "golden", lambda _: None, template_reviewed=True, **self.options())

    async def test_cleanup_failure_preserves_worker_id_for_review(self):
        async def stop():
            raise RuntimeError("cleanup failed")

        async def create_fork(*, name):
            return SimpleNamespace(id="worker", name=name, status="running", mounts=[],
                                   stop=AsyncMethod(stop))

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        async def operation(_):
            return "result"

        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(RuntimeError):
            await run_in_fork(client, "golden", operation, template_reviewed=True, **self.options())
        lease = self.ledger.get("run", "job")
        self.assertEqual((lease["state"], lease["worker_id"]), ("created", "worker"))

    async def test_worker_is_not_stopped_if_ownership_record_cannot_be_saved(self):
        events = []

        async def stop():
            events.append("stop")

        async def create_fork(*, name):
            return SimpleNamespace(id="worker", name=name, status="running", mounts=[],
                                   stop=AsyncMethod(stop))

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        def fail_record(*args):
            raise RuntimeError("ledger failure")

        self.ledger.record_worker = fail_record
        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(RuntimeError):
            await run_in_fork(client, "golden", lambda _: None, template_reviewed=True, **self.options())
        self.assertEqual(events, [])
        self.assertEqual(self.ledger.get("run", "job")["state"], "creating")

    async def test_cleanup_does_not_delete_a_different_sandbox(self):
        events = []

        async def delete():
            events.append("deleted")

        async def stop():
            return SimpleNamespace(id="golden", delete=AsyncMethod(delete))

        async def create_fork(*, name):
            return SimpleNamespace(id="worker", name=name, status="running", mounts=[],
                                   stop=AsyncMethod(stop))

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        async def operation(_):
            return "result"

        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(ValueError):
            await run_in_fork(client, "golden", operation, template_reviewed=True, **self.options())
        self.assertEqual(events, [])
        self.assertEqual(self.ledger.get("run", "job")["state"], "created")

    async def test_fork_response_identifying_golden_is_never_used(self):
        events = []

        async def create_fork(*, name):
            return SimpleNamespace(id="golden", name=name)

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        async def operation(_):
            events.append("operation")

        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(ValueError):
            await run_in_fork(client, "golden", operation, template_reviewed=True, **self.options())
        self.assertEqual(events, [])
        self.assertEqual(self.ledger.get("run", "job")["state"], "creating")

    async def test_fork_with_unexpected_mounts_is_cleaned_without_running_work(self):
        events = []
        worker = SimpleNamespace(id="worker", status="running", mounts=[{"disk_id": "shared"}])

        async def delete():
            events.append("delete")

        async def stop():
            events.append("stop")
            return worker

        async def create_fork(*, name):
            worker.name = name
            return worker

        async def get(_):
            return SimpleNamespace(status="stopped", mounts=[], fork=AsyncMethod(create_fork))

        async def operation(_):
            events.append("operation")

        worker.stop = AsyncMethod(stop)
        worker.delete = AsyncMethod(delete)
        client = SimpleNamespace(sandboxes=SimpleNamespace(get=AsyncMethod(get)))
        with self.assertRaises(ValueError):
            await run_in_fork(client, "golden", operation, template_reviewed=True, **self.options())
        self.assertEqual(events, ["stop", "delete"])
        self.assertEqual(self.ledger.get("run", "job")["state"], "cleaned")


if __name__ == "__main__":
    unittest.main()
