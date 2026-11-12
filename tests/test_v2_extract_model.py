import asyncio
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import httpx

from src.v2_extract import (
    InvalidPromiseDate, QuoteNotFound, _materialize_quotes, _source_segments,
    extract_with_model,
)
from src.v2_model import ModelResponseError
from src.v2_sources import archive_source


class ModelExtractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_saved_source_is_sent_to_free_model_and_result_verified(self):
        requests = []
        response = {"candidates": [{
            "promise_id": "P1", "promise_text": "We will build a library.",
            "speaker": "Mayor", "promised_date": "2024-01-01", "deadline": None,
        }]}
        indexed_response = {"candidates": [{
            "promise_id": "P1", "quote_segment_id": 0,
            "speaker": "Mayor", "promised_date": "2024-01-01", "deadline": None,
        }]}
        outputs = [
            {"tool_calls": [{"function": {
                "name": "record_promise_evidence",
                "arguments": json.dumps(indexed_response),
            }}]},
            {"content": f"<think>reasoning</think>{json.dumps(response)}"},
        ]

        def handler(request):
            if request.method == "GET":
                return httpx.Response(200, json={"data": [{
                    "id": "vendor/model:free", "pricing": {"prompt": "0", "completion": "0"}
                }]})
            requests.append(json.loads(request.content))
            return httpx.Response(200, json={"choices": [{"message": outputs.pop(0)}]})

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", b"Mayor: We will build a library.", ".txt")
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                result, content_fallback = await asyncio.gather(
                    extract_with_model(
                        client, "test-key", ["vendor/model:free"], root=root,
                        promise_id="P1", path=saved["path"], digest=saved["sha256"],
                        source_url="https://sf.gov/news/example",
                    ),
                    extract_with_model(
                    client, "test-key", ["vendor/model:free"], root=root,
                    promise_id="P1", path=saved["path"], digest=saved["sha256"],
                    source_url="https://sf.gov/news/example",
                    ),
                )
        self.assertEqual(result[0].promise_text, "Mayor: We will build a library.")
        self.assertEqual(content_fallback[0].promise_text, "We will build a library.")
        self.assertEqual(requests[0]["model"], "vendor/model:free")
        self.assertIn("We will build a library.", requests[0]["messages"][1]["content"])
        self.assertEqual(
            requests[0]["tool_choice"]["function"]["name"],
            "record_promise_evidence",
        )
        self.assertEqual(
            requests[0]["tools"][0]["function"]["parameters"],
            requests[1]["tools"][0]["function"]["parameters"],
        )
        self.assertEqual(requests[0]["max_tokens"], 4096)
        self.assertEqual(requests[0]["temperature"], 0)

    def test_bad_segment_and_unrelated_approximate_quote_are_rejected(self):
        source = "We will build a library. Another sentence."
        segments = _source_segments(source)
        with self.assertRaises(ValueError):
            _materialize_quotes(json.dumps({"candidates": [{"quote_segment_id": -1}]}),
                                source, segments)
        with self.assertRaises(QuoteNotFound):
            _materialize_quotes(json.dumps({"candidates": [{
                "promise_text": "We will close the public library forever."
            }]}), source, segments)
        with self.assertRaises(QuoteNotFound):
            _materialize_quotes(json.dumps({"candidates": [{
                "promise_text": "We will build a library in 2028."
            }]}), "We will build a library in 2027.",
               _source_segments("We will build a library in 2027."))

    def test_approximate_quote_snaps_to_source_segment(self):
        source = "We will build a public library by 2027."
        response = json.dumps({"candidates": [{
            "promise_text": "We will build a public library by 2027!"
        }]})
        result = json.loads(_materialize_quotes(response, source, _source_segments(source)))
        self.assertEqual(result["candidates"][0]["promise_text"], source)

    async def test_future_promise_date_retries_once_without_replacing_it(self):
        requests = []
        proposed_dates = ["2027-01-01", "2024-01-01"]

        async def completion(messages, **_kwargs):
            requests.append(messages)
            candidate = {"promise_id": "P1", "quote_segment_id": 0, "speaker": None,
                         "promised_date": proposed_dates.pop(0), "deadline": "2027-12-31"}
            return {"choices": [{"message": {"content": json.dumps({"candidates": [candidate]})}}]}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", b"We will build a library.", ".txt")
            result = await extract_with_model(
                None, None, [], root=root, promise_id="P1", path=saved["path"],
                digest=saved["sha256"], source_url="https://sf.gov/example",
                completion=completion, published=date(2024, 2, 1),
            )
        self.assertEqual(result[0].promised_date, date(2024, 1, 1))
        self.assertEqual(len(requests), 2)
        self.assertIn("2024-02-01", requests[0][1]["content"])

    async def test_future_promise_date_after_retry_is_rejected(self):
        calls = []

        async def completion(_messages, **_kwargs):
            calls.append(1)
            candidate = {"promise_id": "P1", "quote_segment_id": 0, "speaker": None,
                         "promised_date": "2027-01-01", "deadline": None}
            return {"choices": [{"message": {"content": json.dumps({"candidates": [candidate]})}}]}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", b"We will build a library.", ".txt")
            with self.assertRaises(InvalidPromiseDate):
                await extract_with_model(
                    None, None, [], root=root, promise_id="P1", path=saved["path"],
                    digest=saved["sha256"], source_url="https://sf.gov/example",
                    completion=completion, published=date(2024, 2, 1),
                )
        self.assertEqual(len(calls), 2)

    async def test_empty_model_response_is_retried_then_blocked(self):
        calls = []

        async def completion(_messages, **_kwargs):
            calls.append(1)
            return {"choices": [{"message": {"content": None}}]}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", b"We will build a library.", ".txt")
            with self.assertRaises(ModelResponseError):
                await extract_with_model(
                    None, None, [], root=root, promise_id="P1", path=saved["path"],
                    digest=saved["sha256"], source_url="https://sf.gov/example",
                    completion=completion, published=date(2024, 2, 1),
                )
        self.assertEqual(len(calls), 2)

    async def test_partial_promise_date_is_not_invented(self):
        calls = []

        async def completion(_messages, **_kwargs):
            calls.append(1)
            candidate = {"promise_id": "P1", "quote_segment_id": 0, "speaker": None,
                         "promised_date": "2024", "deadline": "2027"}
            return {"choices": [{"message": {"content": json.dumps({"candidates": [candidate]})}}]}

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", b"We will build a library.", ".txt")
            with self.assertRaises(InvalidPromiseDate):
                await extract_with_model(
                    None, None, [], root=root, promise_id="P1", path=saved["path"],
                    digest=saved["sha256"], source_url="https://sf.gov/example",
                    completion=completion, published=date(2024, 2, 1),
                )
        self.assertEqual(len(calls), 2)

    async def test_changed_source_is_rejected_before_network(self):
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(500)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            saved = archive_source(root, "P1", b"source", ".txt")
            Path(saved["path"]).write_text("changed")
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                with self.assertRaises(ValueError):
                    await extract_with_model(
                        client, "test-key", ["vendor/model:free"], root=root,
                        promise_id="P1", path=saved["path"], digest=saved["sha256"],
                        source_url="https://sf.gov/news/example",
                    )
        self.assertEqual(calls, [])
