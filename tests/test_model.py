import unittest
from decimal import Decimal
import json
from pathlib import Path
import tempfile

import httpx

from src.model import (
    NebiusBudgetExceeded,
    NebiusSpendLedger,
    completion_with_fallback,
    free_completion,
)


class ModelTests(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limit_rotates_only_free_models(self):
        requests = []

        def handler(request):
            import json
            if request.method == "GET":
                return httpx.Response(200, json={"data": [
                    {"id": "vendor/first:free", "pricing": {"prompt": "0", "completion": "0"}},
                    {"id": "vendor/second:free", "pricing": {"prompt": "0", "completion": "0"}},
                ]})
            requests.append(json.loads(request.content)["model"])
            if len(requests) == 1:
                return httpx.Response(429)
            return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

        async def no_wait(_):
            pass

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            response = await free_completion(
                client, "test-key", ["vendor/first:free", "vendor/second:free"],
                [{"role": "user", "content": "evidence"}], sleep=no_wait,
            )
        self.assertEqual(requests, ["vendor/first:free", "vendor/second:free"])
        self.assertEqual(response["choices"][0]["message"]["content"], "ok")

    async def test_paid_models_are_rejected_before_any_request(self):
        async with httpx.AsyncClient() as client:
            with self.assertRaises(ValueError):
                await free_completion(client, "test-key", ["vendor/model"],
                                      [{"role": "user", "content": "x"}])

    async def test_unlisted_or_nonzero_priced_free_model_is_never_called(self):
        requests = []

        def handler(request):
            requests.append(request.method)
            return httpx.Response(200, json={"data": [{
                "id": "vendor/model:free",
                "pricing": {"prompt": "0", "completion": "0", "request": "0.01"},
            }]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with self.assertRaises(ValueError):
                await free_completion(client, "test-key", ["vendor/model:free"],
                                      [{"role": "user", "content": "x"}])
        self.assertEqual(requests, ["GET"])

    async def test_invalid_tool_response_rotates_free_models(self):
        requests = []

        def handler(request):
            if request.method == "GET":
                return httpx.Response(200, json={"data": [
                    {"id": f"vendor/{name}:free", "pricing": {"prompt": "0", "completion": "0"}}
                    for name in ("first", "second")
                ]})
            model = json.loads(request.content)["model"]
            requests.append(model)
            message = ({"content": None} if model == "vendor/first:free" else
                       {"tool_calls": [{"function": {"name": "record", "arguments": "{}"}}]})
            return httpx.Response(200, json={"choices": [{"message": message}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            response = await free_completion(
                client, "test-key", ["vendor/first:free", "vendor/second:free"],
                [{"role": "user", "content": "evidence"}],
                tools=[{"type": "function", "function": {"name": "record"}}],
                tool_choice={"type": "function", "function": {"name": "record"}},
            )
        self.assertEqual(requests, ["vendor/first:free", "vendor/second:free"])
        self.assertEqual(response["choices"][0]["message"]["tool_calls"][0]["function"]["name"],
                         "record")

    async def test_429_uses_nebius_and_records_actual_spend(self):
        requests = []
        messages = [{"role": "user", "content": "request"}]
        tools = [{"type": "function", "function": {"name": "record_promise_evidence"}}]
        tool_choice = {"type": "function", "function": {"name": "record_promise_evidence"}}

        def handler(request):
            body = json.loads(request.content) if request.method == "POST" else {}
            requests.append((request.method, request.url.host, request.url.path, body))
            if request.url.host == "openrouter.ai" and request.method == "GET":
                return httpx.Response(200, json={"data": [{
                    "id": "vendor/model:free",
                    "pricing": {"prompt": "0", "completion": "0"},
                }]})
            if request.url.host == "openrouter.ai":
                return httpx.Response(429)
            if request.method == "GET":
                return httpx.Response(200, json={"data": [
                    {"id": "vendor/first", "pricing": {
                        "prompt": "0.0000001", "completion": "0.0000003",
                    }},
                    {"id": "vendor/second", "pricing": {
                        "prompt": "0.00000006", "completion": "0.00000024",
                    }},
                ]})
            if body["model"] == "vendor/first":
                return httpx.Response(429)
            return httpx.Response(200, json={
                "choices": [{"message": {
                    "tool_calls": [{"function": {
                        "name": "record_promise_evidence", "arguments": "{}",
                    }}],
                }, "finish_reason": "tool_calls"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            })

        async def no_wait(_):
            pass

        with tempfile.TemporaryDirectory() as directory:
            ledger = NebiusSpendLedger(Path(directory) / "spend.sqlite")
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                response = await completion_with_fallback(
                    client, "openrouter-key", ["vendor/model:free"],
                    messages, nebius_key="nebius-key",
                    nebius_models=["vendor/first", "vendor/second"],
                    spend_ledger=ledger, sleep=no_wait,
                    tools=tools, tool_choice=tool_choice,
                )
            self.assertEqual(
                response["choices"][0]["message"]["tool_calls"][0]["function"]["name"],
                "record_promise_evidence",
            )
            max_input_tokens = len(json.dumps(
                messages, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")) + 32 * len(messages)
            expected_spend = (
                Decimal(max_input_tokens) * Decimal("0.0000001")
                + Decimal(4096) * Decimal("0.0000003")
                + Decimal(10) * Decimal("0.00000006")
                + Decimal(5) * Decimal("0.00000024")
            )
            self.assertEqual(ledger.spent_usd, expected_spend)
        openrouter = [item for item in requests if item[1] == "openrouter.ai"
                      and item[2].endswith("/chat/completions")]
        nebius = [item for item in requests if item[1] == "api.tokenfactory.nebius.com"
                  and item[2].endswith("/chat/completions")]
        self.assertEqual(len(openrouter), 3)
        self.assertEqual([item[3]["model"] for item in nebius],
                         ["vendor/first", "vendor/second"])
        self.assertEqual(nebius[1][3]["tools"], tools)
        self.assertEqual(nebius[1][3]["tool_choice"], tool_choice)
        self.assertNotIn("response_format", nebius[1][3])

    async def test_non_429_openrouter_errors_do_not_call_nebius(self):
        requests = []

        def handler(request):
            requests.append(request.url.host)
            if request.method == "GET":
                return httpx.Response(200, json={"data": [{
                    "id": "vendor/model:free",
                    "pricing": {"prompt": "0", "completion": "0"},
                }]})
            return httpx.Response(401)

        with tempfile.TemporaryDirectory() as directory:
            ledger = NebiusSpendLedger(Path(directory) / "spend.sqlite")
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaises(httpx.HTTPStatusError):
                    await completion_with_fallback(
                        client, "openrouter-key", ["vendor/model:free"],
                        [{"role": "user", "content": "request"}],
                        nebius_key="nebius-key", nebius_models=["vendor/fallback"],
                        spend_ledger=ledger,
                    )
            self.assertEqual(ledger.spent_usd, Decimal("0"))
        self.assertEqual(requests, ["openrouter.ai", "openrouter.ai"])

    async def test_spend_cap_blocks_nebius_request_before_it_is_sent(self):
        requests = []

        def handler(request):
            requests.append((request.method, request.url.host, request.url.path))
            if request.url.host == "openrouter.ai" and request.method == "GET":
                return httpx.Response(200, json={"data": [{
                    "id": "vendor/model:free",
                    "pricing": {"prompt": "0", "completion": "0"},
                }]})
            if request.url.host == "openrouter.ai":
                return httpx.Response(429)
            if request.method == "GET":
                return httpx.Response(200, json={"data": [{
                    "id": "vendor/fallback",
                    "pricing": {"prompt": "0.0000001", "completion": "0.0000003"},
                }]})
            return httpx.Response(200, json={})

        async def no_wait(_):
            pass

        with tempfile.TemporaryDirectory() as directory:
            ledger = NebiusSpendLedger(Path(directory) / "spend.sqlite",
                                       limit_usd=Decimal("0.0000001"))
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaises(NebiusBudgetExceeded):
                    await completion_with_fallback(
                        client, "openrouter-key", ["vendor/model:free"],
                        [{"role": "user", "content": "request"}],
                        nebius_key="nebius-key", nebius_models=["vendor/fallback"],
                        spend_ledger=ledger, sleep=no_wait,
                    )
            self.assertEqual(ledger.spent_usd, Decimal("0"))
        self.assertFalse(any(path.endswith("/chat/completions")
                             for method, host, path in requests
                             if host == "api.tokenfactory.nebius.com"))


if __name__ == "__main__":
    unittest.main()
