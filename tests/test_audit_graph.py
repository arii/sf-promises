import asyncio
import tempfile
import unittest
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.audit_graph import build_audit_graph


class GraphTests(unittest.IsolatedAsyncioTestCase):
    async def test_fanout_respects_limit_and_collects_all_results(self):
        active = 0
        peak = 0

        async def worker(item):
            nonlocal active, peak
            active += 1
            peak = max(active, peak)
            await asyncio.sleep(0.01)
            active -= 1
            return {"id": item["id"]}

        graph = build_audit_graph(worker, max_concurrency=2, verified_capacity=2)
        result = await graph.ainvoke({"items": [{"id": str(i)} for i in range(5)]})
        self.assertEqual(peak, 2)
        self.assertEqual({row["id"] for row in result["results"]},
                         {str(i) for i in range(5)})

    async def test_invalid_limit_is_rejected(self):
        async def worker(item):
            return item

        for value in (0, -1, 1.5, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_audit_graph(worker, max_concurrency=value)

    async def test_parallelism_requires_capacity_review(self):
        async def worker(item):
            return item

        for capacity in (None, 1, True):
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                build_audit_graph(worker, max_concurrency=2, verified_capacity=capacity)

    async def test_sqlite_checkpoint_resumes_failed_fanout_after_reopen(self):
        calls = {"a": 0, "b": 0}

        async def worker(item):
            calls[item["id"]] += 1
            if item["id"] == "b" and calls["b"] == 1:
                raise RuntimeError("interrupted worker")
            return item

        config = {"configurable": {"thread_id": "audit-1"}}
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "checkpoints.sqlite")
            async with AsyncSqliteSaver.from_conn_string(path) as saver:
                graph = build_audit_graph(worker, checkpointer=saver)
                with self.assertRaisesRegex(RuntimeError, "interrupted worker"):
                    await graph.ainvoke({"items": [{"id": "a"}, {"id": "b"}]}, config)
            async with AsyncSqliteSaver.from_conn_string(path) as saver:
                graph = build_audit_graph(worker, checkpointer=saver)
                result = await graph.ainvoke(None, config)
        self.assertEqual({row["id"] for row in result["results"]}, {"a", "b"})
        self.assertEqual(calls, {"a": 1, "b": 2})


if __name__ == "__main__":
    unittest.main()
